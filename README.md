# Finnish Grid Connection Evidence Screener

**Live Next.js Atlas:** [finnish-grid-atlas.vercel.app](https://finnish-grid-atlas.vercel.app/) ·
[Original Streamlit Atlas](https://finnish-grid-atlas.streamlit.app/) ·
[API specification](https://finnish-grid-atlas.vercel.app/api/openapi.json)

**Grid Analyst portfolio release (20 October 2026):** [role-specific case study](https://finnish-grid-atlas.vercel.app/case-study) · [reproducible demonstration](docs/KRIOS_DEMO.md) · [MVP acceptance matrix](docs/KRIOS_PORTFOLIO_RELEASE.md) · [dated status](docs/STATUS.md).

**Overview:** Five selected Fingrid Grid Scope points, 18 original conditional estimates screenshot-matched on 18–19 October, actual Fingrid national and ENTSO-E A65 historical measurements, SQLite/Neon source provenance, 100 MW screening, and separate solver-verified PyPSA research. Operator-confirmed connectable MW remains **zero**. Finland MVP complete at the functional/code level; Dutch stretch and operator-grade AC model not complete.

A **personal, independent grid-data research and screening project**, not a grid operator, a network reconstruction, or a guarantee of available connection capacity. The Next.js website uses an abstract blue data-network identity, with no official flag, map, or agency branding. It exposes a read-only, source-linked REST API and national operational chronology while the original Python Streamlit application remains available.

### Canonical status and evidence history

**Current project status:** [docs/STATUS.md](docs/STATUS.md) ·
[Dated ingestion, source and CI milestones](docs/EVIDENCE_LOG.md) ·
[Contribution discipline](docs/CONTRIBUTING.md).

The active Next.js deployment uses **`website/`** (the `web/` prototype is
archived), read-only Neon PostgreSQL and three historical national energy
feeds. A successful **scheduled** refresh is recorded in the evidence log.
Public operational row counts change as new intervals and retrieval
revisions are stored; query the [overview API](https://finnish-grid-atlas.vercel.app/api/v1/overview)
and [quality API](https://finnish-grid-atlas.vercel.app/api/v1/quality)
instead of treating old README values as permanently current.

**Source verification:** All **18 original indicative Grid Scope transcriptions**
matched human-supplied Fingrid screenshots on 18–19 October 2026
(17 year-specific tooltips and 1 explicit panel MW value), recorded in the
[dated 18-row audit](docs/audits/GRID_SCOPE_18_ROW_SCREENSHOT_RECHECK_2026_10_19.csv).
This **does not** establish physically available transmission-grid headroom,
operator confirmation or guaranteed connectability. Missing combinations
remain unknown, never zero.

Manual Vercel uploads are still distinct from automatic Git-based deployments.
This repository is a portfolio research tool, **not** a SCADA platform or
certified connection-availability system.

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

## Grid connection readiness and Netherlands official-source pilot

The Finland [screening tool](https://finnish-grid-atlas.vercel.app/screening) now independently classifies **Fingrid's 250 MW switchyard-voltage planning guidance** from the published indicative MW threshold, with switchyard/line selection, 110 kV case-by-case exceptions, explicit next actions and a downloadable evidence brief. Two historical 100 MW / 2030 threshold matches remain a **voltage-pathway review**, not feasible site offers.

A separately licensed-conservative [Netherlands source audit](https://finnish-grid-atlas.vercel.app/netherlands) covers **three real original Netbeheer Nederland capacity-map CSV schemas, 896 dated source rows**, source SHA-256 and aggregate TenneT consumption/feed-in codes. It is NOT a Dutch project capacity estimator or a current grid-connection right, and no original location-level Dutch rows are redistributed. [Audit and boundaries](docs/KRIOS_CONNECTION_READINESS_AND_NL_PILOT.md).

## Engineering laboratory (isolated solvers, verified reports)

The optional **[interactive engineering lab](https://finnish-grid-atlas.vercel.app/engineering)** adds nonlinear pandapower CIGRE HV/MV AC power flows, source-accounted HV N−1 contingencies, a common synthetic three-bus independent pandapower/PyPSA nonlinear-AC agreement test, two-region *assumption-bound* Finnish PyPSA v2, and licence-verified 2024 OSM line-template input uncertainty. See [complete engineering methods and reproducibility](docs/KRIOS_ENGINEERING_LAB_RELEASE.md).

The **[interactive OSM proxy coordinate map](https://finnish-grid-atlas.vercel.app/network-map)** displays 104 high-voltage AC virtual source buses and 137 reconstructed source links from a 2024 ODbL-derived network candidate. These 104 points are **NOT** known operator substations or matches for the five source-reviewed Grid Scope points. No approved connection MW, certified 2025 physical network calibration or true Finnish N−1 engineering compliance is claimed.

pandapower 3.5.6 requires pandas 2.3 while PyPSA 1.4 requires pandas 3+. The dedicated Actions workflow builds each solver **in its own pinned environment**, exports JSON and compares solved results separately. Do not force both into the app's ingestion environment.



After the normal manual capacity import, run `python -m src.cli import-verified-model` to load **12** source-hash-verified solver metrics from the already-published four 48-hour PyPSA cases into the **local SQLite scenario_result table**, not into the capacity-observation table. Reruns are idempotent. This command does **not** write Neon or update the hosted capacity API. PyPSA model inputs and outputs are additional historical sensitivity evidence only. See [reproduction and acceptance](docs/KRIOS_PORTFOLIO_RELEASE.md).

## What is real, and what is pending

| Evidence | This release | Meaning |
|---|---|---|
| Published indicative capacity | 18 original source-transcribed readings; 17 screenshot tooltip matches and 1 panel MW match on 18–19 October | Fingrid indicative estimates, not certified or guaranteed available MW |
| Operational context | Historical national Fingrid 124/74 and ENTSO-E A65 records persisted to read-only Neon website; see dated [evidence log](docs/EVIDENCE_LOG.md) and live [API](https://finnish-grid-atlas.vercel.app/api/v1/quality) | Historical retrieval rows include revisions; not nodal headroom |
| Operator confirmation | Zero rows | Would require separate documentary evidence; public map values do not qualify |
| Model scenarios | Verified 48-hour, winter and market-corridor PyPSA JSON studies; 12 optional single-bus metric records can be imported into local SQLite | Hypothetical and separate; never operator headroom or source capacity |
| Reinforcement projects | Separate schema and CSV template, zero rows | No source-verified project-to-point links in this release |
| Netherlands | Source/access assessment only | No congestion data imported or Dutch model claimed |

[Capture log](docs/CAPTURE_LOG.md) documents exactly what was read and spot-checked.
[Independent source-recheck guide](docs/GRID_SCOPE_RECHECK.md) documents
how to manually re-open each direction/year in Grid Scope and preserve audit
evidence. Its blank worksheet is intended for a **new** review; the original sample\x27s completed screenshot comparison is tracked separately in [audit metadata](docs/audits/README.md).
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
interval coverage and the approved scheduled refresh controls.
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
| Model and assess | Solver-verified PyPSA national, winter and market-corridor sensitivities with separate source and model limitations |
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
numbers. The operational ingestion is verified for Fingrid datasets 124/74 and
ENTSO-E actual load A65. Historic Swedish commercial-border data and PyPSA studies are published as distinct research, not nodal telemetry. NTC, reserves, physical AC branch constraints and Netherlands ingestion remain [tracked work](docs/ROADMAP.md). Source refresh is scheduled with an emergency stop control.

Primary sources: [Fingrid Grid Scope](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/),
[Fingrid Open Data](https://data.fingrid.fi/en/instructions),
[ENTSO-E](https://transparency.entsoe.eu/), and
[Netbeheer Nederland](https://www.netbeheernederland.nl/netcapaciteit-en-flexibiliteit/capaciteitskaart).
Source data retains the operator's rights and terms; no blanket data licence is
asserted. This code is intended for the linked public portfolio repository; live API imports
into a **local** database is an optional exercise; hosted Neon source ingestion\nand a screenshot comparison of the original Grid Scope 18-row sample have been completed.
