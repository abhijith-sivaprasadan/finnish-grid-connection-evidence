# Grid connection readiness and Netherlands source pilot — 20 October 2026

These are **independent research portfolio extensions**, not operator-approved connections, bankable grid headroom, or an authoritative network model.

## 1. Fingrid connection-pathway review

Official source: https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/

Fingrid describes standard switchyard arrangements as **110/220 kV for less than 250 MW** and **400 kV for 250 MW and above**. Direct connections to 220/400 kV transmission lines are not permitted, while 110 kV line connections are reviewed case-by-case, including the 40 MVA transformer nominal-size restriction.

The original 100 MW in 2030 Finnish screen remains **two screenshot-matched indicative 400 MW station threshold matches** (Seinäjoki and Uusnivala) and **three exact-year unknowns** in the original five-point Grid Scope sample. The two threshold matches are now independently flagged **review_lower_voltage_switchyard**; the actual 110/220 kV bay or transformer arrangement is NOT demonstrated in the sample. This flag does not mean the site is proven infeasible.

The source-based screening now reports connection arrangement (switchyard, line or unspecified), planning-pathway status, exact-year evidence presence, unverified point-specific reinforcement and the next operator question. UI outputs, read-only API, CSV and downloadable Markdown readiness reports all preserve the original source status; no capacity observations or operator-confirmed classifications are changed.

Further demand-project guidance: https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-code-specifications/grid-specifications-for-demand-connections/ and the May 2026 connection-agreement procedure https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/uusi-liityntakysely/connection-agreement-application/ . These rules are decision gates, **not forecasts, location confirmation or permits**.

## 2. Netherlands — genuinely downloaded official operator source CSVs

Netbeheer Nederland provides original congestion and queue information for TenneT high-voltage and regional distribution feeding areas:
https://capaciteitskaart.netbeheernederland.nl/info/algemene-info/
https://capaciteitskaart.netbeheernederland.nl/info/faq/

Source audit verified on 20 October 2026:
https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39479644314

| Original source | Rows | Original byte SHA-256 |
|---|---:|---|
| TenneT high-voltage feeding areas | 23 | 22cc139287b29b34d3c1f7fbfcf5ef057d42f33e49342cb5e27bc376c92075bf |
| TenneT congestion-area coded statuses | 271 | 633d9bdd676cb1c101f75134537fe361d73593d3435353d0af40fc11eb76a5be |
| Regional DSO feeding areas | 602 | 865d1b036fbd41bce00e53f5e309114b757132a240e4af29505aa6f9b3436c4c |

The 271 TenneT map rows contain separate source coded consumption (afname) statuses **0:11, 1:70, 3:190** and injection (opwek) statuses **0:67, 1:6, 3:198**. Their labels are **not independently decoded or mapped to specific red/orange/available meanings**, and cannot predict site grid rights. Nominal present capacity and waiting-list MW do not mean spare available MW. The official map is a dated indicative snapshot, not a live binding project application.

The source retrieval is reproducible in a dedicated GitHub Actions job; it records source schemas, completeness, row counts and original CSV hashes. Website and API display **aggregate metadata only**. There is no redistribution of original site/feeder-level records or geometry because a standalone derivative-data redistribution licence has not been verified.

Routes: website /netherlands and /api/v1/netherlands/source-summary. The captured source snapshot is static; refreshing the audit is not an automatic deployment or ongoing live-data feed.

## 3. Acceptance and stop conditions

- Fingrid standard switchyard/line rules applied separately from source MW: **implemented**.
- Two indicative threshold matches and three unknown 2030 consumption cells preserved: **implemented**.
- More appropriate engineering next actions and a downloadable follow-up brief: **implemented**.
- Official Netherlands three CSVs source-verified and categories separated by offtake/injection: **implemented**.
- Raw source rights and individual Dutch feeder availability: **not established; not claimed**.
- Authoritative 2025 Fingrid network AC/N−1, Dutch physical DSO model, legally binding connection arrangements: **not supplied or claimed**.
- Release GitHub CI, then separately verify the Vercel production alias; the previous Free deployment quota may prevent immediate publishing.

This extension shows sound grid-analysis judgement: ask a better next question instead of manufacturing a more precise but unjustified capacity answer.
