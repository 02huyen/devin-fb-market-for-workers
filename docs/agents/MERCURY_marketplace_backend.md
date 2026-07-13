# Agent brief: MERCURY — Marketplace Backend

## Context
**Workplace Market** is a scam-free marketplace of verified professionals (work-email login). The MVP backend (`backend/`, FastAPI + SQLAlchemy) has listings with: sell/buy/giveaway types, keyword search, type filter, lat/lng radius filtering (haversine), status lifecycle (`open`/`sold`/`expired`/`removed`), expiry/renew, image uploads, and comments. Auth is session-cookie based (owned by Atlas); messages are owned by Echo.

Key files you own:
- `backend/app/routers/listings.py`
- `backend/app/models.py` and `backend/app/schemas.py` (you are the owner of shared models — review other agents' requested changes)
- `docs/API_CONTRACT.md` (create and maintain it — it is the backend↔frontend interface)

## Goal
1. **Listing lifecycle** — done; maintain `status` (`open`, `sold`, `expired`, `removed`), seller-only status patches, expiry, `POST /listings/{id}/renew`, and `GET /listings` `status` filters (`all`, `removed`, `open`, `sold`, `expired`).
2. **Geocoding**: convert `location_name` to lat/lng server-side (e.g. Nominatim/OpenStreetMap with proper rate limits) so the frontend can drop the coordinate inputs.
3. **Images**: already supports image upload and listing image relations; add `DELETE` for images, resize, and storage backend (S3 / UploadThing) for production.
4. **Pagination & sorting**: cursor or offset pagination on `GET /listings`, sort by newest/price/distance.
5. **Categories**: add a category field + filter (electronics, furniture, etc).
6. Keep `docs/API_CONTRACT.md` updated with every endpoint change.

## Rules
- Only edit `backend/app/routers/listings.py`, `models.py`, `schemas.py`, new service files under `backend/app/services/` (except `email_validation.py`, owned by Atlas), and `docs/API_CONTRACT.md`.
- Do not modify auth code. Use the `get_current_user` dependency as-is.
- Keep existing endpoint contracts backward compatible; additive changes only unless coordinated via the API contract PR.
- One feature branch, one PR per task. Never push to `main`.
- All new endpoints must require authentication.
- See `docs/AGENT_ONBOARDING.md` for the current project overview.
