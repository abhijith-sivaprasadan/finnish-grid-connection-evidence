"""ENTSO-E A03/A01 interval semantics: offline operator-shaped XML only.

Specifications: ENTSO-E XML Schema Use v1.0 and curve-type code lists.
No network access, real API tokens or fabricated measured readings.
"""
from datetime import date
import pytest

from src.db import connect, insert
from src.ingest import entsoe
from src import live_entsoe

STAMP = "2026-10-17T00:00:00Z"


def point(position, quantity):
    return f"<Point><position>{position}</position><quantity>{quantity}</quantity></Point>"


def timeseries(points, *, curve="A03", start="2026-10-14T00:00Z",
               end="2026-10-14T01:00Z", resolution="PT15M",
               domain_tag="outBiddingZone_Domain.mRID", psr=""):
    psr_tag = f"<MktPSRType><psrType>{psr}</psrType></MktPSRType>" if psr else ""
    return f"""<TimeSeries>
      <curveType>{curve}</curveType>
      <quantity_Measure_Unit.name>MAW</quantity_Measure_Unit.name>
      <{domain_tag}>{entsoe.FI_DOMAIN}</{domain_tag}>
      {psr_tag}
      <Period>
        <timeInterval><start>{start}</start><end>{end}</end></timeInterval>
        <resolution>{resolution}</resolution>
        {points}
      </Period>
    </TimeSeries>"""


def document(*series, kind="A65"):
    return f'<GL_MarketDocument xmlns="urn:test-only"><type>{kind}</type>{"".join(series)}</GL_MarketDocument>'


def test_a03_has_explicit_variable_sized_intervals_without_made_up_points(tmp_path):
    xml = document(timeseries(point(1, 100) + point(3, 250)))
    rows = entsoe.normalize(xml, "load", STAMP)
    assert len(rows) == 2
    assert [r.value for r in rows] == [100, 250]
    assert [(r.timestamp_utc, r.interval_end_utc) for r in rows] == [
        ("2026-10-14T00:00:00.000000Z", "2026-10-14T00:30:00.000000Z"),
        ("2026-10-14T00:30:00.000000Z", "2026-10-14T01:00:00.000000Z"),
    ]
    assert all(r.metric == "electricity_consumption" and r.unit == "MW" for r in rows)
    with connect(tmp_path / "a03.sqlite") as conn:
        assert sum(insert(conn, row) for row in rows) == 2
        assert conn.execute("SELECT count(*) FROM operational_series").fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM capacity_observation").fetchone()[0] == 0


def test_a03_single_point_covers_entire_period_not_just_one_resolution_step():
    xml = document(timeseries(point(1, 54)))
    rows = entsoe.normalize(xml, "load", STAMP)
    assert len(rows) == 1
    assert rows[0].timestamp_utc == "2026-10-14T00:00:00.000000Z"
    assert rows[0].interval_end_utc == "2026-10-14T01:00:00.000000Z"


def test_a03_starts_and_ends_respect_change_positions():
    xml = document(timeseries(point(1, 10) + point(4, 20)))
    rows = entsoe.normalize(xml, "load", STAMP)
    assert [(r.timestamp_utc, r.interval_end_utc) for r in rows] == [
        ("2026-10-14T00:00:00.000000Z", "2026-10-14T00:45:00.000000Z"),
        ("2026-10-14T00:45:00.000000Z", "2026-10-14T01:00:00.000000Z"),
    ]


def test_a03_generation_keeps_psr_identity_and_source_intervals():
    xml = document(timeseries(point(1, 50), domain_tag="inBiddingZone_Domain.mRID",
                              psr="B16"), kind="A75")
    rows = entsoe.normalize(xml, "generation", STAMP)
    assert len(rows) == 1
    assert rows[0].dataset_id == "A75"
    assert rows[0].metric == "generation_B16_production"
    assert rows[0].unit == "MW"


def test_a01_sparse_positions_remain_sparse_no_interpolation():
    xml = document(timeseries(point(1, 10) + point(3, 20), curve="A01"))
    rows = entsoe.normalize(xml, "load", STAMP)
    assert len(rows) == 2
    assert rows[0].interval_end_utc == "2026-10-14T00:15:00.000000Z"
    assert rows[1].timestamp_utc == "2026-10-14T00:30:00.000000Z"


@pytest.mark.parametrize(("points", "pattern"), [
    (point(2, 10), "begin at position 1"),
    (point(1, 1) + point(3, 3) + point(2, 2), "strictly increasing"),
    (point(1, 1) + point(1, 2), "duplicate"),
    (point(1, 1) + point(5, 2), "Invalid or duplicate"),
    ("", "begin at position 1"),
])
def test_a03_invalid_positions_fail_instead_of_filling_blanks(points, pattern):
    with pytest.raises(ValueError, match=pattern):
        entsoe.normalize(document(timeseries(points)), "load", STAMP)


@pytest.mark.parametrize(("curve", "pattern"), [
    ("A02", "Unsupported ENTSO-E curveType 'A02'"),
    ("A04", "Unsupported ENTSO-E curveType 'A04'"),
    ("A05", "Unsupported ENTSO-E curveType 'A05'"),
])
def test_other_curve_types_fail_with_safe_code_only(curve, pattern):
    with pytest.raises(ValueError, match=pattern):
        entsoe.normalize(document(timeseries(point(1, 10), curve=curve)), "load", STAMP)


@pytest.mark.parametrize(("start", "end"), [
    ("2026-10-14T01:00Z", "2026-10-14T01:00Z"),
    ("2026-10-14T01:00Z", "2026-10-14T00:00Z"),
    ("2026-10-14T00:00Z", "2026-10-14T00:50Z"),
])
def test_a03_rejects_unaligned_or_negative_periods(start, end):
    with pytest.raises(ValueError, match="resolution-aligned"):
        entsoe.normalize(document(timeseries(point(1, 10), start=start, end=end)),
                         "load", STAMP)


def test_overlap_with_different_interval_end_is_rejected():
    data = document(
        timeseries(point(1, 10)),
        timeseries(point(1, 20), curve="A01"),
    )
    with pytest.raises(ValueError, match="Overlapping ENTSO-E"):
        entsoe.normalize(data, "load", STAMP)


def test_adjacent_non_overlapping_periods_are_valid():
    data = document(
        timeseries(point(1, 10), end="2026-10-14T00:30Z"),
        timeseries(point(1, 20), start="2026-10-14T00:30Z",
                   end="2026-10-14T01:00Z"),
    )
    rows = entsoe.normalize(data, "load", STAMP)
    assert len(rows) == 2
    assert rows[0].interval_end_utc == rows[1].timestamp_utc


def test_live_smoke_accepts_a03_as_temp_db_context_not_substation_capacity(monkeypatch):
    monkeypatch.setenv("ENTSOE_API_TOKEN", "ONLY_A_TEST_TOKEN")
    xml = document(timeseries(point(1, 100) + point(3, 150)))
    result = live_entsoe.live_smoke(
        day="2026-10-14", kind="load", today=date(2026, 10, 17),
        getter=lambda *args: entsoe.normalize(xml, "load", STAMP))
    assert result["records"] == result["inserted"] == 2
    assert result["metrics"] == ["electricity_consumption"]
    assert result["persistence"] == "temporary database deleted after check"
