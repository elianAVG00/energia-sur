"""Isolated tests of CU05 replay logic; real PostgreSQL remains necessary."""

import unittest
from datetime import UTC, datetime
from unittest.mock import Mock

from sqlalchemy.orm import Session

from app import readings
from app.db import DatabaseUnavailable
from app.management import MissingResource
from app.models import ReadingCreation
from app.reading_store import (
    IdempotencyKeyReused,
    create_reading,
    prepare_creation,
    stage_creation,
    validate_key,
)

KEY = "12345678-1234-4234-8234-123456789abc"
WHEN = "2026-01-01T00:00:00Z"
NOW = datetime(2026, 1, 2, tzinfo=UTC)


class ReadingStoreTest(unittest.TestCase):
    def database(self) -> Mock:
        db = Mock(spec=Session)
        db.connection.return_value.get_isolation_level.return_value = "READ COMMITTED"
        db.connection.return_value.in_nested_transaction.return_value = False
        db.in_nested_transaction.return_value = False
        return db

    def call(self, db: Session, value: str = "001") -> dict[str, object]:
        return create_reading(
            db, account_id="account", meter_id="meter", key=KEY, recorded_at=WHEN,
            value_kwh=value, photo=None, photo_key=None, photo_type=None, now=NOW,
        )

    def test_canonical_uuid(self) -> None:
        self.assertEqual(validate_key(KEY), KEY)
        for value in ("bad", KEY.upper(), "{" + KEY + "}"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_key(value)

    def test_new_creation_stages_both_rows_without_committing(self) -> None:
        db = self.database()
        db.scalar.return_value = object()
        db.get.return_value = None
        result = self.call(db)
        self.assertEqual(result["value_kwh"], "1")
        self.assertEqual(db.add.call_count, 2)
        self.assertEqual(db.flush.call_count, 2)
        db.commit.assert_not_called()

    def test_identical_replay_and_changed_payload(self) -> None:
        db = self.database()
        db.scalar.return_value = object()
        db.get.return_value = ReadingCreation(
            account_id="account", meter_id="meter", idempotency_key=KEY,
            fingerprint=readings.creation_fingerprint(WHEN, "001", None),
            reading_id="reading", response={"id": "reading"},
        )
        self.assertEqual(self.call(db), {"id": "reading"})
        db.add.assert_not_called()
        with self.assertRaises(IdempotencyKeyReused):
            self.call(db, "1")

    def test_prepare_checks_replay_before_any_staging(self) -> None:
        db = self.database()
        db.scalar.return_value = object()
        db.get.return_value = ReadingCreation(
            account_id="account", meter_id="meter", idempotency_key=KEY,
            fingerprint=readings.creation_fingerprint(WHEN, "001", b"photo"),
            reading_id="reading", response={"id": "reading"},
        )
        prepared, replay = prepare_creation(
            db, account_id="account", meter_id="meter", key=KEY, recorded_at=WHEN,
            value_kwh="001", photo=b"photo",
        )
        self.assertEqual(replay, {"id": "reading"})
        self.assertTrue(prepared.has_photo)
        db.add.assert_not_called()

    def test_new_photo_is_staged_after_prepare(self) -> None:
        db = self.database()
        db.scalar.return_value = object()
        db.get.return_value = None
        prepared, replay = prepare_creation(
            db, account_id="account", meter_id="meter", key=KEY, recorded_at=WHEN,
            value_kwh="001", photo=b"photo",
        )
        self.assertIsNone(replay)
        db.add.assert_not_called()
        result = stage_creation(db, prepared=prepared, photo_key="opaque", photo_type="image/png", now=NOW)
        self.assertTrue(result["has_photo"])
        self.assertEqual(db.add.call_count, 2)

    def test_staging_refuses_a_different_transaction(self) -> None:
        db = self.database()
        db.scalar.return_value = object()
        db.get.return_value = None
        prepared, replay = prepare_creation(
            db, account_id="account", meter_id="meter", key=KEY, recorded_at=WHEN,
            value_kwh="001", photo=b"photo",
        )
        self.assertIsNone(replay)
        db.get_transaction.return_value = Mock()
        with self.assertRaises(RuntimeError):
            stage_creation(db, prepared=prepared, photo_key="opaque", photo_type="image/png", now=NOW)
        db.add.assert_not_called()

    def test_nested_transaction_is_rejected(self) -> None:
        db = self.database()
        db.in_nested_transaction.return_value = True
        with self.assertRaises(RuntimeError):
            self.call(db)
        db.add.assert_not_called()

    def test_owner_is_checked_before_lookup(self) -> None:
        db = self.database()
        db.scalar.return_value = None
        with self.assertRaises(MissingResource):
            self.call(db)
        db.get.assert_not_called()
        with self.assertRaises(MissingResource):
            create_reading(
                db, account_id="foreign", meter_id="meter", key="invalid", recorded_at="invalid",
                value_kwh="invalid", photo=None, photo_key=None, photo_type=None, now=NOW,
            )
        db.add.assert_not_called()

    def test_unsupported_transaction_isolation_fails_closed(self) -> None:
        db = self.database()
        db.scalar.return_value = object()
        db.connection.return_value.get_isolation_level.return_value = "REPEATABLE READ"
        with self.assertRaises(DatabaseUnavailable):
            self.call(db)
        db.get.assert_not_called()
        db.add.assert_not_called()

    def test_replay_is_not_revalidated_against_a_changed_clock(self) -> None:
        db = self.database()
        db.scalar.return_value = object()
        db.get.return_value = ReadingCreation(
            account_id="account", meter_id="meter", idempotency_key=KEY,
            fingerprint=readings.creation_fingerprint(WHEN, "001", None),
            reading_id="reading", response={"id": "reading"},
        )
        result = create_reading(
            db, account_id="account", meter_id="meter", key=KEY, recorded_at=WHEN,
            value_kwh="001", photo=None, photo_key=None, photo_type=None,
            now=datetime(2025, 1, 1, tzinfo=UTC),
        )
        self.assertEqual(result, {"id": "reading"})
        db.add.assert_not_called()

    def test_rejects_unmatched_photo_metadata(self) -> None:
        db = self.database()
        db.scalar.return_value = object()
        db.get.return_value = None
        with self.assertRaises(ValueError):
            create_reading(
                db, account_id="account", meter_id="meter", key=KEY, recorded_at=WHEN,
                value_kwh="1", photo=b"synthetic", photo_key=None, photo_type=None, now=NOW,
            )
        db.add.assert_not_called()
        for photo, photo_key, photo_type in (
            (None, "key", None), (None, None, "image/png"),
            (b"synthetic", "key", None), (b"synthetic", None, "image/png"),
        ):
            with self.subTest(photo=photo, photo_key=photo_key, photo_type=photo_type):
                with self.assertRaises(ValueError):
                    create_reading(
                        db, account_id="account", meter_id="meter", key=KEY, recorded_at=WHEN,
                        value_kwh="1", photo=photo, photo_key=photo_key, photo_type=photo_type,
                        now=NOW,
                    )
        db.add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
