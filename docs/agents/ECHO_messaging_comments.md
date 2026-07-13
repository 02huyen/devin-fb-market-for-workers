# Agent brief: ECHO — Messaging & Comments

## Context
**Workplace Market** is a scam-free marketplace of verified professionals (work-email login). Auth, listings, comments, and DMs are now built. The backend is `backend/` (FastAPI + SQLAlchemy), the frontend is `frontend/` (Next.js). Comments live in `backend/app/routers/listings.py`; DMs live in `backend/app/routers/messages.py`.

Key areas you own:
- `backend/app/routers/listings.py` (comments routes)
- `backend/app/routers/messages.py` (conversation and message routes)
- `backend/app/models.py` and `schemas.py` for `Comment`/`Conversation`/`Message` — coordinate with Mercury if models need structural changes.

## Goal
1. **Comments on listings** (public Q&A, like FB Marketplace):
   - `Comment` model: id, listing_id, author_id, body, created_at, is_deleted.
   - `GET /listings/{id}/comments`, `POST /listings/{id}/comments`, `DELETE /listings/{id}/comments/{comment_id}` (author or listing owner only).
   - Comments are already read-only on `sold`/`expired` listings; polish deletion, pagination, and author-only edit.
2. **DMs about a listing** (private buyer↔seller):
   - `Conversation` model keyed on `(listing_id, buyer_id)` — one thread per buyer per listing; `Message` model: conversation_id, sender_id, body, created_at, read_at.
   - `POST /messages/conversations?listing_id=...` (start/reuse thread), `GET /messages/conversations`, `GET /messages/conversations/{id}/messages`, `POST /messages/conversations/{id}/messages`, `POST /messages/conversations/{id}/read`.
   - Only the buyer and the listing's seller can access a conversation.
   - Polling is fine for MVP; document a WebSocket upgrade path.
3. Document all endpoint changes in `docs/API_CONTRACT.md`.

## Rules
- Only edit `backend/app/routers/listings.py` (comments), `backend/app/routers/messages.py`, `models.py`/`schemas.py` for new fields, and `docs/API_CONTRACT.md`.
- Never modify auth code (`auth.py`) or listing lifecycle endpoints unless explicitly asked.
- All endpoints require authentication (`get_current_user`); enforce participant-only access on every conversation/message route.
- One feature branch, one PR per task. Never push to `main`.
- Frontend UI for comments/DMs is Nova's — coordinate via the API contract, don't edit `frontend/`.
- See `docs/AGENT_ONBOARDING.md` for the current project overview.
