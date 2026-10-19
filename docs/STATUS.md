# Finnish Grid Atlas — canonical project status

Last editorial verification: **19 October 2026 UTC**. This is a dated
state-of-work record, not a live database metric. For live values, consult
the [overview API](https://finnish-grid-atlas.vercel.app/api/v1/overview),
[quality API](https://finnish-grid-atlas.vercel.app/api/v1/quality) and
[health API](https://finnish-grid-atlas.vercel.app/api/v1/health).
A successful endpoint read is not proof that the underlying source is current.

## Deployed components

- Production website: [Finnish Grid Atlas](https://finnish-grid-atlas.vercel.app/),
  **Next.js in `website/`**. The `web/` folder is an archived prototype.
- Storage: Neon PostgreSQL. A server-only restricted, read-only
  `DATABASE_READ_URL` was confirmed connected on 18 October 2026.
  No client-side database credentials or API tokens are published.
- Historical operations: Fingrid national consumption dataset 124,
  Fingrid national production dataset 74 and ENTSO-E actual total load A65.
  These are **Finland-wide** readings, not a substation's available MW.
  Raw storage keeps retrieval revisions; the latest-observations view
  retains one version per source/interval.
- On 18 October, public APIs returned **864 stored rows, 576 distinct
  historical intervals and 288 retrieval revisions**. This is an
  observation at that point in time, not a permanent number.
- An unattended GitHub Actions source refresh succeeded on 18 October:
  [workflow run 39125767276](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39125767276).
  This is evidence of one scheduled success, not guaranteed continual uptime.
- GitHub login connection was configured and PR #31 production deployed on **19 October 2026** (commit `b019632`). Further changes on draft PR #32 and draft PR #34 are **preview only**, not yet live on the production domain. A source commit/PR preview is not equivalent to a production release.

## Source evidence

- Original 17 October capture: **5 sampled Fingrid 400-kV connection points,
  18 year/direction source-transcribed indicative MW figures**.
- On 18–19 October, **all 18 original values matched human-supplied
  screenshots** from Fingrid Grid Scope: **17 exact chart tooltips and
  1 explicit MW panel number**, no observed numerical discrepancy.
  See [audit ledger](audits/GRID_SCOPE_18_ROW_SCREENSHOT_RECHECK_2026_10_19.csv)
  and [audit scope](audits/README.md). Reviewer screenshots remain
  private pending redistribution-rights review.
- **This validates the numerical transcription comparison only.**
  It does not establish available substation headroom or reconstruct the original 17 October operator display,
  authenticate a network calculation, show actual connectability,
  allocate queue rights, or constitute Fingrid confirmation of available MW.
- **12 of 30** possible sample point/direction/year intersections were not
  transcribed. Unrecorded is **unknown**, not zero. Do not interpolate between
  effective years or sum values across substations.

## Historical operator station inventory work (draft PR #34)

- Fingrid designation appendix: **128 transcribed named substation rows** (400/220/110-kV), but original printed summary **127**; source table caption refers to **1.1.2020** despite appearing on the **2024 designation** page. It does not verify 2026 status.
- Separate staged CSV, validated independent local SQLite archival table, Vercel-previewed `/stations` search and read-only historical JSON. No new MW values or verified geographic coordinates.
- Current/geo-linked operating inventory remains a research objective; Fingrid’s **138 substations for 2025** are a different date/scope and cannot serve as an automatic denominator.
- This stage changes neither live Neon records nor the original five point / 18 capacity evidence sample.

## Remaining scope for Krios-style grid analysis

- **No verified source-to-point reinforcement project relationships** are
  populated; project data remains a template, not an investment-ready forecast.
- **No validated Finnish load-flow study**, operator-authenticated nodal
  connection offers or power availability curve has been completed.
- Netherlands congestion ingestion and pandapower/PyPSA sensitivity studies
  remain planned research extensions, not accomplished work.
- Upcoming priorities: verified reinforcement register, longer historical
  operations, evidence-qualified candidate screening, bounded PyPSA sensitivity,
  then a second market.

See [dated evidence log](EVIDENCE_LOG.md), [roadmap](ROADMAP.md),
[documentation/commit rules](CONTRIBUTING.md), and
[operations runbook](SITE_OPERATIONS.md).
