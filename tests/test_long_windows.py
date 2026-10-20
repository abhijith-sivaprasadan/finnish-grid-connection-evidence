"""Long continuous original-source extraction; zero synthetic source in production."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import pytest
from src.models.long_windows import WINDOWS,BALANCING_ASSUMED,BATTERY_HOURS,verified_window_rows

def test_exact_separate_27day_model_plan():
    assert WINDOWS=={"winter27":("2025-01-18","2025-02-14"),
                     "latewinter27":("2025-02-15","2025-03-14")}
    assert len(BALANCING_ASSUMED)==3
    assert BATTERY_HOURS==(2.,4.,8.)
    assert len(BALANCING_ASSUMED)*2*(1+3)==24

def test_missing_original_source_never_becomes_an_invented_27day_series(tmp_path):
    with pytest.raises((FileNotFoundError,ValueError)):
        verified_window_rows(tmp_path,*WINDOWS["winter27"])
