# Fingrid 2025 fourth source batch — original March off-grid anomaly audited

Manual original-source batch [39447129155](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39447129155), original verified archive artifact [12276347617](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39447129155/artifacts/12276347617).

- Resumed all 24 previously captured immutable original chunks (run 39418640253); fetched **8 new original chunks**; 32 cumulative source chunks (16 consumption + 16 production), representing **112 calendar days Jan 1 through Apr 22, 2025**, UTC.
- Source-only journal: **106 fully paired UTC days**, **6 partially observed days**, **10 original consumption quarter-hour gaps** (production has no regular-source gap), **10,742 genuine paired original 15-min readings**, and 253 not-downloaded calendar days in this journal.
- One off-grid original Fingrid dataset 124 row and an additional dataset 74 row are both timestamped **2025-03-30T10:45:02Z → 11:00:02Z** (durations exactly 15 minutes but start offset by two seconds). Both original records are retained, cryptographically hashed and quarantined rather than silently rounded. Consumption dataset 124 has no authentic 10:45:00Z-aligned interval; source gap remains. Production 74 has the genuine 10:45:00Z record too. The code's optional quarantine is fully regression-tested and strict about native row identity and 15-minute duration.
- The first two failed fourth-batch attempts captured **no new source chunks**: the first had an accidentally incorrect requests pin, and the second rejected this actual off-grid operator reading instead of silently altering it. Corrected collector at tested SHA 65111e9ff69e1cac78214b5a74d78b5f7163062b passed source-integrity tests and batch #39447129155.

### Original dataset 124 exact UTC gaps in the verified January–April journal
2025-01-17 17:00, 17:45; 2025-02-14 17:00, 17:45; 2025-03-14 17:00; **2025-03-30 10:45** (unaligned 10:45:02 source row also preserved separately); **2025-04-11 16:15, 17:15, 17:45**; **2025-04-22 17:00**. An additional original missing 2025-07-11 16:15 was found in a separately authenticated Fingrid query.

### 2025 distinct audited source bank after merging previously verified disjoint archives

- The new journal 106 fully complete dates plus Jun 15–28 (14) and Sep 15–Oct 14 (30) gives **150 distinct, source-complete 2025 UTC dates**, NOT a complete 365-day dataset.
- Across the merged archives: **14,966 unique original paired quarter-hour readings**, including **566 genuine pairs on the six incomplete journal days**. There are **seven dates** with 11 known source-missing 124 slots (six captured partial days + previously identified Jul 11), and **208 dates outside imported original archives**. No values guessed, interpolated or treated as zero.
- The existing independent 14-day winter source overlaps the 112-day journal and has been independently numerically audited; do not double count it.
- The new original ZIP SHA-256 as downloaded: 5a548bfc746e03b0b504d1a8ea67017795604316d1287edb13ef378ae4192974.

Next manual original-source 7-day window starts **2025-04-23** with prior resume GitHub Actions run ID **39447129155**; do not chain further automatic Fingrid requests or bypass 429. This report does NOT validate full-year demand/production, import or 2030 site capacity.
