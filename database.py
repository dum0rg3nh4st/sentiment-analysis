import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Create a .env file (see .env.example) and set it."
        )
    return value


@lru_cache(maxsize=1)
def get_engine():
    database_url = _require_env("DATABASE_URL")
    # Production note: for high throughput you may want to tune pool settings.
    return create_engine(database_url, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_sessionmaker():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db():
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()

