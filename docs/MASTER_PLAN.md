# Workplace Market — Master Plan & Agent Assignment Guide

A trusted, scam-free marketplace where every user is verified via their **work email**. Think Facebook Marketplace, but every buyer/seller is a real, identifiable professional at a real company.

## 1. Current state (already built in this repo)

A working MVP scaffold:

- `backend/` — FastAPI + SQLAlchemy (SQLite for dev)
  - Magic-link login: `POST /auth/request-link` → `POST /auth/verify` → session cookie
  - Work-email validation: free/disposable-provider blocklist + DNS MX check + optional company-enrichment API hook (`EMAIL_VERIFY_API_KEY`)
  - Verified users stored in `users` table with `domain` + `company_name`
  - Listings API: create / list / soft-delete, keyword search, type filter (sell/buy/giveaway), lat/lng + radius filter (haversine)
- `frontend/` — Next.js 14 (App Router) + TypeScript + Tailwind
  - Login page (`/`), verification page (`/verify`), marketplace (`/market`) with search, filters, geolocation radius, and listing creation
- `docs/agents/` — one brief per agent (send each file to its agent)

## 2. Email verification strategy (the plan)

Layered defense — each layer is cheap and catches a different failure mode:

| Layer | What it does | Status |
|---|---|---|
| 1. Syntax | Pydantic `EmailStr` validation | Done |
| 2. Blocklist | Reject known free (gmail, yahoo, outlook…) and disposable (mailinator…) domains | Done |
| 3. MX check | DNS lookup — the domain must actually receive mail | Done |
| 4. Magic link | User must click a link sent to that inbox → proves ownership | Done (dev mode returns link inline; production needs an email provider) |
| 5. Company enrichment (recommended integration) | Confirm the domain belongs to a real company & fetch its name. Options: **Abstract API Company Enrichment** (hook already wired via `EMAIL_VERIFY_API_KEY`), Hunter.io Domain Search, or Clearbit/HubSpot Breeze | Hook wired, needs API key |
| 6. Email sending (production) | Resend, SendGrid, or AWS SES to actually deliver magic links | TODO (Atlas) |

## 3. Setup YOU need to do first (before assigning agents)

1. **Create the GitHub repo** (e.g. `workplace-market`) and grant Devin access, so agents can open PRs without conflicts.
2. **Sign up for an email provider** (Resend is easiest) → get `RESEND_API_KEY`.
3. **Sign up for Abstract API (or Hunter.io)** → get `EMAIL_VERIFY_API_KEY` (free tiers exist).
4. Add both keys as **Devin secrets** (org settings) so agents can use them.
5. Decide production DB: Postgres recommended (Neon/Supabase free tier). Give the `DATABASE_URL` to Forge.
6. Assign agents in the order in section 5, sending each their brief from `docs/agents/`.

## 4. The agents

| Agent | Name | Owns | Brief |
|---|---|---|---|
| Auth & Verification | **Atlas** | `backend/app/routers/auth.py`, `backend/app/services/`, email sending | `docs/agents/ATLAS_auth_verification.md` |
| Marketplace Backend | **Mercury** | `backend/app/routers/listings.py`, models, search/geo | `docs/agents/MERCURY_marketplace_backend.md` |
| Frontend | **Nova** | Everything in `frontend/` | `docs/agents/NOVA_frontend.md` |
| Infra, DB & CI | **Forge** | Docker, Postgres migration, CI, deployment | `docs/agents/FORGE_infra.md` |
| QA & Security | **Sentinel** | Tests (backend + e2e), security review | `docs/agents/SENTINEL_qa.md` |

**Conflict-avoidance rules (apply to all agents):**
- Each agent only edits files in its ownership area (declared in its brief). Shared files (`models.py`, `schemas.py`) are owned by Mercury; others request changes via PR comments or small isolated PRs.
- One feature branch + one PR per agent per task; never push to `main`.
- The API contract (`docs/API_CONTRACT.md`, to be maintained by Mercury) is the interface between backend and frontend agents — change it via PR before implementing.

## 5. Recommended ordering

**Wave 1 (parallel, no conflicts):**
- **Forge**: Dockerize, Postgres + Alembic migrations, CI (lint + typecheck + tests).
- **Atlas**: real email sending (Resend), enrichment API integration, rate limiting.
- **Nova**: profile page, listing detail page, image upload UI (behind API contract).

**Wave 2 (after Wave 1 merges):**
- **Mercury**: image uploads (S3/UploadThing), pagination, categories, geocoding of location names (so users type "Austin, TX" instead of lat/lng).
- **Sentinel**: pytest suite for auth + listings, Playwright e2e for the login→post→search flow.

**Wave 3:**
- Messaging between buyer/seller, notifications, moderation/reporting, deployment to production.

## 6. Running locally

```bash
# Backend (http://localhost:8000)
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload

# Frontend (http://localhost:3000)
cd frontend && npm install && npm run dev
```

Dev mode: the magic link is shown directly on the login page (no email provider needed).
