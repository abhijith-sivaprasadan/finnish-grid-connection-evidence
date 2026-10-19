# Verification and audit record — 17 October 2026

> **Historical integrity snapshot from 17 October 2026.** A subsequent [18/18 screenshot comparison](audits/README.md) was completed on 18–19 October; the older pending review status below was accurate at the time, not current. This is not physical capacity validation.

## Evidence levels

| Evidence | What is supported | What is not supported |
|---|---|---|
| Grid Scope source CSV | 18 named observations at five 400-kV points, an original 17 Oct capture log, source URLs and conditional years | Independent re-observation of any individual published number or actual connectability |
| Internal capacity import | The `audit_integrity` command compares every committed CSV row against its SQLite value, direction, year, unit, source URL, capture date and caveat | It checks **transcription consistency within our project**, not authenticity against Fingrid |
| Fingrid Open Data | 14 Oct 2026 authenticated smoke run parsed and temporarily stored 96 consumption (124) plus 96 production (74) records | Persistence on the user's computer, portal-to-record numeric spot check or substation availability |
| ENTSO-E A65 load | 14 Oct 2026 authenticated smoke run parsed and temporarily stored 96 load records | Independent numeric spot check; A75 generation is not verified |
| Source data vs network capacity | National operational context is separate from connection capacity | Net demand/production or generation-minus-load cannot be used to infer substation headroom |

Fingrid's [Grid Scope description](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/)
independently confirms separate production and consumption layers, estimated
capacity at selected substations, conditional planning information, and that
the map may be incomplete or erroneous. It **does not publicly expose the
specific 18 figures in its ordinary text landing page**. A read-only automated
attempt to access the interactive viewer failed. Accordingly no numeric row
has been independently validated by this audit.

Fingrid's [system explanation](https://www.fingrid.fi/en/electricity-market/power-system/)
states the national consumption number is calculated from production, import
and export; that means cross-provider agreement must be evaluated **against
definitions and interval alignment**, not simply assumed or treated as two
independent source measurements.

## Run the internal audit

From the repo root, after importing the manual sample:

```powershell
python -m src.cli import-manual
python -m src.audit_integrity --output data/audit/integrity-report.json
```

The report checks:

- Matching observation ID, point, direction, source year, value, unit, capture
  time and caveat against the committed manual CSV.
- A documented confirmation citation for any `operator_confirmed` row.
- Area/category separation of national operations versus point estimates.
- Source/dataset/metric/unit invariants (including ENTSO-E MAW → MW and Fingrid
  MWh/h retained unaltered), UTC timestamps, positive intervals, overlaps and
  gaps per separate series.
- Zero locally imported API records is an **action**, not a fabricated
  passing real-data verification.

A `blocker` finding returns exit code 2. A `review` is a non-fatal issue,
and an `action` identifies work to complete. The report is structured JSON,
does not export raw live observations or tokens and refuses to overwrite a
pre-existing audit report. The local `data/audit/` folder is ignored by Git.

## Remaining independent fieldwork

1. Complete every row of [Grid Scope recheck worksheet](GRID_SCOPE_RECHECK.md)
   against the live interactive map. Reconfirm 400-kV point identity, direction,
   stated year, value/unit, capture time and any displayed caveat. Record
   differences as new dated evidence; never silently rewrite the old snapshot.
2. Locally run the [persistent operational importer](LIVE_CONTEXT_IMPORT.md)
   with private provider credentials. Execute the integrity audit on that
   local database, then inspect actual values on the operators' portals for
   aligned 14 Oct UTC intervals and retain comparison evidence privately.
3. Run separate ENTSO-E A75 generation smoke before claiming that feed works.
4. Cross-check the licensing/reuse restrictions before public distribution
   of normalized observations. API smoke output and internal schema tests alone
   are not redistribution permission or physical validation.

**Audit disposition:** code-level reconciliation and structural validation
implemented; source-level numeric verification **pending**, connection-capacity
physics **not validated**, authenticated API availability **observed** for the
listed datasets, durable private local data import **pending**.
