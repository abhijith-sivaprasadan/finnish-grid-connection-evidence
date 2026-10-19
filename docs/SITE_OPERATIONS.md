# Production site runbook — Finnish Grid Atlas

Last documented audit: 19 October 2026. Source of truth: [canonical status](STATUS.md), deployed HTTP responses,
GitHub Actions, and current Vercel project configuration (not a deployment guess).

## What works

- Public website: https://finnish-grid-atlas.vercel.app
- Canonical source root: `website/`; framework Next.js 16, Node 22.
- REST endpoints: `/api/v1/overview`, `/points`, `/capacity`, `/coverage`, `/operations`, `/health`, and `/api/openapi.json`.
- Production routes publicly served. The static capacity fallback is explicit.
- 5 public connection points, 18 transcribed indicative observations, 12 absent combinations in the compiled 2026/2030/2035 matrix. **All 18 original source transcriptions matched reviewer-provided screenshots; this is not validated network headroom.**
- **Verified 18 October 2026:** Sensitive, production-only `DATABASE_READ_URL` exists in Vercel; the deployed health route returns HTTP 200 with connected store; the overview reports `data_mode:neon`, 5 points, 18 original transcriptions, and 288 operational rows **at that dated deployment milestone**. Successful read connectivity is not an audit of PostgreSQL grants or Fingrid source values.
- Public monitor checks deployed pages daily. It cannot use secrets and is not a substitute for independent grid verification.

## Completed: Connect the restricted Neon database reader to Vercel

Completed 18 October 2026; all three operational data feeds have returned nonempty, source-linked rows. The instructions below are retained for rotation and recovery.

1. In **Neon**, open the existing project/branch `production`. Prefer the existing
   `neondb` database and the previously provisioned SELECT-only role
   `grid_dashboard_reader`. If necessary, verify this role has only database
   CONNECT, schema USAGE and SELECT on required tables/views (and **no** CREATE,
   INSERT, UPDATE, DELETE, schema ownership or default elevated membership).
2. In **Vercel**: Project `finnish-grid-atlas` → Settings → Environment
   Variables. Add a **sensitive/server-only** `DATABASE_READ_URL` scoped to
   `production`. It must use the `grid_dashboard_reader` username, a Neon
   `.neon.tech` host and `sslmode=require`. Prefer Neon's pooled endpoint.
   **Never** use the Neon owner/writer or API-management token.
3. Do **not** paste this connection string into chat, GitHub code, or
   `NEXT_PUBLIC_*` variables.
4. Trigger a fresh production deployment so the new setting is loaded.
5. Verify:
   - `GET /api/v1/health` → HTTP 200 with `"status":"ok","store":"connected"`.
   - `GET /api/v1/overview` → `data_mode:"neon"`, nonzero operational rows,
     and an operator interval timestamp.
   - `GET /operations?dataset_id=124` → actual Fingrid 124 intervals and chart.
   - `GET /api/v1/operations?source=fingrid&dataset_id=124&limit=1` → 200
     with a source-linked interval (not a fabricated row).
   - Compare one timestamp/unit against the original operator source.
   - Review new Vercel runtime logs for safe errors; secrets must not be printed.

If configured Neon connection fails, the API intentionally returns 503 rather
than silently substituting the historical compiled snapshot.

## P0: Verify the source transcription

Run the existing worksheet generator and recheck **each point, direction, year and unit**
with the Fingrid live viewer. Keep UTC review time, source URL and findings.
Do not mark a capacity observation `operator_confirmed` merely because the
transcription matches the current publicly indicative map.

See `docs/GRID_SCOPE_RECHECK.md`. For **new** observations, independently recheck the figures against
the public operator interface before using them in any capacity ranking.
Any changed current values belong in a **new dated capture**, not a destructive
edit of the original October 17 2026 source snapshot.

## P1: Live ingestion and freshness

- **Daily source ingestion approved and enabled 18 October 2026.**
  The one-shot trial for 2026-10-16 passed 96 continuous intervals each from
  Fingrid 124, Fingrid 74 and ENTSO-E A65; inserted 288 new observations
  atomically into Neon. Public production readback verified **576** total
  operational rows, latest UTC interval ending 2026-10-17 00:00.
  The original 18 indicative Grid Scope transcriptions were later screenshot-matched on 18–19 October (17 tooltips and one explicit panel MW). Not physical capacity validation.
- `.github/workflows/cloud-refresh.yml` now runs at **07:17 UTC daily** with
  a conservative **three-day publication lag** and one completed UTC day per
  run. It remains confined to `main` and standard runners; upstream API
  credentials and the database writer are restricted to private Actions.
  There is no unguarded push-to-ingest trigger.
- **Emergency stop:** set GitHub Actions repository variable
  `ENABLE_PUBLIC_REFRESH=false` (exact lowercase string), or disable the
  workflow from GitHub Actions. Setting it to `true` or leaving it unset
  permits approved scheduled runs. Manual workflow dispatch remains available
  while scheduled runs are disabled. To avoid the next run, stop it before
  07:17 UTC. A daily successful collection is not real-time telemetry.
- The scheduled `.github/workflows/site-monitor.yml` checks the public site daily with **no secrets**. Since production Neon was verified, the scheduled job now requires a connected database, nonempty stored observations and valid, nonstale operational rows from Fingrid 124, Fingrid 74 and ENTSO-E A65. Source URLs, units and timestamps are checked. Default freshness ceiling is `MAX_OPERATIONAL_AGE_HOURS=168`; the GitHub repository variable can tune that ceiling. A failing run should trigger workflow notifications according to the owner's GitHub preferences. This does **not** perform source ingestion.
- Test one intentional invalid-filter HTTP 400 and one real source link in each
  direction. Do not claim a 200 website health response validates the physical
  transmission system.

## P1: Automatic Vercel deploys from GitHub (still pending)

The current public build was published through direct file deployment because
the Vercel account lacks a GitHub Login Connection even though ChatGPT has
a GitHub connector. Connect GitHub in Vercel, link this **existing** repository,
set its Root Directory to `website`, build `npm run build`, install `npm ci`,
and verify one preview deployment on a harmless PR. Keep the old `web/`
proof-of-concept out of production.

## P2: Scientific analysis (optional)

- Recheck ENTSO-E A75 generation contract before adding it to the collector.
- Finland zonal PyPSA sensitivity must be reported as assumptions-based
  context, **never** as substation connection rights.
- Dutch congestion ingestion and illustrative CIGRE pandapower feeder require
  separate data terms, validation and representation caveats.

## Non-official branding

The independent six-node network symbol, home illustration and Open Graph
thumbnail now contain **no geographic or flag imagery**. They depict an
abstract research pipeline and should never be described as a real
transmission-grid map, actual substations or operator topology.
