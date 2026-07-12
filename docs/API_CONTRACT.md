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
