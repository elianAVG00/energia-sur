"""Add CU05 readings and transactional creation records without rewriting data."""

import sqlalchemy as sa
from alembic import op

revision = "0003_cu05"
down_revision = "0002_cu04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_meter_id_account", "es_meters", ["id", "account_id"])
    op.create_table(
        "es_meter_readings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("meter_id", sa.String(36), sa.ForeignKey("es_meters.id"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value_kwh", sa.Numeric(), nullable=False),
        sa.Column("photo_key", sa.String(64), nullable=True),
        sa.Column("photo_type", sa.String(32), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("meter_id", "recorded_at", name="uq_reading_meter_instant"),
        sa.UniqueConstraint("id", "meter_id", name="uq_reading_id_meter"),
        sa.CheckConstraint("value_kwh >= 0 AND value_kwh = trunc(value_kwh) "
                           "AND value_kwh NOT IN ('NaN'::numeric, 'Infinity'::numeric, "
                           "'-Infinity'::numeric)",
                           name="ck_reading_value"),
        sa.CheckConstraint("version > 0", name="ck_reading_version"),
        sa.CheckConstraint("isfinite(recorded_at) AND date_trunc('second', recorded_at) = recorded_at",
                           name="ck_reading_second"),
    )
    op.create_index("ix_es_meter_readings_meter_id", "es_meter_readings", ["meter_id"])
    op.create_table(
        "es_reading_creations",
        sa.Column("account_id", sa.String(36), sa.ForeignKey("es_accounts.id"), primary_key=True),
        sa.Column("meter_id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(36), primary_key=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("reading_id", sa.String(36), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["meter_id", "account_id"], ["es_meters.id", "es_meters.account_id"],
            name="fk_reading_creation_meter_owner",
        ),
        sa.ForeignKeyConstraint(
            ["reading_id", "meter_id"], ["es_meter_readings.id", "es_meter_readings.meter_id"],
            name="fk_reading_creation_reading_meter",
        ),
    )


def downgrade() -> None:
    raise RuntimeError("Destructive rollback needs separate explicit approval; use forward correction.")
