"""Evidence and sensitivity controls, without needing API key in ordinary CI."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv

import pytest

from src.models.history import parse_window, retrieve, write_pair
from src.models.sweep import make_plan, csv_list, run_sweep
from src.models.finland import load_observed,additional_load,INPUT_PATH


def test_history_windows_strict_and_disallow_old_hourly_data():
    assert (parse_window("2025-09-15","2025-10-15")[1]-
            parse_window("2025-09-15","2025-10-15")[0]).days==30
    for a,b in [("2023-06-01","2023-06-02"),("2025-01-01","2025-01-01"),
                ("2025-10-15","2025-09-15"),("2020-01-01","2021-01-01"),
                ("not-a-date","2025-10-15")]:
        with pytest.raises(ValueError):
            parse_window(a,b)


def test_history_pairing_with_real_repository_observation_shape(tmp_path):
    # Fixtures reflect the existing source CSV's observed values and proven UTC
    # interval alignment, rather than pretending the fixture is a live API read.
    from src.schema import OperationalRecord
    from src.models.finland import INPUT_PATH
    data=load_observed()
    def mocked(id_,a,b):
        lower=datetime.fromisoformat(a.replace("Z","+00:00"))
        upper=datetime.fromisoformat(b.replace("Z","+00:00"))
        out=[]
        for _,r in data.iterrows():
            stamp=datetime.fromisoformat(r["timestamp_utc"].replace("Z","+00:00"))
            if not lower<=stamp<upper:continue
            out.append(OperationalRecord(
                source="fingrid",dataset_id=str(id_),
                metric="electricity_consumption" if id_==124 else "electricity_production",
                unit="MWh/h",
                value=float(r["consumption_mwh_per_hour"] if id_==124 else r["production_mwh_per_hour"]),
                timestamp_utc=r["timestamp_utc"], interval_end_utc=r["interval_end_utc"],
                retrieved_at=r["consumption_retrieved_at"] if id_==124 else r["production_retrieved_at"],
                source_url="https://data.fingrid.fi/en/datasets/"+str(id_)
            ))
        return out
    pairs=retrieve("2026-10-15","2026-10-17",getter=mocked,chunk_days=1)
    assert len(pairs)==192
    out=tmp_path/"verified_2day.csv"
    manifest=write_pair(pairs,out,window_start="2026-10-15",window_end="2026-10-17")
    assert manifest["source_intervals"]==192
    assert manifest["complete_days"]==2
    assert len(load_observed(out))==192
    def missing(id_,a,b):
        batch=mocked(id_,a,b)
        if id_==74 and a.startswith("2026-10-15"):
            return batch[:-1]
        return batch
    with pytest.raises(ValueError,match="incomplete"):
        retrieve("2026-10-15","2026-10-17",getter=missing,chunk_days=1)


def test_sweep_planning_is_bounded_and_full_factorial():
    plan=make_plan((1000,1500,2000),(0,50),(0,100))
    assert len(plan)==12
    assert plan[0]==(1000,0,0)
    assert plan[-1]==(2000,50,100)
    assert csv_list("0,50",allow_zero=True)==[0,50]
    for item in ("-1","NaN","1,,2","1,1","100000000000000000000000000000000"):
        with pytest.raises((ValueError,OverflowError)):
            csv_list(item)


def test_day_neutrality_also_supports_custom_flexible_half_span():
    d=load_observed()
    extra=additional_load(d,"flexible_100mw_with_battery",flex_span_mw=25)
    assert set(extra.unique())=={75.0,125.0}
    assert len(extra)==192
    assert extra.sum()*0.25==4800
    assert all(float(x.sum())*0.25==2400 for _,x in extra.groupby(d.index.date))
    for invalid in (-1,101,float("inf")):
        with pytest.raises(ValueError):
            additional_load(d,"flexible_100mw",flex_span_mw=invalid)


@pytest.mark.model_solver
def test_small_real_source_sensitivity_solves_and_preserves_competing_assumptions(tmp_path):
    pytest.importorskip("pypsa")
    output=tmp_path/"sweep.json"
    s=run_sweep(INPUT_PATH,output=output,limits=(1000,1500),flex_spans=(0,50),battery_powers=(0,100))
    assert s["source_interval_count"]==192
    assert s["sweep_design"]["solved_combinations"]==8
    assert s["sweep_design"]["reference_solutions"]==2
    assert len(s["results"])==8
    assert output.exists()
    assert all(r["solver_status"]=="ok" and r["solver_termination"]=="optimal" for r in s["results"])
    assert all(r["max_balance_error_mw"]<1e-5 for r in s["results"])
    assert all(r["added_load_energy_mwh"]==4800 for r in s["results"])
    assert len({r["balancing_limit_mw_assumed"] for r in s["results"]})==2
    assert len({r["battery_power_mw_assumed"] for r in s["results"]})==2
    assert s["data_kind"]=="model_scenario"
    assert "actual outages" in s["limitations"][0]
