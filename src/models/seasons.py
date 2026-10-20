"""Full-year historical coverage audit and three same-length seasonal PyPSA studies.

Only original Fingrid 124/74 15-minute observations are admitted. The annual
coverage report is OBSERVATIONAL; PyPSA results are separately MODEL_SCENARIO.
No interpolation, gap filling, hidden yearly annualization or local grid claims.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.models.finland import load_observed
from src.models.sweep import run_sweep

YEAR = 2025
SEASON_WINDOWS = {
    "winter": ("2025-01-15", "2025-02-14"),
    "summer": ("2025-06-15", "2025-07-15"),
    "autumn": ("2025-09-15", "2025-10-15"),
}
EXPECTED_DAYS = 365
EXPECTED_INTERVALS = EXPECTED_DAYS * 96
HOURS_PER_INTERVAL = 0.25


def coverage_report(input_path: Path) -> tuple[dict, pd.DataFrame]:
    """Reject annual data unless every UTC quarter hour and provenance validates."""
    observed = load_observed(input_path)
    if len(observed) != EXPECTED_INTERVALS:
        raise ValueError("Full 2025 validation requires exactly 365 complete UTC days")
    if observed["timestamp_utc"].iloc[0] != "2025-01-01T00:00:00.000000Z" or observed["interval_end_utc"].iloc[-1] != "2026-01-01T00:00:00.000000Z":
        raise ValueError("Annual input must be exactly calendar year 2025 UTC")
    residual = observed["consumption_mwh_per_hour"] - observed["production_mwh_per_hour"]
    stats = {
        "status": "complete_source_observations",
        "classification": "observed_fingrid_national_operational_context",
        "calendar_year": YEAR,
        "source_days": EXPECTED_DAYS,
        "quarter_hour_pairs": len(observed),
        "expected_quarter_hour_pairs": EXPECTED_INTERVALS,
        "source_window_utc": {"start": observed["timestamp_utc"].iloc[0], "end": observed["interval_end_utc"].iloc[-1]},
        "source_datasets": [{"dataset_id": 124, "metric": "national_consumption", "native_unit": "MWh/h"},
                            {"dataset_id": 74, "metric": "national_production", "native_unit": "MWh/h"}],
        "source_urls": ["https://data.fingrid.fi/en/datasets/124", "https://data.fingrid.fi/en/datasets/74"],
        "source_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "national_consumption_gwh_observed": round(float(observed["consumption_mwh_per_hour"].sum() * HOURS_PER_INTERVAL / 1000), 3),
        "national_production_gwh_observed": round(float(observed["production_mwh_per_hour"].sum() * HOURS_PER_INTERVAL / 1000), 3),
        "aggregate_residual_mw_quantiles": {str(q): round(float(residual.quantile(q)), 3)
                                          for q in (0.01, 0.1, 0.5, 0.9, 0.99)},
        "aggregate_residual_min_mw": round(float(residual.min()), 3),
        "aggregate_residual_max_mw": round(float(residual.max()), 3),
        "limitations": [
            "Complete UTC source observations are not a validated Finnish transmission model.",
            "Aggregate national consumption minus production is a historical arithmetic residual, not verified spare cross-border capacity or import rights.",
            "Observed energy and residual summary are historical measurements, never future forecasts or operator-confirmed site connection capacity.",
            "Seasonal PyPSA studies are separate hypothetical model assumptions and not observed Finnish electricity outages."
        ],
    }
    return stats, observed


def select_window(observed: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    # ISO date strings are fixed/validated against the actual annual index.
    low = pd.Timestamp(start)
    high = pd.Timestamp(end)
    if high <= low:
        raise ValueError("Season window must have positive duration")
    frame = observed[(observed.index >= low) & (observed.index < high)].copy()
    expect = int((high - low) / pd.Timedelta(minutes=15))
    if len(frame) != expect or frame.index[0] != low or frame.index[-1] + pd.Timedelta(minutes=15) != high:
        raise ValueError("Selected season is incomplete; no interpolation permitted")
    return frame


def write_window(frame: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["timestamp_utc","interval_end_utc","consumption_mwh_per_hour",
            "production_mwh_per_hour","consumption_retrieved_at","production_retrieved_at"]
    frame[cols].to_csv(path, index=False, lineterminator="\n")
    assert len(load_observed(path)) == len(frame)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def perform(input_path: Path, output_dir: Path, *, solver: bool = True) -> dict:
    """Coverage is committed before optional solver; no synth source replacements."""
    coverage, history = coverage_report(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/"annual_2025_coverage.json").write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")
    seasonals = []
    for season, (start, end) in SEASON_WINDOWS.items():
        frame = select_window(history, start, end)
        assert len(frame) == 30 * 96
        source = output_dir / f"fingrid_{season}_2025_15min.csv"
        digest = write_window(frame, source)
        row = {
            "season": season,
            "source_start_utc": start+"T00:00:00.000000Z",
            "source_end_utc": end+"T00:00:00.000000Z",
            "complete_days": 30,
            "source_intervals": len(frame),
            "source_sha256": digest,
            "national_consumption_gwh_observed": round(float(frame["consumption_mwh_per_hour"].sum() * HOURS_PER_INTERVAL / 1000), 3),
            "national_production_gwh_observed": round(float(frame["production_mwh_per_hour"].sum() * HOURS_PER_INTERVAL / 1000), 3),
        }
        if solver:
            solved_path = output_dir / f"pypsa_{season}_2025_sweep.json"
            solved = run_sweep(source, output=solved_path)
            if solved["observed_input_sha256"] != digest or len(solved["results"]) != 12:
                raise AssertionError("Seasonal solver/source digest or scenario count mismatch")
            if any(x["solver_status"] != "ok" or x["solver_termination"] != "optimal" or
                   x["max_balance_error_mw"] > 1e-5 or x["added_load_energy_mwh"] != 72000
                   for x in solved["results"]):
                raise AssertionError("A seasonal result failed mathematical validation")
            row["model_output_sha256"] = hashlib.sha256(solved_path.read_bytes()).hexdigest()
            row["modelled_results"] = solved["results"]
            row["model_reference"] = solved["baselines"]
        seasonals.append(row)
    compare = []
    if solver:
        for limit in (1000.0,1500.0,2000.0):
            for flex in (0.0,50.0):
                for battery in (0.0,100.0):
                    matches = [next(x for x in s["modelled_results"] if
                        x["balancing_limit_mw_assumed"] == limit and
                        x["flex_half_range_mw_assumed"] == flex and
                        x["battery_power_mw_assumed"] == battery)
                        for s in seasonals]
                    vals = [x["incremental_shortfall_vs_reference_mwh"] for x in matches]
                    compare.append({
                        "balancing_limit_mw_assumed":limit,
                        "flex_half_range_mw_assumed":flex,
                        "battery_power_mw_assumed":battery,
                        "incremental_model_shortfall_mwh_by_season":dict(zip(SEASON_WINDOWS, vals)),
                        "range_mwh_across_three_selected_seasons":round(max(vals)-min(vals),4),
                        "median_mwh_across_three_selected_seasons":round(float(np.median(vals)),4),
                        "min_mwh_across_three_selected_seasons":round(min(vals),4),
                        "max_mwh_across_three_selected_seasons":round(max(vals),4),
                    })
    result = {
        "publication_status":"source_and_solver_verified" if solver else "source_coverage_only",
        "historical_data_kind":"observed_fingrid_national_operational_context",
        "model_data_kind":"model_scenario" if solver else None,
        "annual_observations":coverage,
        "season_window_policy":"Three predeclared equal 30-day calendar windows, no ex-post cherry-picking or annualization",
        "seasonal_studies":seasonals,
        "across_season_parameter_comparison":compare,
        "model_assumptions":{
            "project_mean_load_mw":100,
            "balancing_support_limit_mw":[1000,1500,2000],
            "daily_load_shift_half_span_mw":[0,50],
            "battery_power_mw":[0,100],
            "battery_duration_hours_assumed":4,
            "battery_round_trip_efficiency_assumed":0.9,
        },
        "interpretation":"Only three seasonal monthly examples; not a year-long optimized simulation, nor predictive uncertainty or confidence intervals.",
        "limitations":[
            "Three selected 30-day windows contain only 90 of 365 days; the other 275 days have source audit only.",
            "Min/median/max across three windows are descriptive sample sensitivity, NOT statistically estimated confidence intervals.",
            "Hypothetical balancing caps do not equal actual Fingrid imports, operational headroom or connection rights.",
            "Observed generation is fixed, no actual transmission topology, queue, congestion, generator dispatch or observed power outages.",
            "Flexible scheduling is hindsight-guided and battery sizing and cyclic state of charge are hypothetical.",
            "No valid 2030 forecast or location-specific connection conclusion can be drawn.",
        ],
    }
    (output_dir/"seasonal_comparison_2025.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--coverage-only",action="store_true")
    args=parser.parse_args(argv)
    study=perform(args.input,args.output_dir,solver=not args.coverage_only)
    meta = {"year":2025,"annual_days":study["annual_observations"]["source_days"],
            "annual_pairs":study["annual_observations"]["quarter_hour_pairs"],
            "annual_input_sha256":study["annual_observations"]["source_sha256"],
            "seasons":{s["season"]:s["source_sha256"] for s in study["seasonal_studies"]},
            "optimized_combinations":len(study["across_season_parameter_comparison"])}
    print("VERIFIED_SEASONS_JSON="+json.dumps(meta, sort_keys=True))


if __name__=="__main__":
    main()
