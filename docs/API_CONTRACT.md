# Workplace Market API Contract

This document is the source of truth for the HTTP interface between the frontend
and backend. Each endpoint lists the expected request, success response shape,
and common error status codes.

## Auth

All auth endpoints live under `/auth`.

### `POST /auth/request-link`

Request a magic sign-in link sent to the user's work email.

- **Request body:**
  ```json
  {
    "email": "user@company.com"
  }
  ```

- **Success (200):**
  ```json
  {
    "message": "Check your work email for a sign-in link.",
    "dev_magic_link": null
  }
  ```
  In `APP_ENV=dev` with no email provider configured, `dev_magic_link` contains
  the inline sign-in link so the flow can be tested without an email provider.

- **Errors:**
  - `400` — Invalid email or non-work email (free/disposable provider or no MX records).
  - `429` — Rate limit exceeded (per email or per IP).
  - `502` — Production email provider failed to send the message.

### `POST /auth/verify`

Verify a magic link token and establish a session cookie.

- **Query parameter:** `token` (string)

- **Success (200):** Returns the authenticated `User` object and sets the
  `wm_session` session cookie.
  ```json
  {
    "id": 1,
    "email": "user@company.com",
    "domain": "company.com",
    "company_name": "Company",
    "display_name": "User",
    "is_verified": true
  }
  ```

- **Errors:**
  - `400` — Invalid, expired, or already-used token.

### `GET /auth/me`

Return the currently authenticated user.

- **Success (200):** Returns the `User` object.
- **Errors:**
  - `401` — Missing or invalid session cookie.

### `POST /auth/logout`

Clear the session cookie.

- **Success (200):**
  ```json
  {
    "message": "Logged out"
  }
  ```

## Common types

### `User`

```json
{
  "id": 1,
  "email": "user@company.com",
  "domain": "company.com",
  "company_name": "Company",
  "display_name": "User",
  "is_verified": true
}
```

## DMs (private buyer↔seller conversations)

### `POST /listings/{id}/conversations`

Start a new conversation thread for the authenticated buyer about a listing, or
return an existing one keyed on `(listing_id, buyer_id)`. An optional `text` in
the request creates the first message in the same call.

**Request body (optional):**
```json
{
  "text": "Is this still available?"
}
```

**Response:** `ConversationOut`

```json
{
  "id": 1,
  "listing_id": 5,
  "buyer_id": 2,
  "listing": { "id": 5, "title": "Standing desk", "listing_type": "sell" },
  "other_participant": { "id": 3, "display_name": "Alice", "company_name": "Acme" },
  "unread_count": 0,
  "created_at": "2026-07-12T15:00:00",
  "updated_at": "2026-07-12T15:00:00",
  "last_message": null
}
```

A seller cannot start a conversation about their own listing.

---

### `GET /conversations`

Return the authenticated user's inbox — all conversations where they are the
buyer or the listing seller. Sorted by `updated_at` descending.

**Response:** `list[ConversationOut]`

`unread_count` is the number of messages sent by the other participant that
have not yet been marked as read.

---

### `GET /conversations/{id}/messages`

Return all messages in a conversation, oldest first. Also marks any unread
messages from the other participant as read.

**Response:** `list[MessageOut]`

```json
[
  {
    "id": 1,
    "conversation_id": 1,
    "sender_id": 2,
    "text": "Is this still available?",
    "created_at": "2026-07-12T15:00:00",
    "read_at": "2026-07-12T15:05:00",
    "sender": { "id": 2, "display_name": "Bob", "company_name": "Acme" }
  }
]
```

---

### `POST /conversations/{id}/messages`

Send a new message in the conversation. Only the buyer and the listing seller
can access or post to a conversation.

**Request body:**
```json
{
  "text": "Yes, it's still available."
}
```

**Response:** `MessageOut`

---

## Real-time upgrade path (MVP)

The MVP uses polling: the client refetches `GET /conversations` and
`GET /conversations/{id}/messages` on a cadence. A future real-time layer can be
added without changing these route signatures:

- Add a WebSocket endpoint such as `/ws/conversations` protected by the same
  `wm_session` cookie.
- On `connect`, join rooms for each conversation the user participates in.
- Broadcast new messages to the room and update `unread_count` in memory or via
  the same DB queries.
- Keep the REST endpoints as the source of truth for message history and read
  receipts.
