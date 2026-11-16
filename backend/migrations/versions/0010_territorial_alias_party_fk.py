"""Ensure verified locality aliases target a locality in their stated party."""

from alembic import op

revision = "0010_territorial_alias_party_fk"
down_revision = "0009_territorial_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_territorial_locality_id_party",
        "es_territorial_localities",
        ["id", "party_georef_id"],
    )
    op.drop_constraint(
        "es_territorial_name_aliases_locality_id_fkey",
        "es_territorial_name_aliases",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_territorial_alias_locality_party",
        "es_territorial_name_aliases",
        "es_territorial_localities",
        ["locality_id", "party_georef_id"],
        ["id", "party_georef_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_territorial_alias_locality_party",
        "es_territorial_name_aliases",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "es_territorial_name_aliases_locality_id_fkey",
        "es_territorial_name_aliases",
        "es_territorial_localities",
        ["locality_id"],
        ["id"],
    )
    op.drop_constraint(
        "uq_territorial_locality_id_party",
        "es_territorial_localities",
        type_="unique",
    )
