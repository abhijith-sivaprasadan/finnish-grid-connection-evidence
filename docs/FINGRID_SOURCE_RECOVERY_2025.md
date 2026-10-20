# Fingrid calendar-2025 original-source recovery

**Not a completed annual dataset.** The prior authenticated annual audit stopped
on missing Fingrid consumption observations. Three specific dataset-124 original
quarter-hour intervals were absent in independently audited seasonal responses:

| Missing quarter-hour UTC | Dataset | Observed value |
| --- | --- | --- |
| 2025-01-17 17:00 | Fingrid 124 | Not published in audited response |
| 2025-01-17 17:45 | Fingrid 124 | Not published in audited response |
| 2025-07-11 16:15 | Fingrid 124 | Not published in audited response |

The year outside the three audited 30-day source windows is NOT verified gap-free.
Never claim these are the only missing observations in 2025.

Fingrid's source docs note individual missing measurements and recommend reporting
source-data issues to avoindata@fingrid.fi. See:
https://data.fingrid.fi/en/instructions and https://data.fingrid.fi/en/faq.
Fingrid limits API subscriptions to one query every 2 seconds and 10,000/day;
earlier authenticated attempts encountered HTTP 429.

## Added original-source tools

- src/models/recover_fingrid_gaps.py: manual, exact three-slot recheck of the
  original Fingrid 124 dataset. A separate single-attempt 5-second-spaced
  client never automatically retries 429. Only a matching original source
  dataset ID, 15-minute timestamp, native MWh/h unit and value can qualify.
  No missing interval is replaced with zero or estimated via other inputs.
- src/models/annual_journal.py: resumable immutable JSON source chunks,
  covering 53 <=7-day windows for EACH of datasets 124 and 74. Each chunk
  retains source interval values, timestamps, original retrieval timestamps,
  source ID/units, source URL, hash and explicit missing interval list.
  Journal distinguishes not-downloaded from genuine original-source missing.
  Downloads at most 1–16 chunks per manually authorized run, preserving
  prior chunks from a previous workflow artifact.
- .github/workflows/fingrid-manual-recovery.yml: MANUAL-ONLY, no scheduled
  or branch-push source retries, Git commits, production database writes,
  or confidential tokens in files.

## Run in GitHub when API rate limit is cleared

Go to Actions > Manual Fingrid missing-slot recovery and resumable 2025
source audit > Run workflow > branch feature/long-horizon-pypsa-sensitivity.

Choose recheck_three_gaps to make at most THREE original-source requests.
Inspect the artifact's three_original_fingrid_gap_rechecks.json result.

Choose annual_source_chunk_batch, max_new_chunks=8, no previous run ID
for the first bounded collection. Then use resume_run_id set to the prior
recovery workflow run ID to re-use its checked original chunks; each run
uploads the updated partial journal. Artifacts are retained for 30 days.

Full 2025 CSV is created ONLY if the two original source datasets have
35,040 distinct quarter-hour readings EACH and every interval aligns.
Rate-limit failures cause a deferred/partial audit, not annual completeness.
Neither three recovered timestamps nor a complete source audit would
prove Finnish network topology, connection headroom, or a 2030 forecast.

## Existing verified research

The source-verifiable 14-day matched three-season comparison is already
published in draft PR #38 with source hashes and 36 optimal PyPSA cases.
The attempted 26-day run hit HTTP 429 and HAS NO verified result.
Do not merge or claim a new annual optimization from source-recovery code alone.
