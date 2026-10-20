# Finnish Grid Atlas — website and REST API

This is a **separate Next.js website**, complementing the existing
[Streamlit Atlas](https://finnish-grid-atlas.streamlit.app/). It preserves
the Python collector and existing Neon production PostgreSQL schema.

## Pages

- `/analysis` — 48-hour **historical 2026** PyPSA Finland one-bus analysis; source-linked real Fingrid consumption/production, hypothetical balancing constraint, four model scenarios; NOT site-level connection capacity
- `/api/v1/model/finland` — solver-verified historical model results and assumptions as model_scenario data, **not live observations or grid feasibility**

- `/screening` — evidence-qualified screening by demand/year and recorded voltage; never a feasibility conclusion
- `/api/v1/screening` — read-only screening and source-review evidence; 100 MW 2030 pilot returns two indicative threshold matches and three unknowns

- `/` — independent blue research homepage with conceptual evidence network
- `/stations` — historical operator-designation archive: 128 source-listed name+voltage rows (printed source total 127); table label 1.1.2020, not current MW or geography
- `/api/v1/stations` — read-only historical enumeration; optional `voltage` filter 400/220/110; separate from live Neon capacity evidence
- `/connections` — interactive 5-point × 2-direction × 3-year capacity evidence matrix, discrete comparison bars, individual provenance drawer, filtered raw records and source-audit worksheet
- `/operations` — three synchronized source-separated charts, 1/2/3/7 observed UTC-day windows anchored to the latest stored interval, provenance-preserving CSV export
- `/quality` — observed source-day continuity heatmap, distinct intervals versus retrieval revisions, and the original 18-row screenshot-comparison register
- `/method` — scientific method and validation limits
- `/api` — readable REST API documentation
- `/api/openapi.json` — machine-readable OpenAPI 3.1
- `/api/v1/health` — actual DB connectivity health (HTTP 200 or 503)
- `/api/v1/overview` — stored evidence counts and newest interval
- `/api/v1/points` and `/api/v1/points/{id}`
- `/api/v1/capacity` with optional year, direction, point_id
- `/api/v1/coverage` with observed vs missing compiled intersections
- `/api/v1/quality` with 30-day bounded source integrity and revision counts
- `/api/v1/export/recheck` with 18-row CSV reviewer worksheet (no fabricated confirmations)
- `/api/v1/operations` with source/dataset, UTC interval filters and pagination

All public endpoints are **read-only**. Missing numerical Grid Scope cells
are unknown, not zero; reported capacities cannot be added or interpolated.
The original 18 indicative values matched reviewer-provided screenshots on 18–19 October (17 exact tooltips and one visible panel MW). This is not certified connectability.

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

For dated canonical deployment status and numerical counts, see [STATUS](../docs/STATUS.md) and [EVIDENCE_LOG](../docs/EVIDENCE_LOG.md). The next paragraphs record the initial deployment milestone, not necessarily current row counts.\n\nDeployment: **https://finnish-grid-atlas.vercel.app** on Vercel. Live Neon
read connectivity was verified on **18 October 2026**, using a Sensitive,
Production-scoped `DATABASE_READ_URL` for the restricted reader. The public
API returned 5 connection points, 18 source-transcribed capacity records,
and 288 historical national operational intervals; Fingrid 124, Fingrid 74,
and ENTSO-E A65 each returned 96 intervals. These are persisted, historical
measurements, not a claim of real-time feeds or verified substation headroom.

GitHub authentication was connected to Vercel on 19 October 2026 and PR #31 was deployed to production. Subsequent draft PR previews must still be reviewed, merged and verified separately; a preview is not a production release.

## Robustness

- REST endpoint versioning, bounded pagination, explicit 400/404/503 errors.
- Safe query parameters, date windows at most 31 days, no SQL identifier injection.
- Explicit source capture and operational provenance, separate evidence categories.
- Read-only Neon role enforced by URL validation, TLS required.
- Same-origin REST calls, cache headers and defensive response metadata.
- No writes, user accounts, synthetic numerical observations or API keys.
- The original Streamlit app stays online as a fallback.

## Website artwork and live-DB operations

Brand assets use a six-node abstract grid icon and a conceptual network visual.
There are **no national boundaries, country maps, flags or official-looking insignia**
anywhere in the current website branding. The abstract lines and nodes are **not**
actual Fingrid transmission topology or locations of substations. The social
thumbnail is served at `/opengraph-image`.

**Historical production Neon integration milestone (18 October 2026):** the production
Vercel `DATABASE_READ_URL` is scoped Sensitive/Production, the health endpoint
returns HTTP 200 and the overview reports `data_mode:neon`. The 16 October
source refresh inserted 288 rows and the public API read back **576** historical
operational observations (two complete UTC days across three datasets).
The standalone Streamlit instance has its own Neon configuration.

For connection rotation or recovery, use the dedicated
`grid_dashboard_reader` user on the Neon `production` branch, `neondb`
database. Vercel Project → Settings → Environment Variables uses
`DATABASE_READ_URL` scoped **Sensitive/Production**, server-only
(never `NEXT_PUBLIC_*`). It must use a `.neon.tech` host and
`sslmode=require`; prefer the Neon pooler for serverless read queries.

**Do not paste the connection string into a chat or GitHub commit**, and do
not substitute the Neon database owner, backend collector writer, or
`NEON_API_KEY`. After a credential rotation, redeploy production and require:
- `/api/v1/health` → 200, database connected.
- `/api/v1/overview` → `data_mode:"neon"`, nonzero operational rows.
- `/operations` → nonempty, source-linked observations with UTC timestamps.
- `/api/v1/operations?source=fingrid&dataset_id=124&limit=1` → one authenticated historical record.

A configured but inaccessible database produces safe HTTP 503; there is no
automatic silent fallback to the compiled historical source snapshot.

A public-monitor workflow checks production pages and the API once daily
without provider or database secrets: `node website/scripts/check-public-site.mjs`.
The scheduled production workflow now requires a connected Neon database,
valid source-linked operational rows for all three feeds and recent timestamps
within the configured `MAX_OPERATIONAL_AGE_HOURS` (default 168). Standalone
local execution without `EXPECT_LIVE_DB=true` still supports an explicitly
declared historical snapshot. This monitor does not itself ingest new records. See
[the production runbook](../docs/SITE_OPERATIONS.md).

The **source collector** is distinct from the read-only website and monitor:
daily ingestion was approved and enabled 18 October 2026 on the existing
free-tier GitHub Actions schedule, **07:17 UTC daily**, with a conservative
three-day publication lag. It is opt-out via repository variable
`ENABLE_PUBLIC_REFRESH=false`; no push/PR collects source data. Stop it
through the workflow or variable before the next run if desired. Successful
source ingestion adds revision records and is not live telemetry.
