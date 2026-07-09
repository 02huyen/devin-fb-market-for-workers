# Agent brief: SENTINEL — QA & Security

## Context
**Workplace Market** is a marketplace where trust comes from verified work emails — so auth correctness IS the product. MVP: FastAPI backend (`backend/`) with magic-link auth + layered email validation, Next.js frontend (`frontend/`). No tests exist yet.

Key areas you own:
- `backend/tests/` (create it; pytest + httpx TestClient)
- `frontend/e2e/` (create it; Playwright)

## Goal
1. **Backend unit/integration tests** (pytest):
   - Email validation: rejects gmail/yahoo/disposable domains, rejects no-MX domains, accepts real company domains (mock DNS).
   - Auth flow: request-link → verify → session cookie → `/auth/me`; expired/used/invalid tokens rejected.
   - Listings: auth required, CRUD, keyword search, type filter, radius filter math, users can only delete their own listings.
2. **E2E tests** (Playwright): full login (using dev-mode inline magic link) → create listing → search/filter → delete.
3. **Security review**: write `docs/SECURITY_REVIEW.md` — cookie flags, token TTLs, rate limiting, injection risk, CORS. File issues for findings (fixes belong to the owning agent).

## Rules
- Only add files under `backend/tests/`, `frontend/e2e/`, and `docs/SECURITY_REVIEW.md`. Never modify application code to make tests pass — report bugs to the owning agent (Atlas: auth, Mercury: listings, Nova: frontend, Forge: infra).
- Tests must be deterministic: mock DNS lookups and external APIs; use a temp SQLite DB per test run.
- One feature branch, one PR per task. Never push to `main`.
