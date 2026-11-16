"""Add the shared GeoRef territorial catalog and re-key ENRE comparisons."""

import unicodedata
from collections.abc import Callable

import sqlalchemy as sa
from alembic import op

revision = "0009_territorial_catalog"
down_revision = "0008_cu10"
branch_labels = None
depends_on = None


def _new_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(character for character in decomposed
                    if not unicodedata.combining(character))
    return " ".join(plain.casefold().strip().split())


def _old_key(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).strip().casefold().split())


def _rekey(
    table: str, key_column: str, label_column: str, key_builder: Callable[[str], str],
) -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.text(
        f"SELECT id, {label_column} FROM {table}"
    )).all()
    for row_id, label in rows:
        if label is not None:
            connection.execute(
                sa.text(f"UPDATE {table} SET {key_column} = :key WHERE id = :id"),
                {"key": key_builder(label), "id": row_id},
            )


def upgrade() -> None:
    op.create_table(
        "es_territorial_catalog_metadata",
        sa.Column("catalog_key", sa.String(32), primary_key=True),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_url", sa.String(300), nullable=False),
        sa.Column("concession_source_url", sa.String(300), nullable=False),
        sa.Column("province_id", sa.String(2), nullable=False),
    )
    op.create_table(
        "es_territorial_parties",
        sa.Column("georef_id", sa.String(12), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("normalized_name", sa.String(120), nullable=False),
        sa.Column("coverage_status", sa.String(32), nullable=False,
                  server_default="covered"),
        sa.UniqueConstraint("normalized_name", name="uq_territorial_party_normalized_name"),
        sa.CheckConstraint("coverage_status IN ('covered','coverage_unverified')",
                           name="ck_territorial_party_coverage"),
        sa.CheckConstraint(
            "georef_id IN ('06028','06035','06091','06134','06260','06270',"
            "'06274','06434','06490','06648','06658','06778')",
            name="ck_territorial_party_approved_scope",
        ),
    )
    op.create_table(
        "es_territorial_localities",
        sa.Column("id", sa.String(180), primary_key=True),
        sa.Column("party_georef_id", sa.String(12),
                  sa.ForeignKey("es_territorial_parties.georef_id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("normalized_name", sa.String(120), nullable=False),
        sa.Column("coverage_status", sa.String(32), nullable=False,
                  server_default="coverage_unverified"),
        sa.Column("selectable", sa.Boolean(), nullable=False,
                  server_default=sa.text("true")),
        sa.UniqueConstraint("party_georef_id", "normalized_name",
                            name="uq_territorial_locality_party_normalized_name"),
        sa.CheckConstraint(
            "coverage_status IN ('covered','out_of_coverage','coverage_unverified')",
            name="ck_territorial_locality_coverage",
        ),
        sa.CheckConstraint(
            "party_georef_id IN ('06028','06035','06091','06134','06260','06270',"
            "'06274','06434','06490','06648','06658','06778')",
            name="ck_territorial_locality_approved_scope",
        ),
    )
    op.create_index("ix_territorial_locality_party", "es_territorial_localities",
                    ["party_georef_id", "selectable", "name"])
    op.create_table(
        "es_territorial_locality_sources",
        sa.Column("georef_id", sa.String(24), primary_key=True),
        sa.Column("locality_id", sa.String(180),
                  sa.ForeignKey("es_territorial_localities.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("localidad_censal_id", sa.String(24), nullable=True),
        sa.Column("localidad_censal", sa.String(120), nullable=True),
        sa.Column("selector_review", sa.Text(), nullable=True),
    )
    op.create_table(
        "es_territorial_name_aliases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("source_label", sa.String(120), nullable=False),
        sa.Column("normalized_source_key", sa.String(120), nullable=False),
        sa.Column("party_georef_id", sa.String(12),
                  sa.ForeignKey("es_territorial_parties.georef_id"), nullable=False),
        sa.Column("locality_id", sa.String(180),
                  sa.ForeignKey("es_territorial_localities.id"), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("evidence", sa.String(300), nullable=False),
        sa.UniqueConstraint("kind", "party_georef_id", "normalized_source_key",
                            name="uq_territorial_alias_kind_party_key"),
        sa.CheckConstraint("kind IN ('party','locality')", name="ck_territorial_alias_kind"),
        sa.CheckConstraint("status IN ('verified','unresolved')",
                           name="ck_territorial_alias_status"),
        sa.CheckConstraint(
            "(status = 'verified' AND "
            "((kind = 'party' AND locality_id IS NULL) OR "
            "(kind = 'locality' AND locality_id IS NOT NULL))) OR "
            "(status = 'unresolved' AND kind = 'locality' AND locality_id IS NULL)",
            name="ck_territorial_alias_target",
        ),
    )

    _rekey("es_outage_reports", "partido_key", "partido", _new_key)
    _rekey("es_outage_reports", "localidad_key", "localidad", _new_key)
    _rekey("es_scheduled_works", "partido_key", "partido", _new_key)
    _rekey("es_scheduled_works", "localidad_key", "localidad", _new_key)

    from app.territorial_catalog import seed_catalog

    seed_catalog(op.get_bind())


def downgrade() -> None:
    _rekey("es_outage_reports", "partido_key", "partido", _old_key)
    _rekey("es_outage_reports", "localidad_key", "localidad", _old_key)
    _rekey("es_scheduled_works", "partido_key", "partido", _old_key)
    _rekey("es_scheduled_works", "localidad_key", "localidad", _old_key)
    op.drop_table("es_territorial_name_aliases")
    op.drop_table("es_territorial_locality_sources")
    op.drop_index("ix_territorial_locality_party", table_name="es_territorial_localities")
    op.drop_table("es_territorial_localities")
    op.drop_table("es_territorial_parties")
    op.drop_table("es_territorial_catalog_metadata")
