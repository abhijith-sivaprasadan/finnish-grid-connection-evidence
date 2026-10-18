# Finnish Grid Atlas — website and REST API

This is a **separate Next.js website**, complementing the existing
[Streamlit Atlas](https://finnish-grid-atlas.streamlit.app/). It preserves
the Python collector and existing Neon production PostgreSQL schema.

## Pages

- `/` — Kerala2040-style research home with real summary counters
- `/connections` — filtered point-specific indicative estimates
- `/operations` — national operational chart and source intervals
- `/method` — scientific method and validation limits
- `/api` — readable REST API documentation
- `/api/openapi.json` — machine-readable OpenAPI 3.1
- `/api/v1/health` — actual DB connectivity health (HTTP 200 or 503)
- `/api/v1/overview` — stored evidence counts and newest interval
- `/api/v1/points` and `/api/v1/points/{id}`
- `/api/v1/capacity` with optional year, direction, point_id
- `/api/v1/coverage` with observed vs missing compiled intersections
- `/api/v1/operations` with source/dataset, UTC interval filters and pagination

All public endpoints are **read-only**. Missing numerical Grid Scope cells
are unknown, not zero; reported capacities cannot be added or interpolated.
The original 18 values still await *independent* operator recheck.

## Local development

Requires Node 22+:

~~~bash
cd website
npm install
cp .env.example .env.local
# Insert Neon pooled URL for the dedicated grid_dashboard_reader role
npm run dev
npm test
npm run build
npm run typecheck
~~~

When `DATABASE_READ_URL` is absent, the homepage and connection-capacity
endpoints display a **clearly labelled compilation** of the 5 points and 18
indicative values captured in `data/manual/` on 17 October 2026. The public
snapshot is not operator-reconfirmed, not live, and excludes operational
series. The `/api/v1/health` route correctly remains HTTP 503 in this mode.
When a read URL is configured but invalid or the database fails, queries return
safe HTTP 503 errors instead of silently falling back to historical values.
Never set a privileged database credential. The secret is server-side only.

## No-cost deployment option

You can deploy this Next.js app on [Vercel Hobby](https://vercel.com/docs/plans/hobby)
**only if your use meets the plan's non-commercial personal-use terms**.
Create a new Vercel project from the existing GitHub repository and set:

- **Root Directory:** `website`
- **Framework:** Next.js
- **Private server-side environment variable:** `DATABASE_READ_URL`
- **Database credential:** Neon `grid_dashboard_reader` SELECT-only account
- **Database branch:** `production`; database `neondb`; TLS required
- Prefer the **pooled Neon endpoint** for serverless query workloads.

Never expose the DB URL as `NEXT_PUBLIC_*`. Do not use `neondb_owner`,
`NEON_API_KEY`, writer DB credentials or provider API tokens in the
web deployment. Python GitHub Actions remain the sole data collector.

Deployment: **https://finnish-grid-atlas.vercel.app** on Vercel (project
`finnish-grid-atlas`). The first production deploy was made from source files
because the Vercel account lacks a GitHub Login Connection. Automatic Git
releases require connecting GitHub within Vercel. A dedicated Neon reader
credential still needs to be configured in the Vercel project environment.
Until then, public connection observations come from the labelled Git snapshot.

## Robustness

- REST endpoint versioning, bounded pagination, explicit 400/404/503 errors.
- Safe query parameters, date windows at most 31 days, no SQL identifier injection.
- Explicit source capture and operational provenance, separate evidence categories.
- Read-only Neon role enforced by URL validation, TLS required.
- Same-origin REST calls, cache headers and defensive response metadata.
- No writes, user accounts, synthetic numerical observations or API keys.
- The original Streamlit app stays online as a fallback.
