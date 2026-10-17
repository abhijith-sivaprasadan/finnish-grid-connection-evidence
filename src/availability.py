"""Comparison views for published indicative connection capacity.

Never invent missing years, add capacities across network nodes, conflate
consumption/production or silently reconcile different source snapshots.
"""
from __future__ import annotations

import pandas as pd

DIRECTIONS = ("consumption", "production")

COLUMNS = [
    "Point ID", "Connection point", "Direction", "Year",
    "Published estimate", "Evidence", "Value", "Unit",
    "Observation ID", "Source capture UTC", "Source URL",
]


def comparison_grid(capacity: pd.DataFrame, points: pd.DataFrame,
                    years, *, snapshot: str | None = None,
                    source: str | None = None) -> pd.DataFrame:
    """One source-evidence status for every point × direction × selected year.

    At each intersection, show only a unique observed number; multiple
    records (even with the same value) need a human review. A missing cell is
    *not published in the selection*, never zero MW.
    """
    if any(c not in points.columns for c in ("connection_point_id", "name")):
        raise ValueError("Comparison points need connection_point_id and name")
    if any(c not in capacity.columns for c in (
        "connection_point_id", "direction", "effective_year",
        "capacity_value", "capacity_unit", "observation_id",
        "source_observed_at", "source_url",
    )):
        raise ValueError("Comparison requires source-linked published observations")
    years = list(years)
    if any(type(y) is not int for y in years) or len(years) != len(set(years)):
        raise ValueError("Choose distinct integer effective years")
    if points["connection_point_id"].duplicated().any():
        raise ValueError("Comparison point IDs must be unique")
    records = capacity
    if snapshot is not None:
        records = records[records["source_observed_at"] == snapshot]
    elif not records.empty:
        # Never combine different capture sessions and call them one curve.
        newest = max(records["source_observed_at"])
        records = records[records["source_observed_at"] == newest]
    if source is not None:
        records = records[records["source_url"] == source]

    rows = []
    for point in points[["connection_point_id", "name"]].itertuples(index=False, name=None):
        point_id, name = point
        for direction in DIRECTIONS:
            same_point = records[(records["connection_point_id"] == point_id) &
                                 (records["direction"] == direction)]
            for year in years:
                observations = same_point[same_point["effective_year"] == year]
                common = {
                    "Point ID": point_id,
                    "Connection point": name,
                    "Direction": direction,
                    "Year": year,
                }
                if len(observations) == 0:
                    rows.append({
                        **common,
                        "Published estimate": "not published in selected snapshot",
                        "Evidence": "missing_in_selection",
                        "Value": None,
                        "Unit": None,
                        "Observation ID": None,
                        "Source capture UTC": None,
                        "Source URL": None,
                    })
                    continue
                if len(observations) > 1:
                    rows.append({
                        **common,
                        "Published estimate": "multiple observations — review source",
                        "Evidence": "requires_reconciliation",
                        "Value": None,
                        "Unit": None,
                        "Observation ID": None,
                        "Source capture UTC": snapshot or observations.iloc[0]["source_observed_at"],
                        "Source URL": None,
                    })
                    continue
                o = observations.iloc[0]
                rows.append({
                    **common,
                    "Published estimate": f"{o['capacity_value']:g} {o['capacity_unit']}",
                    "Evidence": "published_indicative",
                    "Value": float(o["capacity_value"]),
                    "Unit": str(o["capacity_unit"]),
                    "Observation ID": o["observation_id"],
                    "Source capture UTC": o["source_observed_at"],
                    "Source URL": o["source_url"],
                })
    return pd.DataFrame(rows, columns=COLUMNS)


def coverage_summary(grid: pd.DataFrame) -> dict:
    """Coverage counts only, not a sum of point capacities."""
    counts = grid["Evidence"].value_counts() if not grid.empty else {}
    return {
        "intersections": len(grid),
        "published": int(counts.get("published_indicative", 0)),
        "not_published_in_selection": int(counts.get("missing_in_selection", 0)),
        "needs_reconciliation": int(counts.get("requires_reconciliation", 0)),
    }
