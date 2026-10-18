# Independent Grid Scope audit attempt — 18 October 2026

**Finding:** No new independent numerical confirmations. `0/18` original
source-transcribed observations have been confirmed by a second independent
reading of the current operator viewer.

## Access tested

- Fingrid's official [Grid Scope landing page](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/)
  was accessible and independently confirmed the existence of separate
  production and consumption capacity layers, the changing-year outlook,
  interdependent substation capacity and the explicit rough/uncertain nature
  of estimates. This verifies the **scope and limitations**, not a single
  numeric source observation.
- The embedded [interactive viewer](https://karttapalaute.fingrid.fi/?link=3opMB&setlanguage=en)
  could not be reliably retrieved through read-only automated access in this
  review. No point-detail panel was actually read and compared to the
  17 October source capture; no numerical match was asserted.

## Source preservation and status

- The existing 18-row `data/manual/grid_scope_observations.csv` remains
  unchanged and still classified **published indicative**; none is
  `operator_confirmed`.
- Missing combinations remain **12 not recorded in the sample** (not zero).
- The website's Connection Workbench shows every year/direction intersection,
  the original source link, capture time and a `pending_independent_recheck`
  audit state. A downloadable 18-row worksheet has blank reviewer and
  evidence columns; no fake review times or confirmation links are inserted.
- A future reviewer should use [GRID_SCOPE_RECHECK.md](GRID_SCOPE_RECHECK.md)
  for point-by-point comparison and record any changed current publication
  separately. A correct map transcription still does **not** establish a
  guaranteed connection right.

This review deliberately does not present a broken automated map retrieval
as a completed scientific verification.
