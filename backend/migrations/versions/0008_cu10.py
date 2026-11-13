"""Add the CU10 admin role and persisted per-source refresh configuration."""

import sqlalchemy as sa
from alembic import op

revision = "0008_cu10"
down_revision = "0007_cu03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "es_accounts",
        sa.Column("role", sa.String(16), nullable=False, server_default=sa.text("'user'")),
    )
    op.create_check_constraint(
        "ck_account_role", "es_accounts", "role IN ('user','admin')",
    )
    op.create_table(
        "es_source_config",
        sa.Column("source_key", sa.String(32), primary_key=True),
        sa.Column("interval_seconds", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.CheckConstraint(
            "interval_seconds IN (300,600,900,1800,3600)",
            name="ck_source_config_interval",
        ),
        sa.CheckConstraint("version > 0", name="ck_source_config_version"),
    )
    op.execute(sa.text(
        "INSERT INTO es_source_config (source_key, interval_seconds, version) "
        "VALUES ('outages', 300, 1), ('scheduled_works', 300, 1) "
        "ON CONFLICT (source_key) DO NOTHING",
    ))


def downgrade() -> None:
    op.drop_table("es_source_config")
    op.drop_constraint("ck_account_role", "es_accounts", type_="check")
    op.drop_column("es_accounts", "role")
