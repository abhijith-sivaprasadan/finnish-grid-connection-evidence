"""Release regressions: published solver evidence remains separate from operator MW."""
import json
import sqlite3
from pathlib import Path

import pytest

from src.db import connect
from src.ingest.verified_model_scenarios import OBSERVED, PUBLISHED, run, validate_publication
from src.ingest.manual_grid_scope import ingest


def test_verified_scenarios_import_idempotent_isolated(tmp_path):
    path = tmp_path / "portfolio.sqlite"
    # Five genuine manually sourced Grid Scope points remain unchanged.
    ingest(db_file=path)  # existing importer handles manual inputs and DB setup
    first = run(path)
    second = run(path)
    assert first["inserted"] == 12 and first["metric_records"] == 12
    assert second["inserted"] == 0
    assert second["source_sha256_verified"]
    with connect(path) as db:
        assert db.execute("SELECT count(*) FROM scenario_result").fetchone()[0] == 12
        assert db.execute("SELECT count(*) FROM capacity_observation").fetchone()[0] == 18
        assert db.execute("SELECT count(*) FROM capacity_observation WHERE capacity_status='operator_confirmed'").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM scenario_result WHERE capacity_status='model_scenario'").fetchone()[0] == 12
        assert db.execute("SELECT count(*) FROM scenario_result WHERE metric='modelled_shortfall_under_assumption_mwh'").fetchone()[0] == 4
        record = db.execute("SELECT assumption_set FROM scenario_result LIMIT 1").fetchone()[0]
        assert json.loads(record)["operator_verified_connectability"] is False


def test_modified_original_source_hash_must_fail_closed(tmp_path):
    changed = tmp_path / "fake_source.csv"
    changed.write_bytes(OBSERVED.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="SHA-256"):
        validate_publication(PUBLISHED, changed)


@pytest.mark.parametrize("field,value,expected", [
    ("publication_status", "draft", "solver-verified"),
    ("verified_operator_connectability", True, "connectability"),
    ("model_resolution", "physically validated Finnish network", "Physical model"),
    ("source_job_url", "https://example.com/fake", "provenance"),
])
def test_false_solved_or_operator_claims_rejected(tmp_path, field, value, expected):
    doc = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    doc[field] = value
    candidate = tmp_path / "changed.json"
    candidate.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError, match=expected):
        validate_publication(candidate, OBSERVED)


def test_corrupted_solver_output_rejected_without_database_writes(tmp_path):
    doc = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    doc["scenarios"][0]["termination"] = "infeasible"
    changed = tmp_path / "unsolved.json"
    changed.write_text(json.dumps(doc), encoding="utf-8")
    db_path = tmp_path / "no_insert.sqlite"
    with pytest.raises(ValueError, match="Unsolved"):
        run(db_path, publication=changed)
    assert not db_path.exists()


def test_conflicting_preexisting_scenario_rolls_back(tmp_path):
    db_path = tmp_path / "collision.sqlite"
    first = run(db_path)
    assert first["inserted"] == 12
    with connect(db_path) as db:
        db.execute("UPDATE scenario_result SET value=value+1 WHERE scenario_id=(SELECT min(scenario_id) FROM scenario_result)")
    with pytest.raises(ValueError, match="Conflicting immutable"):
        run(db_path)
    with connect(db_path) as db:
        assert db.execute("SELECT count(*) FROM scenario_result").fetchone()[0] == 12
