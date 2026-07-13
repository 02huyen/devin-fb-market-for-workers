# Agent brief: SENTINEL — QA & Security

## Context
**Workplace Market** is a marketplace where trust comes from verified work emails — so auth correctness IS the product. FastAPI backend (`backend/`) with magic-link auth + layered email validation, Next.js frontend (`frontend/`). Tests now exist in `backend/tests/` and `frontend/src/__tests__/`.

Key areas you own:
- `backend/tests/` (extend pytest coverage)
- `frontend/src/__tests__/` and `frontend/src/app/**/__tests__/` (extend unit/integration tests)
- `docs/SECURITY_REVIEW.md` (if it does not yet exist)

## Goal
1. **Backend unit/integration tests** (pytest):
   - Email validation: rejects gmail/yahoo/disposable domains, rejects no-MX domains, accepts real company domains (mock DNS).
   - Auth flow: request-link → verify → session cookie → `/auth/me`; expired/used/invalid tokens rejected.
   - Listings: auth required, CRUD, keyword search, type filter, radius filter math, users can only delete their own listings.
   - Messages: start conversation, send/receive, unread counts, participant-only access.
2. **Frontend tests** (Jest + Testing Library): exercise `api.ts`, major pages, and shared UI behaviors.
3. **E2E tests** (optional, Playwright): full login (using dev-mode inline magic link) → create listing → search/filter → message → delete.
4. **Security review**: write `docs/SECURITY_REVIEW.md` — cookie flags, token TTLs, rate limiting, injection risk, CORS. File issues for findings (fixes belong to the owning agent).

## Rules
- Add tests; fix only test/pipeline infrastructure. If application code fails a test, report the bug to the owning agent (Atlas: auth, Mercury: listings/messages, Nova: frontend, Forge: infra) unless you are explicitly fixing a discovered bug.
- Tests must be deterministic: mock DNS lookups and external APIs; use a temp SQLite DB per test run.
- One feature branch, one PR per task. Never push to `main`.
- See `docs/AGENT_ONBOARDING.md` for the current project overview and `docs/API_CONTRACT.md` for the API contract.
