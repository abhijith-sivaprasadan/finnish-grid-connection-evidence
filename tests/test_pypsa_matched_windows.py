"""Test strict matched-window selection with synthetic missingness, not fake source publication."""
from datetime import date,timedelta
import pytest
from src.models.observed_windows import runs,selected_block

def test_complete_day_runs_split_on_true_holes():
    base=date(2025,1,1)
    days=[base+timedelta(days=i) for i in (0,1,2,4,5,8,9,10,11)]
    grouped=runs(days)
    assert [len(g) for g in grouped]==[4,3,2]

def test_equal_length_selection_uses_no_missing_days():
    winter=date(2025,1,1)
    summer=date(2025,6,1)
    autumn=date(2025,9,1)
    mapping={"winter":winter,"summer":summer,"autumn":autumn}
    audit={}
    for k,start in mapping.items():
        num={"winter":4,"summer":7,"autumn":10}[k]
        audit[k]={"complete_dates":[start+timedelta(days=i) for i in range(num)]}
    matches=selected_block(audit,min_days=3,max_days=14)
    assert all(len(x)==4 for x in matches.values())
    assert [x[0] for x in matches.values()]==[winter,summer,autumn]

def test_missing_source_does_not_produce_short_fake_season():
    start=date(2025,1,1)
    a={"winter":{"complete_dates":[start]},"summer":{"complete_dates":[start+timedelta(days=i) for i in range(12)]},
       "autumn":{"complete_dates":[start+timedelta(days=i) for i in range(14)]}}
    with pytest.raises(ValueError,match="No 3-day complete matched"):
        selected_block(a)
