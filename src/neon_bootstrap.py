"""Safely initialize the existing Neon PostgreSQL schema and public sample.

Only run after explicitly choosing the manual GitHub Actions workflow. It does
not enable source polling, create a Neon project, or deploy Streamlit.
"""
from __future__ import annotations

import os
from src.cloud_store import collect_sqlite_rows, engine_for, mirror, read_snapshot
from src.db import ROOT, connect
from src.ingest.manual_grid_scope import ingest
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import datetime, timezone


def bootstrap(url, *, local_path=None):
    if not url:
        raise ValueError("Database connection URL not configured")
    engine = engine_for(url)
    try:
        with TemporaryDirectory(prefix="neon-grid-bootstrap-") as folder:
            source = local_path or (Path(folder) / "evidence.sqlite")
            ingest(ROOT / "data" / "manual", source)
            with connect(source) as local:
                batches = collect_sqlite_rows(local)
            expected_capacity = len(batches["capacity_observation"])
            expected_points = len(batches["connection_point"])
            counts = mirror(engine, batches)
        snap = read_snapshot(engine, today=datetime.now(timezone.utc))
        if len(snap["capacity"]) < expected_capacity or len(snap["points"]) < expected_points:
            raise ValueError("Neon mirror readback does not cover the committed sample")
        return {
            "status": "neon_schema_and_sample_readback_passed",
            "points": len(snap["points"]),
            "indicative_capacity_observations": len(snap["capacity"]),
            "operational_rows_recent": len(snap["context"]),
            "inserted": {k: v["inserted"] for k,v in counts.items()},
            "source_value_reverification": "pending_independent_source_audit",
            "public_streamlit_deployed": False,
        }
    finally:
        engine.dispose()


def main():
    import json
    try:
        report = bootstrap(os.getenv("DATABASE_WRITE_URL"))
    except Exception:
        # Database libraries sometimes embed passwords in exception details.
        raise SystemExit("Neon database bootstrap failed. Inspect project/branch, "
                         "owner role and provider status without exposing credentials.")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
