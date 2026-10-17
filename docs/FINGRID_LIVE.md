# Fingrid Open Data live verification (manual and secret-only)

The `avoindata-api.yaml` file in `docs/reference/` is Fingrid's **OpenAPI
specification**, not an API key and not the Grid Scope substation map data.
Fingrid Open Data provides *national operational electricity data*. The
published Grid Scope substation connection-capacity estimates are distinct.

This optional smoke check uses the already-tested Fingrid importer for:

- **124**: Finnish electricity consumption, unit **MWh/h**.
- **74**: Finnish electricity production, unit **MWh/h**.

The values remain national operational **context**, never a MW connection offer.

## Set up the key securely

A Fingrid **primary key was shared in a conversation**. Regenerate that exposed
key in the [Fingrid developer portal](https://developer-data.fingrid.fi/)
(Profile / subscription and API keys), or switch to a different valid key and
revoke/regenerate the exposed key. Keep the replacement out of chat, commits,
`.env.example`, screenshots, workflow input fields and issue comments.

1. Open the repository **Settings → Secrets and variables → Actions →
   New repository secret**.
2. Use the exact name **FINGRID_API_KEY** and paste the **replacement** key as
   its value. GitHub Actions secrets are not stored in Git.
3. Go to **Actions → Fingrid live smoke (manual, secret-only) → Run workflow**.
   Start with `both`. Leave the date blank for a completed UTC day three days
   before execution, or enter a YYYY-MM-DD UTC date.
4. Inspect the run. On success, the log shows only date, dataset IDs, units,
   observation counts and temporary DB checks. **No token, URL with credentials,
   response body or raw readings are printed or uploaded.**

This workflow has no schedule and is restricted to `main`, so it will not
give a pull-request branch access to your repository secret.

## Local alternative (PowerShell)

Set `FINGRID_API_KEY` in the terminal using the private secure-input process
in [SETUP.md](SETUP.md), then run:

```powershell
python -m src.live_fingrid --kind both
```

Fingrid requires the API key in the **`x-api-key` HTTP header**. The importer
uses only that header, never the URL query string, and observes the 2-second
per-key rate limit in a single process.

The check is designed to **fail** on missing credentials, incomplete source
records, unexpected units or rejected responses. Its SQLite database exists
only temporarily and is deleted after the run. Passing it confirms real
authenticated API access and persistence for the selected day; it does **not**
permanently populate the dashboard and it does **not** validate the 18
source-transcribed Grid Scope capacity values.

After a passing smoke check, run the normal **persistent** local CLI importer
to load real national operational context into the dashboard database:

```powershell
python -m src.cli import-manual
python -m src.cli fingrid --start 2026-10-14T00:00:00Z --end 2026-10-15T00:00:00Z
python -m src.cli quality
```

Use a suitable completed interval. Data-ingestion completion and scientific
validation are separate. Do not claim a fully validated site-screening dataset
from an authenticated API smoke test alone.

Reference: https://data.fingrid.fi/en/instructions
