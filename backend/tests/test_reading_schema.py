"""Static CU05 schema checks; these do not replace PostgreSQL integration tests."""

import importlib.util
import io
import unittest
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.schema import CreateTable

from app.models import Meter, MeterReading, ReadingCreation


class ReadingSchemaTest(unittest.TestCase):
    def test_models_include_owner_and_value_constraints(self) -> None:
        meter_constraints = {constraint.name for constraint in Meter.__table__.constraints}
        creation_constraints = {constraint.name for constraint in ReadingCreation.__table__.constraints}
        reading_constraints = {constraint.name for constraint in MeterReading.__table__.constraints}
        self.assertIn("uq_meter_id_account", meter_constraints)
        self.assertIn("fk_reading_creation_meter_owner", creation_constraints)
        self.assertIn("fk_reading_creation_reading_meter", creation_constraints)
        self.assertIn("uq_reading_meter_instant", reading_constraints)

    def test_additive_migration_generates_postgresql_ddl(self) -> None:
        path = Path(__file__).resolve().parents[1] / "migrations" / "versions" / "0003_cu05.py"
        spec = importlib.util.spec_from_file_location("migration_cu05", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = io.StringIO()
        context = MigrationContext.configure(
            dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output},
        )
        module.op = Operations(context)
        module.upgrade()
        ddl = output.getvalue()
        self.assertIn("uq_meter_id_account", ddl)
        self.assertIn("fk_reading_creation_meter_owner", ddl)
        self.assertIn("uq_reading_meter_instant", ddl)
        self.assertIn("'NaN'::numeric", ddl)
        self.assertIn("'Infinity'::numeric", ddl)
        self.assertIn("isfinite(recorded_at)", ddl)
        self.assertNotIn("DROP TABLE", ddl)
        self.assertIn("CREATE TABLE", str(CreateTable(MeterReading.__table__)))


if __name__ == "__main__":
    unittest.main()
