"""Strict evidence types. All timestamps are normalized to UTC before persistence."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import math
from urllib.parse import urlsplit


def utc(value: str) -> str:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamp requires an explicit timezone")
    return dt.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def required(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")


def url(value: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username:
        raise ValueError("A public HTTP(S) source URL is required")
    if any(s in parsed.query.lower() for s in ("token", "api_key", "apikey", "x-api-key", "securitytoken")):
        raise ValueError("Source URLs must not contain credentials")


def finite(value: float, nonnegative: bool = False) -> None:
    if not math.isfinite(value) or (nonnegative and value < 0):
        raise ValueError("Expected a finite, nonnegative value" if nonnegative else "Expected a finite value")


def year(value: int | None) -> None:
    if value is not None and (type(value) is not int or not 1900 <= value <= 2200):
        raise ValueError("Year must be an integer from 1900 to 2200, or blank")


@dataclass(frozen=True)
class ConnectionPoint:
    connection_point_id: str
    operator: str
    name: str
    voltage_kv: float | None
    source_url: str

    def __post_init__(self):
        for field in ("connection_point_id", "operator", "name"):
            required(getattr(self, field), field)
        url(self.source_url)
        if self.voltage_kv is not None:
            finite(self.voltage_kv, True)
            if self.voltage_kv == 0:
                raise ValueError("Voltage must be positive")


@dataclass(frozen=True)
class CapacityObservation:
    observation_id: str
    connection_point_id: str
    direction: str
    effective_year: int | None
    capacity_value: float | None
    capacity_unit: str | None
    capacity_status: str
    source_url: str
    source_observed_at: str
    validity_notes: str
    source_published_on: str | None = None
    confirmation_evidence_url: str | None = None

    def __post_init__(self):
        for field in ("observation_id", "connection_point_id", "validity_notes"):
            required(getattr(self, field), field)
        if self.direction not in {"consumption", "production"}:
            raise ValueError("Direction must be consumption or production")
        year(self.effective_year)
        if self.capacity_value is None:
            raise ValueError("A capacity observation requires a published numeric value; record missing coverage separately")
        finite(self.capacity_value, True)
        if self.capacity_unit not in {"MW", "MVA"}:
            raise ValueError("A numeric estimate needs its source unit: MW or MVA")
        if self.capacity_status not in {"published_indicative", "operator_confirmed"}:
            raise ValueError("Model results belong in scenario_result, never capacity_observation")
        url(self.source_url)
        object.__setattr__(self, "source_observed_at", utc(self.source_observed_at))
        if self.source_published_on:
            from datetime import date
            published = date.fromisoformat(self.source_published_on)
            if published > datetime.fromisoformat(self.source_observed_at).date():
                raise ValueError("Publication date cannot follow capture date")
        if self.capacity_status == "operator_confirmed":
            if not self.confirmation_evidence_url:
                raise ValueError("Operator confirmation needs documentary evidence")
            url(self.confirmation_evidence_url)


@dataclass(frozen=True)
class GridProject:
    project_id: str
    name: str
    commissioning_year: int | None
    uncertainty: str
    source_url: str
    source_observed_at: str
    validity_notes: str

    def __post_init__(self):
        for field in ("project_id", "name", "uncertainty", "validity_notes"):
            required(getattr(self, field), field)
        year(self.commissioning_year)
        url(self.source_url)
        object.__setattr__(self, "source_observed_at", utc(self.source_observed_at))


@dataclass(frozen=True)
class OperationalRecord:
    source: str
    dataset_id: str
    metric: str
    unit: str
    value: float
    timestamp_utc: str
    interval_end_utc: str
    retrieved_at: str
    source_url: str
    area: str = "FI"

    def __post_init__(self):
        if self.source not in {"fingrid", "entsoe"} or self.area != "FI":
            raise ValueError("MVP operational data must identify Fingrid/ENTSO-E and national FI scope")
        for field in ("dataset_id", "metric", "unit"):
            required(getattr(self, field), field)
        finite(self.value)
        url(self.source_url)
        for field in ("timestamp_utc", "interval_end_utc", "retrieved_at"):
            object.__setattr__(self, field, utc(getattr(self, field)))
        if datetime.fromisoformat(self.interval_end_utc) <= datetime.fromisoformat(self.timestamp_utc):
            raise ValueError("Interval end must follow start")


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    model_version: str
    assumption_set: str
    metric: str
    value: float
    unit: str
    created_at: str
    capacity_status: str = "model_scenario"

    def __post_init__(self):
        import json
        for field in ("scenario_id", "model_version", "metric", "unit"):
            required(getattr(self, field), field)
        if not isinstance(json.loads(self.assumption_set), dict):
            raise ValueError("Scenario assumptions must be a JSON object")
        if self.capacity_status != "model_scenario":
            raise ValueError("Scenario results must be labelled model_scenario")
        finite(self.value)
        object.__setattr__(self, "created_at", utc(self.created_at))


def record_dict(record):
    return asdict(record)
