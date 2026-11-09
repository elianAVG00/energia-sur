"""Verify CU05 additive migration in a retained synthetic PostgreSQL schema."""

import importlib
import os
import unittest
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated PostgreSQL")
class ReadingMigrationPostgresTest(unittest.TestCase):
    def test_populated_upgrade_and_constraints(self) -> None:
        engine = create_engine(os.environ["TEST_DATABASE_URL"])
        schema = "cu05_migration_" + uuid4().hex
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
                connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
                context = MigrationContext.configure(connection)
                with Operations.context(context):
                    importlib.import_module("migrations.versions.0001_cu09").upgrade()
                    connection.execute(text("INSERT INTO es_accounts VALUES ('account', 'synthetic', 'hash')"))
                    connection.execute(text("INSERT INTO es_domiciles VALUES ('home', 'account', 'synthetic')"))
                    importlib.import_module("migrations.versions.0002_cu04").upgrade()
                    connection.execute(text(
                        "INSERT INTO es_meters (id, domicile_id, account_id, meter_number) "
                        "VALUES ('meter', 'home', 'account', 'synthetic')"
                    ))
                    importlib.import_module("migrations.versions.0003_cu05").upgrade()
                self.assertEqual(connection.scalar(text("SELECT count(*) FROM es_meters")), 1)
                insert = text(
                    "INSERT INTO es_meter_readings (id, meter_id, recorded_at, value_kwh) "
                    "VALUES (:id, 'meter', CAST(:instant AS timestamptz), CAST(:value AS numeric))"
                )
                connection.execute(insert, {"id": "valid", "instant": "2026-01-01T00:00:00Z", "value": "9" * 131072})
                self.assertEqual(connection.scalar(text("SELECT length(value_kwh::text) FROM es_meter_readings WHERE id='valid'")), 131072)
                for index, (instant, value) in enumerate((
                    ("2026-01-02T00:00:00Z", "NaN"),
                    ("2026-01-02T00:00:00Z", "Infinity"),
                    ("2026-01-02T00:00:00Z", "-1"),
                    ("2026-01-02T00:00:00Z", "1.5"),
                    ("infinity", "1"),
                )):
                    with self.subTest(instant=instant, value=value), self.assertRaises(IntegrityError):
                        with connection.begin_nested():
                            connection.execute(insert, {"id": f"invalid-{index}", "instant": instant, "value": value})
        finally:
            engine.dispose()
