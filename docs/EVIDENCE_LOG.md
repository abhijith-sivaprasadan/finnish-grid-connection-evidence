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

| 2026-10-20 | Four 48-hour Finnish national PyPSA models solved optimally from checksum-matched original 2026 Fingrid data | [Solver-verification run 39388830827](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39388830827); [case study](PYPSA_FINLAND.md) | Single national bus with assumed 1,500 MW support, NOT operator connection MW |
| 2026-10-20 | 171 source-complete historical 2025 UTC dates, 14 original source-gap dates and 180 not covered dates | [Original source batch #5, run 39452882772](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39452882772); [PR #48](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/pull/48) | 17,640 authentic 15-minute pairs including partial days; NOT annual complete grid study |
| 2026-10-20 | Independently verified two 27-day winter study windows, 48 model project cases and six baselines | [Solver job 39419524961](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39419524961); [PR #43](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/pull/43) | Hypothetical market/support bound and batteries; no physical grid outage or headroom inference |
| 2026-10-20 | Historic 2024 ODbL 107-bus / 137-source AC line 220–400 kV Finland proxy reconstructed and audited | [Source runner 39458288987](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39458288987), [PR #49](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/pull/49) | Not an independently verified operator as-built 2025 network, 110 kV incomplete |
| 2026-10-20 | Source template and multigraph-only bridge audit: 22 model edge removals disconnect partial source topology | [Runner 39460934314](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39460934314), [PR #50](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/pull/50) | Topological property only, NOT electrical N−1 compliance |
| 2026-10-20 | Geographic overlap compared 2024 OSM to third-party FCG Feb 2025 line-map, 3,157 source-midpoint samples | [GIS run 39464313780](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39464313780), [PR #51](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/pull/51) | Near-zero median map distances may have common lineage; no equipment validation or third-party geometry redistribution |
| 2026-10-20 | Krios portfolio work reconciled with original phases: optional verified-scenario local SQLite import and role-targeted case study | [Acceptance matrix](KRIOS_PORTFOLIO_RELEASE.md), [current status](STATUS.md) | Completion applies to Finland MVP functionality, not Dutch stretch or live operator site approvals |

**Terminology:** "stored rows" includes retrieval revisions;
"distinct intervals" counts the sampled historical time windows;
"published indicative" means Fingrid's conditional Grid Scope estimate;
"screenshot match" means a human-supplied image agrees with the source
transcription, **not** an operator-confirmed capacity reservation.

New evidence dates must come from a performed, reproducible check. Never
infer an operator publication date from the source capture timestamp.
