# Finland 100 MW Historical Demand Impact — reproducible PyPSA case study

**Status**: PyPSA 1.4.0 with HiGHS optimal solutions, published only after a successful solver job and source-hash check. **Not** a Finnish grid/network reconstruction or a 2030 forecast.

## Real observed input, dated scope

- Data: Fingrid Open Data [electricity consumption, dataset 124](https://data.fingrid.fi/en/datasets/124) and [electricity production, dataset 74](https://data.fingrid.fi/en/datasets/74). Creative Commons Attribution. Fingrid describes consumption as national production plus imports minus exports, not direct metering of a substation.
- Input CSV: `data/model_inputs/fingrid_20261015_20261016_15min.csv`, with **192 consecutive 15-minute paired values**, 15 and 16 October 2026 UTC. Downloaded from Atlas's existing read-only, historically persisted Fingrid observations; original source dataset IDs and retrieval timestamps preserved.
- Native units: `MWh/h` means mean power per hour; numerically equivalent to interval-average MW. Integrate energy as quarter-hour mean × **0.25 h**. All source timestamps are UTC and checked for gaps and duplicates.
- This is a **48-hour historical window**. It is not a year, a future demand forecast, nor a seasonal representation of Finland's network.

## Model schematic and evidence classification

- **Single national bus**, no Finnish line/transformer impedances, voltage constraints, outage schedules or congestion boundaries.
- Fixed aggregate historical observed production generator, paired with observed aggregate national electricity consumption load.
- Modelled balancing supply, capped at an arbitrary **1,500 MW** solely to illustrate the effect of a stressed supply assumption. It is NOT observed interconnector capacity, actual available imports, or Fingrid connection headroom.
- A fictitious surplus sink and a very-high-penalty generator for the model's **unserved relaxation** make all scenarios solvable. Surplus sink does not imply real exports or curtailment. Model unserved energy is NOT a measured power outage.
- Optimise balancing and storage using a **dimensionless synthetic stress-cost index**, not real Nordic power prices or euros. No financial savings are claimed.
- Snapshot weights 0.25 h, explicit energy-balance verification at every time step and nonnegative source data verification. No economic dispatch of source production: production is a fixed historical measurement.

## Four fully solved scenarios

| Scenario | Added load energy in 48h | Behaviour |
| --- | ---: | --- |
| observed_reference | 0 MWh | Fit observed aggregate series through assumed balancing resources; not a calibrated market replay |
| flat_100mw | 4,800 MWh | Constant +100 MW every 15 minutes |
| flexible_100mw | 4,800 MWh | Hypothetical 150 MW for lower-residual half of EACH day and 50 MW otherwise; equal daily energy (2,400 MWh) |
| flat_100mw_with_battery | 4,800 MWh | +100 MW flat; fictional 100 MW, 400 MWh battery, 90% round-trip efficiency and cyclic state-of-charge |

Outputs contain solver status, modelled balancing support, shortage slack under the **assumed 1,500 MW cap**, surplus sink, storage throughput, 15-minute residual checks and original source/assumption provenance.

**Modelled shortfall under an invented capacity ceiling must not be presented as actual electricity unserved in Finland.** Any difference across cases is a mathematical sensitivity to the assumptions and historical input, not grid-connection feasibility at a particular location.

## Reproduce

PyPSA 1.4.0 requires pandas 3, whereas the existing app pins pandas 2.3.3. Use a **dedicated modelling environment** and do not modify the running Neon ingestion environment:

```bash
python -m venv .venv-model
source .venv-model/bin/activate  # Windows: .venv-model\\Scripts\\activate
python -m pip install -r requirements-model.txt
python -m pytest -q tests/test_finland_model.py
python -m src.models.finland --output data/model_outputs/finland_pypsa_20261015_16.json
python -m src.models.verify_publication --solved data/model_outputs/finland_pypsa_20261015_16.json
```

The full output file includes all four × 192 optimized 15-minute results. Generated model files are not needed in the main dashboard database. The published website embeds a small **solver-verified summary** with the source SHA-256; the live source CSV and model code remain reviewable.

GitHub Actions workflow `.github/workflows/pypsa-study.yml` installs the isolated modelling dependencies, reruns the four optimizations, checks the site publication against the fresh optimizer output AND proves the website’s observed chart is an exact projection of the original timestamped CSV, and uploads complete scenario results as a downloadable artifact. Reproducibility is enforced, not merely claimed.

Site: `/analysis`, data API `/api/v1/model/finland`. No database/schema mutation or write credential is required.

## Later improvements

1. Collect broader seasonal/year-long real histories and assess duration / publication issues before claiming representativeness.
2. Independently source actual transmission interconnector statistics, capacities and time-varying prices; distinguish dispatchable generation potential from measured past production.
3. Run explicit parametric sensitivities over **assumed** balancing-support limits (e.g. 1,000–3,000 MW), flexibility factors and battery ratings, reporting robustness.
4. Introduce a separately sourced and licensed topology to study geographic transmission effects, with validation. Do not map one-bus output onto historical 128 substation labels or use as a Grid Scope capacity number.

Reference implementation issue: source-directed Finnish Grid Atlas workstream, following evidence-qualified screening #35.
