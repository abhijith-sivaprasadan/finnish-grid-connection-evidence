# Finnish high-voltage grid: licence-qualified geospatial and electrical audit

**Research baseline: 20 October 2026.** This is an input audit, **not** a power-flow or network feasibility result.

## Selected authentic source (pre-2025 snapshot)

- Xiong, B.; Fioriti, D.; Neumann, F.; Riepin, I.; Brown, T., *Prebuilt Electricity Network for PyPSA-Eur based on OpenStreetMap Data*, Zenodo **version 0.6**, 13 November 2024: https://doi.org/10.5281/zenodo.14144752
- Original underlying data: **© OpenStreetMap contributors**, ODbL 1.0. The *processed data* are explicitly ODbL-1.0. PyPSA-Eur software's MIT licence **does not override the dataset licence**. See https://www.openstreetmap.org/copyright and https://opendatacommons.org/licenses/odbl/1-0/
- Peer-reviewed methodology: Xiong et al. (2025), *Modelling the high-voltage grid using open data for Europe and beyond*, *Scientific Data* 12:277, https://doi.org/10.1038/s41597-025-04550-7
- **Why version 0.6?** Data obtained September 2024 precede the 2025 historical operations series. Newer v0.7 uses an OSM snapshot from February 2026 and cannot directly establish the 2025 network state; it can be independently studied as a *later snapshot*, not silently substituted.
- This source covers European high voltage **220–750 kV**, including Finland; it **does not provide systematic Finnish 110 kV topology**. The 500 m substation aggregation and heuristic reconstruction prevent claiming actual switch-level topology.

## Independent, executable audit

Run the following in an environment with public access to Zenodo:

    python -m pip install pytest==8.4.2
    python -m pytest -q tests/test_osm_finland_topology_audit.py
    python -m src.models.osm_finland_topology_audit --source-dir /tmp/zenodo-osm-v06 --output-dir /tmp/finland-network-v06 --download

The script verifies published **MD5** for each of five versioned source files and records independent SHA-256, then extracts **Finland-labelled original buses** and distinguishes domestic AC lines from cross-country boundary segments. Original source IDs, source headers and coordinates are retained. AC lines, DC links, converters and transformers remain **separate**. Construction flags are inventoried, not assumed operating; all output files carry an ODbL attribution notice. The archive is a GitHub Actions artifact (90 days), not a disguised GitHub-code MIT data release.

For every Finnish domestic AC line, report whether original r, x, b, current/ratings, length and circuit-count fields exist and are valid. These **source-derived numerical estimates are NOT individual Fingrid operator-certified equipment parameters**, even if the CSV field is populated. No missing values are filled, no thermal ratings are manufactured, and commercial cross-border flows/capacities are never used as AC line MVA ratings. If fields are absent or corrupted, the audit reports them as absent or invalid.

## Engineering readiness and evidence gaps

| Item | Evidence class | Allowed use | Still missing |
| --- | --- | --- | --- |
| 2024 OSM 220/400 kV buses/lines | third-party geospatial proxy | Candidate spatial connectivity | Fingrid 2025 operational topology and switch status |
| Source r/x/b | third-party parameter estimates | Exploratory sensitivity only, after unit audit | Equipment datasheets, calibration, parallel circuits |
| Circuit count/current/rating | proxy, NOT Fingrid thermal rating | Field audit only | Verified ampacity, ratings, seasonal derates |
| Transformer rows | third-party topology | Separate equipment inventory | Impedance, winding limits, taps |
| HVDC links/converters | third-party topology | Separate inventory | Converters, loss, terminal limits |
| Fingrid 2025 138 substation aggregate | operator-published aggregate | External scope comparison | 2025 specific IDs, geometry and 110 kV |
| Fingrid P1 and border-market datasets | measured transmission cut / commercial capacity | Separate operating-context verification | Cannot identify AC branch rating |

**Publication gate:** No extracted asset qualifies for approved network access or project-level deliverability. Before physical PyPSA/pandapower simulation as anything beyond exploratory proxy research, resolve units, asset status, merged circuits, transformer characteristics, temporal consistency and regional generation/load mapping. Independently compare P1 operational measurements with appropriate temporal definitions; then validate AC power flow, line limits, N-1 and robustness with explicit uncertainty. The existing physical_grid_evidence_gate.py is only a **structural** check.

**ODbL publishing:** When redistributing adapted network database tables, credit OpenStreetMap and upstream authors and make the derivative database available under ODbL-1.0. Code licensing is separate; do not relabel extracted OSM CSV data as MIT.
