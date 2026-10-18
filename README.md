# Finnish Grid Connection Evidence Screener

**Public Streamlit Atlas:** [finnish-grid-atlas.streamlit.app](https://finnish-grid-atlas.streamlit.app/) ·
[Editorial design specification](docs/ATLAS_DESIGN.md)

The original Streamlit app and newer Next.js website are distinct views over
source-qualified evidence. The Next.js site's blue-and-white design uses an
independent abstract grid/network identity, not an official national flag or a
geographic map. No presentation changes validate Grid Scope capacity estimates.


**New: full-stack website + REST API** — [Next.js site source](website/README.md)
in `website/` provides separate research pages for overview, connections,
national operations, methods and documented versioned
[`/api/v1` read-only endpoints](website/src/app/api/v1). It reuses the
existing source-evidence PostgreSQL database with the restricted
`grid_dashboard_reader` role and keeps the Python collector unchanged.
Node 22 CI runs locked dependency installation, a high-severity dependency
audit, API regression tests, type checking, a production build and HTTP
smoke tests. **The Next.js website is live** at https://finnish-grid-atlas.vercel.app/.
Its public connection estimates currently use a labelled historical snapshot
until the separate read-only Neon connection URL is configured in Vercel.
The existing Streamlit site stays live.

[![Evidence checks](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/workflows/ci.yml/badge.svg)](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/workflows/ci.yml)

A personal portfolio proof of concept for screening **published Finnish grid
connection evidence**. It combines a small, source-transcribed Fingrid Grid Scope
sample, an append-only SQLite evidence store, and a Streamlit dashboard. National
operational data has its own schema and view; it never becomes substation capacity.

**Original Streamlit hosted option:** The Streamlit read-only PostgreSQL
backend and opt-in scheduled collector are implemented. The user linked the
repository to an existing Neon project; its GitHub integration installed
`NEON_API_KEY` (secret) and `NEON_PROJECT_ID` (variable). The repository
can now privately discover the existing database writer URI and run the
[manual Neon bootstrap workflow](.github/workflows/neon-bootstrap.yml)
before the [scheduled refresh workflow](.github/workflows/cloud-refresh.yml)
is explicitly enabled. **Neon production bootstrapped successfully on 18 October 2026:**
[one-time GitHub Actions run](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39079398497)
created the cloud tables and read back **5 connection points and 18 indicative
source-transcribed capacity observations**. A later authenticated persistent import stored **288 historical national
operational records** (Fingrid consumption/production and ENTSO-E load,
15 October 2026 UTC). Automated scheduled refresh remains opt-in.
**Hosted app URL:** [Finnish Grid Atlas](https://finnish-grid-atlas.streamlit.app/).
The account owner confirmed the Streamlit deployment and database connection
on 18 October 2026. The Neon bootstrap had imported 5 points and 18 source-
transcribed capacity observations; the initial operational import succeeded, but independent
Grid Scope value verification remains pending. The site may sleep on the free
hosting tier. See [Free hosting setup and cost controls](docs/FREE_HOSTING.md).

**October 18 website note:** The production Vercel version is live but has no Neon reader environment variable. See [site operations](docs/SITE_OPERATIONS.md) for current blockers, daily monitoring and source verification. The hosted ingestion history below refers to Neon/Streamlit, not the still-disconnected Vercel build.\n\n**Current status:** the capacity-data path runs end to end with **18 source-transcribed
indicative observations at five 400 kV points**, captured on **17 October 2026**.
The original capture log describes same-source transcription checks, **not independent
reconfirmation of all 18 numeric estimates**. Do not present these as validated
operator-confirmed connection offers. Fingrid and ENTSO-E API clients are implemented, fixture-tested and checked
against their relevant response structures. On **17 October 2026**, authenticated
daily smoke runs succeeded for Fingrid consumption/production (datasets 124/74:
96+96 rows) and ENTSO-E actual load (A65: 96 rows), all for **14 October UTC**.
These verified **temporary** databases were deleted by Actions; no operational
records are distributed with the repository. To retain data for the dashboard,
run the opt-in [local persistent importer](docs/LIVE_CONTEXT_IMPORT.md) using
your private credentials. ENTSO-E generation (A75) and independent verification
of Grid Scope capacity estimates remain pending. No model runs are included.

## Run locally

Requires Python 3.11 or newer. From this repository in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m src.cli import-manual
.venv\Scripts\python.exe -m streamlit run app/dashboard.py
```

After installation on Windows, you can also run
`./run-dashboard.ps1`. On Linux/macOS, use `.venv/bin/python` in place of the
Windows executable. Commands assume the repo root. No API keys are needed to view
the published capacity sample.

By default, the dashboard reads `data/evidence.sqlite`, filters by point, direction, effective
year, source URL and capture snapshot, and exports selected evidence as CSV.
It draws discrete points, preserves MW/MVA, and shows `not published` for missing
combinations in this selection. Estimates at different points must not be summed.
The **Power availability outlook** tab compares **both** directions for all five
points across 2026/2030/2035, showing **18 observed and 12 not-present-in-this-compiled-capture
point-direction-year intersections** in the initial capture. Only one snapshot
is shown at a time. No lines are drawn between published years. This is an
indicative evidence comparison, not a ranked list of sites or a connection
entitlement.

## What is real, and what is pending

| Evidence | This release | Meaning |
|---|---|---|
| Published indicative capacity | 18 source-transcribed readings; five points; selected 2026/2030/2035 entries | Reported Fingrid indicative estimates, awaiting independent source cross-check |
| Operational context | Fingrid 124/74 and ENTSO-E A65 authenticated smoke tests passed; repo records a 288-row hosted Neon import, but Vercel remains disconnected | National Finnish load/production, not a substation measurement |
| Operator confirmation | Zero rows | Would require separate documentary evidence; public map values do not qualify |
| Model scenarios | Separate schema, zero rows | PyPSA/pandapower are optional future studies |
| Reinforcement projects | Separate schema and CSV template, zero rows | No source-verified project-to-point links in this release |
| Netherlands | Source/access assessment only | No congestion data imported or Dutch model claimed |

[Capture log](docs/CAPTURE_LOG.md) documents exactly what was read and spot-checked.
[Independent source-recheck guide](docs/GRID_SCOPE_RECHECK.md) documents
how to manually re-open each direction/year in Grid Scope and preserve audit
evidence. Its downloadable 18-row checklist starts entirely **pending**; no
independent numeric verification is claimed.
[Internal verification and integrity audit](docs/INTEGRITY_AUDIT_2026_10_17.md)
documents the difference between CSV-to-database consistency, operational
interval validation and outstanding independent operator-value confirmation.
The `python -m src.audit_integrity` command is part of continuous integration.
[Two-minute Krios-facing walkthrough](docs/KRIOS_DEMO.md) shows what the
outlook proves, what remains unverified, and how to discuss the portfolio
deliverable without claiming operator-confirmed connection headroom.
[Source register](docs/SOURCES.md) records access, reuse terms and unresolved items.
[API setup](docs/SETUP.md) explains account/key setup and the first live commands.
[Free online hosting setup](docs/FREE_HOSTING.md) describes Neon Free +
Streamlit Community Cloud deployment, private API key handling, strict daily
interval coverage and opt-in scheduled refresh.
[Persistent local import](docs/LIVE_CONTEXT_IMPORT.md) fetches all verified
operational feeds, validates the responses, and atomically inserts into a
Git-ignored SQLite database consumed by Streamlit.
[ENTSO-E manual live check](docs/ENTSOE_LIVE.md) provides a secret-backed, opt-in
GitHub Actions probe that never commits tokens or operational data. The ENTSO-E
parser handles both A01 sequential fixed intervals and A03 source-defined
variable-length blocks without interpolation; the corrected A65 load parser
passed an authenticated rerun on 17 October 2026.
[Fingrid manual live check](docs/FINGRID_LIVE.md) performs the analogous
secret-backed probe for consumption/production datasets 124/74 without storing
API credentials or raw operational data in Git.

## Evidence design

- `connection_point`: operator, published point name, voltage and source.
- `capacity_observation`: direction, explicit year (or null for current without a
  stated year), value/unit, status, source URL, capture time, publication date when
  known, and caveats. Imports never update an old observation. A repeated identical
  import is a no-op; conflicting IDs fail atomically.
- `grid_project` / `project_connection_point`: planned year, uncertainty and
  documented relationships. A project date is never converted into a MW release.
- `operational_series`: UTC start/end, metric, unit, source/dataset, retrieval time
  and national area. Retrieval revisions are retained; the context view selects
  the latest retrieved revision per interval.
- `scenario_result`: model version, JSON assumptions and `model_scenario` status.
  It cannot enter the default published-estimate view.

Schema migrations use SQLite `user_version` (currently 2). Version 2 rejects blank
numeric capacities rather than treating empty rows as evidence, and upgrades valid
version-1 databases without dropping historical observations. CSVs and API ingestion
are the reproducible inputs; the generated database is ignored by Git. UTC capture
time is not a substitute for an operator publication date, which stays unknown
when not stated. Source URLs must not contain API credentials.

## Relationship to existing work

This repo follows the evidence and limitations discipline of the existing local
PyPSA-NL and PRO1 projects. It has no dependency on their folders and copies no
coursework code or synthetic network data. [Repository assessment](docs/EXISTING_REPOS.md)
explains what can inform later modelling and why the MVP is original code.

| Grid analyst responsibility | Demonstrable output here |
|---|---|
| Own grid data | Audited registry, source-transcribed capacity records, two authenticated source smoke tests and a tested opt-in local persist operation |
| Understand current/future grid | Five-substation two-direction capacity outlook across discrete published years, unreported-cell visibility, and source-linked audit checklist |
| Model and assess | Clear modelling boundary and reserved scenario schema; no completed model claim |
| Maintain a power-availability database | Reproducible SQLite evidence records and filterable dashboard |

## Verify

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m src.cli quality
```

Tests cover evidence category isolation, units, timestamps, duplicate snapshots,
transaction rollback, API pagination/retries, credential-safe errors, XML interval
handling and dashboard interactions. Test data is labelled synthetic/test only.
Tests verify software behavior and transcription structure; they do not validate
Fingrid's network studies. See [verification record](docs/VERIFICATION.md).

## Scope and limitations

This is a portfolio screening tool, not a production service, connection queue,
reservation service or validated load-flow planning tool. Grid Scope coverage is
selective; observations at named substations do not imply access to the underlying
nodal network model. Finland-wide generation minus load is not connection headroom.
Planned dates and future estimates are conditional. Network interactions mean point
capacities are not independent. Fingrid does not guarantee the viewer is complete
or error-free; discuss an actual connection with the operator.

The sample contains no interpolation, power-factor conversion or fabricated
numbers. The operational clients currently cover Fingrid datasets 124/74 and
ENTSO-E actual load/generation per type only. NTC, flows, outages, reserves, automatic
scheduling and stretch modelling remain [tracked work](docs/ROADMAP.md).

Primary sources: [Fingrid Grid Scope](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/),
[Fingrid Open Data](https://data.fingrid.fi/en/instructions),
[ENTSO-E](https://transparency.entsoe.eu/), and
[Netbeheer Nederland](https://www.netbeheernederland.nl/netcapaciteit-en-flexibiliteit/capaciteitskaart).
Source data retains the operator's rights and terms; no blanket data licence is
asserted. This code is intended for the linked public portfolio repository; live API imports
into a **local** database and independent capacity transcription verification
are still pending.
