{
  "id": "fingrid_real_2026_10_15_to_16",
  "source": "Fingrid Open Data via the separately built Finnish Grid Atlas read-only historical operational archive",
  "source_urls": [
    "https://data.fingrid.fi/en/datasets/124",
    "https://data.fingrid.fi/en/datasets/74"
  ],
  "retrieval_api": "https://finnish-grid-atlas.vercel.app/api/v1/operations",
  "country": "FI",
  "area": "Finland national aggregate",
  "time_start_utc": "2026-10-15T00:00:00.000000Z",
  "time_end_utc": "2026-10-17T00:00:00.000000Z",
  "intervals": 192,
  "interval_minutes": 15,
  "source_native_unit": "MWh/h",
  "interpretation": "Mean power over each 15-minute interval, numerically equivalent to MW; energy=average MW×0.25 h",
  "license": "Creative Commons Attribution (Fingrid Open Data pages); attribute dataset IDs and source URLs",
  "provenance_explanation": "Each row contains its per-dataset historical retrieval timestamp. Originally collected in Neon and exposed as latest distinct revision by read-only Atlas API.",
  "limitations": [
    "Only two consecutive historical days, not a full year or representative annual seasonality",
    "Production is aggregate Finnish production, not generator-level economically dispatchable capacity",
    "Consumption is a national aggregate derived by Fingrid from production and net import/export, not a specific substation load",
    "This archive is a finite historical observation extract; not a 2030 forecast or Grid Scope connection estimate"
  ]
}
