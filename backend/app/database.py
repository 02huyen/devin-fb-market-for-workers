import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///./workplace_market.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {},
    pool_pre_ping=True,
)
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
