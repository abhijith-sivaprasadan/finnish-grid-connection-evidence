"""Exercise dashboard empty, populated and filtered states without network access."""
from streamlit.testing.v1 import AppTest
from src.db import ROOT
from src.ingest.manual_grid_scope import ingest


def test_empty_dashboard(tmp_path, monkeypatch):
    monkeypatch.setenv("GRID_EVIDENCE_DB", str(tmp_path / "empty.sqlite"))
    app = AppTest.from_file(str(ROOT / "app/dashboard.py")).run(timeout=30)
    assert not app.exception
    assert any("No published observations" in x.value for x in app.info)


def test_real_dashboard_filters_and_missing_values(tmp_path, monkeypatch):
    path = tmp_path / "real.sqlite"
    ingest(ROOT / "data/manual", path)
    monkeypatch.setenv("GRID_EVIDENCE_DB", str(path))
    app = AppTest.from_file(str(ROOT / "app/dashboard.py")).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value == "5"
    assert app.metric[1].value == "18"
    assert app.metric[2].value == "0"
    matrix = app.dataframe[0].value
    assert matrix.loc["ALAPITKÄ 400 kV", "2030"] == "not published"
    app.sidebar.selectbox[0].set_value("production").run()
    assert not app.exception
    matrix = app.dataframe[0].value
    assert matrix.loc["ALAPITKÄ 400 kV", "2030"] == "380 MW"
    app.sidebar.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any("Not published" in x.value for x in app.info)
