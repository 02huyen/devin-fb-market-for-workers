import uuid
from unittest.mock import Mock


def _mock_mx(monkeypatch):
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: [Mock()],
    )


def test_request_link_and_verify_flow(client, monkeypatch):
    _mock_mx(monkeypatch)
    email = f"auth-{uuid.uuid4()}@example.com"

    resp = client.post("/auth/request-link", json={"email": email})
    assert resp.status_code == 200
    data = resp.json()
    assert data["dev_magic_link"] is not None
    token = data["dev_magic_link"].split("token=")[1]

    resp = client.post("/auth/verify", params={"token": token})
    assert resp.status_code == 200
    user = resp.json()
    assert user["email"] == email
    assert user["is_verified"] is True

    resp = client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == email

    resp = client.post("/auth/logout")
    assert resp.status_code == 200

    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_request_link_rejects_personal_email(client, monkeypatch):
    _mock_mx(monkeypatch)
    resp = client.post("/auth/request-link", json={"email": "test@gmail.com"})
    assert resp.status_code == 400
    assert "Personal email" in resp.json()["detail"]


def test_verify_rejects_invalid_token(client):
    resp = client.post("/auth/verify", params={"token": "not-a-token"})
    assert resp.status_code == 400
