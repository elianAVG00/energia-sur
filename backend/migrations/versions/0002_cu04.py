"""Add domicile revisions and owned meters without rewriting existing rows."""

import sqlalchemy as sa
from alembic import op

revision = "0002_cu04"
down_revision = "0001_cu09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("es_domiciles", sa.Column("version", sa.Integer(), nullable=False,
                                            server_default="1"))
    op.create_check_constraint("ck_domicile_version", "es_domiciles", "version > 0")
    op.create_unique_constraint("uq_domicile_id_account", "es_domiciles", ["id", "account_id"])
    op.create_table(
        "es_meters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domicile_id", sa.String(36), nullable=False),
        sa.Column("account_id", sa.String(36), nullable=False),
        sa.Column("meter_number", sa.String(120), nullable=False),
        sa.Column("alias", sa.String(120), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["domicile_id", "account_id"],
                                ["es_domiciles.id", "es_domiciles.account_id"],
                                name="fk_meter_domicile_owner"),
        sa.CheckConstraint("version > 0", name="ck_meter_version"),
        sa.CheckConstraint(
            "meter_number <> '' AND meter_number = btrim(meter_number, ' ') "
            "AND meter_number COLLATE \"C\" !~ '[^ -~]'", name="ck_meter_number_ascii"),
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_meter_account_normalized ON es_meters "
        "(account_id, (translate(btrim(meter_number, ' '), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') COLLATE \"C\"))"
    )


def downgrade() -> None:
    raise RuntimeError("Destructive rollback needs separate explicit approval; use forward correction.")
