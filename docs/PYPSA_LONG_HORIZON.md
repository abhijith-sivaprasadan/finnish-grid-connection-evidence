# Long historical PyPSA sensitivity — source and assumptions

Initial study target: 15 September – 15 October 2025 UTC (30 complete days).
Fingrid consumption dataset 124 and production dataset 74 are retrieved
through the authenticated API using the existing FINGRID_API_KEY secret.
Source 15-minute MWh/h samples are compared by timestamp. All missing,
duplicate or misaligned observations cause failure; no interpolation or
synthetic source values are allowed. 30 days requires 2,880 paired samples.

The model varies invented balancing support ceilings of 1000/1500/2000 MW;
hypothetical flexibility half-spans 0/50 MW around a 100 MW mean new load;
and battery power 0/100 MW (4 hours, 90% round-trip efficiency).
That is 12 parameter combinations plus three separate reference solves.

Model shortfall means high-penalty slack under an assumed balancing ceiling.
It does not imply Finnish electricity outages, actual import limits,
connection rights, technical site feasibility, or a forecast for 2030.

Run locally with private FINGRID_API_KEY in environment:

```bash
python -m pip install -r requirements-model.txt requests==2.34.2
python -m src.models.history --start 2025-09-15 --end 2025-10-15 --out data/model_inputs/finland_30day.csv
python -m src.models.sweep --input data/model_inputs/finland_30day.csv --output data/model_outputs/finland_30day_sweep.json --limits 1000,1500,2000 --flex-spans 0,50 --battery-powers 0,100
```

The GitHub Actions workflow on this trusted repository branch is read-only,
uses the API key without printing or storing it, and uploads the source CSV,
SHA-256 manifest, and a solver-verified sensitivity report as an artifact.
The production website remains on the independently verified two-day study
until longer real observations and output provenance have been reviewed.

Fingrid sources:
https://data.fingrid.fi/en/datasets/124
https://data.fingrid.fi/en/datasets/74
https://data.fingrid.fi/en/instructions

## Completed authenticated study and published research preview

2026-10-20 GitHub Actions workflow run [39391985966](https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39391985966) retrieved **2,880 consecutive paired operator observations** (30 complete UTC days), passed source coverage and checksum checks, and solved **12 full-factorial PyPSA/HiGHS scenarios plus 3 reference cases**, all optimal with verified 15-minute energy balance. The source checksum is `3093f704484848919d83feb6c133c2e2abf2299566d5bd02a109e01b7fdec2e0`.

The workflow stores the full source CSV, manifest, and solver output as the temporary artifact `verified-fingrid-long-horizon-pypsa` (GitHub artifact ID `12249992474`). Re-execution with private API credentials can reproduce the retrieval, though revision timestamps may differ across collections. The site embeds only the **verified provenance-linked summary** and renders scenario sensitivity as a mathematically qualified model output. It does not publish the 30-day model as current actual grid or connection headroom.

The 30-day experiment covers September–October 2025 only; neither seasonal representativeness nor 2030 relevance has been demonstrated. Follow-on work should add verified winter and summer windows and true year-long coverage before annualizing results.
