# Evidence-qualified 100 MW screening

This feature is a **pilot source-evidence triage**, not a load-flow model, electrical connection offer, feasibility study, grid booking tool or operator approval.

## Default scenario and exact evidence

- Request: **100 MW new electricity consumption**, effective year **2030**, voltage **all sampled points**.
- Source: original 17 October 2026 Fingrid Grid Scope 5-point sample, 18 transcriptions screenshot-matched by 19 October.
- **Seinäjoki 400 kV: 400 MW** and **Uusnivala 400 kV: 400 MW** in captured 2030 consumption figures: two **indicative threshold matches only**.
- **Vuolijoki, Alapitkä and Alajärvi** lack exact 2030 consumption figures in the sample: three **unknowns**, not zero or technically infeasible.
- Zero operator feasibility assessments are included; the five points are not representative of Finland's entire grid.
- Operator source: https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/

## Access

- UI: /screening — scenario controls, each source record, audit disclosure, JSON and CSV export.
- API: /api/v1/screening?demand_mw=100&year=2030&direction=consumption&voltage=all
- API responses include the exact requested scenario, point coverage, source snapshots, evidence classifications, and scientific limitations. All are read-only.

## Decision rules implemented

1. Match the same point, consumption direction and exact target effective year. **No** extrapolation, interpolation or conversion of production observations.
2. Source-reviewed published indicative MW >= request => **indicative_threshold_met**, not physically feasible.
3. Reviewed indicative MW below request => **indicative_below_request**, not proof of technical infeasibility.
4. Missing exact year/direction => **unknown_not_captured**, capacity null, never zero.
5. A new capture without an independent source recheck => **needs_source_review**. Favorable older observations never outrank newer unreviewed ones.
6. Conflicting observations in the same latest source snapshot => **conflicting_evidence**. Duplicate copies also require review.
7. MVA is not MW without a documented power-factor / conversion rule; **unit_not_comparable** is a separate state.
8. The 18-row screenshot audit establishes **transcription correspondence only**, not physical grid verification or reservable connection rights.
9. If the configured read-only database becomes unavailable, screening responds HTTP 503 rather than switching silently to the repository-compiled sample.
10. Historical 128 station-name rows from the annex headed 1.1.2020 are separate *unscreened research materials*, not current verified connection points.

## Acceptance and next steps

- Automated tests cover baseline 2/3 classification, exact-year and exact-direction matching, inclusive threshold, unknown/null, MVA incompatibility, unreviewed/latest-snapshot behavior, duplicate conflict, param rejection and filtered zero-point scope.
- The source URL, snapshot UTC, evidence category and the non-feasibility disclaimer are included in machine-readable exports.
- Engineering follow-up needs site coordinates, planned service date, load profile, reactive power and power factor, flexibility requirements, system/reinforcement context and an operator-led grid-connection study.
- Dependencies: PR #32 evidence-first UI and PR #34 station archive are both **draft** branches. The screening branch combines their UI changes for evaluation; production still requires reviewed integration and deployment.

Feature tracking: https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/issues/35
