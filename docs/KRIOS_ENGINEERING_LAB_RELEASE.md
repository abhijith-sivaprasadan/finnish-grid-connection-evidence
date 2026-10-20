# Krios power-system engineering lab — solver-verified release (20 Oct 2026)

**Scope:** portfolio add-on beyond the completed source-traceable Finland MVP. **No real Finnish or Dutch grid connection capacity is estimated or approved.** See [interactive engineering lab](https://finnish-grid-atlas.vercel.app/engineering) and [interactive 2024 OSM map](https://finnish-grid-atlas.vercel.app/network-map) *after verifying production has deployed this release*.

## Reproducible solver evidence

[Successful solver workflow #39493594189](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39493594189) independently solved the three source-qualified scientific layers. The artifact archives' SHA-256 are retained in [published engineering summary](../website/src/lib/krios-engineering-verified-2026.json), making the website's numerical figures auditable rather than hypothetical illustrations.

### 1. CIGRE HV 13-bus pandapower AC / line and transformer N−1

The 3.5.6 CIGRE HV model includes 13 buses, 9 lines, 6 transformers and its original 1,474-MW reference load. Additional demand **0/50/100 MW** is injected as a new load at the model's last >=110-kV bus, with explicitly **0.95 lagging power factor**. This placement is a **synthetic scenario**; the CIGRE bus is not mapped to any real customer or Finnish station.

| Added MW | Min bus voltage pu | Peak line loading | Peak trafo loading | Modeled losses MW | N−1 nonconvergent / 15 | Convergent with illustrative threshold issue / 15 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.951046 | 78.35% | 68.07% | 53.366 | 10 | 3 |
| 50 | 0.937290 | 79.97% | 69.47% | 62.016 | 10 | 4 |
| 100 | 0.912236 | 82.05% | 71.29% | 72.629 | 10 | 4 |

The N−1 audit individually removes each original line and transformer. Non-convergence (which can include islanding and solver issues) is **not counted as compliance**. A violation here means a **solved** case exceeded either an illustrative 0.9–1.1 pu comparison band or modeled 100% nameplate loading; it is **not a verified grid-code or regulatory threshold**. Only actual original reference network solver results are displayed.

### 2. CIGRE MV 15-bus pandapower extension

Original high-/medium-voltage boundary preserved; 15 lines and two transformers with CIGRE PV/wind test feeder. Added project loads **0/0.5/1/2 MW**, never an unrealistic 100-MW MV data-centre feeder. All four nominal AC runs solved. Reference losses: 0.16435 MW; at +2 MW: 0.24746 MW. Minimum source bus voltage ~0.946916 pu, max modeled transformer loading 93.889% at +2 MW. **This is neither a Dutch TenneT network nor Netherlands DSO approval.** The real Dutch pilot separately provides source-verified congestion metadata, not feeder electrical measurements.

### 3. Independent pandapower vs PyPSA full AC verification

We created **one explicitly synthetic 110-kV 3-bus 3-line reference** with identical named buses, line R/X, fixed PQ loads, zero shunt susceptance and explicit slack reference. Independently solved **nonlinear AC PF**, not PyPSA DC/linear OPF, in different versions and pandas environments. A dependency-free validator compares buses and from-end branch MW; **maximum differences round to 0.0 pu and 0.0 MW** at published report precision, below predeclared 0.025-pu and 1.5-MW bounds.

**Not done:** comprehensive CIGRE HV transformer taps, shunts and reactive-control parity. Do not describe the three-bus result as full CIGRE cross-validation.

### 4. Source-anchored Finnish PyPSA regional v2

Verified **192 original 15-min Fingrid 124/74 observations**, Oct 15–16 2026, original source CSV SHA-256 `ab0316e695bbea34cc16b498ade06746bcc5087485f2f6cfde4b6630341109e6`. Regional northern source shares are invented: 65% observed national production and 45% national consumption. The internal regional corridor 1,500 MVA nominal and 750 MVA derating are **hypothetical** model parameters; regional balancing generators are also fictional.

Four PyPSA/HiGHS optimum cases: reference, flat +100 MW, energy-equivalent flexible +100 MW, flat +100 MW with synthetic corridor derated to 750 MVA. Number of quarter-hours modelled at or near the **assumed** corridor ceiling: **149/156/153/187**, respectively. The model has **zero mathematical shortfall relaxation in all four cases**, entirely because its hypothetical balancing supply is sufficient—not proof of Finnish supply reliability. No claims about actual P1 flows, R/X of a particular line, 2025 grid topology or site connectable MW are allowed.

### 5. 2024 licensed OSM proxy sensitivity — why actual calibration is blocked

Re-read the **original version-pinned OSM/PyPSA-Eur v0.6** 2024 source CSVs from DOI https://doi.org/10.5281/zenodo.14144752; verify all five original checksums and retain ODbL-1.0 attribution. Source model contains **104 AC buses and 137 internal 220/400-kV AC records** (plus other candidate elements). 22 individual source edge removals disconnect this *partial source graph*, not the actual Finnish grid.

Scaling original **model-assigned nameplate** limits to 75%, 100%, 125% changes the count of nominal source records with assumed rating under 1,500 MVA from **121 to 23 to 23**. This is a sensitivity of *third-party templates*, **not observed loading, real congestion, conditional connection approval, or quantified uncertainty distribution**.

Actual Finnish electrical calibration, operator-style contingency analysis, and output verification against P1 or local bus measurements remain **blocked** until there is operator-identifiable line/transformer equipment data, at least 110/220/400 kV source boundary coverage, year-matched switching/commissioning, spatial demand/generation, measured P1 and independently sourced operational line ratings. No real physical branch-constrained Finnish grid model has been certified or calibrated.

### 6. Interactive geographic proxy visualization

Website `/network-map` shows **107 2024 source virtual bus positions**, 104 AC and 3 DC, and **137 source domestic AC links**, with 220/400-kV AC filter, select node and zoom controls. Positions are **rounded to 0.001°** and joined by original source graph endpoints rather than physical route geometries; this is a simplified diagram, not actual operator switchgear location.

**Source ODbL attribution, share-alike:** © OpenStreetMap contributors and Xiong et al., PyPSA-Eur OSM v0.6 (Zenodo DOI above). The source static arrays in `website/src/lib/osm-2024-proxy-map-odbl.ts` are an ODbL-derived adaptation. This does **not** match the five named Fingrid Grid Scope evidence points to proxy bus coordinates; do not create that crosswalk without source confirmation.

## Crucial version separation

The latest available pandapower 3.5.6 pins pandas **2.3**, whereas PyPSA 1.4.0 requires pandas **3.0+**. Forcing both into one environment fails dependency resolution. CI deliberately runs **two separate pinned solver Python environments** and compares the exported JSON in a third dependency-free job, with independently verified artifact SHA-256.

To run locally:

```bash
# Pandapower v3.5.6 and pandas 2.3
python -m venv .venv-pp
.venv-pp/bin/python -m pip install -r requirements-pandapower-lab.txt
.venv-pp/bin/python -m pytest -q tests/test_pandapower_lab.py
.venv-pp/bin/python -m src.models.cigre_engineering_lab --out /tmp/krios-pp/cigre_ac_n1.json
.venv-pp/bin/python -m src.models.ac_cross_solver_reference --solver pandapower --out /tmp/krios-pp/reference.json

# Separate existing PyPSA v1.4 pandas 3 environment
python -m venv .venv-psa
.venv-psa/bin/python -m pip install -r requirements-model.txt
.venv-psa/bin/python -m pytest -q tests/test_pypsa_regional_v2.py
.venv-psa/bin/python -m src.models.fi_regional_pypsa_v2 --out /tmp/krios-psa/regional.json
.venv-psa/bin/python -m src.models.ac_cross_solver_reference --solver pypsa --out /tmp/krios-psa/reference.json

# Compare same reference on stdlib only
python -m src.models.ac_comparison_validate --pandapower /tmp/krios-pp/reference.json --pypsa /tmp/krios-psa/reference.json --out /tmp/krios-parity.json
```

The OSM stage is independently reproducible with the original source auditor `src.models.osm_finland_topology_audit --download` and `src.models.fi_osm_uncertainty_2024 --extracted-dir ... --out ...`; see [original geo/rights audit](FINLAND_OSM_V06_STANDARD_IMPEDANCE_AND_N1.md).

**Krios interpretation:** This laboratory demonstrates nonlinear AC analysis, contingencies, reactive-demand sensitivity, solver verification, historical source provenance and uncertainty-aware modelling. It must not replace the original operator-owned site-connection feasibility workflow.
