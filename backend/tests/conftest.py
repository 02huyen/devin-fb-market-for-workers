import os
import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

# Use an isolated test database and deterministic secrets/settings before any app imports.
os.environ["APP_SECRET_KEY"] = "test-secret-not-for-production"
os.environ["DATABASE_URL"] = "sqlite:///mercury_test.db"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

# Remove a stale test DB so the app imports create a fresh schema.
_test_db_path = "mercury_test.db"
if os.path.exists(_test_db_path):
    os.remove(_test_db_path)

from app import database as db_module  # noqa: E402
from app.auth_utils import create_session_token  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402

Base = db_module.Base


@pytest.fixture
def client():
    """Provide a TestClient with a fresh test database schema."""
    Base.metadata.drop_all(bind=db_module.engine)
    Base.metadata.create_all(bind=db_module.engine)
    with TestClient(app) as client:
        yield client
    Base.metadata.drop_all(bind=db_module.engine)


@pytest.fixture
def client2():
    """Provide an additional TestClient that shares the test database."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def user(client):
    """Create a verified user, set the session cookie on the client, and return the user."""
    db = db_module.SessionLocal()
    try:
        u = User(
            email=f"test-{uuid.uuid4().hex[:8]}@example.com",
            domain="example.com",
            company_name="Example",
            display_name="Test",
            is_verified=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        u.token = create_session_token(u.id)
        client.cookies.set("wm_session", u.token)
        yield u
    finally:
        db.close()


@pytest.fixture
def other_user(client):
    """Create a second verified user and return it (without setting the client cookie)."""
    db = db_module.SessionLocal()
    try:
        u = User(
            email=f"other-{uuid.uuid4().hex[:8]}@example.com",
            domain="example.com",
            company_name="Other",
            display_name="Other",
            is_verified=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        u.token = create_session_token(u.id)
        yield u
    finally:
        db.close()


@pytest.fixture
def auth_user(client, monkeypatch):
    """Create a verified user via the auth flow and return the client and user."""
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
