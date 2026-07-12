# Deployment Plan

This document proposes a hosting stack for **Workplace Market**. It is a plan only — no production deployment should be performed without owner approval.

## Recommended stack

| Layer | Service | Reason |
|---|---|---|
| Frontend | **Vercel** | Native Next.js 14 hosting, automatic previews on PRs, CDN, and edge functions. |
| Backend | **Fly.io** or **Render** | Fly.io gives a single global anycast network and Postgres-aware platform; Render is simpler and has a generous free tier. |
| Database | **Neon** or **Supabase** (Postgres) | Serverless Postgres with branching, generous free tiers, and connection pooling out of the box. |
| Email | **Resend** | Already integrated in `backend/app/services/email_sender.py`; free tier and simple API. |
| DNS / CDN | **Cloudflare** or the provider's built-in domain (Vercel + Fly/Render custom domains). | Cloudflare offers free SSL, DNS, and caching if needed. |

## Environment variables

| Variable | Set on | Notes |
|---|---|---|
| `DATABASE_URL` | Backend | Postgres connection string from Neon/Supabase. Must include `sslmode=require` for managed Postgres. |
| `APP_SECRET_KEY` | Backend | Strong random secret for session cookie signing. |
| `APP_ENV` | Backend | Set to `production` in production. |
| `FRONTEND_URL` | Backend | Production frontend URL, e.g. `https://workplace-market.vercel.app`. |
| `NEXT_PUBLIC_API_URL` | Frontend | Production backend URL, e.g. `https://workplace-market-api.fly.dev`. |
| `RESEND_API_KEY` | Backend | For sending real magic-link emails. |
| `EMAIL_FROM` | Backend | A verified Resend sender address. |
| `HUNTER_API_KEY` / `EMAIL_VERIFY_API_KEY` | Backend | Optional company-enrichment APIs. |

## Backend deployment

### Fly.io

1. Install `flyctl` and run `fly launch` from `backend/`.  
2. Add a `fly.toml` with the Docker build context pointing to the backend or root `Dockerfile.backend`.  
3. Set secrets via `fly secrets set DATABASE_URL=... APP_SECRET_KEY=... RESEND_API_KEY=...`.  
4. `Dockerfile.backend` CMD already runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.  
5. On deploy, `app.database.setup_database()` runs `alembic upgrade head` automatically.  
6. For migration commands later, `fly ssh console` or `fly deploy` can run `alembic upgrade head`.

### Render

1. Create a **Web Service** and point it at the repo root.  
2. Use `Dockerfile.backend` as the build image.  
3. Set environment variables in the Render dashboard.  
4. Render can bind a managed Postgres or an external Neon/Supabase database.

## Frontend deployment

### Vercel

1. Import the repo and set the **Root Directory** to `frontend/`.  
2. Add `NEXT_PUBLIC_API_URL` under Environment Variables.  
3. Vercel runs `npm run build` automatically.  
4. Configure `FRONTEND_URL` in the backend to match the Vercel production/preview URL.

## Database migration strategy

- Use `alembic` for all production schema changes (`backend/alembic/`).  
- Run `alembic upgrade head` on startup via `app.database.setup_database()`.  
- For zero-downtime deploys, run migrations before the new backend process starts, or keep migrations additive and backward-compatible.

## High-availability / security notes

- Use `https` only for `FRONTEND_URL` and `NEXT_PUBLIC_API_URL`.  
- Set `APP_SECRET_KEY` to a long random value; rotate if leaked.  
- Enable Neon/Supabase connection pooling (PgBouncer) if using serverless Postgres to avoid connection limits.  
- Store all secrets in the hosting provider's secret manager, never in the repo.  
- Consider a separate `production` GitHub environment for CI/CD deploys once a deployment workflow is added.

## Cost estimate (free tier)

| Service | Free tier | Limit |
|---|---|---|
| Vercel | Hobby | 100 GB bandwidth, 6,000 build minutes/month |
| Fly.io | Free allowances | 3 shared-cpu-1x 256MB VMs, 3GB persistent volumes |
| Render | Free | 512 MB RAM, 100 GB bandwidth |
| Neon | Free tier | 0.5 GB storage, 500 compute hours |
| Supabase | Free tier | 500 MB storage, 2GB egress |
| Resend | Free | 100 emails/day |

## Next steps

1. Owner approves the plan and chooses a provider.  
2. Create a `deploy` GitHub Actions workflow (or use Vercel/Fly/Render integrations) triggered on `main` merges.  
3. Add `docker-compose.prod.yml` or `docker-compose.override.yml` if needed for staging.  
4. Set up production secrets and run a manual first deploy.

**Do not deploy to production without owner approval.**
