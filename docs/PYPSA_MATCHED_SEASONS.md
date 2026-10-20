# Matched observed-window seasonal PyPSA design

Autumn 2025, 15 Sep–15 Oct (exclusive end) had an independently complete
30-day paired Fingrid source. A wider strict 365-day audit failed in the
first January week at Fingrid 124 670/672 observations; subsequent independent
30-day winter and summer checks also identified 670/672 and 671/672
in one of their seven-day source chunks. Those missing original intervals
are NOT filled, interpolated, shifted or silently discarded from source audits.

New audit: `src.models.observed_windows` retrieves exactly three predeclared
30-day windows: Jan 15–Feb 14, Jun 15–Jul 15, Sep 15–Oct 15, 2025.
Each dataset's true quarter-hour UTC timestamps and source values are
retained. The program inventories missing timestamps for every UTC date
in the original 30-day window and identifies maximal runs of dates with
all 96 paired source intervals present.

For fair comparison it chooses a common **equal number of consecutive
source-complete UTC days**, using the earliest portion of the longest
complete-day run in each season (min 3, capped at 30). This changes the
study's effective sample length. It is NOT an assertion that an entire
30-day season is complete. The exact selected dates, coverage exclusions
and source hashes are part of the model output.

Each genuine selected-window dataset is then modeled using PyPSA/HiGHS
with 12 identical assumed national balancing, load-flexibility and
battery parameter combinations and 3 matched no-project references.
An optimized model shortfall means penalty slack under invented
1,000–2,000 MW support limits, NOT actual Finnish outages,
import rights, or physical substation capacity.

This is an exploratory **missingness-conditioned sample** and may have
selection bias; the min/median/max across three preselected calendar
windows are descriptive sensitivity, NOT statistical confidence intervals.
Three sampled windows also do NOT amount to a validated annual dispatch
study, seasonal climatology or 2030 forecast.

Workflow `.github/workflows/pypsa-matched-windows.yml` is read-only and
authenticates with existing private Fingrid source key. It produces the
full source-coverage report and complete real interval/model artifacts
without updating production or Neon.
