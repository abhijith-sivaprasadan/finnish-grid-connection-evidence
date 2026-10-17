"""Cloud adapter tests: pure logic and optional real PostgreSQL integration.

CI supplies an ephemeral PostgreSQL container. No Neon account or production
credentials are used by these tests.
"""
from datetime import date, datetime, timedelta, timezone
import os

import pytest
from sqlalchemy import create_engine, text

from src.cloud_store import collect_sqlite_rows, engine_for, mirror, read_snapshot
from src.cloud_sync import verify_day, run
from src.db import ROOT, connect
from src.ingest.manual_grid_scope import ingest
from src.schema import OperationalRecord


def test_reject_non_postgres_and_non_tls_connection_urls():
    with pytest.raises(ValueError, match="Only PostgreSQL"):
        engine_for("sqlite:///wrong.sqlite")
    with pytest.raises(ValueError, match="sslmode=require"):
        engine_for("postgresql://reader:secret@localhost:5432/db?sslmode=disable")


def test_validate_complete_source_day_with_variable_entsoe_blocks():
    day=date(2026,10,14)
    def row(source, ds, metric, start, end):
        return dict(source=source,dataset_id=ds,metric=metric,area="FI",
                    timestamp_utc=start.isoformat(),interval_end_utc=end.isoformat())
    start=datetime(2026,10,14,tzinfo=timezone.utc)
    items=[]
    for ds,metric in (("124","electricity_consumption"),
                       ("74","electricity_production")):
        for n in range(96):
            a=start+timedelta(minutes=15*n)
            items.append(row("fingrid",ds,metric,a,a+timedelta(minutes=15)))
    # A03 can publish variable-size blocks without fabricating 96 records.
    items.append(row("entsoe","A65","electricity_consumption",start,start+timedelta(hours=10)))
    items.append(row("entsoe","A65","electricity_consumption",
                     start+timedelta(hours=10),start+timedelta(days=1)))
    counts=verify_day(items,day)
    assert counts["fingrid:124:electricity_consumption"]==96
    assert counts["fingrid:74:electricity_production"]==96
    assert counts["entsoe:A65:electricity_consumption"]==2
    missing=items[:-1]
    with pytest.raises(ValueError, match="Incomplete end-of-day"):
        verify_day(missing,day)
    overlapping=[r.copy() for r in items]
    overlapping[-1]["timestamp_utc"]=(start+timedelta(hours=9)).isoformat()
    with pytest.raises(ValueError, match="Gap/overlap"):
        verify_day(overlapping,day)
    incomplete_fingrid=[r for r in items if not
                       (r["source"]=="fingrid" and r["dataset_id"]=="124"
                        and r["timestamp_utc"]==(start+timedelta(minutes=30)).isoformat())]
    with pytest.raises(ValueError, match="Gap/overlap"):
        verify_day(incomplete_fingrid,day)


def test_backfill_bounds_before_source_or_database_connection():
    with pytest.raises(ValueError, match="1–7"):
        run(backfill_days=8, url="postgresql://no:secret@host/db",
            today=date(2026,10,17))
    with pytest.raises(ValueError, match="two days old"):
        run(day="2026-10-17",url="postgresql://no:secret@host/db",
            today=date(2026,10,17))
    with pytest.raises(ValueError, match="DATABASE_WRITE_URL"):
        run(day="2026-10-14",url="",today=date(2026,10,17))


@pytest.fixture
def pg_engine():
    url=os.environ.get("POSTGRES_TEST_URL")
    if not url:
        pytest.skip("Ephemeral PostgreSQL service is available only in CI")
    engine=create_engine(url)
    with engine.begin() as db:
        for table in ("operational_series","capacity_observation","connection_point",
                      "grid_project","scenario_result"):
            db.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
    try:
        yield engine
    finally:
        engine.dispose()


def test_real_postgres_mirror_is_idempotent_immutable_and_readable(pg_engine,tmp_path):
    path=tmp_path/"source.sqlite"
    ingest(ROOT/"data/manual",path)
    with connect(path) as db:
        batches=collect_sqlite_rows(db)
    result=mirror(pg_engine,batches)
    assert result["capacity_observation"]["inserted"]==18
    assert result["connection_point"]["inserted"]==5
    assert mirror(pg_engine,batches)["capacity_observation"]["inserted"]==0
    snap=read_snapshot(pg_engine,today=datetime(2026,10,17,tzinfo=timezone.utc))
    assert len(snap["capacity"])==18
    assert len(snap["points"])==5
    assert snap["context"].empty
    assert snap["quality"]["source_values_independently_verified"] is False
    assert snap["quality"]["mvp_data_ready"] is False
    # Existing immutable values must not be overwritten; atomic rollback.
    wrong={k:[x.copy() for x in v] for k,v in batches.items()}
    wrong["capacity_observation"][0]["capacity_value"]=999999.0
    with pytest.raises(ValueError,match="Conflicting immutable"):
        mirror(pg_engine,wrong)
    with pg_engine.connect() as db:
        assert db.execute(text("SELECT count(*) FROM capacity_observation")).scalar_one()==18


def test_postgres_operational_history_stays_separate(pg_engine,tmp_path):
    path=tmp_path/"source.sqlite"
    ingest(ROOT/"data/manual",path)
    from src.db import insert
    with connect(path) as db:
        insert(db,OperationalRecord(source="entsoe",dataset_id="A65",
            metric="electricity_consumption",unit="MW",value=8135.5,
            timestamp_utc="2026-10-14T00:00:00Z",
            interval_end_utc="2026-10-14T00:15:00Z",
            retrieved_at="2026-10-17T00:00:00Z",
            source_url="https://transparency.entsoe.eu/"))
        batches=collect_sqlite_rows(db)
    mirror(pg_engine,batches)
    snap=read_snapshot(pg_engine,today=datetime(2026,10,17,tzinfo=timezone.utc))
    assert snap["context"].iloc[0]["value"]==8135.5
    assert snap["context"].iloc[0]["source"]=="entsoe"
    assert len(snap["capacity"])==18



def test_hosted_streamlit_reads_postgres_without_api_keys(pg_engine,tmp_path,monkeypatch):
    from streamlit.testing.v1 import AppTest
    path=tmp_path/"data.sqlite"
    ingest(ROOT/"data/manual",path)
    with connect(path) as db:
        mirror(pg_engine,collect_sqlite_rows(db))
    monkeypatch.setenv("HOSTED_DASHBOARD","true")
    monkeypatch.setenv("DATABASE_READ_URL",
                       "postgresql://reader:PLACEHOLDER_NOT_A_REAL_KEY@localhost/ci?sslmode=require")
    monkeypatch.delenv("FINGRID_API_KEY",raising=False)
    monkeypatch.delenv("ENTSOE_API_TOKEN",raising=False)
    monkeypatch.setattr("src.cloud_store.engine_for",lambda _:pg_engine)
    app=AppTest.from_file(str(ROOT/"app/dashboard.py")).run(timeout=30)
    assert not app.exception
    assert app.metric[0].value=="5"
    assert app.metric[1].value=="18"
    assert app.metric[2].value=="0"
    assert any("No persisted operational rows" in w.value for w in app.warning)
