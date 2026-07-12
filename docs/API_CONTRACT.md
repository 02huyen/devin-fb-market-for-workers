# Workplace Market — API Contract

This document defines the request/response shapes for the Workplace Market backend. All authenticated endpoints require a valid `wm_session` cookie returned by the auth flow.

## Auth

### `POST /auth/request-link`

Request a magic sign-in link for a work email.

**Request body:**
```json
{
  "email": "user@company.com"
}
```

**Response body:**
```json
{
  "message": "Check your work email for a sign-in link.",
  "dev_magic_link": "http://localhost:3000/verify?token=..."  // dev mode only
}
```

### `POST /auth/verify?token=<token>`

Verify the magic link and create the session cookie.

**Response body:** `UserOut`
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

### `GET /auth/me`

Return the current authenticated user.

**Response body:** `UserOut`

### `POST /auth/logout`

Clear the session cookie.

**Response body:**
```json
{
  "message": "Logged out"
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
- `status` — `open`, `sold`, `expired`, or `removed`. Default: `open`. `removed` is restricted to the seller's own listings.
- `lat`, `lng` — center for radius filtering.
- `radius_miles` — default `50.0`.

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
    }
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

`expires_in_days` must be `7`, `14`, or `30` (default `30`). The listing is created with `status=open` and `expires_at = now + expires_in_days`.

**Response body:** `ListingOut`

### `GET /listings/{id}`

Get a single listing.

**Response body:** `ListingOut`

Removed listings are only returned to the seller.

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
