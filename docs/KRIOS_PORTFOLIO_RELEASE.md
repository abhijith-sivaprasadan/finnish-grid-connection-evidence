# Krios Grid Analyst — portfolio release and original-plan acceptance

**Assessment date:** 20 October 2026. **Project:** Finnish Grid Atlas / Finnish Grid Connection Evidence Screener, an independent personal research proof of concept. This page maps implementation against the Oct 17 "Krios Grid Analyst — Real-Data Project Plan"; it is **not** a Krios or Fingrid project deliverable.

## Release decision

**The plan's Finland-only MVP (Phases 0–3) is functionally implemented.** It requires five genuine Grid Scope observations (or honestly fewer), typed ingestion of Fingrid and ENTSO-E national context, a reproducible database, and an interactive Streamlit power-availability view. The source sample and code meet these requirements. Do not advertise a current capacity offer, a source-validated power flow, two-country data or uninterrupted hosting. Verify the public deployment and current update freshness before a presentation.

## Acceptance evidence, no invented pass conditions

| Original plan requirement | Evidence | Disposition |
| --- | --- | --- |
| Five real capacity observations at points, or documented fewer | Five sampled Fingrid 400-kV Grid Scope points, 18 published-indicative direction/year readings, captured 17 Oct 2026 | **Met** for source-transcribed historical sample; NOT validated current grid headroom |
| Source URLs, observation time, direction, effective year, MW/MVA and status | Immutable manual CSV and normalized typed SQLite records, source-observed capture date, source links, caveats; screenshot review ledger 18/18 | **Met** for the sample. Operator publication date stays unknown where not stated |
| Clear published-indicative vs. model-scenario vs. operator-confirmed classification | Typed schema, distinct tables, capacity screening and API; scenario import rejects false operator claims | **Met**. Operator-confirmed capacity has zero rows |
| Real Fingrid + ENTSO-E data normalized as national context | Authenticated Fingrid 124/74 and ENTSO-E A65; PostgreSQL historical records, revision-preserving ingest, scheduled refresh with a verified successful example | **Met** for core historical feeds; no guarantee of 24/7 updates or per-row portal cross-audit |
| SQLite generated from reproducible source commands | Manual CSV importer, schema v2 and isolated verified-PyPSA scenario importer; tests assert idempotency and rollback | **Met** for local reproducibility; scenario importer is explicitly optional and **does not write Neon** |
| Dashboard filters point, direction, year and capture; shows unknowns | Original Streamlit frontend, published-year matrix, 18/30 captured combinations, 12 unknown; hosted Next.js/Neon variant and REST API | **Met** in application code. The current deployment should be independently checked |
| Honest personal-project README and limitations | Root README, source register, methodology, dated status and dedicated case-study page | **Met** subject to matching the promoted production version |
| Finnish PyPSA sensitivity (stretch Phase 4) | Four source-verified 48-hour one-bus cases; 54 long-winter solves; 24 three-zone cross-border market simulations, all separate from Grid Scope estimates | **Additional verified research**, NOT operator-approved grid simulation or a nodal capacity estimate |
| Netherlands DSO congestion and CIGRE pandapower (stretch Phases 5–6) | No authenticated Dutch dataset import and no completed Dutch model | **Not done — deliberately outside Finland MVP** |
| Polish, job-specific narrative (Phase 7) | Source-linked demonstration and mapping below, independently reproducible code | **Met** once current release CI and deployment are checked |

## Three evidence tiers are never interchangeable

**Tier 1: Published indicative capacity (PRIMARY).** Fingrid Grid Scope source-transcribed MW by exact point, connection direction, capture and effective year. Source screenshot correspondence is not operator confirmation, nor a capacity guarantee; missing years remain null/unknown, not zero.

**Tier 2: National operational history (CONTEXT).** Fingrid datasets 124/74 and ENTSO-E A65 are historical Finnish totals, with source-defined UTC interval boundaries. National generation less consumption cannot establish local substation MW.

**Tier 3: PyPSA model scenarios (OPTIONAL).** Hypothetical dispatch, flexible project load and battery cases anchored to historical national readings or 2025 commercial border market datasets. The modelled support ceiling, generator prices, shortfall slack and storage are assumptions. Do not rank operator connection points by modelled scenario stress.

**Operator confirmed MW: zero.** Real 400/220 kV conductor ratings, 2025 as-built 110-kV network topology, switching and per-project N−1 feasibility are not validated. The research 2024 OSM physical-grid candidate is ODbL 1.0; third-party February 2025 hosted GIS comparison lacks a redistribution licence. No joined third-party raw geometry is shipped.

## Reproduce the three-stage demonstration

From the repository root, with Python 3.11+:

    python -m pip install -r requirements.txt
    python -m src.cli import-manual
    python -m src.cli import-verified-model
    python -m src.cli quality
    python -m src.audit_integrity
    python -m streamlit run app/dashboard.py

**What each step does:** Manual import inserts the five points and 18 original Grid Scope values into local SQLite. The optional model import validates the source-input SHA-256 against the solver-verified publication and inserts **12 separate model-scenario metric rows** (4 scenarios × 3 metrics), never into capacity_observation. Repeat both imports to check idempotency: model import's second run should report **0 inserted**. Quality warns if no local authenticated operational time-series data were pulled: GitHub CI intentionally has no Fingrid/ENTSO-E secrets and cannot fabricate live local context.

The public Next.js Atlas and its read-only Neon API were configured separately. A local importer run is **not** a hosted Neon database update. For the hosted time series use existing approved, secret-protected GitHub Actions jobs and monitor the source timestamp. Do not paste keys into chat or commit raw secrets.

## Two-to-three minute employer demonstration

1. **Problem:** "A Grid Analyst needs both an early capacity signal and a record of why the signal should or should not be trusted. National supply-demand alone is not substation headroom."
2. **Primary source and first screen:** Open /case-study, then /screening?demand_mw=100&year=2030&direction=consumption&voltage=all. In the Oct 17 selected sample, Seinäjoki and Uusnivala recorded **400 MW** each for 2030 consumption, two **indicative threshold matches**, while three other points lack exact captured entries. Not 100-MW technically available capacity, a ranking, or capacity reservations.
3. **Persisted evidence:** Open /connections and point-source details. Show 18/30 sampled intersections; select separate production/consumption, source snapshots and years, then inspect operator links/UTC captures. Point MW values are not additive.
4. **Actual operations:** Open /operations and /quality. Show Fingrid 124/74 and ENTSO-E A65 as national measured context, with interval provenance, coverage/gap/revision checks and oldest/newest UTC source times. If the connected database is stale or unavailable, state it rather than substituting a fake live row.
5. **Model boundary:** Open /analysis and /analysis/borders-2025. The two-day case has **four** optimal solves. Winter studies include **54** solves; market-corridor studies have **24** cases. None proves an individual Finnish branch is safe for a new connection.
6. **Closing engineering follow-up:** Ask Fingrid for the specific site's voltage, consumption profile, planned in-service date, reactive power, actual queue and reinforcement conditions; request an operator-led network study before any investment commitment.

## Job-description traceability

| Krios Grid Analyst activity described in original plan | What to show |
| --- | --- |
| Own grid data and source lineage | /operations, /quality; Fingrid/ENTSO-E authenticated pipelines, time/granularity and revision checks |
| Understand present and future connection signals | /connections, /screening; conditional Grid Scope values by point, direction, year and review state |
| Model and assess | /analysis; PyPSA reproducibility and explicit distinction from real AC power-flow or network feasibility |
| Own power-availability curve | Rebuilt SQLite/Neon source observations, historical forecast-year evidence, immutable snapshot and completeness matrix |

## Release gate and remaining handoff

- [x] Original five-point Grid Scope data captured and screenshot-rechecked 18/18 (18–19 Oct 2026)
- [x] Real Fingrid and ENTSO-E authenticated source smoke tests; Neon persistence and one observed scheduled refresh
- [x] Source-schema validation, idempotent SQLite storage and separate scenario classification
- [x] Historical PyPSA solver outputs under source hashes; separate local scenario import and negative regression tests
- [x] Explicit read-only website, 100 MW screening, national data quality and role-focused walkthrough
- [ ] Confirm current Vercel **production** deployment matches this release SHA; passing GitHub CI or main merge is not by itself a production deployment
- [ ] Check public live source freshness and one point-level original-portal observation again immediately before interview; source numbers may change
- [ ] Compare at least one exact national operational source interval against the operator portal under current credentials, retaining a dated screenshot/record privately
- [ ] Independent Fingrid physical planning study, future-year reinforcement MW or two-country Netherlands expansion, **outside MVP**

The project should be described as **a functional, source-traceable personal grid-analyst proof of concept**, not as a complete Finnish physical connection-capacity predictor.
