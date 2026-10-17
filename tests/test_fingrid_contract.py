"""Synthetic/test-only responses shaped by the user-supplied OpenAPI 1.0 export."""
import pytest
from src.ingest import fingrid
from src.ingest.http import HttpClient
from tests.test_clients import Session, Response, payload, STAMP


def page(data=None, **metadata):
    result = payload() if data is None else {"data": data}
    result["pagination"] = dict(currentPage=1.0, perPage=1.0, **{"from": 0.0, "to": 1.0})
    result["pagination"].update(metadata)
    return result


def test_next_page_without_last_page_uses_returned_page_size():
    first = page()
    second = page(data=[], currentPage=2.0, **{"from": 1.0, "to": 1.0})
    session = Session([Response(first), Response(second)])
    rows = fingrid.fetch(124, STAMP, "2026-10-17T00:00:00Z", "TEST-ONLY",
                         HttpClient(session, sleep=lambda _: None))
    assert len(rows) == 1
    assert len(session.calls) == 2  # Requested 1000 but server reports one per page.
    assert session.calls[0][1]["params"]["oneRowPerTimePeriod"] == "false"
    assert "x-api-key" not in session.calls[0][1]["params"]


def test_optional_next_page_and_total():
    assert fingrid.next_page(page(nextPage=2.0, total=2.0), 1, 1, 1) == 2
    assert fingrid.next_page(page(nextPage=None, total=1.0), 1, 1, 1) is None


def test_empty_result_with_zero_last_page():
    response = page(data=[], lastPage=0.0, total=0.0, nextPage=None, **{"to": 0.0})
    assert fingrid.next_page(response, 1, 0, 0) is None


@pytest.mark.parametrize("metadata", [
    {"lastPage": 1.5}, {"lastPage": True}, {"nextPage": 1.0},
    {"currentPage": 2.0}, {"perPage": 0}, {"lastPage": 2, "nextPage": None},
    {"lastPage": 1, "total": 2}, {"total": float("nan")},
])
def test_inconsistent_metadata_is_rejected(metadata):
    with pytest.raises(ValueError):
        fingrid.next_page(page(**metadata), 1, 1, 1)


def test_missing_required_pagination_is_rejected():
    with pytest.raises(ValueError, match="requires pagination"):
        fingrid.next_page(payload(), 1, 1, 1)


def test_documented_timestamp_format_and_integral_dataset_id():
    data = payload("2023-06-28T12:15:00.0000000+00:00", "2023-06-28T12:30:00.0000000+00:00")
    data["data"][0]["datasetId"] = 124.0
    row = fingrid.normalize(data, 124, STAMP)[0]
    assert row.timestamp_utc == "2023-06-28T12:15:00.000000Z"
    data["data"][0]["datasetId"] = 124.5
    with pytest.raises(ValueError):
        fingrid.normalize(data, 124, STAMP)


def test_source_url_cannot_store_query_api_key():
    from src.schema import url
    with pytest.raises(ValueError):
        url("https://data.fingrid.fi/api/data?x-api-key=TEST-ONLY")
