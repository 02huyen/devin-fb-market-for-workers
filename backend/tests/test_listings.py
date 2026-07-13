import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock

from app.models import Listing


def _create_listing(client, *args, **overrides):
    payload = {
        "title": "Test item",
        "description": "A test item",
        "listing_type": "sell",
        "price": 100.0,
        "location_name": "Austin, TX",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "expires_in_days": 7,
    }
    if args and isinstance(args[0], dict):
        payload.update(args[0])
    payload.update(overrides)
    return client.post("/listings", json=payload)


def _login(client, monkeypatch, email):
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: [Mock()],
    )
    resp = client.post("/auth/request-link", json={"email": email})
    assert resp.status_code == 200, resp.text
    token = resp.json()["dev_magic_link"].split("token=")[1]
    resp = client.post("/auth/verify", params={"token": token})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_listing(user, client):
    res = _create_listing(client)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test item"
    assert data["status"] == "open"
    assert data["is_active"] is True
    assert data["sold_at"] is None
    assert data["expires_at"] is not None
    assert data["seller"]["id"] == user.id


def test_get_listing(user, client):
    created = _create_listing(client).json()
    res = client.get(f"/listings/{created['id']}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == created["id"]
    assert data["status"] == "open"


def test_default_listings_filter_is_open(user, client):
    _create_listing(client, title="Open item")
    res = client.get("/listings")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["title"] == "Open item"
    assert items[0]["status"] == "open"


def test_mark_sold(user, client):
    created = _create_listing(client).json()
    res = client.patch(
        f"/listings/{created['id']}/status",
        json={"status": "sold"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "sold"
    assert data["is_active"] is False
    assert data["sold_at"] is not None

    assert client.get("/listings").json() == []

    items = client.get("/listings?status=sold").json()
    assert len(items) == 1
    assert items[0]["status"] == "sold"


def test_renew_sold_listing(user, client):
    created = _create_listing(client, expires_in_days=7).json()
    client.patch(
        f"/listings/{created['id']}/status",
        json={"status": "sold"},
    )

    res = client.post(
        f"/listings/{created['id']}/renew",
        json={"expires_in_days": 14},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "open"
    assert data["is_active"] is True
    assert data["sold_at"] is None
    assert data["seller"]["id"] == user.id
    expires_at = datetime.fromisoformat(data["expires_at"])
    assert expires_at > datetime.utcnow() + timedelta(days=13)


def test_expired_listing_hidden_and_filterable(user, client, db):
    created = _create_listing(client).json()
    listing = db.get(Listing, created["id"])
    listing.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    assert client.get("/listings").json() == []

    items = client.get("/listings?status=expired").json()
    assert len(items) == 1
    assert items[0]["status"] == "expired"
    assert items[0]["is_active"] is False


def test_remove_listing(user, client):
    created = _create_listing(client).json()
    res = client.delete(f"/listings/{created['id']}")
    assert res.status_code == 200
    assert res.json() == {"message": "Listing removed"}

    assert client.get("/listings").json() == []

    items = client.get("/listings?status=removed").json()
    assert len(items) == 1
    assert items[0]["status"] == "removed"


def test_removed_listing_not_visible_to_others(user, other_user, client):
    listing = _create_listing(client).json()
    client.delete(f"/listings/{listing['id']}")

    client.cookies.set("wm_session", other_user.token)
    res = client.get(f"/listings/{listing['id']}")
    assert res.status_code == 404

    assert client.get("/listings?status=removed").json() == []


def test_seller_only_status_patch(user, other_user, client):
    created = _create_listing(client).json()

    client.cookies.set("wm_session", other_user.token)
    res = client.patch(
        f"/listings/{created['id']}/status",
        json={"status": "sold"},
    )
    assert res.status_code == 403

    client.cookies.set("wm_session", user.token)
    res = client.patch(
        f"/listings/{created['id']}/status",
        json={"status": "sold"},
    )
    assert res.status_code == 200


def test_seller_only_delete(user, other_user, client):
    created = _create_listing(client).json()

    client.cookies.set("wm_session", other_user.token)
    assert client.delete(f"/listings/{created['id']}").status_code == 403

    client.cookies.set("wm_session", user.token)
    assert client.delete(f"/listings/{created['id']}").status_code == 200


def test_seller_only_renew(user, other_user, client):
    created = _create_listing(client).json()
    client.patch(f"/listings/{created['id']}/status", json={"status": "sold"})

    client.cookies.set("wm_session", other_user.token)
    res = client.post(f"/listings/{created['id']}/renew")
    assert res.status_code == 403

    client.cookies.set("wm_session", user.token)
    res = client.post(f"/listings/{created['id']}/renew")
    assert res.status_code == 200


def test_listing_filters(user, client):
    _create_listing(client, title="Blue bike", description="fast", listing_type="sell")
    _create_listing(client, title="Want chair", listing_type="buy")

    items = client.get("/listings?listing_type=sell").json()
    assert len(items) == 1
    assert items[0]["listing_type"] == "sell"

    items = client.get("/listings?q=chair").json()
    assert len(items) == 1
    assert items[0]["title"] == "Want chair"

    items = client.get("/listings?lat=30.2672&lng=-97.7431&radius_miles=1").json()
    assert len(items) == 2

    items = client.get("/listings?lat=0&lng=0&radius_miles=1").json()
    assert len(items) == 0


def test_invalid_expiry_days(user, client):
    res = _create_listing(client, expires_in_days=90)
    assert res.status_code == 400
    assert "expires_in_days" in res.json()["detail"]


def test_invalid_status(user, client):
    created = _create_listing(client).json()
    res = client.patch(
        f"/listings/{created['id']}/status",
        json={"status": "expired"},
    )
    assert res.status_code == 400


def test_all_status_filter(user, client):
    open_item = _create_listing(client, title="Open item").json()
    sold = _create_listing(client, title="Sold item").json()
    client.patch(f"/listings/{sold['id']}/status", json={"status": "sold"})

    items = client.get("/listings?status=all").json()
    assert any(item["id"] == open_item["id"] for item in items)
    assert any(item["id"] == sold["id"] for item in items)


def test_renew_requires_non_open(user, client):
    created = _create_listing(client).json()
    res = client.post(f"/listings/{created['id']}/renew")
    assert res.status_code == 400
    assert "already open" in res.json()["detail"].lower()


# Tests using the auth flow


def test_create_and_list_listings(client, auth_user):
    title = f"bike-{uuid.uuid4().hex[:8]}"
    listing = _create_listing(
        auth_user["client"],
        title=title,
        description="A great bike",
        price=100.0,
        latitude=30.0,
        longitude=-97.0,
    ).json()
    assert listing["title"] == title
    assert listing["seller"]["email"] == auth_user["user"]["email"]
    assert listing["status"] == "open"
    assert listing["expires_at"] is not None

    resp = auth_user["client"].get("/listings", params={"q": title})
    assert resp.status_code == 200
    results = resp.json()
    assert any(item["title"] == title for item in results)


def test_listing_type_filter(client, auth_user, monkeypatch):
    title_sell = f"sell-{uuid.uuid4().hex[:8]}"
    title_buy = f"buy-{uuid.uuid4().hex[:8]}"
    _create_listing(
        auth_user["client"],
        title=title_sell,
        description="",
        listing_type="sell",
        price=1.0,
        location_name="",
        latitude=None,
        longitude=None,
    )
    _create_listing(
        auth_user["client"],
        title=title_buy,
        description="",
        listing_type="buy",
        price=1.0,
        location_name="",
        latitude=None,
        longitude=None,
    )

    resp = auth_user["client"].get("/listings", params={"listing_type": "sell"})
    assert resp.status_code == 200
    results = resp.json()
    assert any(item["title"] == title_sell for item in results)
    assert not any(item["title"] == title_buy for item in results)


def test_status_filter(client, auth_user, monkeypatch):
    title = f"status-{uuid.uuid4().hex[:8]}"
    listing = _create_listing(
        auth_user["client"],
        title=title,
        description="",
        listing_type="sell",
        price=1.0,
        location_name="",
        latitude=None,
        longitude=None,
    ).json()

    resp = auth_user["client"].get("/listings", params={"status": "open"})
    assert resp.status_code == 200
    assert any(item["title"] == title for item in resp.json())

    resp = auth_user["client"].post(f"/listings/{listing['id']}/sold")
    assert resp.status_code == 200

    resp = auth_user["client"].get("/listings", params={"status": "open"})
    assert resp.status_code == 200
    assert not any(item["title"] == title for item in resp.json())

    resp = auth_user["client"].get("/listings", params={"status": "sold"})
    assert resp.status_code == 200
    assert any(item["title"] == title for item in resp.json())


def test_radius_filter(client, auth_user, monkeypatch):
    title = f"nearby-{uuid.uuid4().hex[:8]}"
    _create_listing(
        auth_user["client"],
        title=title,
        description="",
        listing_type="sell",
        price=1.0,
        location_name="",
        latitude=0.0,
        longitude=0.0,
    )

    resp = auth_user["client"].get("/listings", params={"lat": 0.0, "lng": 0.0, "radius_miles": 1})
    assert resp.status_code == 200
    assert any(item["title"] == title for item in resp.json())

    resp = auth_user["client"].get("/listings", params={"lat": 10.0, "lng": 10.0, "radius_miles": 1})
    assert resp.status_code == 200
    assert not any(item["title"] == title for item in resp.json())


def test_delete_listing(client, auth_user, monkeypatch):
    title = f"delete-{uuid.uuid4().hex[:8]}"
    listing = _create_listing(
        auth_user["client"],
        title=title,
        description="",
        listing_type="sell",
        price=1.0,
        location_name="",
        latitude=None,
        longitude=None,
    ).json()

    resp = auth_user["client"].delete(f"/listings/{listing['id']}")
    assert resp.status_code == 200

    resp = auth_user["client"].get("/listings", params={"q": title})
    assert resp.status_code == 200
    assert not any(item["title"] == title for item in resp.json())


def test_only_owner_can_delete(client, client2, auth_user, monkeypatch):
    title = f"owner-{uuid.uuid4().hex[:8]}"
    listing = _create_listing(
        auth_user["client"],
        title=title,
        description="",
        listing_type="sell",
        price=1.0,
        location_name="",
        latitude=None,
        longitude=None,
    ).json()

    _login(client2, monkeypatch, f"other-{uuid.uuid4()}@example.com")
    resp = client2.delete(f"/listings/{listing['id']}")
    assert resp.status_code == 403


def test_comments_read_only_when_closed(client, auth_user, monkeypatch):
    title = f"comment-{uuid.uuid4().hex[:8]}"
    listing = _create_listing(
        auth_user["client"],
        title=title,
        description="",
        listing_type="sell",
        price=1.0,
        location_name="",
        latitude=None,
        longitude=None,
    ).json()

    resp = auth_user["client"].post(f"/listings/{listing['id']}/comments", json={"text": "Is this still available?"})
    assert resp.status_code == 200

    resp = auth_user["client"].post(f"/listings/{listing['id']}/sold")
    assert resp.status_code == 200

    resp = auth_user["client"].post(f"/listings/{listing['id']}/comments", json={"text": "Another comment"})
    assert resp.status_code == 403
