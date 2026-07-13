# Agent Onboarding — Workplace Market

This doc is the single source of truth for any future Devin agent working on the repo. The `docs/agents/` briefs are historical; the current code and `docs/API_CONTRACT.md` are the authoritative interfaces.

## What this app is

A workplace-only marketplace where users prove their identity via a work email and a magic-link flow. Logged-in users can browse, search, post, and manage listings; they can also message sellers about a listing.

## Stack & layout

| Layer | Tech | Location |
|---|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind | `frontend/` |
| Backend API | FastAPI, SQLAlchemy, Pydantic | `backend/app/` |
| Dev DB | SQLite with `DATABASE_URL` fallback | `backend/workplace_market.db` |
| Production DB | Postgres (migrated via Alembic) | `backend/alembic/` |
| Tests | `pytest` (backend), Jest + Testing Library (frontend) | `backend/tests/`, `frontend/src/__tests__/` and `frontend/src/app/**/__tests__/` |
| CI | GitHub Actions | `.github/workflows/ci.yml` |

## How to run locally

```bash
# Backend
cd backend
.venv/bin/uvicorn app.main:app --reload  # http://localhost:8000

# Frontend
cd frontend
npm run dev  # http://localhost:3000
```

Dev mode shows the magic link inline on the login page so no email provider is needed.

## Key backend files

- `backend/app/routers/auth.py` — magic-link request/verify, session cookie, `/auth/me`, logout.
- `backend/app/routers/listings.py` — listings CRUD, search, filters, lifecycle, comments.
- `backend/app/routers/messages.py` — per-listing conversations and messages.
- `backend/app/services/email_validation.py` — domain blocklist, MX check, optional company enrichment.
- `backend/app/services/email_sender.py` — Resend/SendGrid fallback.
- `backend/app/auth_utils.py` — signed session cookie (`wm_session`).
- `backend/app/models.py` and `schemas.py` — shared models/schema definitions (owned by Mercury; if you add models, keep them isolated and update the schema).

## Key frontend files

- `frontend/src/lib/api.ts` — all API calls and TypeScript interfaces. This is the source of truth for frontend types.
- `frontend/src/app/page.tsx` — login.
- `frontend/src/app/verify/page.tsx` — magic-link verification.
- `frontend/src/app/market/page.tsx` — marketplace listing feed with search/filters.
- `frontend/src/app/market/[id]/page.tsx` — listing detail + comments + "Message seller".
- `frontend/src/app/profile/page.tsx` — profile + own listings management.
- `frontend/src/app/messages/page.tsx` — inbox.
- `frontend/src/app/messages/[id]/page.tsx` — conversation thread.

## API contract

`docs/API_CONTRACT.md` documents every endpoint and the request/response shapes. If you change an endpoint, update the contract first and keep the frontend `api.ts` in sync.

## Auth flow

1. `POST /auth/request-link` with `email`.
2. In `dev`, the response returns `dev_magic_link` inline.
3. Visit `/verify?token=...`.
4. `POST /auth/verify?token=...` sets `wm_session` cookie.
5. All authenticated endpoints require that cookie.

## Session/dev notes

- Auth is session-cookie based. `APP_ENV=dev` enables inline magic links and non-Secure cookies.
- Work-email validation rejects free/disposable domains and requires MX records; DNS must be reachable.
- `getImageUrl()` in `api.ts` must be used for `ListingImage.url` values because the backend serves them at `/uploads/` and the frontend may be on a different host in dev.

## Testing

Before any PR:

```bash
cd backend
.venv/bin/ruff check app
.venv/bin/pytest

cd frontend
npm run lint
npx tsc --noEmit
npm test -- --watchAll=false
npm run build
```

## Do not

- Commit secrets or `.env` files.
- Push directly to `main`.
- Skip CI checks.
- Edit `models.py`/`schemas.py` without checking `docs/API_CONTRACT.md` and the relevant frontend types in `api.ts`.

## Common gotchas

- `Listing` `status` values are `open`, `sold`, `expired`, `removed`.
- `GET /listings` defaults to `status=open`; `status=all` is supported.
- `expires_in_days` must be `7`, `14`, or `30`.
- Messages are under `/messages/conversations` with `listing_id` as a query parameter on `POST`.
- `ConversationOut` returns `other_participant` and `listing`, not `buyer`/`seller` full objects.
- `MessageOut` `sender` is a `Participant` (id, display_name, company_name), not a full `User`.
