"""Operator event documentary dates, not historic equipment/AC-flow tests."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from src.models.fi_2025_operator_chronology import evaluate

LEDGER=Path(__file__).resolve().parents[1]/"data/reference/fi_2025_operator_asset_chronology.json"


def data():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def by_id(report):
    return {e["id"]: e for e in report["events"]}


def test_sep_2025_has_uncertain_forssa_and_pre_aurora_state():
    report=evaluate(data(),"2025-09-15")
    statuses=by_id(report)
    assert statuses["aurora_400kv_fi_se1_2025"]["snapshot_assessment"]=="before_reported_completion_window"
    assert statuses["huittinen_forssa_2025"]["snapshot_assessment"]=="completion_date_uncertain_in_source_window"
    assert statuses["estlink2_2025_restoration"]["snapshot_assessment"]=="HVDC_restored_but_time_varying_availability_not_verified"
    assert statuses["lowlands_alajarvi_hausjarvi_future"]["snapshot_assessment"]=="future_not_an_energized_2025_line"
    assert not report["can_auto_patch_2024_osm_topology"]


def test_early_2025_hdvc_unavailable_and_late_2025_aurora_unmapped():
    early=by_id(evaluate(data(),"2025-02-18"))
    assert early["estlink2_2025_restoration"]["snapshot_assessment"]=="existing_HVDC_not_yet_restored_to_commercial_use"
    later=by_id(evaluate(data(),"2025-12-01"))
    assert later["aurora_400kv_fi_se1_2025"]["snapshot_assessment"]=="operator_reports_completed_but_OSM_asset_unmapped"
    assert later["huittinen_forssa_2025"]["snapshot_assessment"]=="operator_reports_completed_but_OSM_asset_unmapped"


def test_ownership_change_not_a_2025_physically_new_line():
    status=by_id(evaluate(data(),"2025-08-01"))
    assert status["alajarvi_lestijarvi_2025_ownership"]["snapshot_assessment"]=="ownership_event_not_new_physical_line"


@pytest.mark.parametrize("value",["2024-12-31","2026-01-01","invalid","2025-02-30"])
def test_refuse_out_of_period_or_invalid_dates(value):
    with pytest.raises(ValueError):
        evaluate(data(),value)


def test_refuse_implicit_source_osm_match_and_unsourced_reconstruction():
    value=data()
    value["events"][0]["osm_asset_id_verified"]="fake-reconstructed-id"
    with pytest.raises(ValueError,match="automatic OSM"):
        evaluate(value,"2025-12-01")
    value=data()
    value["events"][0]["sources"]=[]
    with pytest.raises(ValueError,match="specific Finnish operator"):
        evaluate(value,"2025-12-01")


def test_reject_duplicate_events_and_future_line_labelled_2025():
    value=data()
    value["events"].append(deepcopy(value["events"][0]))
    with pytest.raises(ValueError,match="Duplicate"):
        evaluate(value,"2025-07-01")
    value=data()
    future=next(x for x in value["events"] if x["event_type"]=="planned_future_grid_reinforcement_not_present_in_2025")
    future["source_start"]="2025-01-01"
    with pytest.raises(ValueError,match="Future-only"):
        evaluate(value,"2025-06-30")
