# Fingrid 2025 batch 05 — source irregularity preserved, 171 complete days

**Operator-source collection:** [run 39452882772](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39452882772), [unaltered archived original records](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39452882772/artifacts/12279058480). Source-artifact ZIP SHA-256 `3570602836b1d2f5f002550b3d8046f25de5503ea2376b1b7b8d55ad3416d6f9`.

**Collector repair:** source revision [PR #46](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/pull/46), merged to draft research branch; 30-minute original capture is preserved as original, not substituted for two invented 15-minute readings. A separate 2025-05-08 source diagnosis independently observed the exact 11:30:00–12:00:00 UTC record in Fingrid 124 ([run 39449287073](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39449287073)). No smoothing, timestamp rounding or gap filling.

## Verified archive inventory

- **40 cumulative immutable chunks**, 20 each of Fingrid original datasets 124 consumption and 74 production; 8 new original chunks in this batch.
- **2025-01-01 to 2025-05-21 exclusive** in the journal = 140 UTC dates, with 127 source-complete days, 13 documented incomplete source days, 225 other calendar dates not downloaded in this *journal alone*.
- **13,416 original, genuinely paired 15-minute records** in the journal. An additional 14 complete summer days and 30 complete autumn days were already independently verified and are wholly disjoint from the January–May journal.
- **171/365 complete, distinct source UTC dates** after archive union. **17,640 original matched 15-minute observations** including partial days: 13,416 journal pairs plus 1,344 summer and 2,880 autumn pairs.
- **14 distinct known missing source-gap dates** (13 journal + independently audited 2025-07-11); **180 other dates** not inside the current verified archive bank. These states are distinct: 171 complete + 14 known gap + 180 not covered = 365.
- **24 known missing aligned consumption observations** in the journal, and 1 earlier July gap = **25 quarter-hour slots** across 14 days. Original 74 production data are regular for all captured journal windows.

## Two preserved anomalies

1. 2025-03-30 10:45:02–11:00:02 UTC: source 124 and 74 off-quarter-hour readings preserved separately. The absent aligned 124 slot is not manufactured.
2. 2025-05-08 11:30:00–12:00:00 UTC: source 124 returned one authentic **30-minute** interval. The 11:30 and 11:45 aligned quarter-hour consumption slots are treated as missing for paired modelling. No split or half-average is inferred.

## New complete blocks eligible for independent studies

- 2025-04-23 through May 5 (13 consecutive UTC days).
- May 7 (1 day).
- May 9–11 (3 days).
- May 17–20 (4 days).

The old independently verified January–April blocks, June 15–28 and September 15–October 14 retain their distinct provenance and are not double-counted.

**Limit:** This dataset is **not** a full 2025 annual record and does **not** justify full-calendar energy totals, uninterrupted annual storage schedules, national power outage conclusions or site-connection headroom. The next journal chunk, if requested, begins 2025-05-21 UTC; preserve manual bounded API access and original timestamps.
