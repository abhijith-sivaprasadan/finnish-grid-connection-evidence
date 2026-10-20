# Whole-project data integrity and engineering audit

**Dated 20 October 2026.** Repository: [Finnish Grid Connection Evidence](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence). Baseline revision **713474e741a61c31e6bb6a754e88a90050cc4657**; changes tracked separately on the audit branch. The starting repository inventory included **349 Git tree entries**.

**Verdict:** The work is credible as a **portfolio-grade, source-traceable grid evidence and engineering benchmark prototype**. It is **not independently certified by Fingrid, TenneT, or a physical-network operator**, is not a bankable substation connection-capacity assessment, and lacks source support for a genuine 2025 Finnish AC/N−1 network model. The audit found and corrected real internal evidence-attribution and publication-integrity weaknesses, but external verification and release governance remain open.

## Evidence categories and what this audit can prove

| Category | Evidence reviewed | What passes | What is not established |
| --- | --- | --- | --- |
| Grid Scope point estimates | Five original point rows, 18 original indicative MW rows, 18 screenshot review-ledger rows, 18 published website rows | Entire CSV/ledger/UI field and ID agreement | Underlying screenshot bytes, independent operator source reread, current values, approved MW |
| Fingrid 2026 national operations | Original 192 × 15-minute 124/74 CSV, website compiled series, source retrieval metadata | Exact UTC windows, 192 record-by-record numerical/source agreement, original SHA-256 in modelling output | An independent portal numerical spot check; site-level or regional measurement |
| Historical 2025 national archive | Dated source coverage, prior GitHub source recovery and model runs | Source coverage buckets agree; gaps are explicit | Full 365-day series or 2025 site headroom |
| Neon hosted evidence | Live read-only overview, health, quality endpoint and source code for writer/reader roles | 5 points, 18 indicative values, 1,440 stored operational rows/revisions; health connected | Independently audited live Neon ACLs, all historical revisions numeric-matched to operator portals |
| Netherlands map pilot | Three official source-export hashes, schemas and aggregate source codes | 23 + 271 + 602 = 896 different layer records with distinct direction fields | 896 grid sites, Dutch MW headroom, raw data redistribution rights |
| CIGRE engineering models | Pinned pandapower solver runs, PyPSA runs, original CI ZIPs and publication summary | Actual solved reference-network cases; cross-solver 3-bus parity; source-artifact to website metrics agree | Fingrid/TenneT equipment or operator-grade engineering approvals |
| OSM geography | Five hash-pinned 2024 Zenodo sources, browser source data arrays | All 107 virtual bus coordinate/voltage tuples and 137 displayed edge pairs match original derived FI CSV ordering | Current Fingrid as-built line states, true route identity/ratings, named Grid Scope point crosswalk |

These are **internal publication and scientific boundary checks**, not proof that official source observations are correct in the original system. The live source status and CI results must always be cited with their dates.

## Findings register

| ID | Severity | Status | Finding and evidence |
| --- | --- | --- | --- |
| DI-001 | High | **Fixed in audit branch** | Screenshot-review code used JavaScript millisecond-limited Date.parse, permitting a +1µs or +999µs modified capture timestamp to inherit historical verification. It also did not require the same original source URL. Now canonicalizes full UTC microseconds and requires the historic source link; tampering tests added. |
| DI-002 | High | **Owner action** | The GitHub branch API reports **main.protected=false** while Vercel automatically releases main. Without protected-branch required checks and reviews, direct pushes can bypass the tested release workflow. Turn on a branch ruleset/review/required-CI protections, and restrict release production credentials to reviewed code. No repository security setting was changed by this audit. |
| DI-003 | Medium | **External verification pending** | The 18 screenshot audit ledger stores image fingerprints and a review grade, not the original screenshot image bytes. Audit code can detect metadata drift but cannot independently reopen and compare the original image content; Grid Scope data are dated Oct 17 and may change. Reobserve rights-compliantly and keep new snapshots separately. |
| DI-004 | Medium | **Fixed in audit branch** | The original Grid Scope CSV, hardcoded website capacity fallback, published reviewer JSON and separately generated numerical model JSON previously had no single fail-closed source-to-publication check. New CI audits every site-source value, reviewer shown value/unit/grade/date/fingerprint, all 192 original national numerical intervals, and model-source hashes. Adversarial mutations must fail. |
| DI-005 | Medium | **Fixed in audit branch** | The displayed 2024 OSM network arrays were manually embedded and previously checked mostly by count. A new independent source-backed check compares **every one** of the 107 coordinate/voltage records and **137** graph endpoint pairs to five checksum-pinned original source files. This verifies historical proxy correspondence only. |
| DI-006 | Medium | **Fixed in audit branch** | Hand-curated engineering website figures could drift from the original CIGRE/PyPSA/OSM model artifacts. New independent CI job compares numerical fields with fresh artifacts from the actual solver jobs. One adversarial test found that the published shown_value in the reviewer JSON was not originally checked; the auditor was extended and its test then passed. |
| DI-007 | Medium | **Source gap** | 2025 source archive has **171 complete UTC days**, **14 known gap days**, **180 days not covered**; **17,640** genuine paired 15-minute observations including partial days. Cannot claim a full 2025 measured annual source or annual PyPSA model. ENTSO-E A75 and operator portal exact-value comparisons remain unverified. |
| DI-008 | Medium | **Engineering limitation** | Finnish 2024 OSM geometry and template R/X/B/rating fields lack independently calibrated 2025 operator equipment, switching, 110-kV completeness, nodal loads and generation, local measured flows and actual N−1 operating criteria. Source graph bridge screening is not real Finnish N−1 security compliance. |
| DI-009 | Medium | **External licence review** | OSM-derived 2024 virtual map is attributed under ODbL 1.0 with share-alike obligations. February 2025 third-party map raw geometry and Dutch original feeder CSV redistribution permissions were not independently established; original raw third-party location records should remain unpublished. |
| DI-010 | Medium | **Maintenance hardening pending** | GitHub Actions rely on moving major action refs rather than full vetted SHAs; several indirect dependency versions are floating. Repository also carries legacy Next.js directory web/ alongside canonical website/. Pin reviewed dependencies/action versions and deprecate old runtime only after checking consumers. |
| DI-011 | Low | **Disclosure improvement pending** | The reported maximum PyPSA/pandapower 3-bus AC parity difference rounds to **0** in the model summary but archived unrounded discrepancies are approximately 2.22e-16 pu and 2.27e-13 MW. Scientifically both negligible, but zero at display precision is not literally mathematical identity. |
| DI-012 | Medium | **Fixed in follow-up CI PR** | Original CIGRE N−1 handler caught every Python exception as unresolved contingency; a programming KeyError could be mistaken for an outage. Raw archive has **nine** LoadflowNotConverged exceptions and **one** ValueError (Trafo 9-1) in each of the ten unresolved cases. New handler fails on unexpected exceptions and explicitly distinguishes solver non-convergence from ValueError requiring manual diagnosis. |

## Source and database audit

The original 17 October 2026 Grid Scope capture includes only five selected 400-kV points and 18 source-transcribed estimates across three effective years and two directions. The 18 reviewer metadata records have **17 exact tooltip** and **one explicit panel-number** provenance grades. They are not operator-confirmed MW. Of 30 potential sample combinations, 12 are **uncaptured/unknown, not zero**. It is invalid to add MW between stations, substitute production for consumption, interpolate years or infer that a 100-MW project can connect at an indicated 400-kV station.

The authenticated historic Fingrid 124 consumption and 74 production source sample is exactly **192 native 15-minute intervals, 15–16 October 2026 UTC**. Committed original CSV SHA-256 **ab0316e695bbea34cc16b498ade06746bcc5087485f2f6cfde4b6630341109e6** matches the v1 national PyPSA and v2 two-region source declarations. The audit independently rechecks the HTML website series against each original CSV interval, start/end, original numerical quantity and retrieval timestamp; no reconstructed/interpolated missing records are inserted by this publication check.

The 2025 source archive is partial as described in DI-007. Separate studies comprise **two uninterrupted 27-day winter windows**, 48 project solves plus 6 baselines, and **24 SE1/SE3/FI commercial-corridor scenarios**. Historical remaining intraday market trading capacity is not the same thing as a conductor thermal rating or a purchased import right. Both scientific qualifications remain explicitly documented.

The live Vercel site served commit **713474e7** when inspected, connected to Neon: API overview 5/18 original Grid Scope records and **1,440 stored operational rows**, with newest operator interval ending **18 October 2026 00:00 UTC**. Live quality returned completed latest daily Fingrid 124/74 and ENTSO-E A65 intervals, including revision counts on previous days. Rows include multiple fetch revisions; 1,440 does not mean 1,440 distinct physical electricity intervals. The health response proves SQL SELECT connectivity, not freshness or operator numeric authenticity. The collector deliberately lags completed UTC days and source freshness monitoring defaults to 168 hours; neither is real-time SCADA.

SQLite schema separates published indicative capacity, modelling scenarios and historical national operations. The Neon mirror uses typed tables and append-only/versioned idempotent operations with transaction rollback on duplicate conflicts. The public API uses SQL query parameters and a distinct configured Neon reader username plus SSL. A CI PostgreSQL role test confirms an analogous reader cannot insert; **actual production Neon schema grants were not independently queried**. Hosted site credentials were not requested or surfaced in audit outputs.

## AC benchmark and modelling integrity

**CIGRE 13-bus high voltage:** Three genuine pandapower 3.5.6 nonlinear AC cases with hypothetical 0/50/100 MW incremental load at stated 0.95 lagging power factor. At 100 MW, modelled minimum bus voltage is **0.912236 pu**, losses **72.62941 MW** versus baseline **53.36567 MW**. Fifteen individual reference-network line/transformer removals are evaluated per case; **10/15 N−1 cases were unresolved: 9 pandapower LoadflowNotConverged and 1 separate ValueError (Trafo 9-1)**. Neither nonconvergence nor a ValueError can be scored as an acceptable contingency; the ValueError root cause and possible islanding or solver behaviour still require diagnosis. Illustrative 0.9–1.1 pu thresholds are not official Finnish/Dutch planning-code compliance.

**CIGRE 15-bus medium voltage:** Four genuine 0/0.5/1/2 MW generic feeder load cases, independent of the official Dutch congestion metadata. This benchmark must not be represented as a real Dutch feeder or evaluated for 100-MW data-centre connections.

**Independent AC parity:** Matching explicit artificial 110-kV three-bus full nonlinear AC model, identical P/Q, R/X and slack, independently solved in pandapower and PyPSA isolated pinned environments. **Not** a cross-validation of all CIGRE HV transformers, shunts and control modes. At original float precision maximum numerical differences are **2.220446049250313e-16 pu** and **2.2737367544323206e-13 MW**; published values round to zero at website display precision.

**Finnish PyPSA v2:** Four 192 × 15-minute optimal north/south hypothetical market-network cases using genuine national observed 124/74 records. North production fraction **0.65**, north demand fraction **0.45**, synthetic north–south corridor **1500/750 MVA**, and fictional regional balancing generation are explicit assumptions. All mathematical source-shortfall values are zero because hypothetical resources were provided; that is not a Finnish reliability demonstration, real measured P1 flow or substation headroom estimate.

**2024 OSM proxy:** Five source files checksum checked to Zenodo DOI **10.5281/zenodo.14144752**; 107 FI-labelled virtual buses (104 AC, 3 DC), 137 internally modelled 220/400-kV source AC graph edges. New independent map auditor matches all source bus/edge tuples and keeps ODbL attribution. The count of 22 graph bridges and 75/100/125% template nameplate comparisons are **source-model properties**; they do not prove actual line outages or calibrated Finnish thermal constraints. The map intentionally does not cross-match the five named Fingrid Grid Scope substations to these source virtual bus locations.

## Netherlands source integrity

Three dated Netbeheer Nederland original CSV exports were verified against source file hashes and schema on 20 October 2026: **23 TenneT high-voltage feeding areas**, **271 TenneT congestion rows**, and **602 regional DSO feeding areas**, **896 source rows total** across different levels. Raw TenneT source category codes afname consumption **0:11 / 1:70 / 3:190** and opwek injection **0:67 / 1:6 / 3:198** remain uninterpreted as available/infeasible capacity because no code dictionary was separately certified. The pilot publishes aggregate metadata rather than raw third-party feeder geometry or Dutch site connection MW.

## Security, CI and operations

At audit baseline, GitHub's branch endpoint returned **protected=false for main**. The same branch is used for Vercel production deployment. **Require an owner-configured branch ruleset** with PR review and mandatory evidence, website and engineering workflow checks; otherwise an unreviewed direct push can reach production. The audit does not claim to have enabled protection. Pin action SHAs and publish software bill of materials/resolved dependency lockfiles for longer-term reproducibility; review the older web/ directory before removing. Vercel Hobby runtime logging did not permit reviewing a 24-hour historic window; a **30-minute recent error/fatal query returned no rows**, which is not proof of outage-free operation.

### New enforced integrity protections

- Original Grid Scope CSV, screenshot review ledger and fallback browser data must match in every point/year/direction/value/unit/source-related field.
- The 192 original Fingrid national 2026 source rows must match the compiled website time-series values, UTC windows and retrieval metadata.
- Original site source reviewer attribution must preserve full six-digit UTC capture precision and historic source URL.
- The 2024 ODbL map must match all 107 individual source coordinates and 137 original source graph edges.
- Published engineering JSON must agree numerically with actual fresh pandapower, PyPSA, OSM and independent AC comparison artifacts.
- Seven deliberately corrupted source/document/claim scenarios must be blocked before release (a reviewer shown-value mutation revealed an initial audit gap; the check was fixed).

The new controls are assessed by GitHub Actions. Most are deterministic source-to-publication comparisons, not independent operators' live-source numeric certification.

## Exact owner/research follow-up

1. **Secure production releases:** enable GitHub main branch protection/ruleset and require review plus all relevant Actions checks before auto-deploy to Vercel.
2. **Independent upstream check:** reopen all 18 source estimates as new dated screenshots/tooltips and retain original evidence in a rights-compliant archive; independently compare at least one exact 15-minute Fingrid 124 and 74 value and one ENTSO-E A65 value against the official portals.
3. **Scientific validation:** obtain operator-supported dated 2025 as-built 110/220/400-kV network, physical equipment R/X/B/ratings, actual switching and generation/load allocations before site-specific Finnish AC/N−1 calibration or investment feasibility claims.
4. **Strengthen reproducibility:** pin GitHub action full SHAs and indirect solver dependencies; include machine-readable version/environment metadata, and distinguish raw precision from displayed float rounding.
5. **Rights and infrastructure:** independently review ODbL database share-alike obligations, unlicensed third-party maps/Dutch raw CSV permissions, and actual production Neon reader grants. Treat the historical source portal/capture date and partial 2025 archive as visible decision qualifications.

**Presentation-safe description:** a verified early-stage evidence triage application with independently solved and internally cross-checked reference AC engineering models and explicitly hypothetical Finland PyPSA sensitivity, **not** an operator-certified connection availability engine.
