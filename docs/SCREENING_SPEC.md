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

## Connection arrangement and technical readiness extension (20 October 2026)

The source MW threshold remains unchanged. The API and interactive UI additionally classify **Fingrid's published nominal switchyard power/voltage guidance** separately: requested switchyard below 250 MW at a 400 kV labelled source point is **review_lower_voltage_switchyard**, at >=250 MW a 400 kV switchyard follows nominal voltage guidance only. Direct 400/220 kV transmission-line connections are disallowed, while 110 kV line arrangements require case-by-case review with a 40 MVA transformer restriction. The code refuses to convert MW to MVA or assume the existence of any lower-voltage bay at the sampled point.

Controls: query parameter connection_type=switchyard|line|unspecified (defaults to switchyard); source evidence results include pathway_note, timing_evidence and concrete next_actions, and explicitly show no verified point-specific reinforcement. The readable Markdown export remains **a follow-up evidence brief**, not a grid capacity offer. Fingrid source: https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/. [Detailed source and Netherlands pilot report](KRIOS_CONNECTION_READINESS_AND_NL_PILOT.md).

## Acceptance and next steps

- Automated tests cover baseline 2/3 classification, exact-year and exact-direction matching, inclusive threshold, unknown/null, MVA incompatibility, unreviewed/latest-snapshot behavior, duplicate conflict, param rejection and filtered zero-point scope.
- The source URL, snapshot UTC, evidence category and the non-feasibility disclaimer are included in machine-readable exports.
- Engineering follow-up needs site coordinates, planned service date, load profile, reactive power and power factor, flexibility requirements, system/reinforcement context and an operator-led grid-connection study.
- Implementation status (20 October 2026): **screening PR #36 and historical station-archive PR #34 have merged to main**. Alternative site-design PR #32 remains draft and should not be confused with the merged research pages. Confirm Vercel's current production commit separately rather than treating a GitHub merge as proof of deployment.

Feature tracking: https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/issues/35
