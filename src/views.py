"""Read models shared by the dashboard and tests."""
import pandas as pd


def published(conn):
    return pd.read_sql_query("SELECT * FROM published_capacity ORDER BY name,direction,effective_year,source_observed_at", conn)


def filter_capacity(frame, points=None, direction=None, years=None, snapshot=None, source=None):
    result = frame.copy()
    if points is not None:
        result = result[result["connection_point_id"].isin(points)]
    if direction:
        result = result[result["direction"] == direction]
    if years is not None:
        result = result[result["effective_year"].isin(years)]
    if snapshot:
        result = result[result["source_observed_at"] == snapshot]
    if source:
        result = result[result["source_url"] == source]
    return result


def coverage_matrix(frame, points, direction, years):
    """Blank intersections remain visibly missing; never fill, sum, or convert units."""
    output = []
    for point_id, name in points:
        for year in years:
            found = frame[(frame.connection_point_id == point_id) &
                          (frame.direction == direction) & (frame.effective_year == year)]
            values = [f"{r.capacity_value:g} {r.capacity_unit}" for r in found.itertuples()
                      if pd.notna(r.capacity_value)]
            output.append({"Connection point": name, "Year": str(year),
                           "Published estimate": "; ".join(values) if values else "not published"})
    return pd.DataFrame(output)
