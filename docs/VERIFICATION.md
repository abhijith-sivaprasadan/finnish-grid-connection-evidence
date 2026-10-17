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
| Authenticated Fingrid / ENTSO-E integration | **Not run: user has no credentials yet** |
| PyPSA / pandapower | **Not run: stretch** |
| Remote CI / publication | Pending after import; check the GitHub Actions run on this repository |

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

The quality report recorded 18 numeric published-indicative observations and `mvp_data_ready=false` because there is no live Fingrid operational import. Passing CI establishes application behavior, **not** authenticity or network validity of the source-transcribed capacity figures, connection rights, or live API compatibility.

The supplied OpenAPI export adds contract coverage for integral double-valued IDs
and pagination fields, absent lastPage, returned page sizes, nullable nextPage,
empty result sets, inconsistent metadata and seven-digit timestamp examples.
The source export is retained unchanged with its SHA-256 in `docs/reference/`.
Documentation examples remain outside the application database.
