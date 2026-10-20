# Grid Analyst interview demonstration — Finnish Grid Atlas

**2–3 minutes; evidence-first and independent.** This is a portfolio project inspired by the requirements of a Grid Analyst position. It is NOT a Krios or Fingrid production platform. Dated source scope is documented in [release handoff](KRIOS_PORTFOLIO_RELEASE.md).

## Start: the decision and why it is hard (about 20 seconds)

"A proposed 100 MW electricity load needs an early, defensible site screen. National generation-minus-consumption tells us little about the grid's *local* connection capacity. I therefore start with published point-specific Fingrid Grid Scope estimates, keep the original source and qualifiers, and put operational history and PyPSA modelling into separate layers."

Open the [portfolio case study](https://finnish-grid-atlas.vercel.app/case-study) and [100-MW screening example](https://finnish-grid-atlas.vercel.app/screening?demand_mw=100&year=2030&direction=consumption&voltage=all).

## Part 1: show conditional point data (about 35 seconds)

"Here are five selected 400-kV Fingrid substations, not a sample of all Finnish grid points. The original October 17 snapshot records **18 indicative estimates across 30 possible point × direction × year intersections**. The remaining 12 are *not captured*—not zero. Independent comparison against reviewer-supplied Grid Scope screenshots matched all original figures on 18–19 October: 17 exact tooltips and one displayed panel MW value. This verifies transcription, not physical connection rights."

"The 2030 consumption case has **400 MW** published indicative figures at Seinäjoki and Uusnivala. They pass an **illustrative 100-MW threshold filter**. Neither is approved or ranked as a connectable project. For Vuolijoki, Alapitkä and Alajärvi, the *specific 2030 consumption evidence is missing from this capture*; no technical infeasibility can be inferred."

Click a [source-linked capacity row](https://finnish-grid-atlas.vercel.app/connections). Show unit, direction, effective year, source capture time and the operator URL. Do not add a station's production MW to its consumption MW, or interpolate between 2026/2030/2035.

## Part 2: prove source engineering (about 35 seconds)

"The [national operations](https://finnish-grid-atlas.vercel.app/operations) and [data-quality](https://finnish-grid-atlas.vercel.app/quality) workbenches pull authenticated Fingrid datasets 124 and 74, plus ENTSO-E A65 actual load. They retain native measurement units, exact UTC time intervals, retrieved source provenance, missing intervals and revisions in SQLite or hosted Neon. The dashboard is read-only; scheduled ingestion uses separate private credentials."

"One unattended refresh is documented on October 18. Later historical source-archive work verified **171 complete 2025 UTC days** and preserved original gaps. That archive is NOT the same thing as a complete 2025 annual dataset or a source of point connection MW."

At demonstration time, first inspect actual freshness and health. If a live source is not available, say "last source interval unavailable" or explicitly describe a historical snapshot. Never claim current operational freshness from a passing unit test.

## Part 3: explain PyPSA without overclaiming (about 35 seconds)

"The [PyPSA analysis](https://finnish-grid-atlas.vercel.app/analysis) has **four verified 48-hour historical national cases**. A hypothetical 100-MW new load is compared with flexible demand and storage, bounded by an *assumed* balancing ceiling. A further two noncontiguous 27-day winters contain **54 optimal model solves**, and a three-market-bus Swedish corridor study contains **24 scenarios** using authentic commercial-flow/headroom source data."

"These are **sensitivity studies**, not a validated Fingrid AC network, electrical N−1 security analysis, operator import rights or a local headroom estimate. A numerical model's shortfall slack is not a Finnish power outage."

The 2024 OSM high-voltage network proxy and February 2025 third-party map comparison are deliberately separate research with unverified electrical ratings and unresolved map redistribution rights.

## Finish: handoff to real engineering (about 20 seconds)

"A credible next project step would require a precisely located connection site, proposed commissioning year, time-resolved load and flexibility, voltage, power factor/reactive requirements, published queues and reinforcements, and ultimately a Fingrid connection study. This tool reduces evidence-gathering uncertainty and makes unknowns visible; it doesn't grant grid access."

### Expected questions

**Can a 100-MW data centre connect to Seinäjoki or Uusnivala?** Not established. The figures are conditional 2030 estimates for a small historical snapshot and support only the source threshold classification; they do not state reserved or guaranteed MW.

**Is the PyPSA line network real?** The main studied winter/corridor cases are national or abstract market-bus models, not physical Finnish branch-constrained AC networks. The OSM-derived topology is a separately licensed 2024 *candidate*, with standardized estimated impedances; proximity to another map is not operator engineering verification.

**Why use two years in the same portfolio?** October 2026 is the date of the original Grid Scope sample and 48-hour model; 2025 is historical national 15-minute observations and winter/cross-border sensitivity. The source datasets and their periods are labelled individually, never silently combined.

**Do you have a current 2025 physical-grid headroom estimate?** No. Site physical headroom is intentionally null; operator-confirmed capacity count is zero.

**Is the Netherlands stretch done?** No. The Finnish MVP was the original cut line. The Netherlands DSO data import and optional pandapower feeder would be an independent follow-on with its own licensing and source assurance.

### Local reproducibility

    python -m pip install -r requirements.txt
    python -m src.cli import-manual
    python -m src.cli import-verified-model
    python -m streamlit run app/dashboard.py

The optional model import writes **12 validated scenario metrics** to local SQLite under model_scenario, never into published capacity. It does **not** publish model data to Neon. If no local provider credentials are configured, the Streamlit national-context view may correctly remain empty; hosted live operations are sourced through separate guarded collectors.

Start-to-finish release evidence and the original Krios acceptance requirements: [portfolio release](KRIOS_PORTFOLIO_RELEASE.md), [current dated status](STATUS.md), [source audit](audits/README.md).
