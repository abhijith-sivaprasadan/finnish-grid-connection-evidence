"""Independent historical Fingrid articles provide names, NOT capacity or commissioned state."""
from pathlib import Path
from src.station_catalogue import read_registry, evidence_report

ROOT=Path(__file__).resolve().parents[1]

def test_fingrid_named_leads_are_source_linked_and_not_capacity():
    leads=read_registry(ROOT/"data/catalogue/fingrid_named_leads_20261019.csv")
    existing=read_registry(ROOT/"data/catalogue/seed_20261017.csv")
    assert len(leads)==5
    assert len(existing)==5
    assert all(o.feature_kind=="substation" for o in leads)
    assert all(o.review_state=="source_transcribed" for o in leads)
    assert all(o.operator_evidence=="source_names_fingrid" for o in leads)
    assert all(o.latitude is None and o.voltage_kv is None for o in leads)
    assert all(o.source_feature_id.startswith("LOCAL:") for o in leads)
    report=evidence_report(existing+leads)
    assert report["records"]==10
    assert report["operator_identity_checked"]==0
    assert report["published_capacity_values"]==0
