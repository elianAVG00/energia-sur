"""Add the CU03 guide index and assistant conversation schema (additive)."""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0007_cu03"
down_revision = "0006_cu02"
branch_labels = None
depends_on = None

EMBEDDING_DIMENSION = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "es_guide_documents",
        sa.Column("document_id", sa.String(120), primary_key=True),
        sa.Column("current_version", sa.String(32), nullable=False),
        sa.Column("last_verified_at", sa.Date(), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_name", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(300), nullable=False),
        sa.Column("embedding_model", sa.String(120), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("parser_version", sa.String(32), nullable=False),
    )

    op.create_table(
        "es_guide_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(120),
                  sa.ForeignKey("es_guide_documents.document_id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("last_verified_at", sa.Date(), nullable=False),
        sa.Column("section", sa.String(120), nullable=False),
        sa.Column("article_id", sa.String(16), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("source_name", sa.String(200), nullable=False),
        sa.Column("source_urls", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("information_type", sa.String(300), nullable=False),
        sa.Column("volatility", sa.String(16), nullable=False),
        sa.Column("source_type", sa.String(300), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSION), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("document_id", "article_id", "version",
                            name="uq_guide_article_version"),
    )
    op.create_index("uq_guide_active_article", "es_guide_chunks",
                    ["document_id", "article_id"], unique=True,
                    postgresql_where=sa.text("is_active"))
    op.create_index("ix_guide_chunk_active", "es_guide_chunks",
                    ["document_id", "is_active"])
    op.create_index("ix_guide_chunk_article", "es_guide_chunks",
                    ["document_id", "article_id"])
    op.execute("CREATE INDEX ix_guide_chunk_embedding ON es_guide_chunks "
               "USING hnsw (embedding vector_cosine_ops)")

    op.create_table(
        "es_assistant_conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_id", sa.String(36),
                  sa.ForeignKey("es_accounts.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assistant_conversation_account", "es_assistant_conversations",
                    ["account_id"])

    op.create_table(
        "es_assistant_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36),
                  sa.ForeignKey("es_assistant_conversations.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assistant_message_conversation", "es_assistant_messages",
                    ["conversation_id"])


def downgrade() -> None:
    stored = op.get_bind().execute(
        sa.text("SELECT count(*) FROM es_assistant_messages"),
    ).scalar_one()
    if stored:
        raise RuntimeError(
            "Refusing to drop assistant conversations that contain data",
        )
    op.drop_index("ix_assistant_message_conversation", table_name="es_assistant_messages")
    op.drop_table("es_assistant_messages")
    op.drop_index("ix_assistant_conversation_account", table_name="es_assistant_conversations")
    op.drop_table("es_assistant_conversations")
    op.execute("DROP INDEX IF EXISTS ix_guide_chunk_embedding")
    op.drop_index("ix_guide_chunk_article", table_name="es_guide_chunks")
    op.drop_index("ix_guide_chunk_active", table_name="es_guide_chunks")
    op.drop_index("uq_guide_active_article", table_name="es_guide_chunks")
    op.drop_table("es_guide_chunks")
    op.drop_table("es_guide_documents")
