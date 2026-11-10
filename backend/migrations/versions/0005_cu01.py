"""Add CU01 outage snapshot, normalized rows and fetch-run history."""

import sqlalchemy as sa
from alembic import op

revision = "0005_cu01"
down_revision = "0004_cu06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "es_outage_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("distributor", sa.String(32), nullable=False),
        sa.Column("source_url", sa.String(300), nullable=False),
        sa.Column("source_last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_reported_time", sa.String(16), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("total_users_without", sa.Integer(), nullable=True),
        sa.Column("total_users_with", sa.Integer(), nullable=True),
        sa.Column("users_affected_yesterday", sa.Integer(), nullable=True),
        sa.Column("row_counts", sa.JSON(), nullable=False),
        sa.CheckConstraint("total_users_without IS NULL OR total_users_without >= 0",
                           name="ck_outage_total_without"),
        sa.CheckConstraint("total_users_with IS NULL OR total_users_with >= 0",
                           name="ck_outage_total_with"),
        sa.CheckConstraint("users_affected_yesterday IS NULL OR users_affected_yesterday >= 0",
                           name="ck_outage_total_yesterday"),
    )
    op.create_index("uq_outage_snapshot_current", "es_outage_snapshots", ["is_current"],
                    unique=True, postgresql_where=sa.text("is_current"))

    op.create_table(
        "es_outage_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("snapshot_id", sa.String(36),
                  sa.ForeignKey("es_outage_snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("partido", sa.String(120), nullable=False),
        sa.Column("localidad", sa.String(120), nullable=True),
        sa.Column("partido_key", sa.String(120), nullable=False),
        sa.Column("localidad_key", sa.String(120), nullable=True),
        sa.Column("subestacion_alimentador", sa.String(200), nullable=True),
        sa.Column("affected_users", sa.Integer(), nullable=True),
        sa.Column("normalizacion", sa.String(120), nullable=True),
        sa.CheckConstraint("affected_users IS NULL OR affected_users >= 0",
                           name="ck_outage_report_users"),
        sa.CheckConstraint("category IN ('medium_voltage','low_voltage','preventive')",
                           name="ck_outage_report_category"),
    )
    op.create_index("ix_outage_report_snapshot", "es_outage_reports", ["snapshot_id"])
    op.create_index("ix_outage_report_area", "es_outage_reports",
                    ["partido_key", "localidad_key"])

    op.create_table(
        "es_outage_fetch_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("detail_code", sa.String(64), nullable=True),
        sa.Column("content_sha256", sa.String(64), nullable=True),
        sa.CheckConstraint(
            "outcome IN ('ok','not_modified','http_error','tls_error','parse_error',"
            "'schema_error','source_degraded','timeout','skipped_locked')",
            name="ck_outage_run_outcome",
        ),
    )
    op.create_index("ix_outage_run_started", "es_outage_fetch_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_outage_run_started", table_name="es_outage_fetch_runs")
    op.drop_table("es_outage_fetch_runs")
    op.drop_index("ix_outage_report_area", table_name="es_outage_reports")
    op.drop_index("ix_outage_report_snapshot", table_name="es_outage_reports")
    op.drop_table("es_outage_reports")
    op.drop_index("uq_outage_snapshot_current", table_name="es_outage_snapshots")
    op.drop_table("es_outage_snapshots")
