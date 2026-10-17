# ENTSO-E live verification (manual workflow)

**No API credentials are stored in this repository.** The optional smoke test
makes a single completed-day ENTSO-E Finland request with the existing client
and verifies that returned records can be inserted into a temporary SQLite DB.

## Authentication

The Fingrid `avoindata-api.yaml` OpenAPI document is **an API specification, not
an API key**. Its `x-api-key` authentication is exclusively for the separate
Fingrid Open Data service at `https://data.fingrid.fi/api`.

ENTSO-E Transparency Platform has a separate personal security token. The
existing client reads the `ENTSOE_API_TOKEN` process environment variable.
Never paste real values into `.env.example`, source code, issues, screenshots or
GitHub workflow inputs. A token already pasted into a chat should be regenerated
before use in public-repository automation.

To run on GitHub:

1. Regenerate your ENTSO-E token in the Transparency Platform account settings.
2. In this repository, go to **Settings → Secrets and variables → Actions →
   New repository secret**. Name it **ENTSOE_API_TOKEN** and save the new token.
3. On the default branch, select **Actions → ENTSO-E live smoke (manual,
   secret-only) → Run workflow**. Leave the day blank to check a completed
   day three days before the run, or enter a YYYY-MM-DD day. Start with
   `load`; check `generation` separately.
4. Read the job result: it reports only country, kind, UTC window, counts
   and parsed metric names. It does not print or upload the token, full URL,
   XML payload or raw records.

To run locally, configure `ENTSOE_API_TOKEN` as described in
[SETUP.md](SETUP.md) and execute:

```powershell
python -m src.live_entsoe --kind load
python -m src.live_entsoe --kind generation
```

The network request may fail because of token access, publication delays,
unsupported curve semantics or upstream response changes. These are meaningful
validation failures; do not replace them with synthetic fallback values.

**2026-10-17 live-log follow-up:** the user-supplied GitHub Actions log reached
ENTSO-E and failed on the old A01-only curve restriction. The error did not reveal
the actual returned curve code or XML. The updated parser accepts the documented
**A03 variable-sized block** semantics as well as A01 and reports an explicit,
non-secret code for any remaining unsupported curves. In A03, each point denotes
the beginning of a constant-quantity block; the next point or Period end closes
that block. It is **not** a missing-data gap, and the importer preserves one row
per block without inventing intervening readings. Until the authenticated smoke
workflow is rerun successfully, mark ENTSO-E live verification **pending**.

Definition reference: [ACER field 44 curve type](https://www.acer.europa.eu/64-data-fields-related-secondary-rights-time-series-secondary-rights)
and [ENTSO-E XML Schema Use, section on A01/A03](https://transparency.entsoe.eu/content/static_content/download?loggedUserIsPrivileged=false&path=%2FStatic+content%2Fknowledge+base%2Fentso-e-transparency-xml-schema-use-1-0.pdf).

**Scientific scope:** Passing proves authenticated API access, conservative XML
parsing and temporary SQLite insertion for that day. It does not independently
verify Grid Scope substation estimates or demonstrate electrical connection
capacity. The temporary DB is deleted after execution. The regular CLI
(`python -m src.cli entsoe ...`) supports persistent local ingest, only after
the operator's reuse terms are checked.

The workflow deliberately has **no schedule** and runs only on `main`;
fork/PR submissions cannot invoke it with repository secrets. GitHub's secret
settings must be configured by the repository owner; ChatGPT cannot do so
through the current GitHub connection.
