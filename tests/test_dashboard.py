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


def test_persisted_national_operational_rows_are_visible(tmp_path, monkeypatch):
    from src.db import connect, insert
    from src.schema import OperationalRecord
    path = tmp_path / "national-context.sqlite"
    ingest(ROOT / "data" / "manual", path)
    with connect(path) as conn:
        assert insert(conn, OperationalRecord(
            source="entsoe", dataset_id="A65",
            metric="electricity_consumption", unit="MW", value=8210.0,
            timestamp_utc="2026-10-14T00:00:00Z",
            interval_end_utc="2026-10-14T00:15:00Z",
            retrieved_at="2026-10-17T00:00:00Z",
            source_url="https://transparency.entsoe.eu/",
        ))
    monkeypatch.setenv("GRID_EVIDENCE_DB", str(path))
    app = AppTest.from_file(str(ROOT / "app/dashboard.py")).run(timeout=30)
    assert not app.exception
    assert app.metric[2].value == "1"
    # The context summary must identify provider, scope and source metric.
    dataframes = [w.value for w in app.dataframe]
    assert any("source" in frame.columns and "last_retrieved_utc" in frame.columns
               and "entsoe" in frame["source"].values for frame in dataframes)
