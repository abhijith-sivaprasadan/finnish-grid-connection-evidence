"""Archival substations persist separately and cannot modify capacity evidence."""
from dataclasses import replace
import csv
import sqlite3
import pytest
from src.db import connect,insert
from src.station_catalogue_store import write_archive,DEFAULT_SOURCE
from src.station_catalogue import COLUMNS,read_registry


def test_historical_archive_is_idempotent_and_separate(tmp_path):
    db=tmp_path/"archive.sqlite"
    report=write_archive(DEFAULT_SOURCE,db)
    assert report["inserted"]==128
    assert report["grid_scope_capacity_observations_unchanged"]==0
    second=write_archive(DEFAULT_SOURCE,db)
    assert second["inserted"]==0
    assert second["archived"]==128
    with connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM historical_station_designation").fetchone()[0]==128
        assert conn.execute("SELECT count(*) FROM connection_point").fetchone()[0]==0
        assert conn.execute("SELECT count(*) FROM capacity_observation").fetchone()[0]==0
        assert conn.execute("PRAGMA user_version").fetchone()[0]==2


def test_archive_conflict_rolls_back(tmp_path):
    db=tmp_path/"archive.sqlite"
    write_archive(DEFAULT_SOURCE,db)
    entries=read_registry(DEFAULT_SOURCE)
    rows=[]
    for item in entries:
        value={f:getattr(item,f) for f in COLUMNS}
        for numeric in ("voltage_kv","latitude","longitude"):
            value[numeric]=str(value[numeric]) if value[numeric] is not None else ""
        rows.append(value)
    rows[10]["name"]="SYNTHETIC INCORRECT STATION"
    csvpath=tmp_path/"changed.csv"
    with csvpath.open("w",newline="",encoding="utf-8") as fp:
        w=csv.DictWriter(fp,fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    with pytest.raises(ValueError,match="immutable station archive"):
        write_archive(csvpath,db)
    with connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM historical_station_designation").fetchone()[0]==128
        assert conn.execute("SELECT name FROM historical_station_designation WHERE registry_id=?",(entries[10].registry_id,)).fetchone()[0]==entries[10].name


def test_import_rejects_other_source(tmp_path):
    rows=read_registry(DEFAULT_SOURCE)
    from dataclasses import replace
    doc=tmp_path/"bad.csv"
    with doc.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS)
        w.writeheader()
        r=rows[0]
        out={k:getattr(r,k) for k in COLUMNS}
        out["source_dataset"]="other_source"
        for numeric in ("voltage_kv","latitude","longitude"):
            out[numeric]=str(out[numeric]) if out[numeric] is not None else ""
        w.writerow(out)
    with pytest.raises(ValueError,match="historical Fingrid annex"):
        write_archive(doc,tmp_path/"db.sqlite")
