"""Import source-transcribed CSV; no browser scraper and no invented defaults."""
import csv
from dataclasses import fields
from pathlib import Path
from src.db import connect, insert
from src.schema import CapacityObservation, ConnectionPoint, GridProject


def read_csv(path: Path, cls):
    result = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        expected = {f.name for f in fields(cls)}
        if set(reader.fieldnames or []) != expected:
            raise ValueError(f"{path.name}: expected columns {sorted(expected)}")
        for line, row in enumerate(reader, 2):
            try:
                if None in row or any(v is None for v in row.values()):
                    raise ValueError("Malformed CSV row")
                values = {k: v.strip() for k, v in row.items()}
                for key in ("voltage_kv", "capacity_value"):
                    if key in values:
                        values[key] = float(values[key]) if values[key] else None
                for key in ("effective_year", "commissioning_year"):
                    if key in values:
                        values[key] = int(values[key]) if values[key] else None
                for key in ("capacity_unit", "source_published_on", "confirmation_evidence_url"):
                    if key in values and not values[key]:
                        values[key] = None
                result.append(cls(**values))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"{path.name}:{line}: {exc}") from None
    return result


def ingest(directory: Path, database=None) -> dict:
    groups = [("connection_points.csv", ConnectionPoint),
              ("grid_scope_observations.csv", CapacityObservation),
              ("grid_projects.csv", GridProject)]
    # Validate all files before opening a transaction. Any conflict rolls back the whole batch.
    batches = [(name, read_csv(directory / name, cls)) for name, cls in groups]
    counts = {}
    with connect(database) as conn:
        for name, records in batches:
            counts[name] = sum(insert(conn, record) for record in records)
    return counts
