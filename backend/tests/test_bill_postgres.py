"""Synthetic ASGI CU06 tests against an explicitly isolated PostgreSQL database."""

import asyncio
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import test_api
from test_reading_postgres import ReadingClient

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated migrated PostgreSQL")
class BillPostgresTests(test_api.ApiTests):
    async def prepare_bill_client(self) -> tuple[ReadingClient, str]:
        owner = await self.login()
        domicile = await self.domicile(owner)
        self.assertEqual(await owner.request("POST", f"/domiciles/{domicile}/meters", {
            "meter_number": str(uuid4()), "alias": None,
        }), 201)
        return ReadingClient(cookie=owner.cookie, csrf=owner.csrf), test_api.string(owner.data()["id"])

    def payload(self, start: str = "2026-03-01", end: str = "2026-03-31") -> dict[str, object]:
        return {"period_start": start, "period_end": end, "value_kwh": "10",
                "amount_ars": None, "file_base64": PNG, "overlap_token": None}

    async def test_concurrent_idempotent_replay_and_duplicate(self) -> None:
        client, meter = await self.prepare_bill_client()
        path, key, gate = f"/meters/{meter}/bills", str(uuid4()), Barrier(2)

        def same_key() -> tuple[int, dict[str, object]]:
            request = ReadingClient(cookie=client.cookie, csrf=client.csrf)
            gate.wait(timeout=10)
            return asyncio.run(request.reading_request("POST", path, self.payload(), key)), request.data()

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            first, second = await asyncio.gather(
                loop.run_in_executor(executor, same_key),
                loop.run_in_executor(executor, same_key))
        self.assertEqual((first[0], second[0]), (201, 201))
        self.assertEqual(first[1], second[1])

        other, gate = "2026-04-01", Barrier(2)

        def distinct_keys() -> int:
            request = ReadingClient(cookie=client.cookie, csrf=client.csrf)
            gate.wait(timeout=10)
            return asyncio.run(request.reading_request(
                "POST", path, self.payload(other, "2026-04-30"), str(uuid4())))

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = await asyncio.gather(
                loop.run_in_executor(executor, distinct_keys),
                loop.run_in_executor(executor, distinct_keys))
        self.assertCountEqual(results, [201, 409])

    async def test_concurrent_edits_advance_version_once(self) -> None:
        client, meter = await self.prepare_bill_client()
        path = f"/meters/{meter}/bills"
        self.assertEqual(await client.reading_request("POST", path, self.payload(), str(uuid4())), 201)
        bill = client.data()
        target, gate = f"{path}/{bill['id']}", Barrier(2)

        def edit(value: str) -> int:
            request = ReadingClient(cookie=client.cookie, csrf=client.csrf)
            gate.wait(timeout=10)
            return asyncio.run(request.reading_request("PATCH", target, {
                **self.payload(), "value_kwh": value, "version": 1,
                "file_action": "keep", "file_base64": None}))

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = await asyncio.gather(
                loop.run_in_executor(executor, edit, "11"),
                loop.run_in_executor(executor, edit, "12"))
        self.assertCountEqual(results, [200, 409])
        self.assertEqual(await client.reading_request("GET", target, None), 200)
        self.assertEqual(client.data()["version"], 2)

    async def test_bill_isolation_duplicate_overlap_edit_and_file(self) -> None:
        owner = await self.login()
        foreign = await self.login(self.username_b)
        domicile = await self.domicile(owner)
        self.assertEqual(await owner.request("POST", f"/domiciles/{domicile}/meters", {
            "meter_number": str(uuid4()), "alias": None,
        }), 201)
        meter = test_api.string(owner.data()["id"])
        client = ReadingClient(cookie=owner.cookie, csrf=owner.csrf)
        path = f"/meters/{meter}/bills"
        payload = {"period_start": "2026-01-01", "period_end": "2026-01-31",
                   "value_kwh": "123.125", "amount_ars": None,
                   "file_base64": PNG, "overlap_token": None}
        key = str(uuid4())
        self.assertEqual(await client.reading_request("POST", path, payload, key), 201)
        bill = client.data()
        target = f"{path}/{bill['id']}"
        self.assertEqual(await client.reading_request("POST", path, payload, key), 201)
        self.assertEqual(client.data(), bill)
        self.assertEqual(await client.reading_request("POST", path, payload, str(uuid4())), 409)
        self.assertEqual(client.data()["code"], "DUPLICATE_BILL")
        edit = {**payload, "value_kwh": "124", "version": 1,
                "file_action": "keep", "file_base64": None}
        self.assertEqual(await client.reading_request("PATCH", target, edit), 200)
        self.assertEqual(client.data()["version"], 2)
        self.assertEqual(await client.reading_request("PATCH", target, edit), 409)
        self.assertEqual(client.data()["code"], "VERSION_CONFLICT")
        overlap = {**payload, "period_start": "2026-01-31", "period_end": "2026-02-28"}
        self.assertEqual(await client.reading_request("POST", path, overlap, str(uuid4())), 409)
        warning = client.data()
        self.assertEqual(warning["code"], "OVERLAP_CONFIRMATION_REQUIRED")
        overlap["overlap_token"] = test_api.string(warning["overlap_token"])
        self.assertEqual(await client.reading_request("POST", path, overlap, str(uuid4())), 201)
        self.assertEqual(await owner.request("GET", f"{target}/file"), 200)
        self.assertEqual(owner.headers[b"content-disposition"], b'attachment; filename="bill"')
        self.assertEqual(await foreign.request("GET", f"{target}/file"), 404)
        self.assertEqual(await foreign.request("GET", path), 404)
        self.assertEqual(await owner.request("PATCH", target, edit, csrf=False), 403)
