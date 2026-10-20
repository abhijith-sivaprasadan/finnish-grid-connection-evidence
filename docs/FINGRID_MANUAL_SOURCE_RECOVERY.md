# Manual Fingrid original-source recovery trigger

Only the workflow is added to the default branch here; no research-site
page, inferred capacity number, PyPSA model changes or database write occurs.

The GitHub workflow_dispatch button requires that a workflow file exist on
the repository's default branch. This standalone workflow checks out
the reviewed, pinned research commit 33b2b5ce5e29790288c34b77e56f97405ebaec43
from the unmerged source-recovery development branch. The exact commit ID
is immutable; future changes require an explicit workflow update.

After the Fingrid API subscription is no longer rate-limited, go to Actions
> Manual verified Fingrid source recovery > Run workflow (branch: main).

First select recheck_three_gaps. No interpolation is permitted. The job makes
at most three paced calls to Fingrid dataset 124 and uploads its exact source
recheck outcome. A 429 immediately defers the run instead of retrying.

For a resumable annual audit, choose annual_source_chunk_batch, 8 chunks
maximum, and on later manual runs provide resume_run_id from the preceding
recovery workflow. Original source chunks are hashed and retained in the
private Actions artifact for 30 days. No full-year completeness is claimed
unless exactly 35,040 original aligned 15-minute rows exist in BOTH
datasets 124 and 74.

Important: the verified 14-day winter/summer/autumn study and draft PR #38
are unchanged by this operational bootstrap. The 26-day extension remains
blocked by upstream 429; full 2025 coverage remains unverified.

## Source journal improvement

Pinned journal `33b2b5c` downloads datasets 124 and 74 **for each historical period** before advancing, rather than downloading a whole year of one dataset first. It adds an explicit `annual_2025_day_coverage.json` file to each successful annual batch artifact: a day-by-day ledger with `paired_complete`, `known_source_gap`, or `unknown_not_downloaded`, native source reading counts, exact observed missing intervals and ranked contiguous source-complete UTC windows. Existing source chunks from earlier batches retain immutable attribution and can be resumed without refetching. A complete calendar year remains **unverified** while even one source interval is absent.

All operator calls remain **manual-only** and are not scheduled or retried after HTTP 429.
