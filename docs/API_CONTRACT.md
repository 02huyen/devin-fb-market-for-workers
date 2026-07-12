# Workplace Market — API Contract

This document describes the backend API endpoints. It is the interface between backend and frontend development.

## Auth

### `POST /auth/request-link`
Request a magic sign-in link.

**Body:**
```json
{
  "email": "user@company.com"
}
```

**Response:**
```json
{
  "message": "Check your work email for a sign-in link.",
  "dev_magic_link": "http://localhost:3000/verify?token=..."
}
```

### `POST /auth/verify?token=<token>`
Verify a magic link and set the session cookie.

**Response:**
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
Get the current authenticated user.

### `POST /auth/logout`
Clear the session cookie.

## Listings

### `GET /listings`
List active listings. Supports `q`, `listing_type`, `lat`, `lng`, and `radius_miles` query parameters.

### `POST /listings`
Create a new listing. Requires authentication.

### `DELETE /listings/{id}`
Soft-delete the current user's listing.

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
    "body": "Is this still available?",
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
Create a comment on a listing. The listing must be active (open).

**Body:**
```json
{
  "body": "Is this still available?"
}
```

### `DELETE /comments/{id}`
Soft-delete a comment. Only the comment author or the listing owner may delete.
