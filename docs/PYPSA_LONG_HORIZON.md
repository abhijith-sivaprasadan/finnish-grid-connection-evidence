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
