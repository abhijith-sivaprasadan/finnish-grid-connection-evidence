# Evidence log — dated observations, not timeless status

Append new verified events with UTC time/date, immutable commit or endpoint,
method, measured result and limitations. Do not silently replace an old record.
For the current state, see [STATUS.md](STATUS.md).

| Date (UTC) | Verifiable event | Evidence | Boundary |
|---|---|---|---|
| 2026-10-17 | Five 400 kV points, 18 indicative point/direction/year MW entries compiled | `data/manual/grid_scope_observations.csv`; `docs/CAPTURE_LOG.md` | Original source transcription, not operator-approved headroom |
| 2026-10-18 | Initial hosted operational import and source validation, 288 records | GitHub commits #24–#26 and hosted ingestion records | Initial import count, not permanent total |
| 2026-10-18 | Two complete UTC dates recorded, 576 distinct intervals | [Release #28](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/pull/28) | Three separate national feeds; not substation data |
| 2026-10-18 12:04–12:05 | Scheduled source refresh succeeded: 96 intervals/feed for 2026-10-15; inserted 288 revision rows | [GitHub Actions 39125767276](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39125767276) | One verified unattended run; future schedules not guaranteed |
| 2026-10-18 | Public read-only API reported 864 all-time operational rows, 576 distinct intervals, 288 retrieval revisions | [quality endpoint](https://finnish-grid-atlas.vercel.app/api/v1/quality) | Dated state; revisions are not new time intervals |
| 2026-10-18–19 | 18 original Grid Scope transcriptions matched human-supplied screenshots; 17 exact tooltips, one panel MW value | [18-row audit ledger](audits/GRID_SCOPE_18_ROW_SCREENSHOT_RECHECK_2026_10_19.csv) | Source-number comparison only; screenshot images privately held |
| 2026-10-19 | Original 18-row sample preserved unchanged; audit metadata stored separately | `data/manual/grid_scope_observations.csv`, `docs/audits/` | No new physical/network validation or additional certified capacity |

**Terminology:** "stored rows" includes retrieval revisions;
"distinct intervals" counts the sampled historical time windows;
"published indicative" means Fingrid's conditional Grid Scope estimate;
"screenshot match" means a human-supplied image agrees with the source
transcription, **not** an operator-confirmed capacity reservation.

New evidence dates must come from a performed, reproducible check. Never
infer an operator publication date from the source capture timestamp.
