"""Conservative ENTSO-E A65/A75 parser with explicit A01/A03 block semantics."""
from datetime import datetime, timedelta
import os
from defusedxml import ElementTree as ET
from src.schema import OperationalRecord, now, utc
from .http import HttpClient, SourceError

FI_DOMAIN = "10YFI-1--------U"
GUIDE = "https://transparency.entsoe.eu/"
RESOLUTIONS = {"PT15M": timedelta(minutes=15), "PT30M": timedelta(minutes=30), "PT60M": timedelta(hours=1)}


def normalize(xml, kind, retrieved_at):
    root = ET.fromstring(xml)
    for element in root.iter():
        element.tag = element.tag.rsplit("}", 1)[-1]
    if root.tag == "Acknowledgement_MarketDocument":
        raise SourceError("ENTSO-E returned an acknowledgement rather than time series; check access and date range")
    expected = {"load": "A65", "generation": "A75"}
    if kind not in expected or root.findtext("type") != expected[kind]:
        raise ValueError("Unexpected ENTSO-E document type")
    result = []
    for series in root.findall("TimeSeries"):
        # ENTSO-E documents A01 (fixed intervals) and A03 (variable-size,
        # piecewise-constant blocks). A03 points are *change points*, not gaps.
        curve = series.findtext("curveType", "A01")
        if curve not in {"A01", "A03"}:
            raise ValueError(f"Unsupported ENTSO-E curveType {curve!r}; supported: A01, A03")
        unit = series.findtext("quantity_Measure_Unit.name")
        if unit != "MAW":
            raise ValueError("Expected ENTSO-E MAW (MW) power units")
        domain = series.findtext("inBiddingZone_Domain.mRID") or series.findtext("outBiddingZone_Domain.mRID")
        if domain != FI_DOMAIN:
            raise ValueError("Response is not for the Finland bidding zone")
        psr = series.findtext("MktPSRType/psrType")
        if kind == "generation" and not psr:
            raise ValueError("Generation series needs production type")
        flow = "consumption" if series.findtext("outBiddingZone_Domain.mRID") else "production"
        metric = "electricity_consumption" if kind == "load" else f"generation_{psr}_{flow}"
        for period in series.findall("Period"):
            start = datetime.fromisoformat(utc(period.findtext("timeInterval/start")))
            end = datetime.fromisoformat(utc(period.findtext("timeInterval/end")))
            resolution = period.findtext("resolution")
            if resolution not in RESOLUTIONS:
                raise ValueError("Unsupported ENTSO-E interval resolution")
            step = RESOLUTIONS[resolution]
            if end <= start or (end - start) % step:
                raise ValueError("ENTSO-E period must have a positive, resolution-aligned duration")
            interval_count = (end - start) // step
            positions = set()
            blocks = []
            for point in period.findall("Point"):
                position = int(point.findtext("position"))
                if position < 1 or position > interval_count or position in positions:
                    raise ValueError("Invalid or duplicate ENTSO-E point position")
                if curve == "A03" and blocks and position <= blocks[-1][0]:
                    raise ValueError("ENTSO-E A03 change points must be strictly increasing")
                positions.add(position)
                blocks.append((position, float(point.findtext("quantity"))))
            if curve == "A03" and (not blocks or blocks[0][0] != 1):
                raise ValueError("ENTSO-E A03 variable block must begin at position 1")
            for index, (position, quantity) in enumerate(blocks):
                timestamp = start + (position - 1) * step
                if curve == "A03":
                    # The next reported position is the *end* of this constant
                    # block; the final block extends to the Period's end.
                    # Store one operator-described interval, not invented
                    # 15-minute observations.
                    following = (blocks[index + 1][0] if index + 1 < len(blocks)
                                 else interval_count + 1)
                    interval_end = start + (following - 1) * step
                else:
                    # A01 readings are explicit fixed-size intervals. A
                    # missing position stays missing; never interpolate it.
                    interval_end = timestamp + step
                if interval_end <= timestamp or interval_end > end:
                    raise ValueError("Invalid ENTSO-E interval bounds")
                result.append(OperationalRecord(
                    source="entsoe", dataset_id=expected[kind], metric=metric, unit="MW",
                    value=quantity, timestamp_utc=timestamp.isoformat(),
                    interval_end_utc=interval_end.isoformat(), retrieved_at=retrieved_at, source_url=GUIDE,
                ))
    if not result:
        raise ValueError("ENTSO-E response contains no supported points")
    # Distinct periods or TimeSeries for the same metric cannot overlap, even
    # when block boundaries differ. Reject instead of overwriting or summing.
    by_metric = {}
    for record in result:
        by_metric.setdefault((record.dataset_id, record.metric), []).append(record)
    for values in by_metric.values():
        values.sort(key=lambda r: r.timestamp_utc)
        for previous, current in zip(values, values[1:]):
            if current.timestamp_utc < previous.interval_end_utc:
                raise ValueError("Overlapping ENTSO-E series require explicit reconciliation")
    return result


def fetch(kind, start, end, token=None, client=None):
    a, b = datetime.fromisoformat(utc(start)), datetime.fromisoformat(utc(end))
    if not a < b or b - a > timedelta(days=31):
        raise ValueError("Request a positive interval of at most 31 days")
    if any(d.second or d.microsecond for d in (a, b)):
        raise ValueError("ENTSO-E request boundaries must align to whole minutes")
    if kind not in {"load", "generation"}:
        raise ValueError("Supported ENTSO-E kinds: load, generation")
    key = token or os.environ.get("ENTSOE_API_TOKEN")
    if not key:
        raise SourceError("Set ENTSOE_API_TOKEN; see docs/SETUP.md")
    client, records, retrieved = client or HttpClient(), [], now()
    cursor = a
    while cursor < b:
        stop = min(cursor + timedelta(days=1), b)
        params = {"securityToken": key, "documentType": "A65" if kind == "load" else "A75",
                  "processType": "A16", "periodStart": cursor.strftime("%Y%m%d%H%M"),
                  "periodEnd": stop.strftime("%Y%m%d%H%M")}
        params["outBiddingZone_Domain" if kind == "load" else "in_Domain"] = FI_DOMAIN
        response = client.get("https://web-api.tp.entsoe.eu/api", params=params)
        records.extend(r for r in normalize(response.content, kind, retrieved)
                       if cursor <= datetime.fromisoformat(r.timestamp_utc) < stop)
        cursor = stop
    return records
