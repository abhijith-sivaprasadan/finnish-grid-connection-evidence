"""Only source-transcribed observations; all missing cells remain visibly absent."""
from datetime import date
import csv
import pandas as pd
import pytest

from src.availability import comparison_grid, coverage_summary
from src.audit_capacity import FIELDS, audit_rows, export_checklist
from src.db import ROOT, connect
from src.ingest.manual_grid_scope import ingest
from src.views import published


@pytest.fixture
def source_data(tmp_path):
    path = tmp_path / "source.sqlite"
    ingest(ROOT / "data" / "manual", path)
    with connect(path) as conn:
        data = published(conn)
        points = pd.read_sql_query("SELECT * FROM connection_point ORDER BY name", conn)
    return path, data, points


def test_five_points_both_directions_every_year_without_inventing_missing(source_data):
    _, frame, points = source_data
    grid = comparison_grid(frame, points, [2026, 2030, 2035])
    summary = coverage_summary(grid)
    assert summary == {
        "intersections": 30,
        "published": 18,
        "not_published_in_selection": 12,
        "needs_reconciliation": 0,
    }
    assert len(grid) == 30
    assert not (grid.loc[grid.Evidence == "missing_in_selection", "Value"].notna()).any()
    assert set(grid["Unit"].dropna()) == {"MW"}
    row = grid[(grid["Connection point"] == "ALAPITKÄ 400 kV") &
               (grid["Direction"] == "consumption") & (grid["Year"] == 2030)].iloc[0]
    assert row["Evidence"] == "missing_in_selection"
    assert "not published" in row["Published estimate"]
    assert pd.isna(row["Value"])
    other = grid[(grid["Connection point"] == "ALAPITKÄ 400 kV") &
                 (grid["Direction"] == "production") & (grid["Year"] == 2030)].iloc[0]
    assert other["Published estimate"] == "380 MW"
    assert other["Source URL"].startswith("https://")


def test_consumption_and_production_are_independent_same_point(source_data):
    _, frame, points = source_data
    grid = comparison_grid(frame, points, [2026])
    pair = grid[(grid["Connection point"] == "ALAPITKÄ 400 kV")]
    assert pair.loc[pair.Direction == "consumption", "Published estimate"].item() == "500 MW"
    assert pair.loc[pair.Direction == "production", "Published estimate"].item() == "380 MW"


def test_never_combine_different_capture_sessions(source_data):
    _, frame, points = source_data
    extra = frame.iloc[[0]].copy()
    extra["observation_id"] = "NEW_CAPTURE_TEST_ONLY"
    extra["source_observed_at"] = "2026-10-18T00:00:00Z"
    extra["capacity_value"] = 75
    combined = pd.concat([frame, extra], ignore_index=True)
    grid = comparison_grid(combined, points, [2026])
    assert coverage_summary(grid)["published"] == 1
    assert float(grid.loc[grid.Evidence == "published_indicative", "Value"].iloc[0]) == 75.0
    old_snapshot = frame["source_observed_at"].iloc[0]
    grid_old = comparison_grid(combined, points, [2026], snapshot=old_snapshot)
    assert coverage_summary(grid_old)["published"] == 8


def test_duplicate_source_claims_require_reconciliation(source_data):
    _, frame, points = source_data
    duplicate = frame.iloc[[0]].copy()
    duplicate["observation_id"] = "ANOTHER_SOURCE_TEST_ONLY"
    duplicate["source_url"] = "https://example.com/other-source"
    data = pd.concat([frame, duplicate], ignore_index=True)
    grid = comparison_grid(data, points, [2026],
                           snapshot=frame.source_observed_at.iloc[0])
    assert coverage_summary(grid)["needs_reconciliation"] == 1
    affected = grid[grid.Evidence == "requires_reconciliation"].iloc[0]
    assert pd.isna(affected["Value"])
    assert "multiple" in affected["Published estimate"]


def test_preserve_mva_as_not_comparable_with_mw(source_data):
    _, frame, points = source_data
    mutated = frame.copy()
    mutated.loc[mutated.index[0], "capacity_unit"] = "MVA"
    grid = comparison_grid(mutated, points, [2026])
    assert "MVA" in set(grid["Unit"].dropna())
    assert "MW" in set(grid["Unit"].dropna())


@pytest.mark.parametrize("years", [[2026, 2026], ["2026"], [2026, 2030.0]])
def test_invalid_year_filters_refused(source_data, years):
    _, frame, points = source_data
    with pytest.raises(ValueError, match="distinct integer"):
        comparison_grid(frame, points, years)


def test_audit_checklist_export_has_all_18_unverified_observations(source_data, tmp_path):
    path, _, _ = source_data
    output = tmp_path / "audit" / "checklist.csv"
    result = export_checklist(output, db=path)
    assert result["observations_to_recheck"] == 18
    assert result["independently_verified_by_this_command"] == 0
    with output.open(encoding="utf-8", newline="") as fp:
        rows = list(csv.DictReader(fp))
    assert len(rows) == 18
    assert set(rows[0]) == set(FIELDS)
    assert all(r["independent_recheck_status"] == "pending_independent_recheck" for r in rows)
    assert all(r["verified_value"] == "" and r["verification_evidence_url"] == "" for r in rows)
    assert all(r["capacity_status"] == "published_indicative" for r in rows)
    assert all(r["source_url"].startswith("https://") for r in rows)
    # Never overwrite evidence annotated by a human reviewer.
    output.write_text("manual reviewer findings", encoding="utf-8")
    with pytest.raises(FileExistsError):
        export_checklist(output, db=path)
    assert output.read_text(encoding="utf-8") == "manual reviewer findings"


def test_csv_and_dashboard_audit_extractions_have_same_identifiers(source_data):
    path, _, _ = source_data
    with connect(path) as conn:
        rows = audit_rows(conn)
    assert len(rows) == 18
    assert len({r["observation_id"] for r in rows}) == 18
    assert all(not r["source_published_on"] for r in rows)
