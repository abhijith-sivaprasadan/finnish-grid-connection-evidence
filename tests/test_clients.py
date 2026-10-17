"""Synthetic/test-only API payloads. No live source claims from these fixtures."""
import requests
import pytest
from src.ingest.http import HttpClient, SourceError
from src.ingest import fingrid, entsoe
from src.db import connect, insert
from src.schema import OperationalRecord

STAMP = "2026-10-16T00:00:00Z"


def payload(start=STAMP, end="2026-10-16T00:15:00Z", value=10):
    return {"data": [{"datasetId": 124, "startTime": start, "endTime": end, "value": value}]}


class Response:
    def __init__(self, data=None, status=200, headers=None):
        self.data, self.status_code, self.headers = data, status, headers or {}

    def json(self):
        return self.data


class Session:
    def __init__(self, replies):
        self.replies, self.calls = iter(replies), []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        result = next(self.replies)
        if isinstance(result, Exception):
            raise result
        return result


def test_fingrid_pagination_and_units():
    one, two = payload(), payload("2026-10-16T00:15:00Z", "2026-10-16T00:30:00Z", 20)
    one["pagination"] = {"lastPage": 2.0, "currentPage": 1.0, "perPage": 1.0, "from": 0.0, "to": 1.0}
    two["pagination"] = {"lastPage": 2.0, "currentPage": 2.0, "perPage": 1.0, "from": 1.0, "to": 2.0}
    session, sleeps = Session([Response(one), Response(two)]), []
    client = HttpClient(session, sleep=sleeps.append, clock=lambda: 0)
    result = fingrid.fetch(124, STAMP, "2026-10-17T00:00:00Z", "TEST-ONLY", client)
    assert [r.value for r in result] == [10, 20]
    assert all(r.unit == "MWh/h" and r.area == "FI" for r in result)
    assert session.calls[1][1]["params"]["page"] == 2
    assert session.calls[0][1]["headers"] == {"x-api-key": "TEST-ONLY"}
    assert sleeps == [2.1]


def test_repeated_page_fails_instead_of_silent_partial_result():
    one = payload()
    one["pagination"] = {"lastPage": 3, "currentPage": 1, "perPage": 1, "from": 0, "to": 1}
    client = HttpClient(Session([Response(one), Response(one)]), sleep=lambda _: None)
    with pytest.raises(ValueError, match="repeated a page"):
        fingrid.fetch(124, STAMP, "2026-10-17T00:00:00Z", "TEST-ONLY", client)


@pytest.mark.parametrize("data", [payload(value=None), payload(value=float("nan")), {"data": [{"datasetId": 999}]}])
def test_fingrid_invalid_data_fails(data):
    with pytest.raises(ValueError):
        fingrid.normalize(data, 124, STAMP)


def test_retry_and_error_does_not_leak_token():
    session = Session([Response(status=429, headers={"Retry-After": "3"}), Response(payload())])
    delays = []
    assert HttpClient(session, sleep=delays.append).get("https://example.org/test").status_code == 200
    assert 3 in delays
    session = Session([requests.ConnectionError("secret-token-url")] * 4)
    with pytest.raises(SourceError) as error:
        HttpClient(session, sleep=lambda _: None).get("https://example.org/test")
    assert "secret" not in str(error.value)


def xml(points, curve="A01", unit="MAW", kind="A65", psr="", domain=entsoe.FI_DOMAIN):
    return f'''<GL_MarketDocument xmlns="urn:test-only"><type>{kind}</type><TimeSeries>
    <curveType>{curve}</curveType><quantity_Measure_Unit.name>{unit}</quantity_Measure_Unit.name>
    <outBiddingZone_Domain.mRID>{domain}</outBiddingZone_Domain.mRID>{psr}
    <Period><timeInterval><start>2026-10-16T00:00Z</start><end>2026-10-16T01:00Z</end></timeInterval>
    <resolution>PT15M</resolution>{points}</Period></TimeSeries></GL_MarketDocument>'''


def test_entsoe_positions_and_gaps_preserved():
    points = '<Point><position>1</position><quantity>10</quantity></Point><Point><position>3</position><quantity>30</quantity></Point>'
    rows = entsoe.normalize(xml(points), "load", STAMP)
    assert len(rows) == 2
    assert rows[1].timestamp_utc == "2026-10-16T00:30:00.000000Z"
    assert rows[1].interval_end_utc == "2026-10-16T00:45:00.000000Z"
    assert rows[0].unit == "MW"


@pytest.mark.parametrize("kwargs", [{"curve": "A04"}, {"unit": "MWH"}, {"domain": "WRONG-ZONE"}])
def test_entsoe_unsupported_semantics_rejected(kwargs):
    with pytest.raises(ValueError):
        entsoe.normalize(xml('<Point><position>1</position><quantity>10</quantity></Point>', **kwargs), "load", STAMP)


def test_entsoe_acknowledgement_and_duplicate_points():
    with pytest.raises(SourceError):
        entsoe.normalize('<Acknowledgement_MarketDocument/>', "load", STAMP)
    point = '<Point><position>1</position><quantity>10</quantity></Point>'
    with pytest.raises(ValueError, match="duplicate"):
        entsoe.normalize(xml(point + point), "load", STAMP)


def test_context_revisions_remain_separate_from_capacity(tmp_path):
    original = fingrid.normalize(payload(), 124, STAMP)[0]
    revised = fingrid.normalize(payload(value=11), 124, "2026-10-17T00:00:00Z")[0]
    with connect(tmp_path / "db") as conn:
        assert insert(conn, original)
        assert not insert(conn, original)
        insert(conn, revised)
        assert conn.execute("SELECT count(*) FROM operational_series").fetchone()[0] == 2
        assert conn.execute("SELECT value FROM latest_operational").fetchone()[0] == 11
        assert conn.execute("SELECT count(*) FROM capacity_observation").fetchone()[0] == 0


def test_no_credentials_has_clear_error(monkeypatch):
    monkeypatch.delenv("FINGRID_API_KEY", raising=False)
    monkeypatch.delenv("ENTSOE_API_TOKEN", raising=False)
    with pytest.raises(SourceError, match="FINGRID_API_KEY"):
        fingrid.fetch(124, STAMP, "2026-10-17T00:00:00Z")
    with pytest.raises(SourceError, match="ENTSOE_API_TOKEN"):
        entsoe.fetch("load", STAMP, "2026-10-17T00:00:00Z")
