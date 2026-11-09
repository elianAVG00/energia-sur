"""Synthetic CU05 private photo and OCR integration; needs isolated PostgreSQL.

Run with the persistent synthetic volume mounted at ``/photo-tests``::

    docker run ... -v cu05-photo-test-20261108:/photo-tests \
      -e CU05_PHOTO_DIR=/photo-tests -m unittest discover -s tests
"""

import base64
import json
import os
import unittest
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

import test_api
from PIL import Image
from sqlalchemy.exc import OperationalError
from test_reading_postgres import ReadingClient
from test_tesseract_engine import synthetic_digits

from app.db import dispose_engines
from app.ocr_worker import OCR_FALLBACK_MESSAGE
from app.photo_store import photo_directory, reconcile_photos


def synthetic_png(colour: tuple[int, int, int] = (20, 120, 30), size: tuple[int, int] = (18, 12)) -> bytes:
    stream = BytesIO()
    Image.new("RGB", size, colour).save(stream, format="PNG")
    return stream.getvalue()


def encoded(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class PhotoPostgresTests(test_api.ApiTests):
    def setUp(self) -> None:
        super().setUp()
        self.photos = patch.dict(os.environ, {"CU05_PHOTO_DIR": "/photo-tests"})
        self.photos.start()
        self.addCleanup(self.photos.stop)
        clock = patch("app.reading_api.now", return_value=datetime(2026, 11, 7, 15, tzinfo=UTC))
        clock.start()
        self.addCleanup(clock.stop)
        self.before = self.current_files()

    def current_files(self) -> set[str]:
        return {name for name in os.listdir(photo_directory()) if not name.startswith(".")}

    def new_files(self) -> list[str]:
        return sorted(self.current_files() - self.before)

    async def prepare(self) -> tuple[ReadingClient, str]:
        owner = await self.login()
        domicile = await self.domicile(owner)
        self.assertEqual(await owner.request("POST", f"/domiciles/{domicile}/meters", {
            "meter_number": str(uuid4()), "alias": None,
        }), 201)
        meter_id = test_api.string(owner.data()["id"])
        return ReadingClient(cookie=owner.cookie, csrf=owner.csrf), meter_id

    def payload(self, photo: bytes | None = None, value: str = "100",
                when: str = "2026-11-07T12:00:00-03:00") -> dict[str, object]:
        return {"recorded_at": when, "value_kwh": value, "confirmed": True,
                "photo_base64": encoded(photo) if photo is not None else None}

    async def test_create_retrieve_and_account_isolation(self) -> None:
        owner, meter_id = await self.prepare()
        photo = synthetic_png()
        path = f"/meters/{meter_id}/readings"
        self.assertEqual(await owner.reading_request("POST", path, self.payload(photo), str(uuid4())), 201)
        row = owner.data()
        self.assertIs(row["has_photo"], True)
        reading_id = test_api.string(row["id"])
        photo_path = f"{path}/{reading_id}/photo"
        self.assertEqual(await owner.reading_request("GET", photo_path, None), 200)
        self.assertEqual(owner.content, photo)
        self.assertEqual(owner.headers.get(b"content-type"), b"image/png")
        self.assertEqual(owner.headers.get(b"cache-control"), b"no-store")
        self.assertEqual(owner.headers.get(b"x-content-type-options"), b"nosniff")
        self.assertEqual(len(self.new_files()), 1)

        other = await self.login(self.username_b)
        stranger = ReadingClient(cookie=other.cookie, csrf=other.csrf)
        self.assertEqual(await stranger.reading_request("GET", photo_path, None), 404)
        self.assertEqual(await stranger.reading_request("GET", f"{path}/{reading_id}", None), 404)
        self.assertNotEqual(stranger.content, photo)
        self.assertEqual(await owner.reading_request("GET", f"{path}/{reading_id}", None), 200)
        self.assertIs(owner.data()["has_photo"], True)

    async def test_retry_replays_without_publishing_again(self) -> None:
        owner, meter_id = await self.prepare()
        path, key = f"/meters/{meter_id}/readings", str(uuid4())
        photo = synthetic_png()
        self.assertEqual(await owner.reading_request("POST", path, self.payload(photo), key), 201)
        first = owner.data()
        self.assertEqual(await owner.reading_request("POST", path, self.payload(photo), key), 201)
        self.assertEqual(owner.data(), first)
        self.assertEqual(len(self.new_files()), 1)

    async def test_replace_then_remove_keeps_one_object(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        first = synthetic_png((10, 10, 10))
        self.assertEqual(await owner.reading_request("POST", path, self.payload(first), str(uuid4())), 201)
        reading_id = test_api.string(owner.data()["id"])
        target = f"{path}/{reading_id}"
        second = synthetic_png((200, 20, 20))
        replace = {**self.payload(second), "version": 1, "photo_action": "replace"}
        self.assertEqual(await owner.reading_request("PATCH", target, replace), 200)
        self.assertEqual(owner.data()["version"], 2)
        self.assertEqual(await owner.reading_request("GET", f"{target}/photo", None), 200)
        self.assertEqual(owner.content, second)
        self.assertEqual(len(self.new_files()), 1)

        remove = {**self.payload(None), "version": 2, "photo_action": "remove"}
        self.assertEqual(await owner.reading_request("PATCH", target, remove), 200)
        self.assertIs(owner.data()["has_photo"], False)
        self.assertEqual(await owner.reading_request("GET", f"{target}/photo", None), 404)
        self.assertEqual(self.new_files(), [])

    async def test_definite_rejection_keeps_previous_photo(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        first = synthetic_png((10, 10, 10))
        self.assertEqual(await owner.reading_request("POST", path, self.payload(first), str(uuid4())), 201)
        reading_id = test_api.string(owner.data()["id"])
        target = f"{path}/{reading_id}"
        stale = {**self.payload(synthetic_png((200, 20, 20))), "version": 9, "photo_action": "replace"}
        self.assertEqual(await owner.reading_request("PATCH", target, stale), 409)
        self.assertEqual(owner.data()["code"], "VERSION_CONFLICT")
        self.assertEqual(await owner.reading_request("GET", f"{target}/photo", None), 200)
        self.assertEqual(owner.content, first)
        self.assertEqual(len(self.new_files()), 1)

    async def test_storage_failure_returns_sanitized_503_without_mutation(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        with patch("app.reading_api.publish_photo", side_effect=OSError("synthetic")):
            self.assertEqual(await owner.reading_request(
                "POST", path, self.payload(synthetic_png()), str(uuid4())), 503)
        self.assertEqual(owner.data()["detail"], "El servicio no está disponible temporalmente.")
        self.assertEqual(self.new_files(), [])
        self.assertEqual(await owner.reading_request("GET", path, None), 200)
        self.assertEqual(owner.content, b"[]")

    async def test_failed_publication_on_replace_keeps_the_previous_photo(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        first = synthetic_png((10, 10, 10))
        self.assertEqual(await owner.reading_request("POST", path, self.payload(first), str(uuid4())), 201)
        reading_id = test_api.string(owner.data()["id"])
        target = f"{path}/{reading_id}"
        replace = {**self.payload(synthetic_png((200, 20, 20))), "version": 1, "photo_action": "replace"}
        with patch("app.reading_api.publish_photo", side_effect=OSError("synthetic")):
            self.assertEqual(await owner.reading_request("PATCH", target, replace), 503)
        self.assertEqual(await owner.reading_request("GET", target, None), 200)
        self.assertEqual(owner.data()["version"], 1)
        self.assertEqual(await owner.reading_request("GET", f"{target}/photo", None), 200)
        self.assertEqual(owner.content, first)
        self.assertEqual(len(self.new_files()), 1)

    async def test_missing_stored_photo_is_unavailable_without_details(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        photo = synthetic_png()
        self.assertEqual(await owner.reading_request("POST", path, self.payload(photo), str(uuid4())), 201)
        reading_id = test_api.string(owner.data()["id"])
        photo_path = f"{path}/{reading_id}/photo"
        self.assertEqual(await owner.reading_request("GET", photo_path, None), 200)
        name = self.new_files()[0]
        os.unlink(os.path.join(photo_directory(), name))
        self.assertEqual(await owner.reading_request("GET", photo_path, None), 503)
        self.assertEqual(owner.data()["detail"], "El servicio no está disponible temporalmente.")
        # Restore the synthetic object so fail-closed reconciliation stays meaningful.
        with open(os.path.join(photo_directory(), name), "wb") as stream:
            stream.write(photo)

    async def test_misconfigured_photo_directory_is_503_for_create_edit_and_read(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        self.assertEqual(await owner.reading_request("POST", path, self.payload(synthetic_png()), str(uuid4())), 201)
        reading_id = test_api.string(owner.data()["id"])
        target = f"{path}/{reading_id}"
        replace = {**self.payload(synthetic_png((1, 2, 3))), "version": 1, "photo_action": "replace"}
        with patch.dict(os.environ, {"CU05_PHOTO_DIR": "relative-photos"}):
            self.assertEqual(await owner.reading_request(
                "POST", path, self.payload(synthetic_png()), str(uuid4())), 503)
            self.assertEqual(owner.data()["detail"], "El servicio no está disponible temporalmente.")
            self.assertEqual(await owner.reading_request("PATCH", target, replace), 503)
            self.assertEqual(await owner.reading_request("GET", f"{target}/photo", None), 503)
        # A configuration failure never removes or replaces the existing object.
        self.assertEqual(await owner.reading_request("GET", f"{target}/photo", None), 200)
        self.assertEqual(len(self.new_files()), 1)

    async def test_startup_logs_reconciliation_failure_without_leaking_paths(self) -> None:
        from app.main import app, lifespan

        with patch("app.main.reconcile_photos", side_effect=RuntimeError("/secret/photos")):
            with self.assertLogs("app.main", level="WARNING") as captured:
                async with lifespan(app):
                    pass
        self.assertEqual(len(captured.records), 1)
        self.assertIn("RuntimeError", captured.output[0])
        self.assertNotIn("/secret/photos", captured.output[0])

    async def test_indeterminate_commit_retains_both_until_reconciliation(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        first = synthetic_png((10, 10, 10))
        self.assertEqual(await owner.reading_request("POST", path, self.payload(first), str(uuid4())), 201)
        reading_id = test_api.string(owner.data()["id"])
        target = f"{path}/{reading_id}"
        second = synthetic_png((200, 20, 20))
        replace = {**self.payload(second), "version": 1, "photo_action": "replace"}
        with patch("app.photo_store.PhotoGuard.commit",
                   side_effect=OperationalError("synthetic", {}, Exception("lost"))):
            self.assertEqual(await owner.reading_request("PATCH", target, replace), 503)
        self.assertEqual(owner.data()["detail"], "El servicio no está disponible temporalmente.")
        self.assertEqual(len(self.new_files()), 2)
        self.assertEqual(await owner.reading_request("GET", f"{target}/photo", None), 200)
        self.assertEqual(owner.content, first)
        reconcile_photos()
        self.assertEqual(len(self.new_files()), 1)
        self.assertEqual(await owner.reading_request("GET", f"{target}/photo", None), 200)
        self.assertEqual(owner.content, first)

    async def test_invalid_image_crop_and_oversized_input(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        self.assertEqual(await owner.reading_request(
            "POST", path, {**self.payload(), "photo_base64": encoded(b"synthetic")}, str(uuid4())), 422)
        oversized = encoded(b"\x00" * 5_000_001)
        self.assertEqual(await owner.reading_request(
            "POST", path, {**self.payload(), "photo_base64": oversized}, str(uuid4())), 413)
        png = synthetic_png(size=(20, 10))
        ocr = f"{path}/ocr"
        self.assertEqual(await owner.reading_request(
            "POST", ocr, {"photo_base64": encoded(b"invalid"),
                          "crop": {"x": 0, "y": 0, "width": 10, "height": 10}}), 422)
        self.assertEqual(await owner.reading_request(
            "POST", ocr, {"photo_base64": encoded(png), "crop": {"x": 0, "y": 0, "width": 10, "height": 10}}), 200)
        self.assertEqual(owner.data(), {"status": "abstained", "value_kwh": None,
                                        "message": OCR_FALLBACK_MESSAGE})
        self.assertEqual(await owner.reading_request(
            "POST", ocr, {"photo_base64": encoded(png), "crop": {"x": 15, "y": 0, "width": 10, "height": 10}}), 422)
        self.assertEqual(await owner.reading_request(
            "POST", ocr, {"photo_base64": encoded(png), "crop": {"x": True, "y": 0, "width": 10, "height": 10}}), 422)
        self.assertEqual(await owner.reading_request(
            "POST", ocr, {"photo_base64": encoded(png), "crop": {"x": 0, "y": 0, "width": 10, "height": 10},
                          "extra": 1}), 422)

    async def test_ocr_real_engine_suggestion_does_not_save(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        image = synthetic_digits("56538")
        payload = {"photo_base64": encoded(image),
                   "crop": {"x": 0, "y": 0, "width": 500, "height": 120}}
        self.assertEqual(await owner.reading_request("POST", f"{path}/ocr", payload), 200)
        self.assertEqual(owner.data(), {"status": "suggested", "value_kwh": "56538"})
        self.assertEqual(await owner.reading_request("GET", path, None), 200)
        self.assertEqual(json.loads(owner.content), [])

    async def test_ocr_abstains_if_runtime_privacy_is_unverifiable(self) -> None:
        owner, meter_id = await self.prepare()
        payload = {"photo_base64": encoded(synthetic_digits("56538")),
                   "crop": {"x": 0, "y": 0, "width": 500, "height": 120}}
        with patch("app.reading_api.private_ocr_runtime", return_value=False):
            with patch("app.reading_api.recognize_region") as recognize:
                status = await owner.reading_request("POST", f"/meters/{meter_id}/readings/ocr", payload)
        self.assertEqual(status, 200)
        self.assertEqual(owner.data()["status"], "abstained")
        recognize.assert_not_called()

    async def test_foreign_meter_ocr_and_photo_are_indistinguishable(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        png = synthetic_png()
        self.assertEqual(await owner.reading_request("POST", path, self.payload(png), str(uuid4())), 201)
        reading_id = test_api.string(owner.data()["id"])
        other = await self.login(self.username_b)
        stranger = ReadingClient(cookie=other.cookie, csrf=other.csrf)
        ocr = {"photo_base64": encoded(png), "crop": {"x": 0, "y": 0, "width": 5, "height": 5}}
        self.assertEqual(await stranger.reading_request("POST", f"{path}/ocr", ocr), 404)
        self.assertEqual(stranger.data()["detail"], "El recurso no está disponible.")
        self.assertEqual(await stranger.reading_request(
            "GET", f"{path}/{reading_id}/photo", None), 404)
        self.assertEqual(stranger.data()["detail"], "El recurso no está disponible.")

    async def test_reconciliation_removes_only_unreferenced_objects(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        self.assertEqual(await owner.reading_request("POST", path, self.payload(synthetic_png()), str(uuid4())), 201)
        referenced = self.new_files()[0]
        orphan = "cu05-" + "b" * 32
        temporary = ".cu05-" + "c" * 32 + ".tmp"
        for name in (orphan, temporary):
            with open(os.path.join(photo_directory(), name), "wb") as stream:
                stream.write(b"synthetic")
        reconcile_photos()
        self.assertEqual(self.new_files(), [referenced])

    async def test_photo_survives_new_engine_and_session(self) -> None:
        owner, meter_id = await self.prepare()
        path = f"/meters/{meter_id}/readings"
        photo = synthetic_png()
        self.assertEqual(await owner.reading_request("POST", path, self.payload(photo), str(uuid4())), 201)
        reading_id = test_api.string(owner.data()["id"])
        photo_path = f"{path}/{reading_id}/photo"
        dispose_engines()
        self.assertEqual(await owner.reading_request("GET", photo_path, None), 200)
        self.assertEqual(owner.content, photo)


if __name__ == "__main__":
    unittest.main()
