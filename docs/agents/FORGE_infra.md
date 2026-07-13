# Agent brief: FORGE — Infra, Database & CI

## Context
**Workplace Market** (work-email-verified marketplace) has local Docker Compose, Alembic migrations, and GitHub Actions CI. Production deployment is still manual.

Key areas you own:
- Root-level infra files: `docker-compose.yml`, `Dockerfile`s, `.github/workflows/`
- `backend/app/database.py` and `backend/alembic/` migrations
- Deployment configuration

## Goal
1. **Docker**: maintain `docker-compose.yml` with backend, frontend, and Postgres services. Optimize build and document env overrides.
2. **Postgres migration**: keep `database.py` reading `DATABASE_URL` with SQLite fallback; manage Alembic revisions and generate migrations when models change.
3. **CI (GitHub Actions)**: keep backend `ruff` + `pytest` and frontend `lint` + `tsc` + `test` + `build` running on every PR. Add security scanning or dependency auditing if useful.
4. **Deployment plan**: propose (in a doc PR) hosting: e.g. Vercel for frontend, Fly.io/Render for backend, Neon/Supabase for Postgres. Do not deploy without the owner's approval.

## Rules
- You may edit `backend/app/database.py`, add `backend/alembic/`, root infra files, and `.github/workflows/`. Do not change business logic in routers/services (owned by Atlas/Mercury) or `frontend/src` (owned by Nova) beyond env-variable wiring.
- Never commit secrets; use env vars and document required ones in `.env.example` files.
- One feature branch, one PR per task. Never push to `main`.
- CI must pass on your own PRs before requesting review.
- See `docs/AGENT_ONBOARDING.md` for the current project overview.
