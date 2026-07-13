# Agent brief: ATLAS — Auth & Email Verification

## Context
You are working on **Workplace Market**, a marketplace where only users with verified **work emails** may participate (no gmail/yahoo/etc). The repo already contains a working MVP: FastAPI backend (`backend/`) with magic-link auth and layered work-email validation (blocklist → MX check → magic link → optional enrichment API), and a Next.js frontend (`frontend/`).

Key files you own:
- `backend/app/routers/auth.py` — request-link / verify / me / logout endpoints
- `backend/app/services/email_validation.py` — domain validation layers
- `backend/app/auth_utils.py` — session cookie handling

## Goal
Make authentication production-ready:
1. **Real email delivery**: integrate Resend (or SendGrid) to send the magic link. Keep the current dev-mode inline link behind `APP_ENV=dev`.
2. **Company enrichment**: finish the Abstract API (or Hunter.io) integration in `lookup_company_name` using `EMAIL_VERIFY_API_KEY`; store the verified company name on the user.
3. **Hardening**: rate-limit `/auth/request-link` (per email + per IP), single-use short-lived tokens, secure cookie flags in production, and keep the disposable-domain list current (the `disposable-email-domains` package is already available).

## Rules
- Only edit files under `backend/app/routers/auth.py`, `backend/app/services/`, `backend/app/auth_utils.py`, and new files under those paths. If you need model/schema changes, propose them in your PR description — `models.py`/`schemas.py` are owned by Mercury.
- Never commit API keys; read them from environment variables.
- One feature branch, one PR. Do not push to `main`.
- Keep `POST /auth/request-link`, `POST /auth/verify`, `GET /auth/me`, `POST /auth/logout` contracts backward compatible — the frontend depends on them.
- Add/keep the endpoints documented in `docs/API_CONTRACT.md` via PR if you change anything.
- See `docs/AGENT_ONBOARDING.md` for the current project overview.
