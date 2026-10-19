# Initial public import — evidence and quality boundaries

> **Historical pre-review release audit.** For later screenshot matching of all 18 original transcriptions see the [18–19 October audit](audits/README.md). This does not establish source publication dates or physically connectable MW.

17 October 2026. This repository was imported from a local project snapshot **without** its virtual environment, package cache, generated SQLite database, logs, or local temporary files.

## Evidence levels

- `data/manual/grid_scope_observations.csv` contains 18 source-transcribed numerical entries at five named Fingrid points. These entries are **claims from one recorded map capture**, not numbers independently retrieved and verified during this import. The capture was checked internally against detail/comparison views of the same map, as described in `docs/CAPTURE_LOG.md`.
- Source capture time is not the operator's data publication time. Forecast years are not confirmed connection years. Published indicative MW values are not operator-confirmed allocations, and cannot safely be summed across points.
- No operational imports from credentialed Fingrid or ENTSO-E endpoints have been completed. Tests of API clients use fixtures/contract examples, not live ingestion.
- The repository currently contains **no** operating PyPSA or pandapower grid-connection study. Scenario tables are reserved for future work.

## Software assurance

- `CapacityObservation` and SQLite schema version 2 require a **finite, nonnegative numerical value and a declared MW/MVA source unit**. Unknown or unpublished values are represented by missing observations or explicit UI gaps, never empty numeric observations.
- Existing valid schema-v1 databases migrate to v2 preserving observations; legacy databases with blank values are stopped for manual review rather than silently rewriting evidence.
- The quality report separates **Fingrid-required** operational coverage from **ENTSO-E optional** coverage. Its boolean flags are data-readiness checks, **not an external source authenticity guarantee**.
- Source inputs (CSVs), not `data/evidence.sqlite`, are committed. Use `python -m src.cli import-manual` to recreate the database.

## Next steps before a Krios portfolio showcase

1. Independently re-open Fingrid Grid Scope and verify at least two numerical source observations, the direction, unit, selected year, and point identity. Retain dated, rights-compliant verification evidence outside the public repo as needed; never invent missing values.
2. Use personal Fingrid API credentials locally or in a securely configured workflow to import dataset 124/74 operational context. Record retrieved date and check dataset units/timestamps against Fingrid documentation. Never commit API credentials.
3. Confirm all GitHub Actions tests pass on the actual GitHub-hosted workflow.
4. Produce a transparent five-point site-screening table that distinguishes published estimates, *not published*, forecast dates, and missing information; do not rank unverified or incomplete values as connection-ready sites.
