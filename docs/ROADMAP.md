# Finnish Grid Atlas — acceptance roadmap (reconciled 20 October 2026)

The [original Krios MVP plan](KRIOS_PORTFOLIO_RELEASE.md) ended after Finland Phases **0–3**: sourced point-capacity evidence + two operator context streams + reproducible SQLite/Streamlit. This core is **functionally implemented**. A later release includes real-data PyPSA research and spatial proxy audits, which remain **non-authoritative sensitivity or cartography**. Never claim all seven phases are completed.

## Phase 0–3 / core Finnish MVP

- [x] Five selected Fingrid Grid Scope 400-kV points, original 18 indicative direction/year readings from 17 Oct 2026.
- [x] All 18 original source-transcribed numbers matched independent reviewer-provided screenshots on 18–19 Oct: 17 tooltips and one panel MW; see [source audit](audits/README.md). This proves numeric correspondence, not reserved MW.
- [x] Each numeric observation preserves point identity, direction, unit, exact effective year, link, capture timestamp, evidence status and validity qualifiers; missing intersections remain unknown.
- [x] Typed, migration-safe, immutable/idempotent SQLite capacity, projects, operations and scenario tables.
- [x] Original Streamlit dashboard and hosted Next.js/Neon evidence workbenches, read-only API and 100-MW source-qualified screening.
- [x] Authenticated Fingrid 124/74 and ENTSO-E A65 clients and historical collection; national readings are not site telemetry.
- [x] Private-token scheduled GitHub Actions refresh with an observed successful unattended run [18 Oct](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39125767276), source freshness and database checks. No guarantee of future uptime from a single past run.
- [x] Distinguish published_indicative / operational_context / model_scenario / operator_confirmed at source schema and UI.
- [x] README, source licences, limitation statements, [job-role case study](KRIOS_DEMO.md), and [acceptance handoff](KRIOS_PORTFOLIO_RELEASE.md).

**MVP decision:** ready as an independent source-traceable *portfolio prototype*, subject to checking that the intended GitHub commit is actually deployed to the live domain and reviewing the current source age. Operator-confirmed connectable MW remains **zero** by design.

## Phase 4 / historical model sensitivity — completed as separate, qualified research

- [x] Four PyPSA HiGHS solver-verified, 48-hour October 2026 national one-bus scenarios: hypothetical 100 MW load, flexible load, battery and assumed 1,500 MW stress cap. [Method](PYPSA_FINLAND.md).
- [x] Verified **two 27-day 2025** historic winter windows with 48 project scenarios plus six baselines across hypothetical support constraints. Actual 2025 source collection is still **partial** (171 complete UTC dates).
- [x] 24 historical three-zone Swedish–Finnish trade-corridor model scenarios with verified Fingrid commercial data. Commercial intraday capacity is NOT a transmission conductor's rating. [Boundaries](THREE_ZONE_MARKET_CORRIDOR_LIMITATIONS_2025.md).
- [x] Offline, SHA-256-checked import of four solver-verified cases into 12 metric rows of **local SQLite scenario_result** with explicit model_scenario status. Importing does not affect capacity observations or Neon; rerun is idempotent.
- [x] Website model API and analysis views; all scenario reports explicitly disclaim connection feasibility.

## Additional physical-network exploratory track (not original MVP)

- [x] Source-hashed and licensed ODbL 2024 Finnish high-voltage proxy: 107 bus rows, 137 domestic AC line records, standardized source electrical templates.
- [x] Source-graph-only bridge screening (22 single-edge deletions disconnect the partial OSM graph) and dated 2025 operator asset chronology, without false real grid N−1 claims.
- [x] Voltage-matched 2024/February-2025 cartographic proximity summary (3,157 samples). No raw third-party geometry redistribution because publisher gave no clear reuse permission.
- [ ] Authenticated full 2025 Fingrid 110/220/400-kV as-built branch/substation IDs, electrical limits and commissioning states.
- [ ] Source-supported per-node generation/consumption and validated AC power flow, line overload and operator-style N−1 contingencies.
- [ ] Actual site-specific connection MW evaluation. **Do not derive one from national PyPSA or map proximity.**

## Outstanding independent quality and operations gates

- [ ] Check the **live deployment SHA** after release (a GitHub merge or passing Next.js build is not proof of production deployment).
- [ ] Re-open Grid Scope close to each interview to capture a **new dated source snapshot**; do not silently overwrite 17 Oct 2026 values if Fingrid has updated them.
- [ ] Verify one exact aligned 15-minute Fingrid and ENTSO-E interval against each operator's portal, storing rights-compliant evidence of date, units and revisions.
- [ ] Keep watching scheduled collection, Neon quota, source completeness and actual last interval. Retain emergency-stop and least-privilege credentials.
- [ ] Verify an additional ENTSO-E A75 generation feed *before enabling it* (not necessary for original three-source MVP).
- [ ] Manually document an actual individual point ↔ verified reinforcement relationship before inserting a grid_project record; no forecast MW release can be assumed.
- [ ] Clarify rights and engineering provenance of the February 2025 third-party copy before any geospatial redistribution.

## Original stretch Phase 5–6 (Netherlands): not complete

- [ ] Obtain and check an official Netherlands congestion export/API, schema, date and redistribution rights.
- [ ] Add a separate Dutch congestion evidence category; do not encode an orange/red availability class as MW.
- [ ] Optionally construct an explicitly illustrative CIGRE generic pandapower distribution feeder with real congestion *context*, never a validated Netherlands national/DSO network.

## Phase 7 / presentation and handoff

- [x] A dated source-supported [Krios case study and demo](KRIOS_DEMO.md), [acceptance matrix](KRIOS_PORTFOLIO_RELEASE.md), QA tests and honesty boundaries.
- [ ] Final hands-on browser check of production URL, read-only API, source interval age and screen accessibility against the tested release commit.

Earlier dated milestones are preserved in [evidence log](EVIDENCE_LOG.md), [canonical status](STATUS.md), and [production runbook](SITE_OPERATIONS.md). Historical runbook instructions should not be read as permanent claims about live site condition.
