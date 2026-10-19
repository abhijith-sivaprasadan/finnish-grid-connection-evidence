"""Standalone validation: real seed provenance + synthetic fixture failures."""
from dataclasses import replace
from pathlib import Path
import csv
import pytest
from src.station_catalogue import COLUMNS, RegistryRow, evidence_report, read_registry

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data/catalogue/seed_20261017.csv"


def fixture_row(**edits):
    row = dict(zip(COLUMNS, [
        "TEST:NLS:1", "nls_topodb_review", "nls-object-1",
        "https://www.maanmittauslaitos.fi/en/node/13475",
        "2026-10-18T12:00:00Z", "SYNTHETIC TEST OBJECT", "",
        "mapped_infrastructure", "not_assessed", "", "", "candidate", "",
        "Synthetic test only; not Fingrid identity or MW"
    ]))
    row.update(edits)
    return row


def test_initial_real_pilot_is_staged_without_new_numbers():
    records = read_registry(SEED)
    report = evidence_report(records)
    assert len(records) == 5
    assert set(report["review_states"]) == {"source_transcribed"}
    assert report["published_capacity_values"] == 0
    assert report["operator_identity_checked"] == 0
    assert report["with_wgs84_location"] == 0
    assert all(r.feature_kind == "connection_point" for r in records)


@pytest.mark.parametrize("changes", [
    {"latitude": "65.1"}, {"longitude": "25.8"},
    {"latitude": "600000", "longitude": "6700000"},
    {"voltage_kv": "-400"}, {"voltage_kv": "400000"},
    {"source_url": "https://example.com/?api-key=secret"},
    {"captured_utc": "2026-10-18T12:00:00"},
    {"captured_utc": "2099-01-01T00:00:00Z"},
    {"review_state": "operator_identity_checked"},
    {"operator_evidence": "source_names_fingrid"},
    {"source_feature_id": ""},
    {"source_url": "file:///secret.csv"},
])
def test_provisional_geodata_cannot_claim_fingrid_or_ignore_provenance(changes):
    with pytest.raises(ValueError):
        RegistryRow.parse(fixture_row(**changes))


def test_evidence_requires_independent_document():
    row = fixture_row(source_dataset="national_reference", review_state="operator_identity_checked",
                      operator_evidence="separate_operator_document",
                      review_url="https://www.fingrid.fi/en/grid/")
    assert RegistryRow.parse(row).review_state == "operator_identity_checked"


def test_reject_duplicate_id_and_stable_native_identifier(tmp_path):
    p = tmp_path / "candidates.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerow(fixture_row(registry_id="TEST:NLS:1"))
        w.writerow(fixture_row(registry_id="TEST:NLS:2"))
    with pytest.raises(ValueError, match="duplicate"):
        read_registry(p)


def test_collision_is_reviewed_not_merged():
    a = RegistryRow.parse(fixture_row())
    b = RegistryRow.parse(fixture_row(registry_id="TEST:OTHER:2",source_dataset="other_source",
                                       source_feature_id="other-2",name="Synthetic test object",
                                       voltage_kv=""))
    report = evidence_report([a,b])
    assert report["records"] == 2
    assert len(report["name_voltage_collisions_to_review"]) == 1
