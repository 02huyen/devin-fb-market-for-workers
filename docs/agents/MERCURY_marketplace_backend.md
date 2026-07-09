# Agent brief: MERCURY — Marketplace Backend

## Context
**Workplace Market** is a scam-free marketplace of verified professionals (work-email login). The MVP backend (`backend/`, FastAPI + SQLAlchemy) already supports listings with: sell/buy/giveaway types, keyword search, type filter, and lat/lng radius filtering (haversine). Auth is session-cookie based (owned by Atlas).

Key files you own:
- `backend/app/routers/listings.py`
- `backend/app/models.py` and `backend/app/schemas.py` (you are the owner of shared models — review other agents' requested changes)
- `docs/API_CONTRACT.md` (create and maintain it — it is the backend↔frontend interface)

## Goal
1. **Geocoding**: let users enter "Austin, TX" and resolve to lat/lng server-side (e.g. Nominatim/OpenStreetMap with proper rate limits) so radius filtering works without manual coordinates.
2. **Images**: add listing image upload (S3 pre-signed URLs or UploadThing) with an `images` table/relation.
3. **Pagination & sorting**: cursor or offset pagination on `GET /listings`, sort by newest/price/distance.
4. **Categories**: add a category field + filter (electronics, furniture, etc).
5. Write `docs/API_CONTRACT.md` documenting every endpoint (request/response shapes).

## Rules
- Only edit `backend/app/routers/listings.py`, `models.py`, `schemas.py`, new service files under `backend/app/services/` (except `email_validation.py`, owned by Atlas), and `docs/API_CONTRACT.md`.
- Do not modify auth code. Use the `get_current_user` dependency as-is.
- Keep existing endpoint contracts backward compatible; additive changes only unless coordinated via the API contract PR.
- One feature branch, one PR per task. Never push to `main`.
- All new endpoints must require authentication.
