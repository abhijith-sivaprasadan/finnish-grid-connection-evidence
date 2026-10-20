"""Independent stdlib release-data audit: source CSVs -> compiled UI -> model metadata.

This tests INTERNAL publication lineage, not Fingrid/ENTSO-E operator truth or
real-world connection capacity. All mismatches are release blockers. No secrets.
Usage: python -m src.audit_release_invariants --json /tmp/release-audit.json
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
from src.db import ROOT

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"Empty original CSV {path}")
    return rows

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def is_sha(value):
    return bool(isinstance(value,str) and re.fullmatch(r"[a-f0-9]{64}",value))

def assert_that(condition, description):
    if not condition:
        raise AssertionError(description)

def run(root=ROOT):
    root=Path(root)
    src=root/"data/manual"
    points=read_csv(src/"connection_points.csv")
    grid=read_csv(src/"grid_scope_observations.csv")
    audit=read_csv(root/"docs/audits/GRID_SCOPE_18_ROW_SCREENSHOT_RECHECK_2026_10_19.csv")
    published_review=read_json(root/"website/src/lib/grid-scope-audit.json")
    assert_that(len(points)==5 and len(grid)==len(audit)==len(published_review)==18,
                "Five-point / 18-record evidence count drift")
    pids={r["connection_point_id"] for r in points}
    assert_that(len(pids)==5,"Duplicate source point ID")
    gids={r["observation_id"] for r in grid}
    assert_that(len(gids)==18,"Duplicate original observed ID")
    aid={r["observation_id"]:r for r in audit}
    jreview={r["observation_id"]:r for r in published_review}
    assert_that(set(aid)==set(jreview)==gids, "CSV source/review/website IDs differ")
    combos=set()
    for record in grid:
        rid=record["observation_id"]
        r=aid[rid];v=jreview[rid]
        for field in ("connection_point_id","direction","effective_year","capacity_value",
                      "capacity_unit","source_observed_at"):
            a=str(record[field]); b=str(r[field]); c=str(v[field])
            assert_that(a==b and a==c,f"Field {field} mismatch for {rid}: {a}/{b}/{c}")
        assert_that(record["capacity_status"]=="published_indicative",
                    "Operator-confirmed capacity entered in this historical sample")
        assert_that(record["confirmation_evidence_url"]=="",
                    "Original sample erroneously labelled confirmed")
        assert_that(record["connection_point_id"] in pids,"Orphan Grid Scope point")
        assert_that(r["shown_value"]==r["capacity_value"] and
                    r["shown_unit"]==r["capacity_unit"],"Screenshot-ledger row mismatch")
        assert_that(is_sha(r["evidence_sha256"]),"Missing screenshot fingerprint metadata")
        for verified_field in ("shown_value","shown_unit","evidence_grade","evidence_review_date","evidence_sha256"):
            assert_that(str(v[verified_field])==str(r[verified_field]),
                        f"Published review metadata field {verified_field} differs from original CSV for {rid}")
        assert_that(record["capacity_unit"]=="MW" and
                    float(record["capacity_value"])>=0,"Unexpected source unit/value")
        key=(record["connection_point_id"],record["direction"],record["effective_year"])
        assert_that(key not in combos,"Duplicate year/direction intersection in same original capture")
        combos.add(key)
    grades=Counter(x["evidence_grade"] for x in audit)
    assert_that(grades=={"exact_tooltip":17,"explicit_panel_number":1},
                "Screenshot audit labels/counts changed")
    # Regex must extract every hard-coded UI source transcription, not merely
    # compare counts; old /snapshot compiled mode can otherwise diverge from CSV.
    snap=(root/"website/src/lib/snapshot.ts").read_text(encoding="utf-8")
    values=re.findall(r'\["([A-Z]+)",\s*"(consumption|production)",\s*(\d{4}),\s*(\d+)\]',snap)
    assert_that(len(values)==18,"Compiled fallback snapshot no longer has 18 explicit values")
    snapshot_values={(site,di,int(y),float(val)) for site,di,y,val in values}
    original_values={(r["connection_point_id"].split("-")[2],r["direction"],
                      int(r["effective_year"]),float(r["capacity_value"])) for r in grid}
    assert_that(snapshot_values==original_values,"Snapshot TS values DO NOT match source CSV")
    # The original CSV source URL is the historically captured link; ensure UI
    # fallback retains it rather than silently substituting operator root page.
    original_urls={r["source_url"] for r in grid}
    assert_that(len(original_urls)==1 and next(iter(original_urls)) in snap,
                "Fallback source URL differs from original captured point URL")

    national=read_csv(root/"data/model_inputs/fingrid_20261015_20261016_15min.csv")
    compiled=read_json(root/"website/src/lib/finland-observed.json")
    series=compiled["time_series"]
    assert_that(len(national)==len(series)==192,"2026 model input quarter-hour count wrong")
    observed_sha=hashlib.sha256((root/"data/model_inputs/fingrid_20261015_20261016_15min.csv").read_bytes()).hexdigest()
    v1=read_json(root/"website/src/lib/pypsa-scenario-results.json")
    regional=read_json(root/"website/src/lib/krios-engineering-verified-2026.json")
    assert_that(v1["observed_input_sha256"]==observed_sha and
                regional["fingrid_regional_v2"]["source_national_original_csv_sha256"]==observed_sha,
                "Reported solver provenance hash differs from original Fingrid input CSV")
    stamps=set()
    for srcrow, target in zip(national,series):
        ts=srcrow["timestamp_utc"]
        assert_that(ts==target["timestamp_utc"] and ts not in stamps,"Missing/reordered original timestamp")
        stamps.add(ts)
        t=datetime.fromisoformat(ts.replace("Z","+00:00"))
        end=datetime.fromisoformat(srcrow["interval_end_utc"].replace("Z","+00:00"))
        assert_that(end-t==timedelta(minutes=15),"Unexpected native source interval")
        assert_that(math.isclose(float(srcrow["consumption_mwh_per_hour"]),target["consumption_mw"],abs_tol=1e-10) and
                    math.isclose(float(srcrow["production_mwh_per_hour"]),target["production_mw"],abs_tol=1e-10),
                    "Compiled operational timeseries differs from original source CSV")
        for field in ("consumption_retrieved_at","production_retrieved_at"):
            assert_that(srcrow[field]==target[field],"Source retrieval provenance drift")
    assert_that(list(sorted(stamps))[0]=="2026-10-15T00:00:00.000000Z" and
                list(sorted(stamps))[-1]=="2026-10-16T23:45:00.000000Z",
                "Historic input window is not the audited 48 hours")
    assert_that(v1["classification"]=="model_scenario" and
                v1["verified_operator_connectability"] is False and
                len(v1["scenarios"])==4 and all(s["termination"]=="optimal" for s in v1["scenarios"]),
                "Single-bus reported result is not qualified")
    assert_that(regional["cigre_hv"]["real_network"] is False and
                regional["cigre_mv"]["real_dutch_feeder"] is False and
                regional["fingrid_regional_v2"]["operator_approved_connectable_mw"] is None and
                regional["osm_input_uncertainty"]["operator_calibrated"] is False and
                regional["identical_ac_crosssolver"]["original_CIGRE_crossvalidated"] is False,
                "Engineering website presents unverified reference model as real site")

    cover=read_json(root/"website/src/lib/fingrid-archive-coverage-2025.json")
    assert_that(cover["verified_complete_days"]+cover["known_missing_source_days"]+
                cover["not_covered_by_archives_days"]==365,"2025 coverage buckets no longer partition year")
    assert_that(cover["distinct_original_paired_intervals"]>=96*cover["verified_complete_days"] and
                cover["distinct_original_paired_intervals"]<=96*365 and
                cover["source_year_complete"] is False and
                cover["annual_pypsa_solved"] is False,
                "Historical source coverage or annual-model qualification incorrect")
    dutch=read_json(root/"website/src/lib/netherlands-official-source-summary-2026.json")
    assert_that([a["row_count"] for a in dutch["original_csvs"]]==[23,271,602] and
                sum(a["row_count"] for a in dutch["original_csvs"])==896,
                "Dutch dated original operator CSV count mismatch")
    assert_that(all(is_sha(a["sha256"]) for a in dutch["original_csvs"]) and
                dutch["site_specific_available_mw"] is None and
                dutch["license_for_raw_derivative_redistribution_verified"] is False,
                "Dutch site MW claim or provenance violation")

    assert_that(len(regional["cigre_hv"]["cases"])==3 and
                all(x["n1_tested"]==15 and x["n1_nonconverged"]+
                    x["n1_converged_with_reference_violation"]<=15 for x in regional["cigre_hv"]["cases"]),
                "N-1 ambiguous or impossible outage count")
    assert_that(len(regional["cigre_mv"]["cases"])==4 and
                len(regional["fingrid_regional_v2"]["scenarios"])==4 and
                len(regional["osm_input_uncertainty"]["assumed_rating_scale_cases"])==3,
                "Model case-count drift")
    return {
        "status":"internal_release_source_consistency_passed",
        "audit_scope":"repository source CSV and UI parity; NOT authenticated operator observation values",
        "five_historical_grid_scope_points":len(points),
        "historical_indicative_records":len(grid),
        "screenshot_review_metadata_records":len(audit),
        "original_screenshot_image_bytes_independently_reverified":False,
        "source_original_2026_native_intervals":len(national),
        "source_original_2026_csv_sha256":observed_sha,
        "source_2025_verified_complete_days":cover["verified_complete_days"],
        "source_2025_distinct_original_paired_intervals":cover["distinct_original_paired_intervals"],
        "dutch_dated_original_source_rows":sum(a["row_count"] for a in dutch["original_csvs"]),
        "operator_confirmed_site_connectable_mw":None,
        "physical_operator_network_calibrated":False
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--json",type=Path)
    args=p.parse_args(argv)
    result=run(args.root)
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))

if __name__=="__main__":main()
