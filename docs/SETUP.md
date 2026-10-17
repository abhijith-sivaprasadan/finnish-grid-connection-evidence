# API setup and first live run

The dashboard and CSV-to-SQLite path work without credentials. No API credentials
are included in this repository, and no authenticated network import has yet been
verified. The **Fingrid** client has been checked against the supplied
[OpenAPI contract](reference/README.md); that YAML is **not** a key and is not the
ENTSO-E API schema. Both live services still need authenticated source checks.
The ENTSO-E-only [manual secret-backed smoke workflow](ENTSOE_LIVE.md) can
validate real source access and temporary SQLite persistence after the repository
owner configures a new secret. The full MVP requires a real Fingrid operational
import; ENTSO-E is an optional additional context feed.

## Fingrid

1. Register/sign in at [Fingrid Open Data](https://data.fingrid.fi/en/instructions).
2. Open its developer portal, select Products, subscribe to **Open Data starter**,
   and read/accept the current terms yourself. Manage the key from your profile.
3. Set `FINGRID_API_KEY` in the same terminal that runs the importer. The client
   sends it only in the `x-api-key` header to `data.fingrid.fi`.

For an optional first authenticated probe, see [Fingrid's secret-backed
GitHub Actions smoke test](FINGRID_LIVE.md). The already-shared primary key
should be regenerated before saving a replacement privately as a GitHub Actions
repository secret named `FINGRID_API_KEY`. The `avoindata-api.yaml` file is
Fingrid's API *specification*, not a key.

Fingrid's documented limit is 10,000 requests/day and one request per two seconds
per key. This client spaces requests by at least 2.1 seconds, including retries,
within one process. Do not run concurrent importers with the same key. The request
window is limited to 31 days; pagination is bounded and repeated pages fail.

Verified dataset metadata:

- [124 — electricity consumption](https://data.fingrid.fi/en/datasets/124), source
  unit `MWh/h`, 15-minute period; older history uses hourly resolution.
- [74 — electricity production](https://data.fingrid.fi/en/datasets/74), source
  unit `MWh/h`, 15-minute period; older history uses hourly resolution.

Values retain `MWh/h` even though dimensionally this is average MW. The API's
explicit interval start/end fields determine timestamps; do not infer a new
15-minute interval from older hourly samples.

## ENTSO-E

Register at the [Transparency Platform](https://transparency.entsoe.eu/). Follow
the official [API token guide](https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2FAPI-Token-Management.pdf).
If the Web API Security Token field is absent, its instructions say to request
RESTful API access from the platform helpdesk using the registration email.
No email was sent by this project. Generate and store the token privately, then
set `ENTSOE_API_TOKEN` in the importer terminal. Generating a replacement token
can invalidate an existing token; follow the guide carefully.

Implemented requests: actual total load (A65/A16) and generation per production
type (A75/A16), Finland zone `10YFI-1--------U`. Queries are split into daily
windows. The parser accepts explicit A01 point series at 15/30/60-minute resolution
and rejects unsupported curves rather than inventing gap values. MAW is mapped
to MW (the ENTSO-E code for megawatt); production-type and consumption direction
remain in metric names. Generation components are not silently summed.

## Configure secrets privately

`.env.example` lists variable names only; `.env` is not automatically loaded.
Use a terminal or secret manager to set process environment variables. This
PowerShell pattern avoids placing the key in command history:

```powershell
$secureKey = Read-Host 'Fingrid API key' -AsSecureString
$env:FINGRID_API_KEY = [System.Net.NetworkCredential]::new('', $secureKey).Password
$secureToken = Read-Host 'ENTSO-E API token' -AsSecureString
$env:ENTSOE_API_TOKEN = [System.Net.NetworkCredential]::new('', $secureToken).Password
Remove-Variable secureKey, secureToken
```

Do not paste tokens into chat, commit them, or enable HTTP debug logging. ENTSO-E
requires its token as a query parameter; this client avoids logging request URLs
and emits sanitized HTTP errors. No credentials are used by the dashboard.

## First imports

From the repo root, with the environment set:

```powershell
.venv\Scripts\python.exe -m src.cli import-manual
.venv\Scripts\python.exe -m src.cli fingrid --start 2026-10-15T00:00:00Z --end 2026-10-16T00:00:00Z
.venv\Scripts\python.exe -m src.cli entsoe --kind load --start 2026-10-15T00:00:00Z --end 2026-10-16T00:00:00Z
.venv\Scripts\python.exe -m src.cli entsoe --kind generation --start 2026-10-15T00:00:00Z --end 2026-10-16T00:00:00Z
.venv\Scripts\python.exe -m src.cli quality
```

Choose another completed day if these dates are unavailable. Compare at least one
interval, unit, direction and dataset against each operator portal. Check gaps
and retrieval time in the National context tab. API payload drift should produce
an error and leave the database unchanged, not a plausible fallback value.

Optional `--db <path>` goes **before** the command name; alternatively set
`GRID_EVIDENCE_DB` for both CLI and dashboard. Regenerate a new database from CSVs
using a new path; never discard an existing historical database casually.

After live verification, a scheduler can invoke these CLI commands with a rolling
completed-day window and privately supplied secrets. Scheduling is deliberately
not installed or enabled in this release. Use a single worker, capture exit status,
and retain past capacity snapshots. Operational API refresh does not refresh the
manually captured Grid Scope estimates.
