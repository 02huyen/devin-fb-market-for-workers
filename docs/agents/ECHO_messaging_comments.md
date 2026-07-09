# Agent brief: ECHO — Messaging & Comments

## Context
**Workplace Market** is a scam-free marketplace of verified professionals (work-email login). The MVP backend (`backend/`, FastAPI + SQLAlchemy) has auth (Atlas) and listings (Mercury); the frontend (`frontend/`, Next.js) is owned by Nova. Your job is the social layer: public comments on listings and private DMs about a listing.

Key areas you own:
- `backend/app/routers/comments.py` (create)
- `backend/app/routers/messages.py` (create)
- Comment/DM-related models — propose additions to `models.py`/`schemas.py` via PR to Mercury (the models owner), or in a small isolated PR that only adds new classes without touching existing ones.

## Goal
1. **Comments on listings** (public Q&A, like FB Marketplace):
   - `Comment` model: id, listing_id, author_id, body, created_at, is_deleted (soft delete).
   - `GET /listings/{id}/comments`, `POST /listings/{id}/comments`, `DELETE /comments/{id}` (author or listing owner only).
   - Comments allowed only on `open` listings; read-only once sold/expired.
2. **DMs about a listing** (private buyer↔seller):
   - `Conversation` model keyed on (listing_id, buyer_id) — one thread per buyer per listing; `Message` model: conversation_id, sender_id, body, created_at, read_at.
   - `POST /listings/{id}/conversations` (start/reuse thread), `GET /conversations` (my inbox with unread counts), `GET/POST /conversations/{id}/messages`.
   - Only the buyer and the listing's seller can access a conversation.
   - Polling is fine for MVP (frontend refetch); document a WebSocket upgrade path but don't build it yet.
3. Document all endpoints in `docs/API_CONTRACT.md` (Mercury owns the file — add your section via PR).

## Rules
- Only add new files under `backend/app/routers/` and new model/schema classes; never modify auth code or existing listing endpoints.
- All endpoints require authentication (`get_current_user`); enforce participant-only access on every conversation/message route.
- One feature branch, one PR per task. Never push to `main`.
- Frontend UI for comments/DMs is Nova's — coordinate via the API contract, don't edit `frontend/`.
