# Calendar 2025 source audit and seasonal sensitivity analysis

**Study plan declared before retrieving the data.** The three 30-day windows are
winter 2025-01-15–02-14 UTC, summer 2025-06-15–07-15 UTC, and autumn
2025-09-15–10-15 UTC, all end-exclusive. They are three chosen calendar windows,
not a statistical random sample, not three full meteorological seasons.

The source audit requests **all 365 days of calendar 2025** from Fingrid Open
Data 124 (national consumption) and 74 (national production), authenticated
using the preexisting FINGRID_API_KEY repository secret. Each interval carries
its original UTC timestamps, retrieval time, and MWh/h native unit.
Strict completeness means 35,040 exact quarter-hour samples for EACH dataset,
paired to 35,040 consumption/production rows. No gap fill, invented generation,
hourly averaging, timezone ambiguity or use of unstated current grid topology.

The workflow only publishes source data after validating the entire calendar
year. It extracts three independent 30-day cases, each with 2,880 source pairs.
Each of the three cases solves the same predeclared 12 model parameter combinations
plus 3 scenario-specific no-project reference cases (45 total PyPSA LP solves).

Across-window comparison uses incremental modelled penalty slack versus the
matched no-project baseline under the **same assumed balancing limit**. For each
parameter combination we provide the three original values, minimum, median,
maximum, and descriptive range. These are not sampling confidence intervals.

**Modelling limits:** 1,000/1,500/2,000 MW assumed national balancing ceilings
are NOT actual Fingrid cross-border capacities, import rights or reserves.
Model shortfall is artificial optimization slack, NOT real Finnish power outages.
The annual audit of actual data does NOT mean the full year was optimized;
only the three predeclared windows run the sensitivity solver. The other
275 days enter observed annual coverage and energy statistics only.
Flexibility is hindsight-optimized by observed historical residual rank;
battery efficiency/rating/cyclic state are assumed.
No power-price, generator marginal costs, site-level capacity, transmission
constraints, connection feasibility, or 2030 forecast is derived.

Actions workflow `.github/workflows/pypsa-seasons.yml` is trusted-branch-only,
uses no database writer, commits or deployment credentials, and uploads a
temporary artifact with complete original source CSV, attribution/manifest,
season source slices, complete solver outputs and comparison JSON.
CI failure or unavailable source coverage must not be described as a finished
annual dataset or valid seasonal result.

To reproduce with an existing private Fingrid key:

```bash
python -m pip install -r requirements-model.txt requests==2.34.2
python -m src.models.history --start 2025-01-01 --end 2026-01-01 --out data/model_inputs/fi_2025.csv
python -m src.models.seasons --input data/model_inputs/fi_2025.csv --output-dir data/model_outputs/fi_2025_seasons
```

Source references: https://data.fingrid.fi/en/datasets/124 and
https://data.fingrid.fi/en/datasets/74. No API key belongs in files or logs.
