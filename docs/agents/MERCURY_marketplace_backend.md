# Agent brief: MERCURY — Marketplace Backend

## Context
**Workplace Market** is a scam-free marketplace of verified professionals (work-email login). The MVP backend (`backend/`, FastAPI + SQLAlchemy) already supports listings with: sell/buy/giveaway types, keyword search, type filter, and lat/lng radius filtering (haversine). Auth is session-cookie based (owned by Atlas).

Key files you own:
- `backend/app/routers/listings.py`
- `backend/app/models.py` and `backend/app/schemas.py` (you are the owner of shared models — review other agents' requested changes)
- `docs/API_CONTRACT.md` (create and maintain it — it is the backend↔frontend interface)

## Goal
1. **Listing lifecycle (sold vs open + expiry)** — highest priority:
   - Replace the boolean `is_active` with a `status` field: `open` | `sold` | `expired` | `removed`.
   - `PATCH /listings/{id}/status` — seller-only; marking `sold` records `sold_at`.
   - `expires_at` on every listing: seller picks a duration at creation (7/14/30 days, default 30); expired listings are auto-hidden from default search (lazy-expire on read or a periodic job) with a `POST /listings/{id}/renew` endpoint to relist.
   - `GET /listings` defaults to `status=open`; support `?status=` filter so users can browse recently sold items for price reference, and sellers can see their own sold/expired listings.
2. **Geocoding**: let users enter "Austin, TX" and resolve to lat/lng server-side (e.g. Nominatim/OpenStreetMap with proper rate limits) so radius filtering works without manual coordinates.
3. **Images**: add listing image upload (S3 pre-signed URLs or UploadThing) with an `images` table/relation.
4. **Pagination & sorting**: cursor or offset pagination on `GET /listings`, sort by newest/price/distance.
5. **Categories**: add a category field + filter (electronics, furniture, etc).
6. Write `docs/API_CONTRACT.md` documenting every endpoint (request/response shapes).

Note: comments and DMs are owned by **Echo** (`docs/agents/ECHO_messaging_comments.md`). Echo will PR new model classes (Comment, Conversation, Message) into `models.py`/`schemas.py` — you review those PRs; the listing `status` field is the dependency Echo needs from you (comments lock when a listing is no longer `open`), so ship goal 1 first.

## Rules
- Only edit `backend/app/routers/listings.py`, `models.py`, `schemas.py`, new service files under `backend/app/services/` (except `email_validation.py`, owned by Atlas), and `docs/API_CONTRACT.md`.
- Do not modify auth code. Use the `get_current_user` dependency as-is.
- Keep existing endpoint contracts backward compatible; additive changes only unless coordinated via the API contract PR.
- One feature branch, one PR per task. Never push to `main`.
- All new endpoints must require authentication.
