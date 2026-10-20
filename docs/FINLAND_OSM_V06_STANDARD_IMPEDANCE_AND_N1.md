# Finnish 2024 OSM high-voltage model: source electrical templates and structural N−1

## Scope and independent evidence

This assessment uses the **versioned September 2024 OpenStreetMap-derived** PyPSA-Eur prebuilt **v0.6** source, Zenodo https://doi.org/10.5281/zenodo.14144752 (ODbL-1.0), with original files checked against Zenodo's individual published checksums by the previous auditable original-source workflow.

- Source method: Xiong, B. et al. (2025), "Modelling the high-voltage grid using open data for Europe and beyond," Scientific Data 12:277, https://doi.org/10.1038/s41597-025-04550-7. The paper explicitly describes electrical parameters based on **standard types**.
- Technical inventory: [verified prior source-audit report](FINLAND_OSM_V06_SOURCE_AUDIT_RESULTS.md); **107** Finland-labelled buses including **104 AC**, **137 domestic 220/400-kV line records**, and **four source transformer records**. Source bounds exclude much of the Finnish 110-kV grid.
- Independent CI: source-download + checksum verification + source-template and multi-edge-safe N-1 test in the workflow file '.github/workflows/fi-proxy-topology-n1.yml'. Outputs a separate short-lived artifact with ODbL notice and individual asset IDs. For long-term reproducibility always rerun against pinned original Zenodo v0.6, not against an expired Actions archive.

## Exact source-native impedance template evidence

The audited line records contain populated finite resistance r, reactance x, and shunt susceptance b. But the numbers are not independently verified real-world line electrical measurements: once original **length (metres)** and **number of parallel circuits** are normalized, ALL the Finnish lines follow only two voltage-specific standard types, within 0.1% source-number rounding tolerance.

| Voltage | Domestic source lines | R (ohm/km per circuit) | X (ohm/km per circuit) | Shunt B (S/km per circuit) |
| --- | ---: | ---: | ---: | ---: |
| 400 kV | **114** | **0.0300** | **0.2460** | **about 4.335 × 10⁻⁶** |
| 220 kV | **23** | **0.0600** | **0.3010** | **about 3.927 × 10⁻⁶** |

These are **derived standard model parameter assignments** and not a claim that all actual Finnish conductors share those identical properties. The 400-kV rows use an identical source type and nominal current 2.58 kA; the 220-kV rows another type and nominal current 1.29 kA. Each record's source 's_nom' also agrees with 'sqrt(3) × source voltage kV × current kA × circuits' within source rounding. Thus s_nom is evidence of *internal arithmetic consistency of the source assumptions*, not operator-validated branch thermal MVA.

## Correct multigraph edge-removal research test

Source AC-only buses form four disconnected components: **79, 16, 7, 2**. Four OSM-derived transformer edges produce one connected 104-bus **proxy** graph. The audit then removes **exactly one source-record edge at a time**, preserving genuine parallel links.

Across **141 tested AC and transformer source edges**, **22 distinct single-edge removals cause proxy graph disconnection**: **20 line-source records** and **two transformer-source records**.

These are **graph bridges** under the *limited OSM-extracted topology*, not transmission-system N−1 security violations. Missing 110-kV alternative routes, omitted foreign grids, inferred connectivity and actual operating switching can change the result. Some source line records represent aggregated OSM ways, not operator-defined single circuits. A source bridge is NOT necessarily a single physical failure mode.

Automated synthetic negative tests demonstrate that (a) removing one path in a cycle does not disconnect the graph; (b) one parallel source edge does not render its counterpart a bridge; (c) dangling buses, unknown parameters, unphysical current/rating values and unsupported voltages are rejected.

## Separate licensed operator evidence / what remains unsupported

Fingrid's [2025 transmission overview](https://www.fingrid.fi/en/grid/development/power-transmission-grid-of-fingrid/) states **138 substations** and ~14,900 km of 400/220/110-kV grid combined; those 138 operator substations are not comparable with 104 OSM virtual AC buses. Fingrid's [2025 voltage-level length inventory](https://www.fingrid.fi/en/grid/development/electricity-system-of-finland/) reports about 5,400 km 400 kV, 1,000 km 220 kV and 7,600 km 110 kV, the majority of which is missing from our 220/400-kV representation.

The operator's measured [North–South P1 cut](https://data.fingrid.fi/en/datasets/30) is an **operational cross-section transfer (1-minute 2025 samples)**. It is neither the actual branch-line current nor a substitute for r, x, b, or each conductor thermal rating. Existing Fingrid 38/39 intraday trading space also has no role in physical AC ampacity. A time-consistent geography of P1 branch crossings must be independently reconstructed before one can compare its measured flows to a network simulation.

**Not performed here:** calibrated AC power flow; regional spatial distribution of actual generation or load; dated 2025 switching state; 110-kV completeness; transformer leakage reactance/tap; verified per-conductor ampacity and seasonal derating; operational N−1; short-circuit studies; voltage stability; real disturbance/blackout predictions; or site connection eligibility.

## Reproduce

    python -m pip install pytest==8.4.2
    python -m pytest -q tests/test_fi_proxy_n1_audit.py
    python -m src.models.osm_finland_topology_audit --download \
      --source-dir /tmp/fi-osm-original --output-dir /tmp/fi-osm-source-extract
    python -m src.models.fi_proxy_n1_audit \
      --extracted-dir /tmp/fi-osm-source-extract --output-dir /tmp/fi-osm-n1

The exported JSON records original-source SHA-256, the electrical template audit, all individual graph bridges and ODbL attribution. It **must not** be labelled operator-supplied equipment data or redistributed as MIT data.

## Highest-value next decision

Do not yet start a claim-bearing Finnish power-flow or site-feasibility run. Instead, select a regional corridor with identifiable operator-labelled 400/220-kV substations; reconcile the 2024 OSM source IDs, topology and chronology against licensed Fingrid maps; source actual circuit and transformer properties or retain explicitly uncertain alternatives. Only then build a *separately labelled exploratory* DC/AC simulation, record regional injection provenance, and compare modeled aggregate P1 against Fingrid 2025 measured P1. The current source check is valuable primarily because it shows exactly which apparently precise numbers are assumptions.
