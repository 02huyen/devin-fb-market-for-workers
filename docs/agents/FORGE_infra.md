# Agent brief: FORGE — Infra, Database & CI

## Context
**Workplace Market** (work-email-verified marketplace) MVP runs locally: FastAPI backend on SQLite (`backend/`), Next.js frontend (`frontend/`). No Docker, migrations, or CI yet.

Key areas you own:
- Root-level infra files: `docker-compose.yml`, `Dockerfile`s, `.github/workflows/`
- `backend/app/database.py` and a new `backend/alembic/` migrations setup
- Deployment configuration

## Goal
1. **Docker**: `docker-compose.yml` with backend, frontend, and Postgres services for one-command local dev.
2. **Postgres migration**: switch `database.py` to read `DATABASE_URL` (fall back to SQLite for quick dev), add Alembic and generate the initial migration from existing models.
3. **CI (GitHub Actions)**: backend — ruff + pytest; frontend — `npm run lint` + `npx tsc --noEmit` + `npm run build`. Run on every PR.
4. **Deployment plan**: propose (in a doc PR) hosting: e.g. Vercel for frontend, Fly.io/Render for backend, Neon/Supabase for Postgres. Do not deploy without the owner's approval.

## Rules
- You may edit `backend/app/database.py`, add `backend/alembic/`, root infra files, and `.github/workflows/`. Do not change business logic in routers/services (owned by Atlas/Mercury) or `frontend/src` (owned by Nova) beyond env-variable wiring.
- Never commit secrets; use env vars and document required ones in `.env.example` files.
- One feature branch, one PR per task. Never push to `main`.
- CI must pass on your own PRs before requesting review.
