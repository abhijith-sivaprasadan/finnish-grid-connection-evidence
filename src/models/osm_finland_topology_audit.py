"""Audited Finland-only extraction of PyPSA-Eur OSM v0.6 (2024), NOT a Fingrid grid.

The derived CSVs are OpenStreetMap/Zenodo ODbL 1.0 licensed, not MIT.
Electrical input values are third-party/proxy and NOT operator-vetted ratings.
No power-flow, node headroom, or station identity claim is made.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.request import Request, urlopen

RECORD_ID = 14144752
SOURCE_VERSION = "0.6"
LICENSE = "ODbL-1.0"
DOI = "https://doi.org/10.5281/zenodo.14144752"
SOURCE = f"https://zenodo.org/records/{RECORD_ID}/files/"
# Source-reported MD5 checksums at https://zenodo.org/records/14144752
SOURCE_MD5 = {
    "buses.csv": "6b6059dca66ce5851bef4be06460bc23",
    "lines.csv": "aa4ad8a608323358db2e866430f33458",
    "transformers.csv": "b48673b9152e16324ef155ae7a9b0365",
    "links.csv": "19a92e63b8788c931b227ea796f9abff",
    "converters.csv": "89cdb6dc392bc272a4bf14ba4eb1255d",
}
ASSETS = {"buses": "bus_id", "lines": "line_id", "transformers": "transformer_id",
          "links": "link_id", "converters": "converter_id"}
PARAMETERS = ("r", "x", "b", "i_nom", "s_nom", "length", "circuits")


def hashes(path: Path) -> dict:
    md5, sha = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b""):
            md5.update(chunk)
            sha.update(chunk)
    return {"md5": md5.hexdigest(), "sha256": sha.hexdigest(), "bytes": path.stat().st_size}


def obtain_sources(directory: Path, *, allow_download: bool) -> dict:
    directory.mkdir(parents=True, exist_ok=True)
    audit = {}
    for name, expected_md5 in SOURCE_MD5.items():
        path = directory / name
        if not path.is_file() and not allow_download:
            raise FileNotFoundError(f"{path}: missing; pass --download explicitly")
        if not path.is_file():
            url = SOURCE + name + "?download=1"
            error = None
            for attempt in range(3):
                try:
                    req = Request(url, headers={"User-Agent": "FinnishGridAtlasResearch/1.0 (academic reproducibility)"})
                    with urlopen(req, timeout=120) as response, path.with_suffix(".part").open("wb") as f:
                        for chunk in iter(lambda: response.read(1024 * 1024), b""):
                            f.write(chunk)
                    path.with_suffix(".part").replace(path)
                    error = None
                    break
                except (OSError, TimeoutError) as exc:
                    error = exc
                    path.with_suffix(".part").unlink(missing_ok=True)
                    time.sleep(attempt + 1)
            if error:
                raise RuntimeError(f"Could not retrieve pinned Zenodo source {name}: {error}") from error
        stamp = hashes(path)
        if stamp["md5"] != expected_md5:
            raise ValueError(f"Zenodo original checksum mismatch for {name}: {stamp['md5']} != {expected_md5}")
        audit[name] = {**stamp, "source_url": SOURCE + name, "source_md5_verified": True}
    return audit


def load_csv(path: Path, primary_key: str) -> tuple[list[dict], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, quotechar="'", strict=True)
        names = reader.fieldnames or []
        if primary_key not in names:
            raise ValueError(f"{path.name}: missing primary ID {primary_key}; got {names}")
        if len(names) != len(set(names)):
            raise ValueError(f"{path.name}: duplicate columns")
        rows = list(reader)
    seen = set()
    for row in rows:
        identifier = row[primary_key]
        if not identifier or identifier in seen:
            raise ValueError(f"{path.name}: missing/duplicate original ID: {identifier}")
        if None in row:
            raise ValueError(f"{path.name}: inconsistent field count in row {identifier}")
        seen.add(identifier)
    return rows, names


def numeric_info(rows: list[dict], key: str, *, require_positive=False) -> dict:
    available = invalid = zero = 0
    for row in rows:
        val = row.get(key, "")
        if val is None or not str(val).strip():
            continue
        try:
            n = float(val)
            if not math.isfinite(n) or (require_positive and n <= 0):
                invalid += 1
            else:
                available += 1
                if n == 0:
                    zero += 1
        except ValueError:
            invalid += 1
    return {"populated_and_finite": available, "missing": len(rows) - available - invalid,
            "invalid": invalid, "zero_values": zero,
            "source_field_present": bool(rows and key in rows[0]),
            "classification": "OSM_derived_or_engineering_proxy_NOT_Fingrid_measured"}


def internal_and_boundary(rows: list[dict], fi_bus_ids: set[str]) -> tuple[list[dict], list[dict]]:
    domestic, boundary = [], []
    for row in rows:
        left, right = row.get("bus0"), row.get("bus1")
        if left in fi_bus_ids and right in fi_bus_ids:
            domestic.append(row)
        elif (left in fi_bus_ids) != (right in fi_bus_ids):
            boundary.append(row)
    return domestic, boundary


def summarize(tables: dict[str, tuple[list[dict], list[str]]], verified: dict) -> tuple[dict, dict]:
    buses, bus_cols = tables["buses"]
    required_bus_fields = {"bus_id", "voltage", "country", "x", "y", "dc"}
    if not required_bus_fields.issubset(bus_cols):
        raise ValueError("OSM source bus schema incomplete")
    fi_buses = [row for row in buses if row["country"] == "FI"]
    if not fi_buses:
        raise ValueError("No Finland-labelled buses in source; fail closed")
    fi_ids = {row["bus_id"] for row in fi_buses}
    if any(not row["x"] or not row["y"] for row in fi_buses):
        raise ValueError("Missing source geocoordinates on Finnish bus")
    result = {"buses": fi_buses}
    asset_counts = {}
    boundary_counts = {}
    for name in ("lines", "transformers", "links", "converters"):
        raw, names = tables[name]
        if not {"bus0", "bus1"}.issubset(names):
            raise ValueError(f"{name}: no source endpoints")
        domestic, boundary = internal_and_boundary(raw, fi_ids)
        result[name] = domestic
        result[name + "_boundary"] = boundary
        asset_counts[name] = len(domestic)
        boundary_counts[name] = len(boundary)
    lines = result["lines"]
    if not lines:
        raise ValueError("No source AC line endpoints in Finnish buses")
    voltage_counts = Counter(str(bus["voltage"]) for bus in fi_buses)
    line_voltage_counts = Counter(str(line.get("voltage", "unknown")) for line in lines)
    under_construct = lambda rows: sum(str(row.get("under_construction", "")).lower() in ("true", "t", "1") for row in rows)
    line_params = {k: numeric_info(lines, k, require_positive=k in ("x", "length")) for k in PARAMETERS}
    only_native = len(lines) > 0 and all(line_params[k]["populated_and_finite"] == len(lines) for k in ("r", "x", "b"))
    geo = {"longitude_min": min(float(r["x"]) for r in fi_buses),
           "longitude_max": max(float(r["x"]) for r in fi_buses),
           "latitude_min": min(float(r["y"]) for r in fi_buses),
           "latitude_max": max(float(r["y"]) for r in fi_buses)}
    manifest = {
        "record": DOI, "source_release": SOURCE_VERSION,
        "source_snapshot_year": 2024, "analysis_target_year": 2025,
        "source_native_voltage_scope": ">=220kV primarily; incomplete 110kV coverage by construction",
        "research_status": "historical_georeferenced_OSM_proxy_candidate_NOT_2025_operator_topology",
        "dataset_licence": LICENSE,
        "attribution": "OpenStreetMap contributors; Xiong, Fioriti, Neumann, Riepin & Brown (PyPSA-Eur OSM v0.6)",
        "original_source_verified": verified,
        "source_field_headers": {name: columns for name, (_, columns) in tables.items()},
        "geographic_inventory": {"fi_ac_buses": sum(str(b["dc"]).lower() in ("false", "f", "0") for b in fi_buses),
            "fi_all_buses_including_dc": len(fi_buses), "voltage_kv_bus_counts": dict(sorted(voltage_counts.items())),
            "bbox_wgs84": geo, "under_construction_bus_count": under_construct(fi_buses),
            "domestic_edge_counts": asset_counts, "cross_border_edge_counts": boundary_counts,
            "domestic_ac_line_voltages_kv": dict(sorted(line_voltage_counts.items())),
            "under_construction_ac_line_count": under_construct(lines)},
        "electrical_parameter_inventory_ac_lines": line_params,
        "electrical_parameter_classification": {
            "r_x_b": "source_native_third_party_OSM_estimated_not_operator_measured",
            "nominal_current_or_rating": "source_if_present_not_Fingrid_certified; no thermal rating inferred",
            "transformer_values": "source_values_or_proxies; no taps or validated impedance inferred",
            "geometry": "OSM_geocoding_and_heuristic_reconstruction_not_operator_confirmed",
        },
        "all_domestic_ac_lines_have_source_r_x_b": only_native,
        "external_source_scope_confirmed_by_checksum": bool(verified),
        "operator_verified_physical_network": False,
        "2025_as_built_snapshot_verified": False,
        "line_thermal_limit_operationally_validated": False,
        "ac_load_flow_or_n_minus_one_validated": False,
        "approved_site_connection_headroom_mw": None,
        "suitable_for_exploratory_topology_reconciliation": True,
        "suitable_for_investment_grade_connection_study": False,
        "blocking_gaps": [
            "2024 OSM proxy is NOT an authenticated 2025 Fingrid as-built topology or station inventory.",
            "110kV main-grid assets are not systematically covered by this >=220kV release.",
            "OSM geometry and assigned connections are heuristically inferred and unvalidated for Finnish operation.",
            "Original r/x/b and ratings can be technical estimates, not operator equipment records; no ratings invented.",
            "DC links, converter stations, and transformers require separate physical parameter review.",
            "Regional generation/load, switching, security constraints and observed AC flows are not reconciled.",
            "Separate ODbL share-alike obligations apply when distributing derived network data."
        ],
    }
    return manifest, result


def write_outputs(manifest: dict, tables: dict, result: dict, directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "audit.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, rows in result.items():
        fields = tables[name.removesuffix("_boundary")][1]
        with (directory / ("fi_" + name + ".csv")).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    (directory / "DATA_LICENSE_ODBL.txt").write_text(
        "Derived OSM-based network data: Open Data Commons Open Database License 1.0 (ODbL).\n"
        "Attribution: © OpenStreetMap contributors; Xiong et al., PyPSA-Eur prebuilt v0.6 (2024).\n"
        "Original https://doi.org/10.5281/zenodo.14144752; https://opendatacommons.org/licenses/odbl/1-0/\n"
        "No claim of Fingrid engineering certification, 2025 as-built state or project headroom.\n",
        encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--download", action="store_true", help="Allow download of the 5 checksum-pinned Zenodo 0.6 CSVs")
    args = p.parse_args(argv)
    checks = obtain_sources(args.source_dir, allow_download=args.download)
    tables = {name: load_csv(args.source_dir / f"{name}.csv", key) for name, key in ASSETS.items()}
    manifest, result = summarize(tables, checks)
    write_outputs(manifest, tables, result, args.output_dir)
    print("FI_PHYSICAL_PROXY_AUDIT_JSON=" + json.dumps({
        "release": SOURCE_VERSION,
        "buses": manifest["geographic_inventory"]["fi_all_buses_including_dc"],
        "domestic_ac_lines": manifest["geographic_inventory"]["domestic_edge_counts"]["lines"],
        "domestic_transformers": manifest["geographic_inventory"]["domestic_edge_counts"]["transformers"],
        "boundary_assets": manifest["geographic_inventory"]["cross_border_edge_counts"],
        "r_x_b_all_populated": manifest["all_domestic_ac_lines_have_source_r_x_b"],
        "operator_verified": False, "status": manifest["research_status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
