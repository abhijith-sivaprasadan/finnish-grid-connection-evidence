"""Conservative ENTSO-E A65/A75 parser. Unsupported curve types fail explicitly."""
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
        if series.findtext("curveType", "A01") != "A01":
            raise ValueError("Only explicit sequential A01 points are supported; no gap interpolation")
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
            step, positions = RESOLUTIONS[resolution], set()
            for point in period.findall("Point"):
                position = int(point.findtext("position"))
                if position < 1 or position in positions:
                    raise ValueError("Invalid or duplicate ENTSO-E point position")
                positions.add(position)
                timestamp = start + (position - 1) * step
                if timestamp + step > end:
                    raise ValueError("ENTSO-E point exceeds period")
                result.append(OperationalRecord(
                    source="entsoe", dataset_id=expected[kind], metric=metric, unit="MW",
                    value=float(point.findtext("quantity")), timestamp_utc=timestamp.isoformat(),
                    interval_end_utc=(timestamp + step).isoformat(), retrieved_at=retrieved_at, source_url=GUIDE,
                ))
    if not result:
        raise ValueError("ENTSO-E response contains no supported points")
    # Multiple overlapping series must not silently become a summed national quantity.
    keys = [(r.dataset_id, r.metric, r.timestamp_utc, r.interval_end_utc) for r in result]
    if len(keys) != len(set(keys)):
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
