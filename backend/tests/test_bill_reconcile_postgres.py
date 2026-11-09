"""Opt-in CU06 reconciliation tests; requires a dedicated migrated database.

Run only against an isolated synthetic database that contains no other bill
fixtures, because reconciliation fails closed when any referenced file is absent
from the single private volume.
"""

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from threading import Thread
from unittest.mock import patch
from uuid import uuid4

import test_api
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from test_reading_postgres import ReadingClient

from app.bill_files import locked_directory, publish, read
from app.bill_reconcile import reconcile_bills
from app.diary import BUENOS_AIRES
from app.models import Account
from app.security import hash_password

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


@unittest.skipUnless(os.environ.get("TEST_BILL_RECONCILE_DATABASE_URL"),
                     "Needs a dedicated migrated PostgreSQL database")
class BillReconcilePostgresTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.url = os.environ["TEST_BILL_RECONCILE_DATABASE_URL"]
        cls.engine = create_engine(cls.url)
        cls.username = f"reconcile-{uuid4()}"
        cls.password = "Synthetic-only-reconcile-password"
        with Session(cls.engine) as db:
            db.add(Account(username=cls.username, password_hash=hash_password(cls.password)))
            db.commit()

    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {"DATABASE_URL": self.url})
        self.clock = patch("app.api.now", return_value=datetime(2026, 5, 1, 12, tzinfo=BUENOS_AIRES))
        self.environment.start()
        self.clock.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.clock.stop)

    @classmethod
    def tearDownClass(cls) -> None:
        from app.db import get_engine
        with patch.dict(os.environ, {"DATABASE_URL": cls.url}):
            get_engine().dispose()
        cls.engine.dispose()

    async def login(self) -> test_api.Client:
        client = test_api.Client()
        self.assertEqual(await client.request("POST", "/login", {
            "username": self.username, "password": self.password,
        }), 200)
        client.csrf = test_api.string(client.data()["csrf_token"])
        return client

    async def test_reconcile_retains_live_files_and_removes_only_orphans(self) -> None:
        owner = await self.login()
        self.assertEqual(await owner.request(
            "POST", "/domiciles", {"display_address": "Synthetic reconcile address"}), 201)
        domicile = test_api.string(owner.data()["id"])
        self.assertEqual(await owner.request("POST", f"/domiciles/{domicile}/meters", {
            "meter_number": str(uuid4()), "alias": None,
        }), 201)
        meter = test_api.string(owner.data()["id"])
        client = ReadingClient(cookie=owner.cookie, csrf=owner.csrf)
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {"CU06_BILL_DIR": root}):
            self.assertEqual(await client.reading_request("POST", f"/meters/{meter}/bills", {
                "period_start": "2026-05-01", "period_end": "2026-05-31", "value_kwh": "10",
                "amount_ars": None, "file_base64": PNG, "overlap_token": None,
            }, str(uuid4())), 201)
            key = next(entry.name for entry in Path(root).iterdir() if entry.name.startswith("cu06-"))
            with locked_directory(root) as directory:
                expected = read(directory, key)
                # Models a rolled-back create, an unknown-commit candidate and a
                # publication that crashed before removing its temporary name.
                orphan = publish(directory, b"orphan-after-rollback")
                Path(root, "cu05-" + "d" * 32).write_bytes(b"cu05 synthetic")
                Path(root, ".cu06-" + "c" * 32 + ".tmp").write_bytes(b"crashed publication")
            failures: list[str] = []

            def reader() -> None:
                try:
                    for _ in range(20):
                        with locked_directory(root) as directory:
                            if read(directory, key) != expected:
                                failures.append("content changed")
                except Exception as error:
                    failures.append(type(error).__name__)

            thread = Thread(target=reader)
            thread.start()
            reconcile_bills()
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertTrue(Path(root, key).is_file())
            self.assertFalse(Path(root, orphan).exists())
            self.assertFalse(Path(root, ".cu06-" + "c" * 32 + ".tmp").exists())
            self.assertTrue(Path(root, "cu05-" + "d" * 32).is_file())

            # A missing referenced object must block every deletion.
            Path(root, key).unlink()
            with locked_directory(root) as directory:
                remaining = publish(directory, b"must-not-be-removed")
            reconcile_bills()
            self.assertTrue(Path(root, remaining).is_file())
            self.assertTrue(Path(root, "cu05-" + "d" * 32).is_file())
