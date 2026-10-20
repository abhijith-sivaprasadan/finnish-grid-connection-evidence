# Source bank from separately verified historical Fingrid artifacts

This research step reuses validated GitHub Actions source captures rather than
making additional authenticated Fingrid API requests (recent attempts returned HTTP 429).

Original archive captures are SHA-256-pinned:
- Autumn 30-day historical 2025-09-15..2025-10-15 UTC: 3093f704484848919d83feb6c133c2e2abf2299566d5bd02a109e01b7fdec2e0.
- Winter 14-day 2025-01-18..2025-02-01 UTC: b0504230744d16020e253dd48bbeb7693459414ab0893f3770f6adc188596977.
- Summer 14-day 2025-06-15..2025-06-29 UTC: d8ad5dc81ecee9b7b410aa19c2316faff16d55827a48d5fd59bcb667bf16a679.
- Autumn 14-day overlap, separately recaptured, 2025-09-15..2025-09-29 UTC:
  a38d703c23037bae75370e6414ff4b0034eb64b9832ea15167e40141c44235be.

Prior archived Actions runs: 39391985966 and 39396079522.
The 14-day autumn archive is overlap validation, not additional coverage.
Captured differences in retrieval timestamps may be genuine. Differences
in original consumption or production *values* fail closed and require
source-revision review; they are not silently averaged or substituted.

If the source archives cross-validate, the verified historical source bank has
58 distinct complete UTC days and 5,568 paired original quarter-hour observations.
This does NOT constitute an annual dataset or a 2030 forecast. Uncovered dates
are not filled or extrapolated. The 2025-01-17 and 2025-07-11 dates are
separately qualified as original-source-missing based on successful operator
recheck run 39406458886. The source bank does not assert all other uncovered
dates have complete operator histories.

The output is a per-day original data-coverage inventory, with distinct
source-complete / known original gap / absent-from-archive statuses. It
reports energy quantities only over actual archived original observations,
never a 2025 national energy total. Do not stitch disjoint periods into one
continuous battery operation or translate them into substation connection rights.

Workflow .github/workflows/verify-fingrid-archives.yml has read-only
GitHub Actions permissions, downloads two existing trusted archived
observations as artifacts, verifies fingerprints and CSV interval/source
integrity, uploads an offline-verified source coverage report, and uses
no Fingrid API key or operator requests. Artifacts have retention limits.

Source pages: https://data.fingrid.fi/en/datasets/124 and
https://data.fingrid.fi/en/datasets/74.
