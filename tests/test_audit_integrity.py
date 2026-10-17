"""Offline integrity-audit regression tests with synthetic operational records."""
import sqlite3
from src.db import connect, insert, ROOT
from src.ingest.manual_grid_scope import ingest
from src.schema import OperationalRecord
from src.audit_integrity import audit


def record(metric="electricity_consumption", unit="MW", start="2026-10-14T00:00:00Z",
           end="2026-10-14T00:15:00Z", value=10., dataset="A65"):
    return OperationalRecord(
        source="entsoe", dataset_id=dataset, metric=metric, unit=unit,
        value=value, timestamp_utc=start, interval_end_utc=end,
        retrieved_at="2026-10-17T00:00:00Z",
        source_url="https://transparency.entsoe.eu/"
    )


def test_committed_csv_matches_18_sqlite_records_but_does_not_claim_verified(tmp_path):
    db=tmp_path/"evidence.sqlite"
    ingest(ROOT/"data/manual",db)
    with connect(db) as conn:
        findings=audit(conn)
    assert findings["counts"]["capacity"]==18
    assert findings["counts"]["manual_csv_rows"]==18
    assert findings["source_values_independently_verified"] is False
    assert findings["operator_value_verification_pending"] is True
    assert findings["operational_rows_in_db"] is False
    assert findings["internal_integrity_passed"] is True, findings["findings"]
    assert [f["code"] for f in findings["findings"]]==["NO_PERSISTED_OPERATIONS"]


def test_wrong_ingested_value_is_detected(tmp_path):
    db=tmp_path/"audit.sqlite"
    ingest(ROOT/"data/manual",db)
    with connect(db) as conn:
        conn.execute("UPDATE capacity_observation SET capacity_value=9999 WHERE observation_id='gs-20261017-vuolijoki-400-production-2026'")
    with connect(db) as conn:
        report=audit(conn)
    assert report["internal_integrity_passed"] is False
    assert "CSV_DB_MISMATCH" in [f["code"] for f in report["findings"]]


def test_synthetic_context_can_pass_structural_checks_without_source_verification(tmp_path):
    db=tmp_path/"context.sqlite"
    ingest(ROOT/"data/manual",db)
    with connect(db) as conn:
        assert insert(conn,record())
        result=audit(conn)
    assert result["internal_integrity_passed"] is True, result["findings"]
    assert result["operational_rows_in_db"] is True  # database has rows: fixture is NOT live source proof
    assert result["operator_value_verification_pending"] is True
    assert result["counts"]["source_counts"]["entsoe:A65"]==1


def test_wrong_unit_flags_blocker(tmp_path):
    db=tmp_path/"bad-unit.sqlite"
    with connect(db) as conn:
        insert(conn,record(unit="MWh/h"))
        result=audit(conn)
    assert any(f["code"]=="METRIC_UNIT_MISMATCH" for f in result["findings"])
    assert not result["internal_integrity_passed"]


def test_overlap_rejected_but_gap_only_review(tmp_path):
    db=tmp_path/"overlap.sqlite"
    with connect(db) as conn:
        insert(conn,record(end="2026-10-14T00:30:00Z"))
        insert(conn,record(start="2026-10-14T00:15:00Z",
                           end="2026-10-14T00:45:00Z"))
        result=audit(conn)
    assert any(f["code"]=="OPERATIONAL_OVERLAP" for f in result["findings"])
    assert not result["internal_integrity_passed"]
    db2=tmp_path/"gap.sqlite"
    with connect(db2) as conn:
        insert(conn,record())
        insert(conn,record(start="2026-10-14T00:30:00Z",
                           end="2026-10-14T00:45:00Z"))
        result=audit(conn)
    assert any(f["code"]=="OPERATIONAL_GAP" for f in result["findings"])
    assert result["internal_integrity_passed"] is True
