# Fingrid 2025 historical source collection — second paired batch

**Status: source collection and archive union verified; full-year history NOT complete.**

## Actual authenticated batch results (20 October 2026)

- [GitHub Actions run 39416081929](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39416081929) completed successfully. Source artifact: [12261961998](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39416081929/artifacts/12261961998), name `fingrid-original-2025-recovery`.
- This run **restored and cryptographically revalidated** the first eight original source chunks captured in [run 39413812083](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39413812083), then captured exactly **eight NEW original operator-source chunks**, four matched seven-day windows × Fingrid 124 (consumption) and 74 (production).
- **16 total journal chunks** (8 per dataset), covering UTC 1 January through 25 February 2025 inclusive: **5,372 original paired 15-minute readings**, **54 complete paired days**, **two incomplete days**, **309 days not yet downloaded into the journal**.
- API rate limit was respected and no HTTP 429 or access-deferral occurred. No interpolation or synthetic original records.
- Immutable source journal contains individual dataset identity, native MWh/h unit, UTC start/end, numeric observation, operator URL, source retrieval time, per-chunk hash, and the exact daily coverage ledger.
- Original source artifact ZIP SHA-256 (downloaded exact artifact bytes): `c75692f63995234f9b94aef037288b70478cc73aaddb3a511b37b469d9a80ee3`.

## New source gap discovered in dataset 124

| UTC source interval | Original 124 consumption | Original 74 production |
| --- | --- | --- |
| 2025-01-17 17:00–17:15 | Missing at source | Available |
| 2025-01-17 17:45–18:00 | Missing at source | Available |
| 2025-02-14 17:00–17:15 | **Newly found missing** | Available |
| 2025-02-14 17:45–18:00 | **Newly found missing** | Available |

Also separately confirmed missing through the operator recheck: **2025-07-11 16:15–16:30 UTC** (dataset 124). Track data corrections in [issue #40](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/issues/40). These five intervals across three days are the **known audited gaps**, not proof no other historical gaps exist.

Fully contiguous source-complete runs from the current source journal:
- Jan 1–16: 16 days
- Jan 18–Feb 13: 27 days
- Feb 15–25: 11 days

The two source-gap days (Jan 17 and Feb 14) each retain **94 genuine paired original observations**; those days must not be passed as continuous 96-interval modelling input.

## Cross-validation against earlier archived observations

Original SHA-pinned 14-day winter source archive from [run 39396079522](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39396079522) was compared numerically with the new journal:

- **1,344 shared UTC quarter hours**, January 18–31.
- Dataset 124 **and** 74 source values agree exactly on all overlap intervals.
- No overlap values were duplicated.

The independently validated source bank from prior [archive run 39412085922](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39412085922) had 58 distinct source-complete days. New journal has 54, with 14 overlap, yielding **98 distinct original-source-complete 2025 days**.

Union of original sources from the 30-day autumn archive, 14-day winter/summer archives, and 56-day January–February journal:

| Verification item | Count |
| --- | ---: |
| Distinct complete historical UTC days | 98 |
| Quarter-hour observations on complete days | 9,408 |
| Observations on two partially captured days | 188 |
| **Unique original paired quarter-hour intervals** | **9,596** |
| Known original-source gap dates | 3 |
| Dates outside these verified original archives | 264 |
| Complete original 2025 calendar history | **No** |
| Annual PyPSA optimization solved | **No** |

A complete source-year input still requires original 15-minute records for both Fingrid 124 and 74 at **all 35,040 UTC quarter-hour intervals**. Nothing in this source collection validates real Finnish network capacity, substation headroom or future 2030 electrical feasibility.

## Resume the NEXT batch safely

Do not rerun the second batch from scratch. Instead:

- On **main**, manually start [Manual verified Fingrid source recovery](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/workflows/fingrid-source-recovery.yml).
- Operation: `annual_source_chunk_batch`.
- `resume_run_id=39416081929` (this batch's artifact).
- `max_new_chunks=8`. Existing 16 chunks must be revalidated and skipped; new retrieval should begin at the **26 February 2025** UTC chunk.
- Check the resulting source journal for gaps and API response before accepting new source-complete days.

The source artifact has **30-day retention**. Do not rely on it indefinitely without preserving it. No additional batches are automatically scheduled.

**Important:** The PR's existing 58-day coverage web page describes the earlier archive-only inventory. It does **not** yet incorporate these later source journals; a separate verified UI update should follow only after full source reconciliation.
