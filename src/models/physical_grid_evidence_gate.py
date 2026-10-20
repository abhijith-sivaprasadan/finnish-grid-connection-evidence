"""Fail-closed structural screening of proposed *physical* Finnish grid inputs.

This is NOT a reconstructed Finnish grid, licensed network database, or
operator certification. It never infers parameters from Fingrid market-capacity
time series or publishes a site-connection MW value. It checks externally
reviewed input candidates before any separate electrical-simulation study.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from urllib.parse import urlparse

VOLTAGE_LEVELS = {110., 220., 400.}
MARKET_FIELDS = {"market_capacity_mw", "intraday_capacity_mw", "trade_capacity_mw",
                 "available_connection_capacity_mw", "site_headroom_mw"}


def _nonnegative_number(value, label: str, *, positive=False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}: must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: must be a finite number") from exc
    if not math.isfinite(number) or number < 0 or (positive and number == 0):
        raise ValueError(f"{label}: invalid nonnegative physical value")
    return number


def _source(row: dict, label: str) -> None:
    url = row.get("evidence_url", "")
    parsed = urlparse(url) if isinstance(url, str) else None
    if not parsed or parsed.scheme != "https" or not parsed.hostname or parsed.username:
        raise ValueError(f"{label}: specific HTTPS documentary evidence_url required")
    if row.get("parameter_evidence") not in ("operator_document", "published_technical_record",
                                              "proxy_estimate"):
        raise ValueError(f"{label}: parameter_evidence classification required")
    if row.get("captured_utc", "").endswith("Z") is False:
        raise ValueError(f"{label}: source capture timestamp required")


def audit(data: dict) -> dict:
    """Reject missing electrical parameters, opaque provenance, and market-MW substitutions.

    'structurally_screenable' is not verification of published physics: even a
    complete, proxy-derived network remains an exploratory hypothesis.
    """
    if data.get("country") != "FI" or data.get("study_year") != 2025:
        raise ValueError("Must explicitly scope a 2025 Finland network candidate")
    buses = data.get("buses")
    lines = data.get("ac_lines")
    if not isinstance(buses, list) or not isinstance(lines, list) or not buses or not lines:
        raise ValueError("Explicit nonempty buses and AC physical lines required")
    if data.get("site_connection_approved") is True:
        raise ValueError("Site connection approval cannot be asserted by an input manifest")
    bus_ids = set()
    bus_voltages = {}
    for i, bus in enumerate(buses):
        label = f"bus[{i}]"
        if not isinstance(bus, dict):
            raise ValueError(f"{label}: object required")
        identifier = bus.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in bus_ids:
            raise ValueError(f"{label}: unique nonempty bus ID required")
        _source(bus, label)
        kv = _nonnegative_number(bus.get("voltage_kv"), f"{label}.voltage_kv", positive=True)
        if kv not in VOLTAGE_LEVELS:
            raise ValueError(f"{label}: voltage outside explicitly audited 110/220/400 kV scope")
        bus_ids.add(identifier)
        bus_voltages[identifier] = kv

    line_ids = set()
    source_kinds = Counter()
    for i, line in enumerate(lines):
        label = f"ac_line[{i}]"
        if not isinstance(line, dict):
            raise ValueError(f"{label}: object required")
        identifier = line.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in line_ids:
            raise ValueError(f"{label}: unique nonempty AC line ID required")
        if MARKET_FIELDS.intersection(line):
            raise ValueError(f"{label}: market capacity or site headroom cannot be a line rating")
        _source(line, label)
        src, dst = line.get("bus0"), line.get("bus1")
        if src not in bus_ids or dst not in bus_ids or src == dst:
            raise ValueError(f"{label}: both endpoints must identify distinct registered buses")
        kv = _nonnegative_number(line.get("voltage_kv"), f"{label}.voltage_kv", positive=True)
        if kv != bus_voltages[src] or kv != bus_voltages[dst]:
            raise ValueError(f"{label}: bus voltage mismatch; transformers need a separate verified model")
        for key in ("r_ohm", "b_siemens", "length_km"):
            _nonnegative_number(line.get(key), f"{label}.{key}")
        _nonnegative_number(line.get("x_ohm"), f"{label}.x_ohm", positive=True)
        _nonnegative_number(line.get("thermal_rating_mva"), f"{label}.thermal_rating_mva", positive=True)
        if line.get("kind") != "AC_overhead_or_cable":
            raise ValueError(f"{label}: do not model DC interconnectors or transformers as AC lines")
        line_ids.add(identifier)
        source_kinds[line["parameter_evidence"]] += 1

    return {
        "country": "FI",
        "study_year": 2025,
        "bus_count": len(buses),
        "ac_line_count": len(lines),
        "structurally_screenable": True,
        "operator_verified_physical_network": False,
        "validated_site_connection_headroom_mw": None,
        "proxy_parameter_line_count": source_kinds["proxy_estimate"],
        "readiness": "exploratory_input_only_not_approved_grid_model",
        "warnings": [
            "The manifest is self-declared: source documents, licence, and topology must be independently verified.",
            "No N-1, transformer, DC converter, calibration, generation geography, or operator approval is established.",
            "No model output may be presented as guaranteed site connection headroom."
        ]
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args(argv)
    result = audit(json.loads(args.candidate.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
