import os

import httpx
import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.services.rate_limiter import rate_limiter

os.environ.setdefault("APP_SECRET_KEY", "test-secret")
os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="function")
def test_engine():
    """Create a fresh in-memory SQLite engine with a single shared connection."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db(test_engine):
    """Provide a fresh session bound to the test engine."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function", autouse=True)
def override_db(db):
    """Override FastAPI's get_db dependency to use the test session."""
    def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def mock_dns_resolver(monkeypatch):
    """Avoid real DNS lookups by returning a fake MX record."""
    def _fake_resolve(*args, **kwargs):
        return [object()]

    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        _fake_resolve,
    )


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    """Reset the in-memory rate limiter between tests."""
    rate_limiter._windows.clear()
    yield


@pytest.fixture(scope="function")
async def client():
    """Async HTTP client backed by the FastAPI app."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c
