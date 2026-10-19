"""Ensure audit metadata never leaks to modified observations or becomes grid validation."""
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data/manual/grid_scope_observations.csv"
REVIEW=ROOT/"docs/audits/GRID_SCOPE_18_ROW_SCREENSHOT_RECHECK_2026_10_19.csv"
TS=ROOT/"website/src/lib/grid-scope-audit.json"

def test_screenshot_review_matches_exact_source_tuples():
    source=list(csv.DictReader(SOURCE.open(encoding="utf-8",newline="")))
    review=list(csv.DictReader(REVIEW.open(encoding="utf-8",newline="")))
    js=json.loads(TS.read_text(encoding="utf-8"))
    assert len(source)==len(review)==len(js)==18
    s={r["observation_id"]:r for r in source}
    p={r["observation_id"]:r for r in review}
    assert len(s)==len(p)==len(set(x["observation_id"] for x in js))==18
    assert s.keys()==p.keys()
    for row in js:
        o=s[row["observation_id"]]; a=p[row["observation_id"]]
        assert row["connection_point_id"]==o["connection_point_id"]
        assert row["direction"]==o["direction"]
        assert str(row["effective_year"])==o["effective_year"]
        assert row["capacity_value"]==row["shown_value"]==float(o["capacity_value"])
        assert row["capacity_unit"]==o["capacity_unit"]==row["shown_unit"]=="MW"
        assert row["source_observed_at"]==o["source_observed_at"]
        assert row["evidence_sha256"]==a["evidence_sha256"]
        assert len(row["evidence_sha256"])==64
        int(row["evidence_sha256"],16)
        assert row["evidence_grade"] in {"exact_tooltip","explicit_panel_number"}
    assert sum(x["evidence_grade"]=="exact_tooltip" for x in js)==17
    assert sum(x["evidence_grade"]=="explicit_panel_number" for x in js)==1

def test_original_public_capacity_csv_is_not_edited_or_operator_confirmed():
    body=SOURCE.read_text(encoding="utf-8")
    assert len(body.splitlines())==19
    assert all("published_indicative" in line for line in body.splitlines()[1:])
    assert all("operator_confirmed" not in line for line in body.splitlines()[1:])
    assert not list((ROOT/"docs/audits").rglob("*.png"))
