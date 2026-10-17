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

## 1. Create the free Neon database (owner action)

1. Register at https://console.neon.tech/ and choose **Free**, preferably a
   nearby EU region. Confirm it displays **$0/month**.
2. Create a project (e.g. `finnish-grid-evidence`) and note its database name
   (commonly `neondb`). Never commit or share any database password/URL.
3. Copy the *writer* PostgreSQL connection URL with SSL enabled; it is normally
   of the form `postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require`.
   The collector needs CREATE TABLE/VIEW, INSERT and SELECT privileges.
4. In this public GitHub repository, go to **Settings → Secrets and variables →
   Actions → Secrets**. Create `DATABASE_WRITE_URL` containing the URL.
5. Ensure valid replacement API tokens are already saved there as
   `FINGRID_API_KEY` and `ENTSOE_API_TOKEN`. Regenerate any previously
   exposed API keys first. The new code does not contain tokens.

**The API endpoints cannot be tested against your Neon instance without these
private secrets. Do not paste them into an issue or chat.**

## 2. Bootstrap the hosted database (owner action)

1. Review source rights, attribution and the limits in
   [SOURCES.md](SOURCES.md). Fingrid-produced Open Data is CC BY 4.0 and
   requires a visible credit and license link; ENTSO-E and Grid Scope have
   separately documented terms.
2. Open **GitHub → repository Settings → Secrets and variables → Actions →
   Variables**, add repository variable `ENABLE_PUBLIC_REFRESH` with value
   `true` only when you explicitly approve hosted source retrieval.
3. Open **Actions → Hosted Finland evidence refresh (opt-in, free tier) →
   Run workflow** on the `main` branch. Leave the day blank and
   `backfill_days=1`. This checks coverage for both Fingrid 124/74 and
   ENTSO-E A65 before an **atomic Postgres upload**.
4. Confirm the workflow concludes successfully and its safe output includes
   `hosted_postgres_mirror_completed`, the requested UTC day, coverage
   counts and inserted rows. No API keys or raw values are logged.
5. Optionally run one manual backfill with 3 or 7 *consecutive* completed
   days (ending at least two days earlier). If any feed has missing
   intervals, the workflow **fails closed without uploading a partial batch**.

The scheduled refresh begins only when the enable variable is present. To
stop scheduled collection, set `ENABLE_PUBLIC_REFRESH=false` or delete it.
Avoid leaving an enabled collector with missing secrets.

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

- **No secrets, variable disabled:** collection is skipped; no Neon data is
  uploaded. The hosted app cannot truthfully call itself live.
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
