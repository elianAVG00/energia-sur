"""Add account, session, domicile and interruption tables without touching old data."""

import sqlalchemy as sa
from alembic import op

revision = "0001_cu09"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("es_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(80), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(512), nullable=False))
    op.create_table("es_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("es_accounts.id"), nullable=False),
        sa.Column("csrf_token", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False))
    op.create_index("ix_es_sessions_account_id", "es_sessions", ["account_id"])
    op.create_table("es_domiciles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("es_accounts.id"), nullable=False),
        sa.Column("display_address", sa.String(300), nullable=False))
    op.create_index("ix_es_domiciles_account_id", "es_domiciles", ["account_id"])
    op.create_table("es_interruptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domicile_id", sa.String(36), sa.ForeignKey("es_domiciles.id"), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("complaint_number", sa.String(120), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.CheckConstraint("end_at IS NULL OR end_at > start_at", name="es_cut_positive"),
        sa.CheckConstraint("version > 0", name="es_cut_version"))
    op.create_index("ix_es_interruptions_domicile_id", "es_interruptions", ["domicile_id"])
    op.create_index("ix_es_interruptions_start_at", "es_interruptions", ["start_at"])


def downgrade() -> None:
    raise RuntimeError("Destructive rollback needs separate explicit approval; use forward correction.")
