# Source transcriptions

The CSVs contain real Fingrid Grid Scope readings captured on 17 October 2026.
They contain no synthetic examples. `tests/` uses clearly labelled synthetic fixtures.

The selection covers five 400 kV connection points, not all Finland. For three points,
production was transcribed at 2026, 2030 and 2035. For two points, consumption was
transcribed at the same years. The current-year consumption comparison table supplies
the other three consumption observations. Missing combinations remain missing.

Capture details, source attribution, direction checks and limitations:
[capture log](../../docs/CAPTURE_LOG.md) and [sources](../../docs/SOURCES.md).

To add a snapshot:

1. Open Grid Scope, select **one** connection-capacity direction and the desired year.
2. Open the named point and verify its voltage and the detail panel's direction text.
   After changing layers the viewer can retain a previously opened detail panel;
   close it and select a different point before trusting its values.
3. Transcribe only explicit numbers, source units and explicit years. A missing value
   is a blank CSV cell, never zero. Leave publication date blank if not stated.
4. Assign a new observation ID and a timezone-aware `source_observed_at` for the
   new snapshot. Use the same capture timestamp for rows from one capture session.
5. Retain old snapshots. Add assumptions and source caveats to `validity_notes`.
6. Run `python -m src.cli import-manual`, then `python -m src.cli quality`.

Imports are atomic and repeatable. Conflicting IDs or duplicate snapshot keys are
rejected. Never set `operator_confirmed` without a documentary confirmation URL.
Model results belong in `scenario_result`; they cannot enter this CSV.
