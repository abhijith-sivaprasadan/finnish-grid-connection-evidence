# Fingrid Grid Scope — original sample screenshot recheck

**Review date:** 18–19 October 2026. **Original capture:** 17 October 2026.
**Scope:** 18 manually transcribed indicative MW values at five selected 400 kV points.

The attached [18-row audit ledger](GRID_SCOPE_18_ROW_SCREENSHOT_RECHECK_2026_10_19.csv) records
the original observation identifier and numerical tuple, the matching value displayed
in human-supplied Fingrid Grid Scope screenshots, evidence grade, review date and SHA-256
of the private screenshot. Every tuple matched; 17 have a year-specific chart tooltip,
one (Alajärvi production 2026) has a displayed 400 MW panel number with 2026 selected.

**18 of 18 screenshot comparisons matched; zero numerical differences were observed.**
This independently checks the *transcription against a subsequently displayed public
viewer*, not the historical source publication date, grid topology, deliverable capacity,
operator approval, allocation, connection rights, or feasibility for a data-centre load.
The 12 intersections not in the original 30-cell sample remain unknown, not zero.

The source observations in `data/manual/grid_scope_observations.csv` are left intact.
Reviewer screenshot files are retained **outside this public repository** while
redistribution terms are evaluated. A SHA-256 is a traceability reference and does
not independently authenticate Fingrid or make an inaccessible image publicly auditable.
Reviewer supplies source evidence; Fingrid has not certified this audit.

**Important identity rule:** the screenshot comparison applies only to the exact
original observation ID, connection point, direction, effective year, MW unit,
capture timestamp and numerical value. It MUST NOT automatically transfer to an
updated/new map capture, modified value, or future source release. Any changed
source estimate must be captured as a new record and reviewed independently.

Further interpretation and new screening outputs must explicitly distinguish
`source_transcription_screenshot_match` from `operator_confirmed` and
`physically_validated`; the latter two are **not established**.
