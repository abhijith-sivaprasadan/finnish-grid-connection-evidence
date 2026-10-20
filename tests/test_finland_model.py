"""Historical-input and scenario tests. Solver integration runs in optional CI job."""
import copy
from pathlib import Path
import pytest
import pandas as pd
from src.models.finland import (
    INPUT_PATH,SCENARIOS,load_observed,additional_load,stress_cost_proxy,run
)


def test_real_source_input_has_no_gaps_or_invented_values():
    df=load_observed()
    assert len(df)==192
    assert df["timestamp_utc"].iloc[0].startswith("2026-10-15")
    assert df["interval_end_utc"].iloc[-1].startswith("2026-10-17")
    assert df["consumption_retrieved_at"].notna().all()
    assert df["production_retrieved_at"].notna().all()
    assert 7000 < df["consumption_mwh_per_hour"].mean() < 11000
    assert 6000 < df["production_mwh_per_hour"].mean() < 12000


def test_all_extra_load_scenarios_have_identical_daily_energy():
    df=load_observed()
    scenarios={case:additional_load(df,case) for case in SCENARIOS}
    assert scenarios["observed_reference"].sum()==0
    for name in SCENARIOS[1:]:
        assert float(scenarios[name].sum()*0.25)==4800
        assert all(abs(float(group.sum())-9600)<1e-8
                   for _,group in scenarios[name].groupby(df.index.date))
    flex=scenarios["flexible_100mw"]
    assert set(flex.unique())=={50.0,150.0}
    assert float(flex.mean())==100
    assert (stress_cost_proxy(df)>=1).all()


def test_model_input_rejects_critical_source_errors(tmp_path):
    data=pd.read_csv(INPUT_PATH)
    for label,change in [
        ("missing",lambda d:d.drop(index=2)),
        ("duplicates",lambda d:d.assign(timestamp_utc=d["timestamp_utc"].mask(d.index==3,d["timestamp_utc"].iloc[2]))),
        ("negative",lambda d:d.assign(production_mwh_per_hour=d["production_mwh_per_hour"].mask(d.index==10,-2))),
        ("gap",lambda d:d.assign(interval_end_utc=d["interval_end_utc"].mask(d.index==30,d["interval_end_utc"].iloc[29]))),
    ]:
        path=tmp_path/(label+".csv")
        change(data.copy()).to_csv(path,index=False)
        with pytest.raises(ValueError):
            load_observed(path)


@pytest.mark.model_solver
def test_pypsa_solver_returns_balance_and_scenario_provenance(tmp_path):
    pytest.importorskip("pypsa")
    result=run(output=tmp_path/"result.json")
    assert len(result["scenarios"])==4
    assert len(result["intervals"])==192*4
    assert result["verified_operator_connectability"] is False
    assert result["model_resolution"].startswith("one aggregate")
    assert all(s["solver_status"]=="ok" and s["termination"]=="optimal"
               and s["max_model_balance_error_mw"]<1e-5 for s in result["scenarios"])
    assert result["scenarios"][0]["new_demand_mwh"]==0
    assert all(s["new_demand_mwh"]==4800 for s in result["scenarios"][1:])
    assert result["scenarios"][3]["battery_charge_mwh"]>0
    assert (tmp_path/"result.json").exists()
