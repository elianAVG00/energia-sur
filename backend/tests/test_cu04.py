"""CU04 contract and real PostgreSQL optimistic-concurrency regressions."""

import asyncio
import importlib
import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from uuid import uuid4

import test_api
from alembic.migration import MigrationContext
from alembic.operations import Operations
from psycopg import Cursor
from psycopg.errors import CheckViolation
from sqlalchemy import create_engine, event, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app import management
from app.db import get_engine
from app.models import Domicile, Meter


class Cu04Tests(test_api.ApiTests):
    async def check_meter_write_error(self, *, constraint: bool) -> None:
        owner = await self.login()
        domicile = await self.domicile(owner)
        base = f"/domiciles/{domicile}/meters"
        self.assertEqual(await owner.request("POST", base, {
            "meter_number": str(uuid4()), "alias": "Original",
        }), 201)
        before = owner.data()
        meter_id = test_api.string(before["id"])
        path = f"{base}/{meter_id}"
        engine = get_engine()
        attempted = False
        observed_constraint = None

        def fail_write(conn: object, cursor: Cursor[tuple[object, ...]], statement: str, parameters: object,
                       context: object, executemany: bool) -> None:
            nonlocal attempted, observed_constraint
            if statement.startswith("UPDATE es_meters"):
                attempted = True
                if constraint:
                    # Produce a real PostgreSQL ck_meter_version violation on this
                    # request's connection, not the duplicate-number index.
                    try:
                        cursor.execute("UPDATE es_meters SET version = 0 WHERE id = %s", (meter_id,))
                    except CheckViolation as error:
                        observed_constraint = error.diag.constraint_name
                        raise
                else:
                    raise SQLAlchemyError("Synthetic internal failure; must not reach the client")

        event.listen(engine, "before_cursor_execute", fail_write)
        try:
            status = await owner.request("PATCH", path, {
                "meter_number": "Changed", "alias": "Changed", "version": before["version"],
            })
        finally:
            event.remove(engine, "before_cursor_execute", fail_write)
        self.assertTrue(attempted)
        if constraint:
            self.assertEqual(observed_constraint, "ck_meter_version")
        self.assertEqual(status, 503)
        self.assertEqual(owner.data(), {"detail": "El servicio no está disponible temporalmente."})
        self.assertEqual(owner.headers[b"cache-control"], b"no-store")
        self.assertEqual(await owner.request("GET", path), 200)
        self.assertEqual(owner.data(), before)

    async def test_meter_sqlalchemy_failure_is_sanitized_and_atomic(self) -> None:
        await self.check_meter_write_error(constraint=False)

    async def test_meter_nonduplicate_integrity_failure_is_sanitized_and_atomic(self) -> None:
        await self.check_meter_write_error(constraint=True)

    async def test_stale_noop_matches_current_values_for_both_resources(self) -> None:
        owner = await self.login()
        domicile = await self.domicile(owner)
        base = f"/domiciles/{domicile}"
        number = str(uuid4())
        self.assertEqual(await owner.request("POST", base + "/meters", {
            "meter_number": number, "alias": None,
        }), 201)
        meter_path = base + "/meters/" + test_api.string(owner.data()["id"])
        for path, payload in (
            (base, {"display_address": "Synthetic own address", "version": 1}),
            (meter_path, {"meter_number": number, "alias": None, "version": 1}),
        ):
            self.assertEqual(await owner.request("PATCH", path, payload), 200)
            self.assertEqual(owner.data()["version"], 2)
            self.assertEqual(await owner.request("PATCH", path, payload), 409)
            self.assertEqual(owner.data()["code"], "VERSION_CONFLICT")
            read_path = path + "/management" if path == base else path
            self.assertEqual(await owner.request("GET", read_path), 200)
            self.assertEqual(owner.data()["version"], 2)
            for key, value in payload.items():
                if key != "version":
                    self.assertEqual(owner.data()[key], value)

    async def test_contract_security_validation_and_history(self) -> None:
        owner, foreign = await self.login(), await self.login(self.username_b)
        domicile = await self.domicile(owner)
        other = await self.domicile(owner)
        foreign_domicile = await self.domicile(foreign)
        cut = await self.cut(owner, domicile)
        base = f"/domiciles/{domicile}"
        self.assertEqual(await owner.request("GET", base + "/management"), 200)
        self.assertEqual(owner.data()["version"], 1)
        self.assertEqual(await owner.request("GET", base + "/meters"), 200)
        self.assertEqual(json.loads(owner.content), [])
        for value in ("", "  ", "é", "a\n", "a\x00", "a\x7f", "a" * 121):
            self.assertEqual(await owner.request("POST", base + "/meters", {
                "meter_number": value,
            }), 422)
        for alias in ("a\n", "a\x00", "a" * 121):
            self.assertEqual(await owner.request("POST", base + "/meters", {
                "meter_number": "valid", "alias": alias,
            }), 422)
        number = f"{uuid4()}-Ab"
        self.assertEqual(await owner.request("POST", base + "/meters", {
            "meter_number": f"  {number}  ", "alias": " Medidor eléctrico ",
        }), 201)
        created = owner.data()
        self.assertEqual(created["meter_number"], number)
        self.assertEqual(created["alias"], "Medidor eléctrico")
        meter_id = test_api.string(created["id"])
        meter_path = base + "/meters/" + meter_id
        self.assertEqual(await owner.request("POST", f"/domiciles/{other}/meters", {
            "meter_number": number.lower(),
        }), 409)
        self.assertEqual(owner.data()["code"], "DUPLICATE_METER")
        self.assertEqual(await foreign.request("POST", f"/domiciles/{foreign_domicile}/meters", {
            "meter_number": number.lower(),
        }), 201)
        for method, path, body in (
            ("GET", base + "/management", None),
            ("PATCH", base, {"display_address": "new", "version": 1}),
            ("GET", base + "/meters", None),
            ("POST", base + "/meters", {"meter_number": "other"}),
            ("GET", meter_path, None),
            ("PATCH", meter_path, {"meter_number": "other", "alias": None, "version": 1}),
            ("GET", f"/domiciles/{foreign_domicile}/meters/{meter_id}", None),
        ):
            self.assertEqual(await foreign.request(method, path, body), 404)
            self.assertEqual(foreign.data(), {"detail": "El recurso no está disponible."})
        for path, payload in (
            (base, {"display_address": "new", "version": 1}),
            (meter_path, {"meter_number": number, "alias": None, "version": 1}),
        ):
            self.assertEqual(await owner.request("PATCH", path, payload, csrf=False), 403)
            self.assertEqual(await owner.request("PATCH", path, payload, origin="https://invalid.example"), 403)
        self.assertEqual(await owner.request("POST", base + "/meters", {
            "meter_number": "not-created",
        }, csrf=False), 403)
        self.assertEqual(await owner.request("POST", base + "/meters", {
            "meter_number": "not-created",
        }, origin="https://invalid.example"), 403)
        for invalid_version in (True, 0, "1"):
            self.assertEqual(await owner.request("PATCH", base, {
                "display_address": "new", "version": invalid_version,
            }), 422)
        self.assertEqual(await owner.request("PATCH", base, {
            "display_address": "New synthetic address", "version": 1,
        }), 200)
        self.assertEqual(owner.data()["version"], 2)
        self.assertEqual(await owner.request("GET", base + "/interruptions"), 200)
        self.assertEqual(json.loads(owner.content)[0]["id"], cut["id"])
        self.assertEqual(await owner.request("GET", "/domiciles"), 200)
        rows = json.loads(owner.content)
        self.assertTrue(all(set(row) == {"id", "display_address"} for row in rows))

    async def test_atomic_versions_and_duplicate_rollback(self) -> None:
        owner = await self.login()
        domicile = await self.domicile(owner)
        base = f"/domiciles/{domicile}"
        number = str(uuid4())
        self.assertEqual(await owner.request("POST", base + "/meters", {"meter_number": number}), 201)
        meter_id = test_api.string(owner.data()["id"])
        meter_path = base + "/meters/" + meter_id
        self.assertEqual(await owner.request("POST", base + "/meters", {"meter_number": number + "x"}), 201)
        for path, original, changed in (
            (base, {"display_address": "Synthetic own address"}, {"display_address": "Changed"}),
            (meter_path, {"meter_number": number, "alias": None},
             {"meter_number": number, "alias": "Changed"}),
        ):
            self.assertEqual(await owner.request("PATCH", path, {**changed, "version": 1}), 200)
            self.assertEqual(owner.data()["version"], 2)
            self.assertEqual(await owner.request("PATCH", path, {**changed, "version": 2}), 200)
            self.assertEqual(owner.data()["version"], 3)
            for stale in (changed, original):
                self.assertEqual(await owner.request("PATCH", path, {**stale, "version": 1}), 409)
                self.assertEqual(owner.data()["code"], "VERSION_CONFLICT")
            self.assertEqual(await owner.request("PATCH", path + "-missing", {**changed, "version": 3}), 404)
        self.assertEqual(await owner.request("PATCH", meter_path, {
            "meter_number": number + "x", "alias": "must roll back", "version": 3,
        }), 409)
        self.assertEqual(owner.data()["code"], "DUPLICATE_METER")
        self.assertEqual(await owner.request("GET", meter_path), 200)
        self.assertEqual((owner.data()["meter_number"], owner.data()["alias"], owner.data()["version"]),
                         (number, "Changed", 3))

    async def test_independent_connection_competing_patches(self) -> None:
        owner = await self.login()
        domicile = await self.domicile(owner)
        base = f"/domiciles/{domicile}"
        number = str(uuid4())
        self.assertEqual(await owner.request("POST", base + "/meters", {"meter_number": number}), 201)
        meter_id = test_api.string(owner.data()["id"])
        with Session(self.engine) as db:
            account_id = db.scalar(select(Domicile.account_id).where(Domicile.id == domicile))
        self.assertIsNotNone(account_id)
        assert account_id is not None

        def compete(kind: str) -> list[str]:
            barrier = Barrier(2)
            def worker(value: str) -> str:
                with Session(self.engine) as db:
                    db.connection()
                    barrier.wait(timeout=10)
                    try:
                        if kind == "domicile":
                            management.correct_domicile(db, account_id, domicile, value, 1)
                        else:
                            management.correct_meter(db, account_id, domicile, meter_id, number, value, 1)
                        return "success"
                    except management.VersionConflict:
                        return "conflict"
            with ThreadPoolExecutor(max_workers=2) as pool:
                return list(pool.map(worker, ["first", "second"]))

        for kind in ("domicile", "meter"):
            self.assertCountEqual(await asyncio.to_thread(compete, kind), ["success", "conflict"])
        with Session(self.engine) as db:
            self.assertEqual(db.get(Domicile, domicile).version, 2)
            self.assertEqual(db.get(Meter, meter_id).version, 2)

    async def test_composite_foreign_key(self) -> None:
        owner, foreign = await self.login(), await self.login(self.username_b)
        domicile, other = await self.domicile(owner), await self.domicile(foreign)
        with Session(self.engine) as db:
            foreign_account = db.scalar(select(Domicile.account_id).where(Domicile.id == other))
            db.add(Meter(domicile_id=domicile, account_id=foreign_account,
                         meter_number=str(uuid4()), alias=None))
            with self.assertRaises(IntegrityError):
                db.commit()
            db.rollback()

    async def test_concurrent_creates_and_changed_before_old_value(self) -> None:
        owner = await self.login()
        domicile = await self.domicile(owner)
        base = f"/domiciles/{domicile}"
        number = str(uuid4())
        self.assertEqual(await owner.request("POST", base + "/meters", {"meter_number": number}), 201)
        meter_id = test_api.string(owner.data()["id"])
        with Session(self.engine) as db:
            account_id = db.scalar(select(Domicile.account_id).where(Domicile.id == domicile))
        assert account_id is not None

        def concurrent_creates() -> list[str]:
            barrier = Barrier(2)
            def worker(value: str) -> str:
                with Session(self.engine) as db:
                    db.connection()
                    barrier.wait(timeout=10)
                    try:
                        management.create_meter(db, account_id, domicile, value, None)
                        return "success"
                    except management.DuplicateMeter:
                        return "duplicate"
            with ThreadPoolExecutor(max_workers=2) as pool:
                return list(pool.map(worker, [number + "Z", number + "z"]))

        self.assertCountEqual(await asyncio.to_thread(concurrent_creates), ["success", "duplicate"])

        def race(kind: str) -> None:
            changed = Event()
            release = Event()

            def writer() -> None:
                with Session(self.engine) as db:
                    if kind == "domicile":
                        db.execute(update(Domicile).where(Domicile.id == domicile).values(
                            display_address="Committed change", version=Domicile.version + 1))
                    else:
                        db.execute(update(Meter).where(Meter.id == meter_id).values(
                            alias="Committed change", version=Meter.version + 1))
                    changed.set()
                    if not release.wait(timeout=10):
                        raise AssertionError("Old-value writer did not start")
                    db.commit()

            def stale() -> str:
                if not changed.wait(timeout=10):
                    raise AssertionError("Changed writer did not start")
                with Session(self.engine) as db:
                    db.connection()
                    release.set()
                    try:
                        if kind == "domicile":
                            management.correct_domicile(db, account_id, domicile,
                                                        "Synthetic own address", 1)
                        else:
                            management.correct_meter(db, account_id, domicile, meter_id,
                                                     number, None, 1)
                    except management.VersionConflict:
                        return "conflict"
                    return "unexpected success"

            with ThreadPoolExecutor(max_workers=2) as pool:
                first, second = pool.submit(writer), pool.submit(stale)
                first.result(timeout=15)
                self.assertEqual(second.result(timeout=15), "conflict")

        for kind in ("domicile", "meter"):
            await asyncio.to_thread(race, kind)
        with Session(self.engine) as db:
            home = db.get(Domicile, domicile)
            device = db.get(Meter, meter_id)
            self.assertIsNotNone(home)
            self.assertIsNotNone(device)
            assert home is not None and device is not None
            self.assertEqual((home.display_address, home.version), ("Committed change", 2))
            self.assertEqual((device.alias, device.version), ("Committed change", 2))

    async def test_concurrent_meter_edits_to_same_number(self) -> None:
        owner = await self.login()
        domicile = await self.domicile(owner)
        base = f"/domiciles/{domicile}/meters"
        identifiers = []
        for _ in range(2):
            self.assertEqual(await owner.request("POST", base, {"meter_number": str(uuid4())}), 201)
            identifiers.append(test_api.string(owner.data()["id"]))
        with Session(self.engine) as db:
            account_id = db.scalar(select(Domicile.account_id).where(Domicile.id == domicile))
        assert account_id is not None
        target = str(uuid4()) + "Ab"

        def compete() -> list[str]:
            barrier = Barrier(2)

            def worker(index: int) -> str:
                with Session(self.engine) as db:
                    db.connection()
                    barrier.wait(timeout=10)
                    try:
                        management.correct_meter(db, account_id, domicile, identifiers[index],
                                                 target if index == 0 else target.lower(), None, 1)
                        return "success"
                    except management.DuplicateMeter:
                        return "duplicate"

            with ThreadPoolExecutor(max_workers=2) as pool:
                return list(pool.map(worker, range(2)))

        self.assertCountEqual(await asyncio.to_thread(compete), ["success", "duplicate"])
        with Session(self.engine) as db:
            rows = list(db.scalars(select(Meter).where(Meter.id.in_(identifiers))))
            self.assertCountEqual([row.version for row in rows], [1, 2])

    async def test_failed_domicile_write_rolls_back(self) -> None:
        owner = await self.login()
        domicile = await self.domicile(owner)
        with Session(self.engine) as db:
            home = db.get(Domicile, domicile)
            assert home is not None
            account_id = home.account_id
            connection = db.connection()

            def fail_write(conn: object, cursor: object, statement: str, parameters: object,
                           context: object, executemany: bool) -> None:
                if statement.startswith("UPDATE es_domiciles"):
                    raise SQLAlchemyError("Synthetic write failure")

            event.listen(connection, "before_cursor_execute", fail_write)
            with self.assertRaises(SQLAlchemyError):
                management.correct_domicile(db, account_id, domicile, "Not saved", 1)
        with Session(self.engine) as db:
            home = db.get(Domicile, domicile)
            assert home is not None
            self.assertEqual((home.display_address, home.version), ("Synthetic own address", 1))


@unittest.skipUnless(
    os.environ.get("TEST_DATABASE_URL") and os.environ.get("TEST_CU04_MIGRATION") == "1",
    "Needs an isolated synthetic PostgreSQL database with CREATE SCHEMA permission",
)
class PopulatedMigrationTests(unittest.TestCase):
    def test_additive_upgrade_from_populated_0001(self) -> None:
        engine = create_engine(os.environ["TEST_DATABASE_URL"])
        schema = "cu04_migration_" + uuid4().hex
        try:
            with engine.begin() as connection:
                # Generated hexadecimal identifier; the synthetic schema is retained.
                connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
                connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
                context = MigrationContext.configure(connection)
                with Operations.context(context):
                    importlib.import_module("migrations.versions.0001_cu09").upgrade()
                    connection.execute(text(
                        "INSERT INTO es_accounts (id, username, password_hash) "
                        "VALUES ('account', 'synthetic', 'synthetic')"
                    ))
                    connection.execute(text(
                        "INSERT INTO es_domiciles (id, account_id, display_address) "
                        "VALUES ('domicile', 'account', 'Synthetic address')"
                    ))
                    connection.execute(text(
                        "INSERT INTO es_interruptions (id, domicile_id, start_at, version) "
                        "VALUES ('cut', 'domicile', '2026-01-01T00:00:00Z', 1)"
                    ))
                    importlib.import_module("migrations.versions.0002_cu04").upgrade()
                row = connection.execute(text(
                    "SELECT d.id, d.account_id, d.display_address, d.version, i.id, i.domicile_id "
                    "FROM es_domiciles d JOIN es_interruptions i ON i.domicile_id = d.id"
                )).one()
                self.assertEqual(tuple(row), ("domicile", "account", "Synthetic address", 1,
                                              "cut", "domicile"))
                self.assertEqual(connection.scalar(text("SELECT count(*) FROM es_meters")), 0)
        finally:
            engine.dispose()
