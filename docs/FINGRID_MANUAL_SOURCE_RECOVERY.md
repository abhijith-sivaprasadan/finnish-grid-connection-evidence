# Manual Fingrid original-source recovery trigger

Only the workflow is added to the default branch here; no research-site
page, inferred capacity number, PyPSA model changes or database write occurs.

The GitHub workflow_dispatch button requires that a workflow file exist on
the repository's default branch. This standalone workflow checks out
the reviewed, pinned research commit f9fa6630318e5c8cea426b82a6c847cd88dc9ff5
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
