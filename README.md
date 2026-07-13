# Workplace Market

A scam-free marketplace where every user is verified via their **work email** (no gmail/yahoo/etc). Buy, sell, and give away items with real, identifiable professionals — filter by keyword, type, and location radius, and see who is selling from what company.

- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind — `frontend/`
- **Backend**: FastAPI + SQLAlchemy (SQLite dev) — `backend/`
- **Plan & agent briefs**: `docs/MASTER_PLAN.md` and `docs/agents/`

## Quick start

```bash
# Backend → http://localhost:8000
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload

# Frontend → http://localhost:3000
cd frontend
npm install && npm run dev
```

Sign in with any real company email (e.g. `you@yourcompany.com`). In dev mode the magic link is shown inline on the login page — no email provider needed. Gmail/Yahoo/disposable domains are rejected.

## Testing

Backend tests use pytest and `fastapi.testclient` with a temporary SQLite DB:

```bash
cd backend
.venv/bin/pytest
.venv/bin/ruff check app
```

Frontend tests use Jest + Testing Library:

```bash
cd frontend
npm test -- --watchAll=false
npm run lint
npx tsc --noEmit
npm run build
```

## Docker local dev

One-command setup with Postgres, backend, and frontend:

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Postgres: `localhost:5432` (user/pass/db in `.env`)

The first build may take a few minutes. Use `docker compose down -v` to remove the Postgres volume.

## Environment variables

| Var | Where | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | frontend | Backend URL (default `http://localhost:8000`) |
| `FRONTEND_URL` | backend | For magic links + CORS (default `http://localhost:3000`) |
| `APP_SECRET_KEY` | backend | Session cookie signing (set in production) |
| `APP_ENV` | backend | `dev` (inline magic link) or `production` |
| `RESEND_API_KEY` | backend | Optional, for real magic-link email delivery |
| `HUNTER_API_KEY` / `EMAIL_VERIFY_API_KEY` | backend | Optional company-enrichment APIs |
