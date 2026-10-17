"""Versioned SQLite schema; immutable evidence and idempotent ingestion."""
from contextlib import contextmanager
from dataclasses import asdict
import os
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "evidence.sqlite"

DDL = """
CREATE TABLE connection_point (
 connection_point_id TEXT PRIMARY KEY, operator TEXT NOT NULL, name TEXT NOT NULL,
 voltage_kv REAL CHECK(voltage_kv > 0), source_url TEXT NOT NULL
);
CREATE TABLE capacity_observation (
 observation_id TEXT PRIMARY KEY,
 connection_point_id TEXT NOT NULL REFERENCES connection_point,
 direction TEXT NOT NULL CHECK(direction IN ('consumption','production')),
 effective_year INTEGER CHECK(effective_year BETWEEN 1900 AND 2200),
 capacity_value REAL NOT NULL CHECK(capacity_value >= 0),
 capacity_unit TEXT NOT NULL CHECK(capacity_unit IN ('MW','MVA')),
 capacity_status TEXT NOT NULL CHECK(capacity_status IN ('published_indicative','operator_confirmed')),
 source_url TEXT NOT NULL, source_observed_at TEXT NOT NULL, validity_notes TEXT NOT NULL,
 source_published_on TEXT, confirmation_evidence_url TEXT,
 CHECK(capacity_status != 'operator_confirmed' OR
       (confirmation_evidence_url IS NOT NULL AND length(confirmation_evidence_url) > 0))
);
CREATE UNIQUE INDEX capacity_snapshot ON capacity_observation
 (connection_point_id, direction, coalesce(effective_year, -1), source_observed_at, source_url);
CREATE TABLE grid_project (
 project_id TEXT PRIMARY KEY, name TEXT NOT NULL, commissioning_year INTEGER,
 uncertainty TEXT NOT NULL, source_url TEXT NOT NULL, source_observed_at TEXT NOT NULL,
 validity_notes TEXT NOT NULL
);
CREATE TABLE project_connection_point (
 project_id TEXT REFERENCES grid_project, connection_point_id TEXT REFERENCES connection_point,
 relationship_source_url TEXT NOT NULL, PRIMARY KEY(project_id, connection_point_id)
);
CREATE TABLE operational_series (
 source TEXT NOT NULL CHECK(source IN ('fingrid','entsoe')), dataset_id TEXT NOT NULL,
 metric TEXT NOT NULL, unit TEXT NOT NULL, value REAL NOT NULL,
 timestamp_utc TEXT NOT NULL, interval_end_utc TEXT NOT NULL, retrieved_at TEXT NOT NULL,
 source_url TEXT NOT NULL, area TEXT NOT NULL CHECK(area='FI'),
 evidence_category TEXT NOT NULL DEFAULT 'operational_context' CHECK(evidence_category='operational_context'),
 PRIMARY KEY(source,dataset_id,metric,area,timestamp_utc,interval_end_utc,retrieved_at)
);
CREATE TABLE scenario_result (
 scenario_id TEXT PRIMARY KEY, model_version TEXT NOT NULL, assumption_set TEXT NOT NULL,
 metric TEXT NOT NULL, value REAL NOT NULL, unit TEXT NOT NULL, created_at TEXT NOT NULL,
 capacity_status TEXT NOT NULL CHECK(capacity_status='model_scenario')
);
CREATE VIEW published_capacity AS SELECT c.*, p.name, p.operator, p.voltage_kv
 FROM capacity_observation c JOIN connection_point p USING(connection_point_id)
 WHERE c.capacity_status='published_indicative';
CREATE VIEW latest_operational AS SELECT * FROM (
 SELECT *, row_number() OVER (PARTITION BY source,dataset_id,metric,area,timestamp_utc,interval_end_utc
 ORDER BY retrieved_at DESC) AS revision_rank FROM operational_series
) WHERE revision_rank=1;
PRAGMA user_version = 2;
"""


def db_path(path=None) -> Path:
    return Path(path or os.environ.get("GRID_EVIDENCE_DB") or DEFAULT_DB).resolve()


@contextmanager
def connect(path=None):
    target = db_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version > 2:
            raise ValueError("Database schema is newer than this application")
        if version == 0:
            conn.executescript("BEGIN;\n" + DDL + "\nCOMMIT;")
        elif version == 1:
            invalid = conn.execute("SELECT COUNT(*) FROM capacity_observation WHERE capacity_value IS NULL OR capacity_unit IS NULL").fetchone()[0]
            if invalid:
                raise ValueError(f"Legacy database contains {invalid} blank capacity observations; review/remove them before schema v2 migration")
            # Migrate real v1 databases without discarding observations or historical snapshots.
            new_ddl = DDL.split("CREATE TABLE capacity_observation (", 1)[1].split("CREATE UNIQUE INDEX", 1)[0]
            new_table = "CREATE TABLE capacity_observation_v2 (" + new_ddl.replace("capacity_observation (", "capacity_observation_v2 (")
            cols = [r[1] for r in conn.execute("PRAGMA table_info(capacity_observation)")]
            sqlcols = ",".join(cols)
            conn.executescript("BEGIN;\nDROP VIEW IF EXISTS published_capacity;\n" + new_table +
                f"INSERT INTO capacity_observation_v2 ({sqlcols}) SELECT {sqlcols} FROM capacity_observation;\n" +
                "DROP TABLE capacity_observation;\nALTER TABLE capacity_observation_v2 RENAME TO capacity_observation;\n" +
                "CREATE UNIQUE INDEX capacity_snapshot ON capacity_observation "
                "(connection_point_id, direction, coalesce(effective_year, -1), source_observed_at, source_url);\n" +
                "CREATE VIEW published_capacity AS SELECT c.*, p.name, p.operator, p.voltage_kv "
                "FROM capacity_observation c JOIN connection_point p USING(connection_point_id) "
                "WHERE c.capacity_status='published_indicative';\n"
                "PRAGMA user_version = 2;\nCOMMIT;")
        with conn:
            yield conn
    finally:
        conn.close()


TABLES = {
    "ConnectionPoint": ("connection_point", "connection_point_id"),
    "CapacityObservation": ("capacity_observation", "observation_id"),
    "GridProject": ("grid_project", "project_id"),
    "ScenarioResult": ("scenario_result", "scenario_id"),
    "OperationalRecord": ("operational_series", None),
}


def insert(conn, record) -> bool:
    table, key = TABLES[type(record).__name__]
    values = asdict(record)
    if key:
        existing = conn.execute(f"SELECT * FROM {table} WHERE {key}=?", (values[key],)).fetchone()
        if existing:
            if any(existing[k] != v for k, v in values.items()):
                raise ValueError(f"Conflicting immutable {table} record: {values[key]}; capture a new snapshot")
            return False
    else:
        keys = [k for k in values if k not in {"value", "unit", "source_url"}]
        existing = conn.execute(
            "SELECT * FROM operational_series WHERE " + " AND ".join(f"{k}=?" for k in keys),
            [values[k] for k in keys],
        ).fetchone()
        if existing:
            if any(existing[k] != v for k, v in values.items()):
                raise ValueError("Conflicting operational revision")
            return False
    conn.execute(f"INSERT INTO {table} ({','.join(values)}) VALUES ({','.join('?' for _ in values)})", list(values.values()))
    return True
