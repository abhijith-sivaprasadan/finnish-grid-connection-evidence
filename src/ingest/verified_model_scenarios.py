"""Load only solver-verified published Finland scenario summaries into local SQLite.

This is *never* connection-capacity evidence. Source JSON and observed CSV are
repository-pinned, read offline, and verified before an atomic/idempotent import.
No Neon write, operator headroom, or credentials are involved.

Run: python -m src.ingest.verified_model_scenarios --db data/evidence.sqlite
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from src.db import ROOT, connect, insert
from src.schema import ScenarioResult

PUBLISHED = ROOT / "website/src/lib/pypsa-scenario-results.json"
OBSERVED = ROOT / "data/model_inputs/fingrid_20261015_20261016_15min.csv"
SOURCE_RUN_COMPLETED_UTC = "2026-10-20T07:48:22Z"
MODEL = "pypsa-fi-single-bus-v1"
NAMES = {"observed_reference", "flat_100mw", "flexible_100mw",
         "flat_100mw_with_battery"}
MEASURES = {
    "new_demand_mwh": "MWh",
    "modelled_shortfall_under_assumption_mwh": "MWh",
    "assumed_balancing_support_mwh": "MWh",
}


def validate_publication(path: Path = PUBLISHED, observed_path: Path = OBSERVED) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("publication_status") != "verified_solver_output":
        raise ValueError("Model summary is not solver-verified")
    if raw.get("classification") != "model_scenario" or raw.get("model_version") != MODEL:
        raise ValueError("Unexpected model evidence class or version")
    if raw.get("verified_operator_connectability") is not False:
        raise ValueError("Cannot import operator-connectability claims as model scenarios")
    if raw.get("model_resolution") != "one aggregate Finland bus; NO geographical or physical grid model":
        raise ValueError("Physical model boundary not declared")
    src_url = raw.get("source_job_url", "")
    if not src_url.startswith(
        "https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/"
    ):
        raise ValueError("Missing expected immutable original solver provenance link")
    source = raw.get("source_window_utc", {})
    if source.get("start") != "2026-10-15T00:00:00.000000Z" or source.get("end") != "2026-10-17T00:00:00.000000Z":
        raise ValueError("Unknown source period; cannot reuse audited timestamp")
    digest = hashlib.sha256(observed_path.read_bytes()).hexdigest()
    if raw.get("observed_input_sha256") != digest:
        raise ValueError("Original observed source CSV SHA-256 differs from solver publication")
    scenarios = raw.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != len(NAMES) or {
        s.get("scenario") for s in scenarios if isinstance(s, dict)
    } != NAMES:
        raise ValueError("Expected precisely the four published solved scenarios")
    assumptions = raw.get("assumptions")
    if not isinstance(assumptions, dict) or assumptions.get("balancing_support_limit_mw") != 1500:
        raise ValueError("Unrecognized hypothetical balancing assumptions")
    for case in scenarios:
        if case.get("solver_status") != "ok" or case.get("termination") != "optimal":
            raise ValueError("Unsolved model scenario")
        if case.get("historical_interval_count") != 192 or case.get("window_hours") != 48:
            raise ValueError("Incomplete or wrong-length model input")
        if abs(float(case.get("max_model_balance_error_mw", 1e20))) > 1e-6:
            raise ValueError("Model power-balance residual exceeds verified tolerance")
        for key in MEASURES:
            value = case.get(key)
            if type(value) not in (int, float):
                raise ValueError("Missing numeric solver output for " + key)
            import math
            if not math.isfinite(value) or value < 0:
                raise ValueError("Invalid solver output for " + key)
        expected = 0 if case["scenario"] == "observed_reference" else 4800
        if abs(case["new_demand_mwh"] - expected) > 1e-6:
            raise ValueError("New-load energy no longer matches assumed 48-hour scenario")
    return raw


def build_rows(model: dict) -> list[ScenarioResult]:
    common = {
        "source_json_path": "website/src/lib/pypsa-scenario-results.json",
        "source_run_url": model["source_job_url"],
        "observed_csv_sha256": model["observed_input_sha256"],
        "source_window_utc": model["source_window_utc"],
        "scope": "national_one_bus_historical_assumed_balancing_NOT_substation_capacity",
        "operator_verified_connectability": False,
        "model_assumptions": model["assumptions"],
    }
    records = []
    for case in sorted(model["scenarios"], key=lambda x: x["scenario"]):
        for metric, unit in MEASURES.items():
            records.append(ScenarioResult(
                scenario_id=f"{MODEL}:{case['scenario']}:{metric}",
                model_version=MODEL,
                assumption_set=json.dumps({**common, "scenario": case["scenario"]},
                                          sort_keys=True, separators=(",", ":")),
                metric=metric,
                value=float(case[metric]),
                unit=unit,
                created_at=SOURCE_RUN_COMPLETED_UTC,
                capacity_status="model_scenario",
            ))
    return records


def run(db_path=None, *, publication=PUBLISHED, observed=OBSERVED):
    model = validate_publication(Path(publication), Path(observed))
    rows = build_rows(model)
    # Validate EVERY row before opening a DB; with connect() also enforces
    # all-or-nothing rollback for any conflict in the immutable scenario IDs.
    with connect(db_path) as conn:
        before = conn.execute("SELECT COUNT(*) FROM capacity_observation").fetchone()[0]
        inserted = sum(insert(conn, record) for record in rows)
        after = conn.execute("SELECT COUNT(*) FROM capacity_observation").fetchone()[0]
        if before != after:
            raise AssertionError("Model import touched operator-published capacity evidence")
    return {
        "category": "model_scenario",
        "model_version": MODEL,
        "source_sha256_verified": True,
        "scenario_count": len(NAMES),
        "metric_records": len(rows),
        "inserted": inserted,
        "operator_confirmed_capacity": False,
        "location_specific_headroom": None,
        "database": "local_sqlite_only",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", type=Path, help="Local SQLite evidence DB; defaults to GRID_EVIDENCE_DB/data/evidence.sqlite")
    p.add_argument("--publication", type=Path, default=PUBLISHED)
    p.add_argument("--observed", type=Path, default=OBSERVED)
    args = p.parse_args(argv)
    print(json.dumps(run(args.db, publication=args.publication, observed=args.observed),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
