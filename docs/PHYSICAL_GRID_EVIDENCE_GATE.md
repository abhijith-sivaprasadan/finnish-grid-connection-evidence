# Physical Finnish transmission-network model: evidence gate (20 October 2026)

## Current assessment

**The publicly released three-zone SE1/SE3/FI PyPSA market sensitivity is NOT a physical power-flow network.** Its two time-varying Fingrid 38/39 bounds are unused post-day-ahead *commercial* intraday capacity and must **never** be repurposed as AC branch thermal limits, connection rights, or domestic Finnish transmission capacity.

The next model must be treated as a distinct research track. The *input screening module* `src/models/physical_grid_evidence_gate.py` and its tests are implemented. **No Finnish physical network has passed this gate or been simulated.** No line impedances or site MW values are manufactured.

## Evidence inventory

| Candidate data source | Supported use | Unsupported inference |
| --- | --- | --- |
| [Fingrid main-grid description](https://www.fingrid.fi/en/grid/development/power-transmission-grid-of-fingrid/) | 2025 overview of the 400/220/110 kV main-grid scope and 138 substations | Not a full validated bus-branch admittance table or site headroom |
| [Fingrid Grid Scope](https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-scope/) | Indicative geographic infrastructure and separate future connection *estimates*; independently review individual cells | Not approved connection rights, phase-angle line data, ratings, historical 2025 grid state |
| [Fingrid intraday SE1→FI 38](https://data.fingrid.fi/en/datasets/38) and [SE3→FI 39](https://data.fingrid.fi/en/datasets/39) | Historical 15-minute remaining commercial intraday market transfer possibilities after day-ahead | Not thermal branch rating, geographic load flow or grid congestion |
| [PyPSA-Eur open model](https://github.com/PyPSA/pypsa-eur/) | **Alternative** open, OSM-derived European high-voltage topology and possible proxy electrical parameters for an explicitly unvalidated sensitivity | Not a Fingrid-certified Finnish model; do not label its OSM geometries/estimates operator-verified |
| [Fingrid P1 30](https://data.fingrid.fi/en/datasets/30) | Measured operational context for Finland's internal north–south transfer; native cadence must be handled separately | Not a thermal rating for every component on P1, not a 15-minute AC branch admittance |
| [Fingrid directional P1 28/29](https://data.fingrid.fi/en/datasets/28) and [29](https://data.fingrid.fi/en/datasets/29) | Historical *planned* transfer limits with ended publication (availability to be audited) | Not a contemporary 2025 internal branch impedance/rating table |

## Acceptance sequence

1. **Licensed geospatial candidate extraction**: Obtain an explicitly versioned and licenced ≥110 kV Finnish transmission layout (Fingrid documents, or separately labelled OSM-derived PyPSA-Eur). Retain source-native IDs and retrieval date. Do not equate the historic 2020 designation list with the 2025 138-substation inventory.
2. **Topological reconciliation**: For each bus and conductor, cross-check identity, nominal kV, terminals, switching/operation status in the studied period, duplicate parallel circuits, regional load and generation mapping. Never promote coordinates alone to verified electrical connectivity.
3. **Electrical source review**: Acquire actual branch-series `r_ohm`, `x_ohm`, `b_siemens`, ratings `thermal_rating_mva`, explicit length, transformer tap and phase-shift where required. Record source URL/page and the distinction between operator-published, technical third-party and estimates. Label inferred data as proxies.
4. **Input gate**: For every proposed 2025 AC network candidate, run `python -m src.models.physical_grid_evidence_gate --candidate candidate.json`. Unknown or invalid electrical values fail; the tool returns *structural input eligibility only*. It cannot independently certify a source, topology, licence, Finnish security limits or connection approvals.
5. **Separate simulation and calibration**: With independently reviewed data, perform documented AC load-flow and DC approximation cross-checks against operator aggregate transfer measurements, generation geography, regional demand (do **not** distribute national load arbitrarily without labelled assumptions), and N−1/contingency checks. Treat HVDC converters and transformers as distinct components, not AC `Line` shortcuts. Compare source periods consistently.
6. **Publication gate**: Release first as `exploratory_proxy_network` with provenance and error/robustness results. An operator-grade or site-connectability conclusion would require independent validation and formal grid-connection studies beyond any code-level check.

## Safety invariants

- A 15-minute trading headroom of 1,000 MW is **not** a 1,000 MW electrical conductor rating.
- A bus without published electrical properties is **unknown**, not a zero-impedance link.
- Apparent Finnish model flexibility under artificial supply/slack settings is **not** observed unserved energy.
- Physical reliability requires thermal/current, voltage/reactive, N−1 and dynamic/stability constraints appropriate to the study. Passing a screening schema or solving an LP does not establish them.
- No source-derived Finnish network results or eligible project-location MW have been claimed at this stage.

This is designed to prevent erroneous physical conclusions until defensible data have been acquired.
