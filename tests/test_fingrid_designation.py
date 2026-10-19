"""Regression: the official appendix names are historical station identities, never MW."""
import json
from pathlib import Path
from src.station_catalogue import read_registry, evidence_report
ROOT=Path(__file__).resolve().parents[1]

def test_fingrid_designation_archival_extract_preserves_source_discrepancy():
    records=read_registry(ROOT/"data/catalogue/fingrid_main_grid_annex_2024.csv")
    assert len(records)==128  # 128 visually/textually listed rows
    from collections import Counter
    assert Counter(int(r.voltage_kv) for r in records)=={400:49,220:13,110:66}
    assert all(r.feature_kind=="substation" for r in records)
    assert all(r.review_state=="source_transcribed" for r in records)
    assert all(r.operator_evidence=="source_names_fingrid" for r in records)
    assert all(r.latitude is None and r.longitude is None for r in records)
    report=evidence_report(records)
    assert report["published_capacity_values"]==0
    assert report["operator_identity_checked"]==0
    assert {r.name for r in records if r.voltage_kv==400}.issuperset(
        {"VUOLIJOKI","ALAPITKÄ","ALAJÄRVI","SEINÄJOKI","UUSNIVALA"})
    archive=json.loads((ROOT/"website/src/lib/main-grid-designation.json").read_text(encoding="utf-8"))
    assert archive["parsed_rows"]==len(records)
    assert archive["source_printed_total"]==127
    assert archive["count_discrepancy_unresolved"] is True
    assert archive["source_table_caption"]=="Kantaverkko 1.1.2020"
    assert [(r.name,r.voltage_kv) for r in records]==[(a["name"],a["voltage_kv"]) for a in archive["rows"]]
