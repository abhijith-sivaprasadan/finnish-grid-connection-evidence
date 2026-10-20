# Finnish 2024 versus February 2025 high-voltage route concordance — preliminary evidence

**Status:** GEOGRAPHIC OVERLAY ONLY. Not an operator-validated as-built Finnish transmission model.

## Two separate datasets, with different levels of authority

1. **2024:** Xiong et al., PyPSA-Eur OSM prebuilt v0.6, from OpenStreetMap geometry acquired September 2024. Original source https://doi.org/10.5281/zenodo.14144752; reusable under **ODbL 1.0** with conditions. The existing importer pins and independently verifies each original Zenodo MD5, preserves SHA-256 and Finnish source-native line records.
2. **22 February 2025 copy:** [Suomen sähköverkko, ArcGIS feature item c24608cc5f5943469d04821c77954e95](https://www.arcgis.com/home/item.html?id=c24608cc5f5943469d04821c77954e95), owned/hosted by **henri.korhonen_fcg (FCG)**, uploaded March 3, 2025; description says its source is a Fingrid map (karttapalaute.fingrid.fi). Its line layer is a public vector-polyline layer with 110/220/400/500-kV voltage classifications, but **NO documented licence grant** (the ArcGIS item's licenseInfo field is empty). Neither the map attribution nor open read access demonstrates certified Fingrid topology, verified ownership rights or permission to redistribute geometry.

The hosted 2025 copy has only FID, the voltage-category field Tyyppi, line-length and generic shape fields. **No verified named substation IDs, physical line equipment IDs, R/X/B, thermal ratings, switching timestamps or commissioning evidence are supplied** in this layer.

For this reason, the new workflow accesses its 400/220-kV geometry only *transiently* in a GitHub Actions worker and discards it. It exports only aggregate cross-dataset proximity statistics and high-level provenance warnings. It does **not** commit or upload 2025 third-party feature geometry, source feature IDs, individual cross-provider joins, or a redistributed dataset.

## Reproducible comparison

At each voltage separately:
- Take each 2024 OSM line record, retaining its original trace in memory.
- Transform both sources from WGS84 to **EPSG:3067** (Finland's metric projection). This avoids pretending geographic coordinate degrees are metric distances.
- Sample OSM route midpoints at approximately **2-km intervals**, selecting a nearest same-voltage hosted polyline for each sample. No endpoint-name or branch-rating matches are claimed.
- Count midpoint distances <=250 m, <=1,000 m and <=5,000 m; summarize medians and original OSM routes with >=80% of samples within the stated threshold.
- Fail on absent original-source licence/provenance, unexpected layer owner or capture date, incomplete pagination, duplicate FCG feature IDs, nonpositive-length geometry or unsupported source voltages.

**Independent success:** [GitHub Actions run #39463599318](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39463599318); same source-proximate numerical findings reproduced in [run #39463500842](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39463500842) after correcting an overly strict short-polyline exclusion. The workflow uses five intentionally artificial synthetic test cases and source checksum verification.

### Measured comparative summary

| Comparison | 220 kV | 400 kV |
| --- | ---: | ---: |
| OSM 2024 model source lines | **23** | **114** |
| Hosted Feb 2025 mirror GIS polyline records | **59** | **409** |
| OSM midpoint samples (about every 2 km) | **525** | **2,632** |
| Midpoint share within 250 m | **99.619%** | **98.024%** |
| Midpoint share within 1 km | **100.000%** | **98.062%** |
| Midpoint share within 5 km | **100.000%** | **98.328%** |
| Median nearest SAME-voltage polyline distance | **1.1 m** | **1.4 m** |
| OSM routes with >=80% sampled points within 1 km | **23 of 23** | **112 of 114** |

Values were produced by the independent GitHub runner, not inferred from published descriptions. Native source line records and mirror polyline features are **different segmentation units**, so 137 versus 468 must not be interpreted as numbers of actual physical power circuits, power lines, or official Fingrid stations.

### Interpretation: very high proximity can be misleading

The very low median (roughly **1 m**) does NOT mean two fully independent electrical-network sources confirm each other. The two datasets may include **shared upstream digitization, cartographic alignment, or processing lineage**. The hosted layer itself explicitly attributes its source to Fingrid's public map, but this does not establish detailed field validity or the creation/provenance chain.

High positional concordance confirms mainly that the 2024 OSM reconstructed 220/400-kV paths occupy broadly the same mapped route locations in this February 2025 cartographic snapshot. It **cannot** verify which individual conductors exist, the number of physically separate circuits, circuit thermal ampacity, transformer capacity, switch state or substation topology. The two 400-kV source routes with low >=80% threshold coverage are **unresolved**, not evidence of removal, construction, operator mistakes or real outages.

The Feb-2025 snapshot also PRE-DATES both the Q3 2025 commissioning of Huittinen–Forssa 400+110 kV and the November 2025 Aurora Line 400-kV FI–SE1 commissioning. It cannot validate whether those projects are correctly represented after their in-service dates. See the [dated Fingrid operator chronology](../data/reference/fi_2025_operator_asset_chronology.json) and [previous source topology audit](FINLAND_OSM_V06_STANDARD_IMPEDANCE_AND_N1.md).

## What is and is not achieved

**Done:**
- Source-authenticated 2024 ODbL Finnish 220/400 kV geometry;
- a real February 2025 geospatial reference from a separately hosted third-party map copy;
- a reproducible, voltage-aware source-map concordance metric over **3,157 source midpoints**;
- strict raw-geometry non-redistribution, plus a repeatable cryptographic fingerprint of the mutable hosted source, while comparison-layer rights remain unresolved.

**Still unresolved / explicit stop conditions:**
- permission to redistribute the hosted FCG geometry (none granted by the visible ArcGIS item);
- per-line FCG/Fingrid provenance, geometry lineage independence and authoritative Fingrid asset IDs;
- exact 2025 dated commissioned topology and source-to-operator geographic matching;
- major omitted Finnish 110 kV branches and transformer specificity;
- physical line ratings, impedances, dynamic operating states and AC/N-1 validation.

The current Python physical-grid evidence gate must **NOT** be marked as having verified an operator-grade Finnish network based on this proximity result. No power-flow or grid-connection MW estimate is provided.

## Reproduce without distributing unlicensed hosted data

Execute on a machine with access to the public Zenodo and ArcGIS endpoints:

    python -m pip install pytest==8.4.2 shapely==2.1.2 pyproj==3.7.2
    python -m pytest -q tests/test_fi_spatial_concordance_2025.py
    python -m src.models.osm_finland_topology_audit --download \
      --source-dir /tmp/osm-v06-native --output-dir /tmp/osm-fi-source
    python -m src.models.fi_spatial_concordance_2025 \
      --osm-dir /tmp/osm-fi-source \
      --out /tmp/osm-fi-aggregated/AGGREGATED_COUNTS_ONLY.json

Do not commit the source FCG response, query-result geometry or source-ID joins. The output contains aggregates and rights/status metadata only, without raw coordinates, IDs, or source-side private/redistribution-unapproved contents. Live upstream GIS updates can change the results; the workflow records the item ID, owner and public collection date and creates a non-reversible SHA-256 fingerprint of the actually served 220/400-kV features in memory. On subsequent runs, that fingerprint detects changes in the hosted copy; it **cannot prove** that the mutable third-party copy faithfully reproduces Fingrid's exact 22 February 2025 original or establish redistribution rights.

**Next grounded asset-identity milestone:** Obtain an explicit Fingrid-licensed authoritative time-stamped map or branch list, or rights clearance and technical lineage for the GIS copy; manually match a *limited named 400-kV corridor* against original OSM IDs and equipment ratings with independent operator documents. Without those inputs, geographic map proximity alone cannot promote any branch to operator-verified status.
