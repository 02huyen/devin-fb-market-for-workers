# Agent brief: NOVA — Frontend

## Context
**Workplace Market** is a scam-free marketplace of verified professionals. The frontend (`frontend/`, Next.js 14 App Router + TypeScript + Tailwind) currently has: login page (`/`), verification (`/verify`), marketplace (`/market`) with search/filters/listing creation, listing detail (`/market/[id]`), profile (`/profile`), inbox (`/messages`), and conversation thread (`/messages/[id]`). Comments and DMs are wired end-to-end.

Key files you own: **everything under `frontend/`**. The API client lives in `frontend/src/lib/api.ts`.

## Goal
1. **Listing detail page** (`/market/[id]`): already exists; polish layout, add image gallery, improve contact CTAs.
2. **My listings / profile page** (`/profile`): already exists; add stats, pagination, and better empty states.
3. **Image display & upload UI**: already wired; switch to `next/image` for optimization, add image deletion.
4. **Listing lifecycle UI**: already exists; add expiry warnings, bulk actions, and clearer status badges.
5. **Comments UI**: already exists; add real-time updates, comment deletion by author/owner.
6. **DM UI**: already exists; add optimistic updates, polling for new messages, and better notifications.
7. **UX polish**: loading states, empty states, mobile responsiveness, nicer location picker (text input + geocoding once Mercury ships it).

## Rules
- Only edit files under `frontend/`. Never edit backend code — if the API is missing something, request it from Mercury via an issue/PR comment referencing `docs/API_CONTRACT.md`.
- Follow the existing patterns: typed API calls in `src/lib/api.ts`, Tailwind styling, client components with hooks.
- `npm run lint`, `npx tsc --noEmit`, `npm test -- --watchAll=false`, and `npm run build` must pass before every PR.
- One feature branch, one PR per task. Never push to `main`.
- Keep the dev-mode magic-link display on the login page (it's how the app is tested without an email provider).
- See `docs/AGENT_ONBOARDING.md` for the current project overview and `docs/API_CONTRACT.md` for the API contract.
