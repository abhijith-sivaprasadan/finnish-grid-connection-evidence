# Production site runbook — Finnish Grid Atlas

Last audited: 18 October 2026. Source of truth: deployed HTTP responses,
GitHub Actions, and current Vercel project configuration (not a deployment guess).

## What works

- Public website: https://finnish-grid-atlas.vercel.app
- Canonical source root: `website/`; framework Next.js 16, Node 22.
- REST endpoints: `/api/v1/overview`, `/points`, `/capacity`, `/coverage`, `/operations`, `/health`, and `/api/openapi.json`.
- Production routes publicly served. The static capacity fallback is explicit.
- 5 public connection points, 18 transcribed indicative observations, 12 absent combinations in the compiled 2026/2030/2035 matrix. **None of the 18 have a completed independent source-value audit.**
- GitHub repository records a Neon production bootstrap and one persistent import of 288 operational records; this does not prove that Vercel can read them.
- Public monitor checks deployed pages daily. It cannot use secrets and is not a substitute for independent grid verification.

## P0: Connect the restricted Neon database reader to Vercel

Observed blocker: Vercel project `finnish-grid-atlas` had **no environment variables** when checked on 18 October 2026. Public `/api/v1/health` returned HTTP 503 and `/api/v1/overview` reported `data_mode:"compiled_snapshot"` and null latest operational interval.

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

See `docs/GRID_SCOPE_RECHECK.md`. Independently recheck the 18 figures against
the public operator interface before using them in any capacity ranking.
Any changed current values belong in a **new dated capture**, not a destructive
edit of the original October 17 2026 source snapshot.

## P1: Live ingestion and freshness

- The repository has `.github/workflows/cloud-refresh.yml`; it supports
  authenticated source-to-Neon persistence. Its daily schedule is guarded by
  repository variable `ENABLE_PUBLIC_REFRESH=true`. Leave that setting off
  until a **manual** complete-day run is rechecked for completeness and source
  consistency; setting it on makes real daily API requests.
- A separate `.github/workflows/site-monitor.yml` runs every day, querying
  public endpoints without private credentials. By default it validates the
  snapshot-versus-live mode honestly but does **not** assert Neon is connected.
- After confirming the reader + working operational persistence, set
  GitHub Actions repository variable `EXPECT_LIVE_DB=true`. This makes
  the monitor require Neon mode, nonempty operations, and an interval not older
  than `MAX_OPERATIONAL_AGE_HOURS` (default 168 hours). GitHub Actions
  will mark runs failed when those constraints fail; repository notification
  delivery depends on GitHub account settings.
- Test one intentional invalid-filter HTTP 400 and one real source link in each
  direction. Do not claim a 200 website health response validates the physical
  transmission system.

## P1: Automatic Vercel deploys from GitHub

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

## No false-official visual symbols

The cross/flag mark was removed. New branding uses an independent network
symbol, with public-domain, simplified Natural Earth regional geography.
The geographic background is real low-resolution boundary geometry; the grid
lines/nodes in the graphic are **illustrative**. Never market them as Fingrid's
actual circuit routes or connection-point coordinates.
