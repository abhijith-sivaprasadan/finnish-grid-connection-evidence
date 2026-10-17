# Acceptance status and remaining work

## Delivered locally

- [x] New standalone Git repository under the requested workspace.
- [x] Inspect relevant PyPSA-NL and PRO1 context; document reuse boundaries.
- [x] Confirm usable numeric Grid Scope observations through the public viewer.
- [x] Five source-identified points, 18 observations, explicit units and directions.
- [x] Source capture log, timestamps, caveats and same-source spot checks.
- [x] Typed validators, versioned SQLite schema, atomic repeatable imports.
- [x] Historical snapshots retained; conflicting input rejected.
- [x] Streamlit filters, discrete published-year chart, gap labels and CSV export.
- [x] Five-substation Power availability outlook for both directions across
      2026/2030/2035, with 18 published / 12 missing cells in the source capture.
- [x] Independent-source-recheck CSV exporter and per-row audit protocol;
      all values marked pending until an actual second review.
- [x] National context isolated from capacity; scenarios isolated from both.
- [x] Fingrid and ENTSO-E client implementation and offline synthetic tests.
- [x] Credential setup instructions and honest README.

## Needed to complete the real-data MVP

- [x] Configure private GitHub Actions secrets for Fingrid and ENTSO-E (keys
      are never committed).
- [x] Authenticated Fingrid 124/74 and ENTSO-E A65 load smoke tests for 14 Oct
      2026 passed on 17 Oct (96+96 and 96 records respectively).
- [x] Add atomic, opt-in local persistence command and synthetic regression tests.
- [ ] Perform a real **local** persistence run and inspect both context feeds
      in the Streamlit National context tab; the public repo contains no live rows.
- [ ] Reconcile one actual interval against each operator portal and independently
      re-check the source-transcribed Grid Scope numeric estimates using the
      [pending per-row review checklist](GRID_SCOPE_RECHECK.md); no completed
      independent check has been recorded yet.
- [ ] Run a separate ENTSO-E A75 generation smoke check before enabling that
      optional feed in persistent capture.

## Later operational coverage

- Verify dataset definitions before adding reserves, cross-border flows, NTC or
  outages. Do not use an ambiguous "reserve margin" series as connection headroom.
- Support additional ENTSO-E curve types only with explicit documented semantics
  and tests. Current unsupported curves stop the import.
- After live checks, configure a single-worker scheduled refresh with securely
  supplied secrets and failure reporting. No background schedule is enabled yet.
- Add verified grid-project records and source-documented point relationships.
- Extend capture coverage; capture new Grid Scope snapshots without overwriting old ones.

## Stretch, only after live MVP

1. Finland zonal PyPSA sensitivity: documented assumptions, input period and model
   version; results only in `scenario_result`. It cannot generate nodal capacity.
2. Dutch national congestion feed: verify download, schema and licence. Add a
   dedicated congestion-status table; never force a colour flag into a MW field.
3. Optional pandapower CIGRE illustration: standalone generic feeder with explicit
   provenance and licence checks; not a reconstructed Dutch grid.

The supplied plan contains both an optional ENTSO-E-client description and a
stricter final requirement for both operational feeds. This implementation uses
the stricter acceptance criterion, rather than declaring completion without
authenticated live data. Phases beyond the Finland MVP are not claimed complete.
