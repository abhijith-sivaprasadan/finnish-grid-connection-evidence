"""Time-scope operator event audit for Finnish 2025 hypothetical network studies.

Operator-named projects are NOT mapped to OSM source IDs, and no electrical
parameters or actual switching records are inferred from news releases.
"""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path

DEFAULT_LEDGER = Path(__file__).resolve().parents[2] / "data" / "reference" / "fi_2025_operator_asset_chronology.json"
NEW_EVENTS = {"new_cross_border_ac_connection", "new_reinforcement_and_110kv_replacement"}
EXISTING_RESTORATION = "existing_hvdc_link_operational_restoration"


def evaluate(source: dict, snapshot: str) -> dict:
    try:
        instant = date.fromisoformat(snapshot)
    except ValueError as exc:
        raise ValueError("Use a valid snapshot date YYYY-MM-DD") from exc
    if instant.year != 2025:
        raise ValueError("Chronology is specifically bounded to calendar year 2025")
    events = source.get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("Original Fingrid operator event registry is required")
    ids = set()
    output = []
    for event in events:
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id or event_id in ids:
            raise ValueError("Duplicate or missing Fingrid event identity")
        ids.add(event_id)
        src = event.get("sources")
        if not isinstance(src, list) or not src or not all(isinstance(x,str) and x.startswith("https://www.fingrid.fi/") for x in src):
            raise ValueError("Named event must have specific Finnish operator source URLs")
        if event.get("eligible_for_auto_addition") is not False or event.get("osm_asset_id_verified") is not None:
            raise ValueError("No source-event asset is allowed to claim automatic OSM line mapping")
        start = date.fromisoformat(event["source_start"])
        end = date.fromisoformat(event["source_end_exclusive"])
        if start >= end:
            raise ValueError("Unordered operator documentary date window")
        typ = event.get("event_type")
        if typ in NEW_EVENTS:
            status = ("before_reported_completion_window" if instant < start else
                      "completion_date_uncertain_in_source_window" if instant < end else
                      "operator_reports_completed_but_OSM_asset_unmapped")
        elif typ == EXISTING_RESTORATION:
            status = ("existing_HVDC_not_yet_restored_to_commercial_use" if instant < start else
                      "HVDC_restoration_day_boundary_requires_timestamp_evidence" if instant < end else
                      "HVDC_restored_but_time_varying_availability_not_verified")
        elif typ == "ownership_change_of_2024_built_line":
            status = "ownership_event_not_new_physical_line"
        elif typ == "planned_future_grid_reinforcement_not_present_in_2025":
            if start.year <= 2025:
                raise ValueError("Future-only project must not be placed within 2025")
            status = "future_not_an_energized_2025_line"
        else:
            raise ValueError(f"Unknown operator event class: {typ}")
        output.append({"id": event_id, "event_type": typ, "snapshot_assessment": status,
                       "source_urls": src, "mapped_source_osm_asset_id": None,
                       "verified_2025_electrical_parameters": False})
    return {
        "snapshot": snapshot,
        "historical_operator_statement_coverage": "selected_non_exhaustive_facts_only",
        "OSM_2024_as_built_2025_certified": False,
        "actual_Fingrid_grid_power_flow_verified": False,
        "can_auto_patch_2024_osm_topology": False,
        "events": output,
        "limitations": [
            "This is not a complete 2025 Fingrid commissioning log.",
            "Documentary windows do not supply switching timestamps or asset coordinates.",
            "No OSM original source edge is mapped to a Fingrid named route.",
            "Operator reference to HVDC commercial use is not a minute-by-minute converter dispatch series.",
            "Physical model topology, electrical properties and per-asset N-1 remain unverified."
        ]
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger",type=Path,default=DEFAULT_LEDGER)
    p.add_argument("--snapshot",required=True)
    p.add_argument("--output",type=Path)
    a = p.parse_args(argv)
    result=evaluate(json.loads(a.ledger.read_text(encoding="utf-8")), a.snapshot)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("FI_2025_CHRONOLOGY_JSON="+json.dumps({
        "snapshot":a.snapshot, "events_audited":len(result["events"]),
        "operator_network_certified":False,
        "future_and_unmapped_events":{x["id"]:x["snapshot_assessment"] for x in result["events"]}
    },sort_keys=True))
    return result


if __name__=="__main__":
    main()
