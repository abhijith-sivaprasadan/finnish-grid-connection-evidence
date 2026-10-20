"""Fingrid Open Data v1, explicitly national operational context."""
from datetime import datetime, timedelta
import os
import math
from src.schema import OperationalRecord, now, utc
from .http import HttpClient, SourceError

# Units preserved verbatim from the operator's dataset pages.
DATASETS = {
    124: ("electricity_consumption", "MWh/h"),
    74: ("electricity_production", "MWh/h"),
    # Genuine historical cross-border MARKET evidence; never a substation capacity value.
    # Dataset 31/32 signed: positive FI export, negative import. Never clamp to zero.
    31: ("commercial_flow_FI_SE1", "MW"),
    32: ("commercial_flow_FI_SE3", "MW"),
    # Unused intraday import-market space AFTER day-ahead allocation, not total
    # transmission rights, physical import capability, or dispatchable supply.
    38: ("intraday_capacity_SE1_FI", "MW"),
    39: ("intraday_capacity_SE3_FI", "MW"),
}


def integer_number(value, name, minimum=0):
    """OpenAPI uses number/double even for IDs and pagination counts."""
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value != int(value) or value < minimum):
        raise ValueError(f"Invalid Fingrid {name}: expected an integral JSON number >= {minimum}")
    return int(value)


def next_page(payload, requested_page, row_count, received_count):
    """Follow optional links/counts; use returned perPage when neither exists."""
    pagination = payload.get("pagination")
    if not isinstance(pagination, dict):
        raise ValueError("Fingrid response requires pagination metadata")
    for field in ("currentPage", "perPage", "from", "to"):
        if field not in pagination:
            raise ValueError(f"Fingrid pagination is missing {field}")
    current = integer_number(pagination["currentPage"], "currentPage", 1)
    per_page = integer_number(pagination["perPage"], "perPage", 1)
    first = integer_number(pagination["from"], "from")
    final = integer_number(pagination["to"], "to")
    if current != requested_page or per_page > 20000 or row_count > per_page or final < first:
        raise ValueError("Inconsistent Fingrid pagination metadata")
    terminal = []
    if "lastPage" in pagination:
        last = integer_number(pagination["lastPage"], "lastPage")
        if last < current and not (last == 0 and row_count == received_count == 0 and current == 1):
            raise ValueError("Fingrid lastPage precedes the current page")
        terminal.append(current >= last)
    if "nextPage" in pagination:
        next_value = pagination["nextPage"]
        if next_value is not None and integer_number(next_value, "nextPage", 1) != current + 1:
            raise ValueError("Fingrid nextPage must advance sequentially")
        terminal.append(next_value is None)
    if "total" in pagination:
        total = integer_number(pagination["total"], "total")
        if received_count > total:
            raise ValueError("Fingrid returned more rows than its stated total")
        terminal.append(received_count == total)
    if terminal and len(set(terminal)) != 1:
        raise ValueError("Conflicting Fingrid pagination counts/links; refusing a partial import")
    finished = terminal[0] if terminal else row_count < per_page
    if not finished and row_count == 0:
        raise ValueError("Empty Fingrid page before the end of the result")
    return None if finished else current + 1


def normalize(payload, dataset_id, retrieved_at):
    if dataset_id not in DATASETS:
        raise ValueError("Dataset is not in the verified dataset registry")
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("Unexpected Fingrid response: expected data array")
    metric, unit = DATASETS[dataset_id]
    rows = []
    for item in payload["data"]:
        if integer_number(item["datasetId"], "datasetId", 1) != dataset_id:
            raise ValueError("Fingrid response contains an unexpected dataset")
        if item["value"] is None:
            raise ValueError("Fingrid returned a missing value; inspect source before import")
        rows.append(OperationalRecord(
            source="fingrid", dataset_id=str(dataset_id), metric=metric, unit=unit,
            value=float(item["value"]), timestamp_utc=item["startTime"], interval_end_utc=item["endTime"],
            retrieved_at=retrieved_at, source_url=f"https://data.fingrid.fi/en/datasets/{dataset_id}",
        ))
    return rows


def fetch(dataset_id, start, end, api_key=None, client=None):
    start, end = utc(start), utc(end)
    a, b = datetime.fromisoformat(start), datetime.fromisoformat(end)
    if not a < b or b - a > timedelta(days=31):
        raise ValueError("Request a positive interval of at most 31 days")
    if dataset_id not in DATASETS:
        raise ValueError("Unknown dataset")
    key = api_key or os.environ.get("FINGRID_API_KEY")
    if not key:
        raise SourceError("Set FINGRID_API_KEY; see docs/SETUP.md")
    client = client or HttpClient()
    retrieved = now()
    result, seen, intervals = [], set(), set()
    received_count = 0
    for page in range(1, 1001):
        response = client.get(f"https://data.fingrid.fi/api/datasets/{dataset_id}/data",
            headers={"x-api-key": key}, params={"startTime": start, "endTime": end,
            "format": "json", "oneRowPerTimePeriod": "false", "pageSize": 1000,
            "page": page, "sortBy": "startTime", "sortOrder": "asc"})
        payload = response.json()
        rows = normalize(payload, dataset_id, retrieved)
        signature = tuple((r.timestamp_utc, r.interval_end_utc) for r in rows)
        if signature and signature in seen:
            raise ValueError("Fingrid repeated a page; refusing a partial import")
        seen.add(signature)
        if len(set(signature)) != len(signature) or intervals.intersection(signature):
            raise ValueError("Fingrid returned duplicate intervals across rows/pages")
        intervals.update(signature)
        received_count += len(rows)
        result.extend(r for r in rows if a <= datetime.fromisoformat(r.timestamp_utc) < b)
        if next_page(payload, page, len(rows), received_count) is None:
            return result
    raise ValueError("Pagination limit reached; split the time window")
