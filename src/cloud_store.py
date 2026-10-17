"""Neon/PostgreSQL adapter for the public read-only dashboard and private collector.

Never place a connection URL in a log, exception, table, or repository.
The collector and the dashboard must use different database roles.
Local SQLite remains the source for typed ingestion and offline tests.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

# These tables mirror the verified SQLite evidence types, not the operators'
# network models. Application users receive SELECT only, never CREATE/INSERT.
DDL = (
    """CREATE TABLE IF NOT EXISTS connection_point (
        connection_point_id TEXT PRIMARY KEY, operator TEXT NOT NULL,
        name TEXT NOT NULL, voltage_kv DOUBLE PRECISION,
        source_url TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS capacity_observation (
        observation_id TEXT PRIMARY KEY,
        connection_point_id TEXT NOT NULL REFERENCES connection_point,
        direction TEXT NOT NULL CHECK (direction IN ('consumption','production')),
        effective_year INTEGER,
        capacity_value DOUBLE PRECISION NOT NULL CHECK (capacity_value >= 0),
        capacity_unit TEXT NOT NULL CHECK (capacity_unit IN ('MW','MVA')),
        capacity_status TEXT NOT NULL CHECK (capacity_status IN
            ('published_indicative','operator_confirmed')),
        source_url TEXT NOT NULL, source_observed_at TEXT NOT NULL,
        validity_notes TEXT NOT NULL, source_published_on TEXT,
        confirmation_evidence_url TEXT,
        CHECK (capacity_status <> 'operator_confirmed'
          OR confirmation_evidence_url IS NOT NULL))""",
    """CREATE TABLE IF NOT EXISTS operational_series (
        source TEXT NOT NULL CHECK (source IN ('fingrid','entsoe')),
        dataset_id TEXT NOT NULL, metric TEXT NOT NULL, unit TEXT NOT NULL,
        value DOUBLE PRECISION NOT NULL, timestamp_utc TEXT NOT NULL,
        interval_end_utc TEXT NOT NULL, retrieved_at TEXT NOT NULL,
        source_url TEXT NOT NULL, area TEXT NOT NULL CHECK (area='FI'),
        evidence_category TEXT NOT NULL DEFAULT 'operational_context'
          CHECK (evidence_category='operational_context'),
        PRIMARY KEY (source,dataset_id,metric,area,timestamp_utc,
                     interval_end_utc,retrieved_at))""",
    """CREATE TABLE IF NOT EXISTS grid_project (
        project_id TEXT PRIMARY KEY, name TEXT NOT NULL,
        commissioning_year INTEGER, uncertainty TEXT NOT NULL,
        source_url TEXT NOT NULL, source_observed_at TEXT NOT NULL,
        validity_notes TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS scenario_result (
        scenario_id TEXT PRIMARY KEY, model_version TEXT NOT NULL,
        assumption_set TEXT NOT NULL, metric TEXT NOT NULL,
        value DOUBLE PRECISION NOT NULL, unit TEXT NOT NULL,
        created_at TEXT NOT NULL, capacity_status TEXT NOT NULL
          CHECK (capacity_status='model_scenario'))""",
    """CREATE OR REPLACE VIEW published_capacity AS
        SELECT c.*, p.name, p.operator, p.voltage_kv
        FROM capacity_observation AS c
        JOIN connection_point AS p USING (connection_point_id)
        WHERE c.capacity_status='published_indicative'""",
    """CREATE OR REPLACE VIEW latest_operational AS
        SELECT * FROM (
            SELECT *, row_number() OVER
            (PARTITION BY source,dataset_id,metric,area,timestamp_utc,interval_end_utc
             ORDER BY retrieved_at DESC) AS revision_rank
            FROM operational_series
        ) AS t WHERE revision_rank=1""",
)

# No arbitrary SQL or arbitrary table names enter this module.
TABLE_KEYS = {
    "connection_point": ("connection_point_id",),
    "capacity_observation": ("observation_id",),
    "operational_series": ("source", "dataset_id", "metric", "area",
                           "timestamp_utc", "interval_end_utc", "retrieved_at"),
    "grid_project": ("project_id",),
    "scenario_result": ("scenario_id",),
}
READ_SQL = {
    "capacity": "SELECT * FROM published_capacity ORDER BY name,direction,effective_year,source_observed_at",
    "points": "SELECT * FROM connection_point ORDER BY name",
    # Cap read volume to protect the free database and Streamlit app. Latest
    # 14 days are displayed; full history stays in persistent PostgreSQL.
    "context": """SELECT * FROM latest_operational
        WHERE timestamp_utc >= :earliest
        ORDER BY timestamp_utc DESC LIMIT 12000""",
    "projects": "SELECT * FROM grid_project",
    "scenarios": "SELECT * FROM scenario_result",
}
READ_TABLES = ("capacity_observation", "connection_point", "operational_series",
               "grid_project", "scenario_result")


def engine_for(url: str):
    """Only PostgreSQL is accepted: prevent accidental SQLite cloud writes."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Missing PostgreSQL connection configuration")
    parsed = make_url(url)
    if parsed.drivername not in ("postgresql", "postgresql+psycopg"):
        raise ValueError("Only PostgreSQL URLs are supported for hosted mode")
    if parsed.drivername == "postgresql":
        parsed = parsed.set(drivername="postgresql+psycopg")
    # Network encryption is mandatory for the free hosted database.
    if parsed.query.get("sslmode", "require") != "require":
        raise ValueError("Hosted PostgreSQL must use sslmode=require")
    return create_engine(parsed.update_query_dict({"sslmode": "require"}),
                         pool_pre_ping=True, pool_size=1, max_overflow=1,
                         connect_args={"connect_timeout": 15})


def collect_sqlite_rows(conn) -> dict:
    """Copy SQLite evidence without exporting a local database file to Git."""
    return {table: [dict(row) for row in conn.execute(f"SELECT * FROM {table}")]
            for table in TABLE_KEYS}


def mirror(engine, batches: dict) -> dict:
    """Append-only, all-or-nothing upload of typed evidence to PostgreSQL.

    A duplicate immutable ID with changed fields is an error rather than
    silently overwriting the historical capture. Same-source re-fetches with
    a new retrieval timestamp are stored as distinct revisions.
    """
    if set(batches) != set(TABLE_KEYS):
        raise ValueError("Cloud mirror requires all five typed evidence categories")
    result = {}
    with engine.begin() as db:
        for ddl in DDL:
            db.execute(text(ddl))
        for table, pk in TABLE_KEYS.items():
            records = batches[table]
            inserted = 0
            for record in records:
                keys = list(record)
                if not keys or any(k.startswith("_") or not k.isidentifier() for k in keys):
                    raise ValueError("Unsafe evidence schema in cloud mirror")
                # Column names originate from the fixed typed SQLite schema,
                # not a web request or caller-controlled filter.
                placeholders = ", ".join(":" + k for k in keys)
                cols = ", ".join(keys)
                added = db.execute(text(
                    f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) "
                    "ON CONFLICT DO NOTHING RETURNING 1"
                ), record).first()
                if added:
                    inserted += 1
                    continue
                clause = " AND ".join(k + "=:" + k for k in pk)
                existing = db.execute(text(f"SELECT {cols} FROM {table} WHERE {clause}"),
                                      {k: record[k] for k in pk}).mappings().one_or_none()
                if existing is None or any(existing[k] != record[k] for k in keys):
                    raise ValueError("Conflicting immutable published evidence; cloud rollback")
            result[table] = {"submitted": len(records), "inserted": inserted}
    return result


def read_snapshot(engine, *, today=None) -> dict:
    """Read the hosted database through a SELECT-only connection.

    Never report 'verified operator values' just because a DB contains rows.
    """
    today = today or datetime.now(timezone.utc)
    earliest = (today - timedelta(days=14)).isoformat(timespec="microseconds").replace("+00:00", "Z")
    with engine.connect() as db:
        frames = {}
        for name, query in READ_SQL.items():
            values = {"earliest": earliest} if name == "context" else {}
            frames[name] = pd.read_sql_query(text(query), db, params=values)
        counts = {table: db.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
                  for table in READ_TABLES}
    # Keeps quality reporting honest even when the operator's numeric map
    # has not been independently re-opened and all source values are pending.
    sources = set(frames["context"]["source"].dropna()) if not frames["context"].empty else set()
    issues = ["Grid Scope numeric observations are source transcriptions; independent source-value verification is pending"]
    if not sources:
        issues.append("No operational observations found within the last 14 days")
    else:
        for required in ("fingrid", "entsoe"):
            if required not in sources:
                issues.append(f"No recent {required} operational observations")
    frames["quality"] = {
        "counts": counts, "issues": issues,
        "source_values_independently_verified": False,
        "hosted_source_data_recent": sources == {"fingrid", "entsoe"},
        "mvp_data_ready": False,  # Not scientifically sign-off ready.
    }
    return frames
