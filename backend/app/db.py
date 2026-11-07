"""Lazy PostgreSQL connections: importing the app never requires a database."""

import os
from functools import lru_cache
from threading import Lock

from sqlalchemy import Engine, create_engine

_live_engines: set[Engine] = set()
_lock = Lock()


class DatabaseUnavailable(RuntimeError):
    """Configuration is absent without disclosing its contents."""


@lru_cache(maxsize=4)
def _engine(url: str) -> Engine:
    engine = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)
    with _lock:
        _live_engines.add(engine)
    return engine


def dispose_engines() -> None:
    """Release existing pools at shutdown without creating or configuring one."""
    with _lock:
        for engine in _live_engines:
            engine.dispose()
        _live_engines.clear()
        _engine.cache_clear()


def get_engine() -> Engine:
    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("postgresql+psycopg://"):
        raise DatabaseUnavailable("Database service is not configured.")
    return _engine(url)
