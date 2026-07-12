from datetime import datetime, timedelta

from app.models import MagicLinkToken, User


async def test_request_link_valid(async_client):
    r = await async_client.post("/auth/request-link", json={"email": "user@example.com"})
    assert r.status_code == 200
    body = r.json()
    assert body["dev_magic_link"] is not None
    assert "link below" in body["message"]


async def test_request_link_free_email(async_client):
    r = await async_client.post("/auth/request-link", json={"email": "user@gmail.com"})
    assert r.status_code == 400
    assert "work email" in r.json()["detail"]


async def test_request_link_disposable_email(async_client):
    r = await async_client.post("/auth/request-link", json={"email": "user@mailinator.com"})
    assert r.status_code == 400
    assert "Disposable" in r.json()["detail"]


async def test_request_link_disposable_package_blocklist(async_client):
    r = await async_client.post("/auth/request-link", json={"email": "user@laptoplonghai.com"})
    assert r.status_code == 400
    assert "Disposable" in r.json()["detail"]


async def test_request_link_rate_limit_per_email(async_client):
    email = "user@example.com"
    for _ in range(5):
        r = await async_client.post("/auth/request-link", json={"email": email})
        assert r.status_code == 200

    r = await async_client.post("/auth/request-link", json={"email": email})
    assert r.status_code == 429
    assert "Too many requests" in r.json()["detail"]


async def test_request_link_rate_limit_per_ip(async_client):
    for i in range(20):
        r = await async_client.post(
            "/auth/request-link", json={"email": f"user{i}@example.com"}
        )
        assert r.status_code == 200

    r = await async_client.post("/auth/request-link", json={"email": "user20@example.com"})
    assert r.status_code == 429


async def test_verify_and_me(async_client):
    r = await async_client.post("/auth/request-link", json={"email": "user@example.com"})
    token = r.json()["dev_magic_link"].split("token=")[1]

    r = await async_client.post(f"/auth/verify?token={token}")
    assert r.status_code == 200
    assert r.json()["is_verified"] is True

    r = await async_client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "user@example.com"


async def test_verify_unknown_token(async_client):
    r = await async_client.post("/auth/verify?token=not-a-real-token")
    assert r.status_code == 400


async def test_verify_reused_token(async_client):
    r = await async_client.post("/auth/request-link", json={"email": "user@example.com"})
    token = r.json()["dev_magic_link"].split("token=")[1]

    r = await async_client.post(f"/auth/verify?token={token}")
    assert r.status_code == 200

    r = await async_client.post(f"/auth/verify?token={token}")
    assert r.status_code == 400


async def test_verify_expired_token(async_client, db, monkeypatch):
    user = User(
        email="user@example.com",
        domain="example.com",
        company_name="Example",
        display_name="User",
        is_verified=False,
    )
    db.add(user)
    db.commit()

    token = "expired-token"
    db.add(
        MagicLinkToken(
            token=token,
            email=user.email,
            expires_at=datetime.utcnow() - timedelta(minutes=1),
            used=False,
        )
    )
    db.commit()

    r = await async_client.post(f"/auth/verify?token={token}")
    assert r.status_code == 400


async def test_logout_clears_session(async_client):
    r = await async_client.post("/auth/request-link", json={"email": "user@example.com"})
    token = r.json()["dev_magic_link"].split("token=")[1]

    r = await async_client.post(f"/auth/verify?token={token}")
    assert r.status_code == 200

    r = await async_client.get("/auth/me")
    assert r.status_code == 200

    r = await async_client.post("/auth/logout")
    assert r.status_code == 200

    r = await async_client.get("/auth/me")
    assert r.status_code == 401


async def test_production_cookie_flags(async_client, db, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")

    user = User(
        email="user@example.com",
        domain="example.com",
        company_name="Example",
        display_name="User",
        is_verified=False,
    )
    db.add(user)
    db.commit()

    token = "prod-token"
    db.add(
        MagicLinkToken(
            token=token,
            email=user.email,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            used=False,
        )
    )
    db.commit()

    r = await async_client.post(f"/auth/verify?token={token}")
    assert r.status_code == 200

    set_cookie = r.headers["set-cookie"]
    assert "Secure" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "samesite=none" in set_cookie.lower()
