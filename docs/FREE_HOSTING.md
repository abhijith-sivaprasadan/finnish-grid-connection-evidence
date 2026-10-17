# Deploy the Finnish Grid Evidence dashboard online — free-tier path

**Status: deployment-ready code path; no Neon project or Streamlit app is
created by committing this repository. A live public URL does not exist until
the account owner completes the steps below.**

The application runs on [Streamlit Community Cloud](https://share.streamlit.io/)
and reads *persisted* observations from
[Neon PostgreSQL](https://neon.com/pricing). Private
[GitHub Actions](https://docs.github.com/en/actions) secrets are consumed by
the backend collector. Existing local SQLite and tests continue to work.

## Cost guardrails (checked 17 October 2026)

| Component | Account plan | Scope / safeguard |
|---|---|---|
| Streamlit | Community Cloud free | App may hibernate and be subject to resource limits |
| Neon | Free, $0/month | 1 GB/project (2 Oct 2026 announcement), 100 CU-hours/month/project and 5 GB egress/month; compute scales to zero |
| GitHub Actions | Standard runners in the **public** repository | Free; 1 run/day after owner explicitly enables it |
| Domain | No custom domain | Public `*.streamlit.app` subdomain, no domain purchase |
| Scheduler | `.github/workflows/cloud-refresh.yml` | **Disabled** until `ENABLE_PUBLIC_REFRESH=true`; opt-in, does not run on PRs |
| Database retention | Append-only | Monitor space; historical revision rows use storage; collector stops writes above 750 MiB, before the 1 GB quota |

The app is a **regularly refreshed evidence dashboard**, *not* a real-time
SCADA feed. The conservative collector chooses a completed UTC day **three
days before execution** by default to reduce source-publication delays and
runs at 07:17 UTC daily. Latest source interval and its age are visible.

Cloud Free plans and quotas change; limits and account status must be checked
before deployment. **Do not add payment details, enable paid add-ons, use
larger Actions runners, or upgrade plans** if a strict $0 budget matters.
Neon service usage may be throttled or suspended when quotas are reached.
This setup cannot guarantee 24/7 uptime or an immutable future price.

## 1. Reuse the existing Neon–GitHub integration

As of 18 October 2026, the owner connected the existing repository to Neon
project `fragrant-dawn-65247206`, organization
`org-snowy-band-13101282`. The integration automatically added:

- GitHub **secret** `NEON_API_KEY` (private: never show or copy to the app).
- GitHub **repository variable** `NEON_PROJECT_ID` (public project ID).

**Do not create another Neon project, paste the API key into chat, or create a
writer connection URL secret.** The repository's
[`src/neon_connection.py`](../src/neon_connection.py) resolves the writer
URL through Neon's documented read-only management API methods:
list branches, list databases, retrieve connection URI. It masks the
credential and gives it only to a subsequent Actions step.

**Verified branch for this project (18 October 2026): `production`.**
GitHub Actions read-only diagnostic [run 39078919990](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39078919990)
reported `BRANCH_NOT_FOUND` for `main` and discovered only `production`.
The manual bootstrap and scheduled refresh now both default to `production`;
keep the GitHub workflow itself on the GitHub branch `main`.
You may optionally set the repository Actions variable
`NEON_BRANCH_NAME=production` explicitly. If an already-defined
`NEON_BRANCH_NAME` variable has another value, correct it before enabling
scheduled refresh. The connection tool fails rather than silently switching
branches. Set `NEON_DATABASE_NAME` only when multiple databases exist on
the selected Neon branch. No new Neon compute or branch is created.

## 2. Bootstrap the already-existing Neon database (one-time owner action)

1. Open **GitHub → Actions → Neon existing project bootstrap (manual)**.
2. Click **Run workflow** on `main`. Select your existing Neon database
   branch `production` (confirmed by the Neon API on 18 October).
3. The action uses only `NEON_API_KEY` and `NEON_PROJECT_ID`. It validates
   connectivity, creates the application tables/views and appends the
   *source-transcribed* 18 Grid Scope observations at five connection points.
   A second run is idempotent; history must never be silently overwritten.
   This does **not** confirm the 18 operator numbers against Grid Scope.
4. Check that the run reports
   `neon_schema_and_sample_readback_passed` with five points and 18
   indicative capacity observations. No URL, raw readings or passwords should
   appear in the Actions logs.
5. For real operational data, confirm valid `FINGRID_API_KEY` and
   `ENTSOE_API_TOKEN` GitHub secrets (regenerate any previously exposed
   keys). Only **then**, after checking reuse terms, explicitly enable
   `ENABLE_PUBLIC_REFRESH=true` under GitHub repository Actions variables.
   Daily collection remains off by default.
6. Run **Actions → Hosted Finland evidence refresh (opt-in, free tier) →
   Run workflow** once with `backfill_days=1` and inspect the result before
   relying on any automatic schedule. The job resolves Neon credentials
   privately each run. You no longer need `DATABASE_WRITE_URL` in GitHub.

Bootstrap does not use Fingrid or ENTSO-E credentials and does not publish a
public dashboard. Only the separately enabled collector retrieves national
operational data. It strictly rejects partial observed days and never
converts national demand into per-substation headroom.

## Troubleshooting Neon bootstrap (safe to share)

On 18 October, a manual bootstrap run failed in the **Resolve selected Neon
branch database privately** step. Its log confirmed that `NEON_API_KEY` and
`NEON_PROJECT_ID` were available, but the previous script suppressed the exact
error. The bootstrap import step was skipped; no tables were created by that run.

Re-run the updated workflow once. It now reports a safe stage code:

| Stage / code | Meaning | Fix |
|---|---|---|
| `LIST_BRANCHES: HTTP_401` / `HTTP_403` | Neon API key rejected or lacks permission for this project | Check the correct GitHub integration, organization and key permissions in Neon |
| `LIST_BRANCHES: HTTP_404` | The API key cannot see the supplied project ID | Verify the Neon project currently connected to this repository |
| `BRANCH_NOT_FOUND` | The requested Neon branch doesn't exist | Use one of the printed branch names; GitHub `main` is not necessarily Neon `main` |
| `LIST_DATABASES: ...` | Neon cannot list databases on the selected branch | Check branch and API permissions |
| `DATABASE_NOT_FOUND_OR_AMBIGUOUS` | No unique database was selected | Set `NEON_DATABASE_NAME` repository variable to an existing DB |
| `GET_CONNECTION_URI: HTTP_4xx` | Cannot obtain a writer URI for the selected DB owner | Inspect Neon project role and key permissions |
| `GET_CONNECTION_URI: returned URI failed TLS/driver validation` | URI shape/SSL configuration not accepted by the app | Review whether the project returns a supported direct PostgreSQL URI |

The message **does not show passwords, connection strings or API response
bodies**. Avoid pasting raw secrets to obtain help.

## 3. Create a separate SELECT-only PostgreSQL role (owner action)

**Do not reuse the collector's writer URL in the public Streamlit app.**

In Neon SQL Editor, after the first successful import creates the schema,
create a role with a strong independently generated password. Adjust the
database name if yours is different:

```sql
CREATE ROLE grid_dashboard_reader LOGIN PASSWORD 'REPLACE_WITH_PRIVATE_STRONG_PASSWORD';
GRANT CONNECT ON DATABASE neondb TO grid_dashboard_reader;
GRANT USAGE ON SCHEMA public TO grid_dashboard_reader;
GRANT SELECT ON connection_point, capacity_observation, operational_series,
                grid_project, scenario_result,
                published_capacity, latest_operational
TO grid_dashboard_reader;
```

If the provider's role UI supports creating a restricted login, use it instead
of hand-written SQL. Test that this role can SELECT but cannot INSERT or
CREATE. Grant future views explicitly when they are introduced.

Generate a **separate read-only URL** for the new role with
`sslmode=require`. Do not put its password in the repo or screenshot.

## 4. Deploy Streamlit Community Cloud (owner action)

1. Sign in at https://share.streamlit.io/ using GitHub.
2. Choose **Create app → Deploy a public app from GitHub**.
3. Repository: `abhijith-sivaprasadan/finnish-grid-connection-evidence`.
   Branch: `main`. Main file path: `app/dashboard.py`.
4. In **Advanced settings → Secrets**, paste this template, replacing only
   the private connection URL:
   ```toml
   HOSTED_DASHBOARD = "true"
   DATABASE_READ_URL = "postgresql://grid_dashboard_reader:PRIVATE_URLENCODED_PASSWORD@YOUR_NEON_HOST/neondb?sslmode=require"
   ```
5. Deploy and check that the app says **Hosted read-only PostgreSQL
   snapshot**. It must show the five selected Grid Scope connection points,
   plus persisted national operational records from the successful import.
   If the database is absent, the app should show an explicit failure rather
   than generate fake data.
6. Record the *actual* `https://....streamlit.app` URL in README only after
   you verify the live deployment. Never guess that a chosen subdomain is
   available or claim a deployed app while it is not.

The Streamlit app does **not** receive Fingrid or ENTSO-E API keys. It does
not write data, create tables or initiate source ingestion. Public users
can only query the SELECT-only database role's authorized objects.

## 5. Check the no-cost budget monthly

- Neon: Free plan active, storage below the code-enforced 750 MiB upload limit and 1 GB project allowance, compute below the monthly
  100 CU-hour/project allowance, egress below 5 GB/month. A lightly visited
  portfolio site should usually consume little, but traffic affects usage.
- Streamlit: Free Community Cloud plan still active; check memory and
  hibernation messages. Cached public reads refresh every 10 minutes.
- GitHub: Keep public repository with **standard** runners, scheduled
  refresh **one per day**. Workflow failures will be shown in Actions.
- Data freshness: compare the newest source UTC interval to the current
  time. **A delayed or stopped update must remain visibly stale**, not be
  called live telemetry.
- Review ENTSO-E and Fingrid publication terms if datasets or display
  products change. Avoid reproducing protected private-source data.

## Failure modes and boundaries

- **Refresh variable disabled:** daily collection is skipped; one-time manual
  bootstrap remains available, but there is no automatically updated time series.
- **Provider does not publish a full day:** the strict coverage check fails.
  It will not publish partial data as a complete day.
- **Neon becomes unavailable or resource-limited:** app shows an error;
  historical data remains in the managed DB subject to provider policies.
- **Source revision:** new retrieval timestamps are preserved as
  independently dated rows. Do not overwrite old observations.
- **Grid Scope:** still manually source-transcribed, awaiting an independent
  value-by-value audit; no automated Grid Scope API is claimed.
- **ENTSO-E generation A75:** excluded from this scheduled pipeline until its
  separate authenticated smoke test succeeds.
- **Scientific scope:** national load/production context is not substation
  connection-capacity confirmation.

Official documents:
[Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) ·
[Streamlit secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) ·
[Neon Free Plan](https://neon.com/pricing) ·
[GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) ·
[Fingrid data attribution](https://data.fingrid.fi/en/about).
