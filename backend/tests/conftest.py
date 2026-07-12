import os
import uuid
from unittest.mock import Mock

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def client2():
    return TestClient(app)


@pytest.fixture
def auth_user(client, monkeypatch):
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
