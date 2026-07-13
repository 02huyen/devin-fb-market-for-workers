# Workplace Market API Contract

This document is the source of truth for the HTTP interface between the frontend
and backend. All authenticated endpoints require a valid `wm_session` cookie
returned by the auth flow.

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
    "dev_magic_link": "http://localhost:3000/verify?token=..."
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

### `PATCH /auth/me`

Update the authenticated user's display name.

- **Request body:**
  ```json
  {
    "display_name": "New Name"
  }
  ```

- **Success (200):** Returns the updated `User` object.

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

## Comments

### `GET /listings/{id}/comments`

Return all non-deleted comments on a listing, oldest first.

**Response:**
```json
[
  {
    "id": 1,
    "listing_id": 1,
    "author_id": 2,
    "text": "Is this still available?",
    "is_deleted": false,
    "created_at": "2026-07-12T15:00:00",
    "author": {
      "id": 2,
      "display_name": "Jane",
      "company_name": "Acme"
    }
  }
]
```

### `POST /listings/{id}/comments`

Create a comment on a listing. The listing must be `open`.

**Body:**
```json
{
  "text": "Is this still available?"
}
```

**Response:** `CommentOut`

### `DELETE /comments/{id}`

Soft-delete a comment. Only the comment author or the listing owner may delete.

**Response:**
```json
{
  "message": "Comment removed"
}
```

## Listings

Status values:

- `open` — visible in default search (not expired).
- `sold` — seller marked the item as sold; `sold_at` is set.
- `expired` — `expires_at` has passed; hidden by default search.
- `removed` — soft-deleted by the seller; hidden from all but the seller.

The `is_active` boolean on `ListingOut` is derived from `status == "open"` and is kept for backward compatibility.

### `GET /listings`

List listings. Defaults to `status=open` (active, non-expired listings).

**Query parameters (all optional):**

- `q` — keyword search across `title` and `description`.
- `listing_type` — `sell`, `buy`, or `giveaway`.
- `status` — `open`, `sold`, `expired`, `removed`, or `all`. Default: `open`. `removed` is restricted to the seller's own listings; `all` shows every non-removed listing plus the current seller's own removed listings.
- `lat`, `lng` — center for radius filtering.
- `radius_miles` — default `50.0`.
- `seller_id` — filter by a specific seller.

**Response body:** `ListingOut[]`

```json
[
  {
    "id": 1,
    "title": "Desk chair",
    "description": "Ergonomic chair",
    "listing_type": "sell",
    "price": 100.0,
    "location_name": "Austin, TX",
    "latitude": 30.2672,
    "longitude": -97.7431,
    "status": "open",
    "expires_at": "2026-07-19T15:55:07.703449",
    "sold_at": null,
    "is_active": true,
    "created_at": "2026-07-12T15:55:07.704476",
    "seller": {
      "id": 1,
      "email": "user@company.com",
      "domain": "company.com",
      "company_name": "Company",
      "display_name": "User"
    },
    "images": []
  }
]
```

Expired `open` listings are lazily marked `expired` on read and excluded from the default `open` search.

### `POST /listings`

Create a new listing.

**Request body:** `ListingIn`

```json
{
  "title": "Desk chair",
  "description": "Ergonomic chair",
  "listing_type": "sell",
  "price": 100.0,
  "location_name": "Austin, TX",
  "latitude": 30.2672,
  "longitude": -97.7431,
  "expires_in_days": 30
}
```

`expires_in_days` (or `expiry_days` for frontend compatibility) must be `7`, `14`, or `30` (default `30`). The listing is created with `status=open` and `expires_at = now + expires_in_days`.

**Response body:** `ListingOut`

### `GET /listings/{id}`

Get a single listing.

**Response body:** `ListingOut`

Removed listings are only returned to the seller.

### `POST /listings/{id}/sold`

Mark a listing as sold. Seller-only.

**Response body:** `ListingOut`

### `PATCH /listings/{id}/status`

Update a listing's status. Seller-only.

**Request body:**

```json
{
  "status": "sold",
  "expires_in_days": 30
}
```

Allowed `status` values: `open`, `sold`, `removed`.

- `sold` — sets `status=sold` and `sold_at` to the current time.
- `open` — reactivates the listing, clears `sold_at`, and sets `expires_at` to `now + expires_in_days`.
- `removed` — soft-deletes the listing.

`expires_in_days` is only used when `status` is `open` and must be `7`, `14`, or `30` (default `30`).

**Response body:** `ListingOut`

### `POST /listings/{id}/renew`

Relist a sold/expired/removed listing. Seller-only.

**Request body (optional):**

```json
{
  "expires_in_days": 30
}
```

`expires_in_days` must be `7`, `14`, or `30` (default `30`).

Sets `status=open`, clears `sold_at`, and sets `expires_at` to `now + expires_in_days`.

Returns `400` if the listing is already `open`.

**Response body:** `ListingOut`

### `DELETE /listings/{id}`

Soft-delete a listing (sets `status=removed`). Seller-only.

**Response body:**
```json
{
  "message": "Listing removed"
}
```

### `POST /listings/{id}/images`

Upload an image for a listing. Seller-only.

- **Request body:** multipart/form-data with `file`.
- **Success (200):** `ListingImageOut`
- **Errors:**
  - `400` — Unsupported image type.
  - `403` — Only the seller can upload images.

## Messages

### Common types

#### `ConversationOut`

```json
{
  "id": 1,
  "listing_id": 1,
  "buyer_id": 2,
  "listing": {
    "id": 1,
    "title": "Desk chair",
    "listing_type": "sell"
  },
  "other_participant": {
    "id": 1,
    "display_name": "Seller",
    "company_name": "Company"
  },
  "unread_count": 0,
  "created_at": "2026-07-12T15:55:07.704476",
  "updated_at": "2026-07-12T15:55:07.704476",
  "last_message": null
}
```

#### `MessageOut`

```json
{
  "id": 1,
  "conversation_id": 1,
  "sender_id": 2,
  "text": "Hello, is this still available?",
  "created_at": "2026-07-12T15:55:07.704476",
  "read_at": null,
  "sender": {
    "id": 2,
    "display_name": "Buyer",
    "company_name": "Company"
  }
}
```

### `GET /messages/conversations`

List the authenticated user's conversations.

**Response body:** `ConversationOut[]`

### `POST /messages/conversations`

Start a conversation about a listing.

- **Query parameter:** `listing_id` (int)
- **Success (201):** `ConversationOut`
- **Errors:**
  - `400` — Cannot message yourself.
  - `404` — Listing not found.

### `GET /messages/conversations/{id}/messages`

Get messages for a conversation.

**Response body:** `MessageOut[]`

### `POST /messages/conversations/{id}/messages`

Send a message in a conversation.

**Request body:**
```json
{
  "text": "Hello, is this still available?"
}
```

**Response body:** `MessageOut`

### `POST /messages/conversations/{id}/read`

Mark all messages from the other participant as read.

**Response body:**
```json
{
  "message": "Marked as read"
}
```
