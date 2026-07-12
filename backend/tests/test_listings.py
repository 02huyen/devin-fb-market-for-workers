import uuid
from unittest.mock import Mock


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


def _create_listing(client, payload):
    resp = client.post("/listings", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_create_and_list_listings(client, auth_user, monkeypatch):
    title = f"bike-{uuid.uuid4().hex[:8]}"
    payload = {
        "title": title,
        "description": "A great bike",
        "listing_type": "sell",
        "price": 100.0,
        "location_name": "Austin, TX",
        "latitude": 30.0,
        "longitude": -97.0,
    }

    listing = _create_listing(auth_user["client"], payload)
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
    _create_listing(auth_user["client"], {
        "title": title_sell,
        "description": "",
        "listing_type": "sell",
        "price": 1.0,
        "location_name": "",
        "latitude": None,
        "longitude": None,
    })
    _create_listing(auth_user["client"], {
        "title": title_buy,
        "description": "",
        "listing_type": "buy",
        "price": 1.0,
        "location_name": "",
        "latitude": None,
        "longitude": None,
    })

    resp = auth_user["client"].get("/listings", params={"listing_type": "sell"})
    assert resp.status_code == 200
    results = resp.json()
    assert any(item["title"] == title_sell for item in results)
    assert not any(item["title"] == title_buy for item in results)


def test_status_filter(client, auth_user, monkeypatch):
    title = f"status-{uuid.uuid4().hex[:8]}"
    listing = _create_listing(auth_user["client"], {
        "title": title,
        "description": "",
        "listing_type": "sell",
        "price": 1.0,
        "location_name": "",
        "latitude": None,
        "longitude": None,
    })

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
    _create_listing(auth_user["client"], {
        "title": title,
        "description": "",
        "listing_type": "sell",
        "price": 1.0,
        "location_name": "",
        "latitude": 0.0,
        "longitude": 0.0,
    })

    resp = auth_user["client"].get("/listings", params={"lat": 0.0, "lng": 0.0, "radius_miles": 1})
    assert resp.status_code == 200
    assert any(item["title"] == title for item in resp.json())

    resp = auth_user["client"].get("/listings", params={"lat": 10.0, "lng": 10.0, "radius_miles": 1})
    assert resp.status_code == 200
    assert not any(item["title"] == title for item in resp.json())


def test_delete_listing(client, auth_user, monkeypatch):
    title = f"delete-{uuid.uuid4().hex[:8]}"
    listing = _create_listing(auth_user["client"], {
        "title": title,
        "description": "",
        "listing_type": "sell",
        "price": 1.0,
        "location_name": "",
        "latitude": None,
        "longitude": None,
    })

    resp = auth_user["client"].delete(f"/listings/{listing['id']}")
    assert resp.status_code == 200

    resp = auth_user["client"].get("/listings", params={"q": title})
    assert resp.status_code == 200
    assert not any(item["title"] == title for item in resp.json())


def test_only_owner_can_delete(client, client2, auth_user, monkeypatch):
    title = f"owner-{uuid.uuid4().hex[:8]}"
    listing = _create_listing(auth_user["client"], {
        "title": title,
        "description": "",
        "listing_type": "sell",
        "price": 1.0,
        "location_name": "",
        "latitude": None,
        "longitude": None,
    })

    _login(client2, monkeypatch, f"other-{uuid.uuid4()}@example.com")
    resp = client2.delete(f"/listings/{listing['id']}")
    assert resp.status_code == 403


def test_comments_read_only_when_closed(client, auth_user, monkeypatch):
    title = f"comment-{uuid.uuid4().hex[:8]}"
    listing = _create_listing(auth_user["client"], {
        "title": title,
        "description": "",
        "listing_type": "sell",
        "price": 1.0,
        "location_name": "",
        "latitude": None,
        "longitude": None,
    })

    resp = auth_user["client"].post(f"/listings/{listing['id']}/comments", json={"text": "Is this still available?"})
    assert resp.status_code == 200

    resp = auth_user["client"].post(f"/listings/{listing['id']}/sold")
    assert resp.status_code == 200

    resp = auth_user["client"].post(f"/listings/{listing['id']}/comments", json={"text": "Another comment"})
    assert resp.status_code == 403
