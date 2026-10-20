# Finland OSM v0.6 — verified original-source audit (20 October 2026)

**Original independently successful Actions audit:** https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39457185877

**ODbL-1.0 licensed Finnish-only extract and full JSON:** https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39457185877/artifacts/12280153734

**Original archive artifact SHA-256:** aee86dd808ddf36462541d4c32c8f9b5026260542c107af09612fef8dcca92a5. Retention 90 days; long-term reproducibility requires the five original Zenodo v0.6 records, not this expiring artifact.

## Source authenticity, not equipment authenticity

All five PyPSA-Eur OSM v0.6 CSV originals had MD5 values independently matched to the version-specific hashes published at https://zenodo.org/records/14144752 . Independent SHA-256:

| Original | Original SHA-256 |
| --- | --- |
| buses.csv | a409bece539c38f75e1dbbf4822105759b9ab3e8f434c1aa62e10f4bfa682d64 |
| lines.csv | 034cabeafc3f06b075409d4a61a39c83d758e6bff882c2194b3779ab72754ed5 |
| transformers.csv | 527c6ce8f98cf1a197f35a979a6a247ab2451d4f06ad2ab7e7cd5c71b89e8afd |
| links.csv | 1b46f989ca26627aed198d64f134a0d4d8aa184839491347e7a5997d5f5b8a17 |
| converters.csv | bac72748cdd69cefd2f8e2a6aa1f6aee2fcdbaced6dba2975e3bd9118ca3be03 |

The data were acquired from OpenStreetMap September 2024 and published November 2024; nothing in this verification shows they depict the as-built Fingrid 2025 network.

## Reconstructed Finland-only network inventory

| Original row classification | Count |
| --- | ---: |
| Finland-labelled buses, AC and DC | **107** |
| AC buses | **104** |
| DC buses | **3** |
| Domestic nominal 400-kV AC segments | **114** |
| Domestic nominal 220-kV AC segments | **23** |
| Domestic AC segments combined | **137** |
| Domestic 220/400-kV transformer records | **4** |
| Domestic converter records | **3** |
| Cross-border AC line segments | **4** |
| Cross-border HVDC link records | **4** |

Four AC-only connected components contain **79, 16, 7 and 2** of the 104 AC buses. Including four OSM-derived transformers gives one connected graph of 104 AC buses. This is **topological consistency within a heuristic input**, not verified operating connectivity.

The source-native line-length column is **metres, not kilometres**. Domestic route length summed from this extraction: approximately **5,155.62 km at 400 kV**, **1,028.40 km at 220 kV**. Fingrid separately reports 2025 grid lengths **5,400 km 400 kV, 1,000 km 220 kV, 7,600 km 110 kV**: https://www.fingrid.fi/en/grid/development/electricity-system-of-finland/ . Similar totals do not validate endpoints, circuits, ownership or equipment; **most 110-kV grid is absent from this dataset**.

## Native electrical-parameter audit and source classes

All **137/137** domestic source AC rows contain finite numeric values for resistance (r), reactance (x), susceptance (b), nominal current (i_nom), source nominal rating (s_nom), length and circuits. **These are authentic source-file values, not independently verified physical equipment measurements.**

Only **two conductor type labels** occur in the 137 Finland source AC line records, mapping precisely to their nominal voltage:

| Source AC voltage | Lines | Source standard conductor label | Repeated nominal current | Modelled s_nom, one/two circuits |
| --- | ---: | --- | ---: | --- |
| 400 kV | 114 | Al/St 240/40 4-bundle 380.0 | 2.58 | 1,787.476 / 3,574.953 |
| 220 kV | 23 | Al/St 240/40 2-bundle 220.0 | 1.29 | 491.556 / 983.112 |

Native model current and nominal-rating numbers are **third-party templated electrical assumptions**. Every Finnish source line at the same voltage is assigned the same conductor/current template; s_nom doubles with two circuits. Before applying those values as PyPSA AC constraints, verify upstream units, circuit aggregation convention, voltage definitions, line types, and calibration. The source R/X/B are also **engineering proxies**, not line-specific Fingrid test results.

Four modelled transformer nominal values are **1,788, 3,575, 5,363, 8,938**; particularly the very high values must not be read as measured single-transformer nameplate ratings. The three source converter nominal power values are **350, 650, 1,300**, also unconfirmed equipment parameters.

These facts make a useful geographically detailed **proxy network candidate**, not an operator-grade network. No Fingrid line ratings, historic switch state, approved power-connection rights, AC security validation or location-specific headroom has been established. The ODbL-1.0 derivative database remains separately licensed from the MIT code.

## Next acceptance gate

Reconcile OSM source buses and lines with licensed 2025-specific Fingrid 110/220/400-kV maps, transformer locations, and commissioning dates; independently verify line impedance and thermal-rating evidence for an initial regional pilot; retain explicit estimate classification for each synthetic/proxy assumption. Then build a deliberately unvalidated PyPSA/pandapower pilot with AC power flow and uncertainty / N-1 checks and measured P1 transfer validation. This full workflow must not use commercial intraday market capacity as branch thermal MVA or pretend national demand belongs at one substation.
