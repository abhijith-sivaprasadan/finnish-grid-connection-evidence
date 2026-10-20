"""Independent seasonal retrieval resilience; synthetic fixtures stay inside tests."""
import pytest
from src.models.season_blocks import execute
from src.models.seasons import SEASON_WINDOWS
from src.models.finland import INPUT_PATH,load_observed
from src.schema import OperationalRecord

def test_each_failed_window_is_clearly_rejected_not_synthetic(tmp_path):
    # A getter returning no Fingrid rows is an INCOMPLETE source, not zero demand.
    report=execute(tmp_path,getter=lambda id,a,b:[],solve=False)
    assert report["valid_season_count"]==0
    assert report["rejected_season_count"]==3
    assert report["publication_state"]=="partial_seasonal_source_coverage"
    assert report["annual_2025_complete"] is False
    assert len(report["parameter_comparisons"])==12
    assert all(x["sample_count"]==0 for x in report["parameter_comparisons"])
    assert all(x["status"]=="source_incomplete_or_incompatible" for x in report["historical_seasons"])
    assert all("incomplete" in x["diagnostic"] for x in report["historical_seasons"])
