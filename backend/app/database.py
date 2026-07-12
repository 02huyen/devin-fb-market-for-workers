import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///./workplace_market.db"

_engine_kwargs = {
    "pool_pre_ping": True,
}
if SQLALCHEMY_DATABASE_URL == "sqlite:///:memory:":
    _engine_kwargs.update(
        {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    )
elif SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def setup_database() -> None:
    """Create tables for SQLite dev, or run Alembic migrations for Postgres."""
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        return

    from alembic import command
    from alembic.config import Config

    alembic_ini = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    command.upgrade(alembic_cfg, "head")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
