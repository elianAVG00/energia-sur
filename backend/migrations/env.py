"""Run explicit additive migrations with backend-only connection configuration."""

from alembic import context

from app.db import get_engine
from app.models import Base

with get_engine().connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
