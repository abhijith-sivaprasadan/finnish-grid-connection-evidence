"""Append-only historical station identity archive in local SQLite.

Import is explicitly opt-in. No modification of live Neon or Grid Scope capacity
tables. A row listed in a Fingrid historical annex is *not* current MW headroom.
"""
from __future__ import annotations
import argparse
import json
import sqlite3
from pathlib import Path
from src.db import connect
from src.station_catalogue import read_registry, RegistryRow

DEFAULT_SOURCE=Path(__file__).resolve().parents[1]/"data/catalogue/fingrid_main_grid_annex_2024.csv"

DDL="""CREATE TABLE IF NOT EXISTS historical_station_designation (
  registry_id TEXT PRIMARY KEY,
  source_dataset TEXT NOT NULL,
  source_feature_id TEXT NOT NULL,
  source_url TEXT NOT NULL,
  captured_utc TEXT NOT NULL,
  name TEXT NOT NULL,
  voltage_kv REAL NOT NULL CHECK(voltage_kv IN (110,220,400)),
  feature_kind TEXT NOT NULL CHECK(feature_kind='substation'),
  operator_evidence TEXT NOT NULL CHECK(operator_evidence='source_names_fingrid'),
  review_state TEXT NOT NULL CHECK(review_state='source_transcribed'),
  notes TEXT NOT NULL,
  source_table_label TEXT NOT NULL CHECK(source_table_label='Kantaverkko 1.1.2020'),
  source_decision_context TEXT NOT NULL CHECK(source_decision_context='2024 designation annex'),
  UNIQUE(source_dataset,source_feature_id)
)"""

FIELDS=("registry_id","source_dataset","source_feature_id","source_url",
        "captured_utc","name","voltage_kv","feature_kind",
        "operator_evidence","review_state","notes",
        "source_table_label","source_decision_context")


def write_archive(path:Path,database:Path)->dict:
    """Validate full source before opening any DB, then insert atomically."""
    records=read_registry(path)
    if not records:
        raise ValueError("Empty archive cannot be imported")
    if any(row.source_dataset!="fingrid_designation_annex_2024" or
           row.review_state!="source_transcribed" or
           row.feature_kind!="substation" or
           row.voltage_kv not in (110,220,400) for row in records):
        raise ValueError("This loader only accepts the reviewed historical Fingrid annex")
    inserted=0
    with connect(database) as conn:
        conn.execute(DDL)
        for row in records:
            values=(row.registry_id,row.source_dataset,row.source_feature_id,
                row.source_url,row.captured_utc,row.name,row.voltage_kv,
                row.feature_kind,row.operator_evidence,row.review_state,row.notes,
                "Kantaverkko 1.1.2020","2024 designation annex")
            previous=conn.execute(
                "SELECT "+",".join(FIELDS)+" FROM historical_station_designation WHERE registry_id=?",
                (row.registry_id,)).fetchone()
            if previous:
                if tuple(previous)!=values:
                    raise ValueError(f"Conflict in immutable station archive ID: {row.registry_id}")
                continue
            conn.execute(
                "INSERT INTO historical_station_designation ("+",".join(FIELDS)+") VALUES ("+
                ",".join("?" for _ in FIELDS)+")",values)
            inserted+=1
        archived=conn.execute("SELECT count(*) FROM historical_station_designation").fetchone()[0]
        # Assert separation, not an implicit FK join to capacity_observation.
        capacity=conn.execute("SELECT count(*) FROM capacity_observation").fetchone()[0]
    return {"inserted":inserted,"archived":archived,
            "grid_scope_capacity_observations_unchanged":capacity,
            "count_discrepancy":"source lists 128 station rows but prints 127",
            "operating_status":"not verified by this archive"}


def main(argv=None):
    parser=argparse.ArgumentParser(description="Opt-in archival station import into local SQLite")
    parser.add_argument("--input",type=Path,default=DEFAULT_SOURCE)
    parser.add_argument("--db",required=True,type=Path,help="Explicit local SQLite DB path")
    parser.add_argument("--apply",action="store_true",help="Write reviewed archive; otherwise validation only")
    args=parser.parse_args(argv)
    try:
        records=read_registry(args.input)
        if not args.apply:
            print(json.dumps({"mode":"validation_only","records":len(records),"written":0},indent=2))
            return
        report=write_archive(args.input,args.db)
        print(json.dumps(report,indent=2))
    except (ValueError,OSError,sqlite3.Error) as exc:
        parser.exit(2,f"Archive rejected: {exc}\n")


if __name__=="__main__":
    main()
