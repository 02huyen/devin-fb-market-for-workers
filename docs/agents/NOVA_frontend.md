# Agent brief: NOVA — Frontend

## Context
**Workplace Market** is a scam-free marketplace of verified professionals. The MVP frontend (`frontend/`, Next.js 14 App Router + TypeScript + Tailwind) already has: login page with work-email magic link (`/`), verification page (`/verify`), and a marketplace page (`/market`) with search, sell/buy/giveaway filter, geolocation radius filter, listing creation, and seller company attribution.

Key files you own: **everything under `frontend/`**. The API client lives in `frontend/src/lib/api.ts`.

## Goal
1. **Listing detail page** (`/market/[id]`): full description, seller info (name, company, domain, location), contact CTA.
2. **My listings / profile page** (`/profile`): manage your own listings, edit display name.
3. **Image display & upload UI** (coordinate with Mercury's image API via `docs/API_CONTRACT.md`).
4. **Listing lifecycle UI** (after Mercury ships listing status/expiry): expiry-duration picker on the create form, "Mark as sold" / "Renew" buttons on your own listings, SOLD/EXPIRED badges, and a status filter (default: open only).
5. **Comments UI** (after Echo ships the comments API): public comment thread on the listing detail page; read-only once the listing is sold/expired.
6. **DM UI** (after Echo ships the messaging API): "Message seller" button on a listing, an inbox page (`/messages`) with unread counts, and a conversation thread view (poll/refetch for MVP).
7. **UX polish**: loading states, empty states, mobile responsiveness, nicer location picker (text input once Mercury ships geocoding — replace the raw lat/lng inputs).

## Rules
- Only edit files under `frontend/`. Never edit backend code — if the API is missing something, request it from Mercury via an issue/PR comment referencing `docs/API_CONTRACT.md`.
- Follow the existing patterns: typed API calls in `src/lib/api.ts`, Tailwind styling, client components with hooks.
- `npm run lint` and `npx tsc --noEmit` must pass before every PR.
- One feature branch, one PR per task. Never push to `main`.
- Keep the dev-mode magic-link display on the login page (it's how the app is tested without an email provider).
