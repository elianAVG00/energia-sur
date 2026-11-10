"""Add CU02 scheduled-work snapshot, normalized rows and fetch-run history."""

import sqlalchemy as sa
from alembic import op

revision = "0006_cu02"
down_revision = "0005_cu01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "es_scheduled_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("source_url", sa.String(300), nullable=False),
        sa.Column("source_last_modified", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_reported_time", sa.String(16), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("row_counts", sa.JSON(), nullable=False),
        sa.Column("unverified_collections", sa.JSON(), nullable=False),
        sa.Column("comunicados_present", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
    )
    op.create_index("uq_scheduled_snapshot_current", "es_scheduled_snapshots", ["is_current"],
                    unique=True, postgresql_where=sa.text("is_current"))

    op.create_table(
        "es_scheduled_works",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("snapshot_id", sa.String(36),
                  sa.ForeignKey("es_scheduled_snapshots.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("partido", sa.String(120), nullable=False),
        sa.Column("localidad", sa.String(120), nullable=True),
        sa.Column("partido_key", sa.String(120), nullable=False),
        sa.Column("localidad_key", sa.String(120), nullable=True),
        sa.Column("subestacion_alimentador", sa.String(200), nullable=True),
        sa.Column("affected_users", sa.Integer(), nullable=True),
        sa.Column("restoration_estimate_text", sa.String(120), nullable=True),
        sa.CheckConstraint("affected_users IS NULL OR affected_users >= 0",
                           name="ck_scheduled_work_users"),
        sa.CheckConstraint("category = 'maintenance'", name="ck_scheduled_work_category"),
    )
    op.create_index("ix_scheduled_work_snapshot", "es_scheduled_works", ["snapshot_id"])
    op.create_index("ix_scheduled_work_area", "es_scheduled_works",
                    ["partido_key", "localidad_key"])

    op.create_table(
        "es_scheduled_fetch_runs",
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
            name="ck_scheduled_run_outcome",
        ),
    )
    op.create_index("ix_scheduled_run_started", "es_scheduled_fetch_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_scheduled_run_started", table_name="es_scheduled_fetch_runs")
    op.drop_table("es_scheduled_fetch_runs")
    op.drop_index("ix_scheduled_work_area", table_name="es_scheduled_works")
    op.drop_index("ix_scheduled_work_snapshot", table_name="es_scheduled_works")
    op.drop_table("es_scheduled_works")
    op.drop_index("uq_scheduled_snapshot_current", table_name="es_scheduled_snapshots")
    op.drop_table("es_scheduled_snapshots")
