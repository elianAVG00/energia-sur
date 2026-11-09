"""Add CU06 private bill metadata without changing existing records."""

import sqlalchemy as sa
from alembic import op

revision = "0004_cu06"
down_revision = "0003_cu05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "es_electricity_bills",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("meter_id", sa.String(36), sa.ForeignKey("es_meters.id"), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("value_kwh", sa.Numeric(), nullable=False),
        sa.Column("amount_ars", sa.Numeric(), nullable=True),
        sa.Column("file_key", sa.String(64), nullable=False),
        sa.Column("file_type", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("meter_id", "period_start", "period_end", name="uq_bill_meter_period"),
        sa.UniqueConstraint("id", "meter_id", name="uq_bill_id_meter"),
        sa.CheckConstraint("isfinite(period_start) AND isfinite(period_end) AND period_start <= period_end",
                           name="ck_bill_period"),
        sa.CheckConstraint("value_kwh >= 0 AND value_kwh < 1000000000000000000 "
                           "AND value_kwh = trunc(value_kwh, 3)", name="ck_bill_kwh"),
        sa.CheckConstraint("amount_ars IS NULL OR (amount_ars >= 0 AND "
                           "amount_ars < 1000000000000000000 AND amount_ars = trunc(amount_ars, 2))",
                           name="ck_bill_amount"),
        sa.CheckConstraint("version > 0", name="ck_bill_version"),
    )
    op.create_index("ix_es_electricity_bills_meter_id", "es_electricity_bills", ["meter_id"])
    op.create_table(
        "es_bill_creations",
        sa.Column("account_id", sa.String(36), sa.ForeignKey("es_accounts.id"), primary_key=True),
        sa.Column("meter_id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(36), primary_key=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("bill_id", sa.String(36), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["meter_id", "account_id"], ["es_meters.id", "es_meters.account_id"],
                                name="fk_bill_creation_meter_owner"),
        sa.ForeignKeyConstraint(["bill_id", "meter_id"],
                                ["es_electricity_bills.id", "es_electricity_bills.meter_id"],
                                name="fk_bill_creation_bill_meter"),
    )


def downgrade() -> None:
    raise RuntimeError("Destructive rollback needs separate explicit approval; use forward correction.")
