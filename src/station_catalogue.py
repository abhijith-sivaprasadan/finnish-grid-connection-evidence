"""Source-attributed staging intake for a future nationwide Finnish station register.

This is NOT Grid Scope capacity ingestion and NEVER promotes raw map features to
operator-confirmed substations. No network connection or third-party endpoint is
called by this module. All inputs are reviewed offline CSV exports.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

COLUMNS = (
    "registry_id", "source_dataset", "source_feature_id", "source_url",
    "captured_utc", "name", "voltage_kv", "feature_kind",
    "operator_evidence", "latitude", "longitude", "review_state",
    "review_url", "notes",
)
KINDS = {"connection_point", "substation", "mapped_infrastructure", "unspecified"}
REVIEWS = {"candidate", "source_transcribed", "operator_identity_checked"}
OPERATORS = {"not_assessed", "source_names_fingrid", "separate_operator_document"}
# At present no externally collected new station identities qualify for
# operator_identity_checked. It requires independent, row-scoped proof.
MAX_ROWS = 50000


def _link(value: str) -> None:
    p = urlsplit(value)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        raise ValueError("Expected a public HTTP(S) evidence URL")
    if any(x in p.query.casefold() for x in ("token=", "api-key=", "apikey=", "api_key=", "key=")):
        raise ValueError("Do not retain API keys or tokens in evidence URLs")


def _moment(value: str) -> str:
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as e:
        raise ValueError("captured_utc must be ISO 8601") from e
    if d.tzinfo is None:
        raise ValueError("captured_utc must be timezone aware")
    d = d.astimezone(timezone.utc)
    if d > datetime.now(timezone.utc):
        raise ValueError("captured_utc cannot be in the future")
    return d.isoformat(timespec="seconds").replace("+00:00", "Z")


def _coordinate(value: str, low: float, high: float) -> float | None:
    if not value:
        return None
    try:
        v = float(value)
    except ValueError as e:
        raise ValueError("Invalid WGS84 coordinate") from e
    if not low <= v <= high:
        raise ValueError("Coordinate outside Finnish WGS84 bounds; check EPSG:3067 conversion")
    return v


@dataclass(frozen=True)
class RegistryRow:
    registry_id: str
    source_dataset: str
    source_feature_id: str
    source_url: str
    captured_utc: str
    name: str
    voltage_kv: float | None
    feature_kind: str
    operator_evidence: str
    latitude: float | None
    longitude: float | None
    review_state: str
    review_url: str
    notes: str

    @classmethod
    def parse(cls, raw: dict[str, str]) -> "RegistryRow":
        if set(raw) != set(COLUMNS):
            raise ValueError("Unexpected or missing columns")
        record = {k: v.strip() for k, v in raw.items()}
        for name in ("registry_id", "source_dataset", "source_feature_id", "name", "notes"):
            if not record[name]:
                raise ValueError(name + " is required")
        if not re.fullmatch(r"[A-Za-z0-9._:-]{4,128}", record["registry_id"]):
            raise ValueError("registry_id must be a stable identifier")
        if record["feature_kind"] not in KINDS or record["review_state"] not in REVIEWS:
            raise ValueError("Unknown feature kind or review state")
        if record["operator_evidence"] not in OPERATORS:
            raise ValueError("Unrecognized operator evidence category")
        _link(record["source_url"])
        if record["review_url"]:
            _link(record["review_url"])
        if record["review_state"] == "operator_identity_checked" and (
            record["operator_evidence"] != "separate_operator_document" or not record["review_url"]
        ):
            raise ValueError("Independent operator identity documentation required")
        if record["operator_evidence"] == "separate_operator_document" and not record["review_url"]:
            raise ValueError("Document URL required for separate operator evidence")
        if record["source_dataset"].casefold().startswith("nls") and record["operator_evidence"] != "not_assessed":
            raise ValueError("NLS map objects alone cannot assert the grid operator")
        if record["source_dataset"].casefold().startswith("osm") and record["review_state"] != "candidate":
            raise ValueError("OSM-derived objects remain candidates until independently documented")
        latitude = _coordinate(record["latitude"], 58.5, 71.5)
        longitude = _coordinate(record["longitude"], 18.0, 33.0)
        if (latitude is None) != (longitude is None):
            raise ValueError("Latitude/longitude must be supplied together")
        voltage = None
        if record["voltage_kv"]:
            try:
                voltage = float(record["voltage_kv"])
            except ValueError as e:
                raise ValueError("Invalid voltage") from e
            if not 0 < voltage <= 1000:
                raise ValueError("Invalid voltage: source voltage must be in kV")
        return cls(
            record["registry_id"], record["source_dataset"],
            record["source_feature_id"], record["source_url"],
            _moment(record["captured_utc"]), record["name"], voltage,
            record["feature_kind"], record["operator_evidence"],
            latitude, longitude, record["review_state"],
            record["review_url"], record["notes"],
        )


def read_registry(path: Path) -> list[RegistryRow]:
    rows: list[RegistryRow] = []
    identifiers: set[str] = set()
    native_ids: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError("Staging CSV header mismatch; use docs/STATION_INVENTORY.md")
        for line, raw in enumerate(reader, 2):
            if len(rows) >= MAX_ROWS:
                raise ValueError("Station registry exceeds maximum safe staged row count")
            if None in raw or any(v is None for v in raw.values()):
                raise ValueError(f"Row {line}: malformed CSV")
            try:
                row = RegistryRow.parse(raw)
            except ValueError as e:
                raise ValueError(f"Row {line}: {e}") from e
            source_id = (row.source_dataset, row.source_feature_id)
            if row.registry_id in identifiers or source_id in native_ids:
                raise ValueError(f"Row {line}: duplicate registry ID or source-native feature ID")
            identifiers.add(row.registry_id)
            native_ids.add(source_id)
            rows.append(row)
    return rows


def _name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).casefold()
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def evidence_report(rows: list[RegistryRow]) -> dict:
    by_source = Counter(row.source_dataset for row in rows)
    by_status = Counter(row.review_state for row in rows)
    # Name+voltage collisions are *review flags*, never automated cross-source merges.
    duplicates = defaultdict(list)
    for row in rows:
        if row.name:
            duplicates[(_name(row.name), row.voltage_kv)].append(row.registry_id)
    return {
        "scope": "Candidate/staged geography and identity records only; NOT capacity",
        "records": len(rows),
        "source_datasets": dict(sorted(by_source.items())),
        "review_states": dict(sorted(by_status.items())),
        "with_wgs84_location": sum(row.latitude is not None for row in rows),
        "with_source_reported_voltage": sum(row.voltage_kv is not None for row in rows),
        "operator_identity_checked": by_status["operator_identity_checked"],
        "name_voltage_collisions_to_review": [
            {"name_key": name, "voltage_kv": voltage, "registry_ids": ids}
            for (name, voltage), ids in sorted(duplicates.items())
            if len(ids) > 1
        ],
        "published_capacity_values": 0,
        "note": "Cannot equate cartographic objects with 138 Fingrid substations (2025), or with Grid Scope capacity observations.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit staged station catalogue, without loading live DB")
    parser.add_argument("--input", type=Path, default=Path("data/catalogue/seed_20261017.csv"))
    parser.add_argument("--output", type=Path, help="Optional reviewed JSON report (no secrets)")
    args = parser.parse_args(argv)
    try:
        rows = read_registry(args.input)
        report = evidence_report(rows)
        payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        print(payload, end="")
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Station catalogue validation failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
