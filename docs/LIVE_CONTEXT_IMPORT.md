# Persisting verified operational context locally

The Fingrid live smoke (datasets **124** and **74**) and ENTSO-E **load**
smoke (document **A65**) both passed on 17 October 2026 for
**14 October 2026 00:00–15 October 2026 00:00 UTC**. Those smoke checks
used temporary SQLite databases, which were deleted after each run.

A production-like, reproducible next step is to populate the **local** evidence
database that Streamlit already reads. `src.sync_context` fetches all requested
datasets first, validates scope/units/intervals, then inserts into SQLite in
**one transaction**, preserving retrieval revisions and rolling back everything
if one source or row fails.

## First use (PowerShell, Windows)

Clone/pull the repository and install dependencies as explained in
[README](../README.md). Configure the **current rotated** keys privately in
the same terminal, using the `Read-Host -AsSecureString` procedure in
[SETUP](SETUP.md). Keep both values out of shell history and public files.

```powershell
.venv\Scripts\python.exe -m src.cli import-manual
.venv\Scripts\python.exe -m src.sync_context --day 2026-10-14
.venv\Scripts\python.exe -m src.cli quality
.venv\Scripts\python.exe -m streamlit run app/dashboard.py
```

The second command writes national operational context from **both** verified
feeds into the Git-ignored `data/evidence.sqlite` (or a local path provided
via `--db`). The dashboard opens the same file; select **National context**
to plot each source separately. Never interpret national electricity generation
minus consumption as available *substation* connection headroom.

Other supported forms:

```powershell
# Only Fingrid 124+74: requires FINGRID_API_KEY
python -m src.sync_context --day 2026-10-14 --scope fingrid

# Only ENTSO-E A65 load: requires ENTSOE_API_TOKEN
python -m src.sync_context --day 2026-10-14 --scope entsoe

# Repeat for another completed day (at least two days in the past)
python -m src.sync_context --day 2026-10-13
```

### Important interpretation

- **No server-side persistence is implied.** The manual Actions smoke tests
  discard temporary databases. This local importer retains data on **your
  computer**, not in GitHub. Back up your local `.sqlite` file if needed.
- Raw operator observations are not automatically published or attached to
  GitHub Actions, pending verification of the current platform redistribution
  terms. The repository contains the source code, synthetic tests, docs and
  a manually transcribed indicative capacity sample only.
- Re-running a retrieval may add a *new retrieval revision* with a new
  `retrieved_at`; the `latest_operational` view selects the newest revision
  for each interval. Replaying the exact same revision is idempotent.
- ENTSO-E `generation` (`A75`) remains a **separate, unverified live mode**.
  First run **ENTSO-E live smoke** with `generation`; only after a successful
  result should `--include-generation` be used locally.
- Capacity estimates remain **18 source-transcribed values at five points**.
  They are not validated connection offers, and API ingestion does not verify
  their accuracy.

### Verification states (17 October 2026)

| Stage | Status |
|---|---|
| Fingrid authenticated dataset 124, daily interval | Passed, 96 records |
| Fingrid authenticated dataset 74, daily interval | Passed, 96 records |
| ENTSO-E authenticated A65 load, daily interval | Passed, 96 records |
| ENTSO-E authenticated A75 generation | Not yet checked |
| Local importer software/atomicity | Tested with fixture data, live local run pending |
| Verified Grid Scope figures / connection rights | Independent numeric verification pending |

Reference: Fingrid [124](https://data.fingrid.fi/en/datasets/124),
[74](https://data.fingrid.fi/en/datasets/74) and the
[ENTSO-E Transparency Platform](https://transparency.entsoe.eu/).
