"""Synthetic fixtures verify boundaries, never scientific validity."""
from dataclasses import replace
import sqlite3
import pandas as pd
import pytest
from src.db import connect, insert, ROOT
from src.ingest.manual_grid_scope import ingest
from src.schema import ScenarioResult, utc
from src.views import published, filter_capacity, coverage_matrix


@pytest.mark.parametrize("change", [
    {"capacity_value": None}, {"capacity_value": float("nan")}, {"capacity_value": float("inf")},
    {"capacity_value": -1}, {"capacity_unit": None}, {"capacity_unit": "GW"},
    {"direction": "bidirectional"}, {"capacity_status": "model_scenario"},
    {"capacity_status": "operator_confirmed"}, {"source_url": ""},
    {"source_url": "https://example.org/?securityToken=TEST"},
    {"source_observed_at": "2026-10-16T00:00:00"}, {"validity_notes": ""},
    {"source_published_on": "2027-01-01"},
])
def test_invalid_evidence_is_rejected(observation, change):
    with pytest.raises(ValueError):
        replace(observation, **change)


def test_timezone_normalization():
    assert utc("2026-10-16T02:00:00+02:00") == utc("2026-10-16T00:00:00Z")


def test_snapshot_history_and_conflict_rollback(tmp_path, point, observation):
    path = tmp_path / "evidence.sqlite"
    with connect(path) as conn:
        insert(conn, point)
        assert insert(conn, observation)
        assert not insert(conn, observation)
        insert(conn, replace(observation, observation_id="TEST-NEW", source_observed_at="2026-10-17T00:00:00Z", capacity_value=20))
    with pytest.raises(ValueError, match="Conflicting immutable"):
        with connect(path) as conn:
            insert(conn, replace(point, connection_point_id="ROLLBACK-POINT"))
            insert(conn, replace(observation, capacity_value=99))
    with connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM connection_point").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM capacity_observation").fetchone()[0] == 2
        assert conn.execute("SELECT capacity_value FROM capacity_observation WHERE observation_id='TEST-OBS'").fetchone()[0] == 10


def test_snapshot_key_null_year_not_duplicated(tmp_path, point, observation):
    with connect(tmp_path / "db") as conn:
        insert(conn, point)
        insert(conn, replace(observation, effective_year=None))
        with pytest.raises(sqlite3.IntegrityError):
            insert(conn, replace(observation, observation_id="OTHER-ID", effective_year=None))


def test_evidence_categories_and_unit_preservation(tmp_path, point, observation):
    with connect(tmp_path / "db") as conn:
        insert(conn, point)
        insert(conn, observation)
        insert(conn, ScenarioResult("TEST-SCENARIO", "test-v1", '{"synthetic_test_only": true}', "test-output", 50, "MW", "2026-10-16T00:00:00Z"))
        insert(conn, replace(observation, observation_id="CONFIRMED-TEST", source_observed_at="2026-10-17T00:00:00Z",
                            capacity_status="operator_confirmed", confirmation_evidence_url="https://example.org/test-confirmation"))
        frame = published(conn)
        assert len(frame) == 1
        assert frame.iloc[0].capacity_unit == "MVA"
        assert frame.iloc[0].capacity_value == 10
        matrix = coverage_matrix(frame, [(point.connection_point_id, point.name)], "consumption", [2030, 2031])
        assert list(matrix["Published estimate"]) == ["10 MVA", "not published"]
        assert filter_capacity(frame, direction="production").empty
        assert filter_capacity(frame, points=[]).empty


def test_real_csv_rebuild_is_idempotent_and_has_provenance(tmp_path):
    path = tmp_path / "db"
    result = ingest(ROOT / "data/manual", path)
    assert result["grid_scope_observations.csv"] == 18
    assert not any(ingest(ROOT / "data/manual", path).values())
    with connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM connection_point").fetchone()[0] == 5
        assert conn.execute("SELECT count(*) FROM capacity_observation WHERE capacity_status != 'published_indicative'").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM operational_series").fetchone()[0] == 0
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_sql_operator_confirmation_requires_document(tmp_path, point, observation):
    with connect(tmp_path / "db") as conn:
        insert(conn, point)
        insert(conn, observation)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE capacity_observation SET capacity_status='operator_confirmed'")


def test_sql_rejects_blank_numeric_capacity(tmp_path, point, observation):
    with connect(tmp_path / "db") as conn:
        insert(conn, point)
        insert(conn, observation)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE capacity_observation SET capacity_value=NULL")


def test_quality_requires_real_numeric_evidence_and_fingrid(tmp_path, point, observation):
    from src.quality import report
    with connect(tmp_path / "db") as conn:
        insert(conn, point)
        for n in range(5):
            insert(conn, replace(observation, observation_id=f"TEST-{n}",
                source_observed_at=f"2026-10-{10+n:02d}T00:00:00Z"))
        outcome = report(conn)
        assert outcome["numeric_capacity_observations"] == 5
        assert outcome["live_context_ready"] is False
        assert outcome["entsoe_optional_ready"] is False
        assert outcome["mvp_data_ready"] is False


def test_upgrade_v1_preserves_numeric_history(tmp_path, point, observation):
    from src.db import DDL
    # Construct a genuine version-1 SQLite database from its old schema.
    path = tmp_path / "legacy.sqlite"
    old = DDL.replace("capacity_value REAL NOT NULL", "capacity_value REAL")
    old = old.replace("capacity_unit TEXT NOT NULL", "capacity_unit TEXT")
    old = old.replace("PRAGMA user_version = 2;", "PRAGMA user_version = 1;")
    from dataclasses import asdict
    conn = sqlite3.connect(path)
    conn.executescript(old)
    pv, ov = asdict(point), asdict(observation)
    conn.execute(f"INSERT INTO connection_point ({','.join(pv)}) VALUES ({','.join('?' for _ in pv)})", list(pv.values()))
    conn.execute(f"INSERT INTO capacity_observation ({','.join(ov)}) VALUES ({','.join('?' for _ in ov)})", list(ov.values()))
    conn.commit()
    conn.close()
    with connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
        assert not insert(conn, observation)
    with connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM published_capacity").fetchone()[0] == 1
        assert conn.execute("SELECT capacity_value FROM capacity_observation").fetchone()[0] == 10
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE capacity_observation SET capacity_value=NULL")
