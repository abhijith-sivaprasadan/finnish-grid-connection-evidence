# Local verification

Verified on 17 October 2026, Windows, Python **3.12.14**.

| Check | Result |
|---|---|
| Unit/integration/UI suite | **48 passed in 9.14 seconds** after supplied OpenAPI contract audit |
| Real CSV import into new SQLite database | Five connection points, 18 observations |
| Repeat the same CSV import | Zero inserted rows; history preserved |
| Quality command | Correctly reports both operational feeds missing |
| Python compile check | `src/` and `app/` compile successfully |
| Live local dashboard | Served at `127.0.0.1:8517`; browser verified headings, counts, controls, chart and missing-data table |
| Authenticated Fingrid / ENTSO-E integration | **Fingrid 124/74 passed (96+96); ENTSO-E A65 load passed (96)**, all 14 Oct 2026 UTC; temporary GH Actions DBs deleted |
| PyPSA / pandapower | **Not run: stretch** |
| Remote CI / publication | Imported to GitHub; current suite covers all source clients, persistence, rollback and dashboard views |

The suite includes Streamlit AppTest coverage for empty data, real CSV data,
direction changes and empty point selections. Data tests check MW/MVA preservation,
strict category separation, snapshot history, duplicate rejection, transaction
rollback, timezone normalization and provenance. Synthetic API fixtures test
pagination, repeated-page protection, rate-limit waits, retries, safe errors,
missing/invalid data, XML intervals and gap preservation. These fixtures are not
live-response captures and cannot establish API compatibility without a live run.

The Windows sandbox initially blocked its default temporary directory and the
loopback socket used by Python's event loop. The successful full suite ran with
approved execution outside that restriction and a repo-local temporary base:

```powershell
.venv\Scripts\python.exe -m pytest -q --basetemp .tmp\pytest-contract-full --tb=short
```

In a normal terminal or CI, `python -m pytest -q` is sufficient. `--basetemp`
designates a disposable test directory; never point it at valuable data.

GitHub Actions **passed 52 tests** on 17 October 2026 (Ubuntu, Python 3.12), and independently rebuilt the manual-data SQLite evidence store from committed CSVs. [View passing CI run](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39064038557). The original 48-test result is a historical Windows-local run. The new CI run includes the additional data-quality and database-migration regression tests.

The *fresh CI database* contains 18 numeric published-indicative observations and `mvp_data_ready=false`, since CI intentionally does **not** inject secrets or make live imports. The historical authenticated smoke runs instead proved real API access for Fingrid 124/74 and ENTSO-E A65, but deleted their temporary SQLite files. The local persistent sync has been fixture-tested and still requires an actual local run. Passing CI and smoke tests do **not** establish authenticity or physical validity of the source-transcribed Grid Scope capacity figures or any connection rights.

The supplied OpenAPI export adds contract coverage for integral double-valued IDs
and pagination fields, absent lastPage, returned page sizes, nullable nextPage,
empty result sets, inconsistent metadata and seven-digit timestamp examples.
The source export is retained unchanged with its SHA-256 in `docs/reference/`.
Documentation examples remain outside the application database.

## Authenticated-source and local-persistence follow-up (17 October 2026)

- [Fingrid authenticated smoke](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39066439315): source data parsed and inserted in a temporary SQLite database, 96 consumption (124) and 96 production (74) records for 14 October UTC.
- [ENTSO-E authenticated A65 load smoke log](../docs/ENTSOE_LIVE.md): 96 valid actual-load records inserted in a separate temporary SQLite database for the same UTC day after A03 parser correction. A75 generation remains unverified.
- The new [local persistent importer](LIVE_CONTEXT_IMPORT.md) retrieves all requested sources before one atomic transaction, preserves operator-reported source units and intervals, and never includes secrets in printed metadata. Offline tests prove successful insertion, repeatability for an identical snapshot, rollback on later failure, wrong-source rejection, and secret preflight.
- The Streamlit National context tab now shows source-level record coverage and retrieval dates when a locally populated database is available.

No real operational observations are committed or distributed with the code. Downloading the repository alone does not reproduce live operator readings until credentials are configured and an authenticated local import is run.
