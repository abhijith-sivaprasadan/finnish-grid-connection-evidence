"""Synthetic *test fixture* for historical integrity; never publish as source data."""
import json
from pathlib import Path

import pytest

from src.models.finland import load_observed, INPUT_PATH
from src.models.seasons import coverage_report, select_window, write_window, SEASON_WINDOWS


def test_annual_report_rejects_short_real_dataset():
    with pytest.raises(ValueError,match="365 complete UTC days"):
        coverage_report(INPUT_PATH)


def test_selection_only_uses_exact_existing_quarter_hour_rows(tmp_path):
    original=load_observed(INPUT_PATH)
    subset=select_window(original,"2026-10-15","2026-10-16")
    assert len(subset)==96
    assert subset.index[0].isoformat()=="2026-10-15T00:00:00"
    assert subset.index[-1].isoformat()=="2026-10-15T23:45:00"
    output=tmp_path/"one_day_source.csv"
    digest=write_window(subset,output)
    assert len(digest)==64
    assert len(load_observed(output))==96
    with pytest.raises(ValueError,match="incomplete"):
        select_window(original,"2026-10-14","2026-10-16")


def test_windows_are_exante_nonoverlap_equal_length():
    assert set(SEASON_WINDOWS)=={"winter","summer","autumn"}
    from datetime import date
    intervals=[]
    for start,end in SEASON_WINDOWS.values():
        lo,hi=date.fromisoformat(start),date.fromisoformat(end)
        assert (hi-lo).days==30
        assert lo.year==hi.year==2025
        intervals.append(set(range(lo.toordinal(),hi.toordinal())))
    assert not intervals[0]&intervals[1]
    assert not intervals[0]&intervals[2]
    assert not intervals[1]&intervals[2]
