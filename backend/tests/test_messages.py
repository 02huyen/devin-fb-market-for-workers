from app.models import Conversation, Message


def _login(client, monkeypatch, email):
    monkeypatch.setattr(
        "app.services.email_validation.dns.resolver.resolve",
        lambda *args, **kwargs: [object()],
    )
    resp = client.post("/auth/request-link", json={"email": email})
    assert resp.status_code == 200, resp.text
    token = resp.json()["dev_magic_link"].split("token=")[1]
    resp = client.post("/auth/verify", params={"token": token})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _create_listing(client, title="Test item"):
    resp = client.post(
        "/listings",
        json={
            "title": title,
            "description": "A test item",
            "listing_type": "sell",
            "price": 100.0,
            "location_name": "Austin, TX",
            "latitude": 30.2672,
            "longitude": -97.7431,
            "expires_in_days": 7,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_start_conversation_as_buyer(client, client2, monkeypatch):
    seller = _login(client, monkeypatch, "seller@example.com")
    listing = _create_listing(client, "Bike")

    buyer = _login(client2, monkeypatch, "buyer@example.com")
    resp = client2.post(f"/messages/conversations?listing_id={listing['id']}")
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["buyer_id"] == buyer["id"]
    assert data["listing_id"] == listing["id"]
    assert data["other_participant"]["id"] == seller["id"]


def test_start_conversation_is_idempotent(client, client2, monkeypatch):
    _login(client, monkeypatch, "seller@example.com")
    listing = _create_listing(client, "Bike")

    _login(client2, monkeypatch, "buyer@example.com")
    resp1 = client2.post(f"/messages/conversations?listing_id={listing['id']}")
    assert resp1.status_code == 201
    resp2 = client2.post(f"/messages/conversations?listing_id={listing['id']}")
    assert resp2.status_code == 201
    assert resp1.json()["id"] == resp2.json()["id"]


def test_seller_cannot_message_self(client, monkeypatch):
    _login(client, monkeypatch, "seller@example.com")
    listing = _create_listing(client, "Bike")
    resp = client.post(f"/messages/conversations?listing_id={listing['id']}")
    assert resp.status_code == 400
    assert "own listing" in resp.json()["detail"].lower()


def test_send_and_receive_messages(client, client2, monkeypatch):
    _login(client, monkeypatch, "seller@example.com")
    listing = _create_listing(client, "Bike")

    _login(client2, monkeypatch, "buyer@example.com")
    conv = client2.post(f"/messages/conversations?listing_id={listing['id']}").json()

    resp = client2.post(
        f"/messages/conversations/{conv['id']}/messages",
        json={"text": "Is this still available?"},
    )
    assert resp.status_code == 201
    assert resp.json()["text"] == "Is this still available?"
    assert resp.json()["sender"]["id"] == conv["buyer_id"]

    # Seller can see the message
    resp = client.get(f"/messages/conversations/{conv['id']}/messages")
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 1
    assert messages[0]["text"] == "Is this still available?"


def test_non_participant_cannot_access_messages(client, client2, monkeypatch):
    _login(client, monkeypatch, "seller@example.com")
    listing = _create_listing(client, "Bike")

    _login(client2, monkeypatch, "buyer@example.com")
    conv = client2.post(f"/messages/conversations?listing_id={listing['id']}").json()

    other = _login(client, monkeypatch, "other@example.com")
    # Recreate a client with other user's cookie
    # client already authenticated? no, client is seller. Use client to get a token for other.
    assert other["id"] != conv["buyer_id"]
    resp = client.get(f"/messages/conversations/{conv['id']}/messages")
    assert resp.status_code == 403


def test_conversations_list(client, client2, monkeypatch):
    _login(client, monkeypatch, "seller@example.com")
    listing = _create_listing(client, "Bike")

    _login(client2, monkeypatch, "buyer@example.com")
    client2.post(f"/messages/conversations?listing_id={listing['id']}")

    resp = client2.get("/messages/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["listing"]["title"] == "Bike"
    assert data[0]["unread_count"] == 0


def test_unread_count_and_mark_read(client, client2, monkeypatch):
    _login(client, monkeypatch, "seller@example.com")
    listing = _create_listing(client, "Bike")

    _login(client2, monkeypatch, "buyer@example.com")
    conv = client2.post(f"/messages/conversations?listing_id={listing['id']}").json()
    client2.post(
        f"/messages/conversations/{conv['id']}/messages",
        json={"text": "Hello"},
    )

    # Seller's inbox shows unread
    resp = client.get("/messages/conversations")
    assert resp.status_code == 200
    seller_conv = resp.json()[0]
    assert seller_conv["unread_count"] == 1

    # Seller opens messages (mark read endpoint)
    resp = client.post(f"/messages/conversations/{conv['id']}/read")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Marked as read"}

    resp = client.get("/messages/conversations")
    assert resp.json()[0]["unread_count"] == 0
