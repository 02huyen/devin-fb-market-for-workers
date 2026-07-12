from datetime import datetime, timedelta

from app import database as db_module
from app.models import Listing


def _create_listing(client, **overrides):
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
    payload.update(overrides)
    return client.post("/listings", json=payload)


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

    # Default list no longer shows the item.
    assert client.get("/listings").json() == []

    # But it appears under status=sold.
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


def test_expired_listing_hidden_and_filterable(user, client):
    created = _create_listing(client).json()
    # Force the listing to expire by setting expires_at in the past.
    db = db_module.SessionLocal()
    try:
        listing = db.get(Listing, created["id"])
        listing.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()

    # Default search should be empty (lazy-expiry runs on read).
    assert client.get("/listings").json() == []

    # Expired filter should show it.
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

    # Switch to another user.
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


def test_renew_requires_non_open(user, client):
    created = _create_listing(client).json()
    res = client.post(f"/listings/{created['id']}/renew")
    assert res.status_code == 400
    assert "already open" in res.json()["detail"].lower()
