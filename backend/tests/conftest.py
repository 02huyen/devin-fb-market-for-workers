import os
import uuid
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.services.rate_limiter import rate_limiter

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["APP_SECRET_KEY"] = "test-secret"
os.environ["APP_ENV"] = "dev"
os.environ["FRONTEND_URL"] = "http://localhost:3000"


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
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: [object()],
    )


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    """Reset the in-memory rate limiter between tests."""
    rate_limiter._windows.clear()
    yield


@pytest.fixture(scope="function")
def client():
    """Synchronous TestClient for tests that use regular def test_*."""
    return TestClient(app)


@pytest.fixture(scope="function")
def client2():
    """Second synchronous TestClient for tests that need a second user."""
    return TestClient(app)


@pytest.fixture(scope="function")
def auth_user(client, monkeypatch):
    """Create a verified user and return the TestClient + user JSON."""
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: [Mock()],
    )
    email = f"test-{uuid.uuid4()}@example.com"
    resp = client.post("/auth/request-link", json={"email": email})
    assert resp.status_code == 200, resp.text
    link = resp.json()["dev_magic_link"]
    token = link.split("token=")[1]
    resp = client.post("/auth/verify", params={"token": token})
    assert resp.status_code == 200, resp.text
    return {"client": client, "user": resp.json()}


@pytest.fixture(scope="function")
async def async_client():
    """Async HTTP client backed by the FastAPI app for async test_*."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c
