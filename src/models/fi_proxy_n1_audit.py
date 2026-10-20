"""2024 Finnish OSM proxy: source line-template and graph-only N-1 audit.

Derived input data remains ODbL 1.0. This is not a Fingrid power-flow,
reliability study, actual equipment-ratings audit, or connection approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median

RECORD = "https://doi.org/10.5281/zenodo.14144752"


def load_rows(path: Path, id_column: str) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or id_column not in reader.fieldnames:
            raise ValueError(f"OSM source schema or source ID missing: {path.name}")
        rows = list(reader)
    if not rows or any(not row[id_column] for row in rows):
        raise ValueError(f"Empty/missing source IDs: {path.name}")
    if len({r[id_column] for r in rows}) != len(rows):
        raise ValueError(f"Duplicate source IDs: {path.name}")
    return rows


def finite_positive(value, label: str) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: missing/invalid numeric value") from exc
    if not math.isfinite(n) or n <= 0:
        raise ValueError(f"{label}: positive finite value required")
    return n


def verify_archive(directory: Path) -> tuple[dict, dict]:
    audit = json.loads((directory / "audit.json").read_text(encoding="utf-8"))
    if (audit.get("record") != RECORD or audit.get("source_release") != "0.6"
            or audit.get("dataset_licence") != "ODbL-1.0"):
        raise ValueError("Unrecognized licensed/versioned source")
    if audit.get("operator_verified_physical_network") is not False:
        raise ValueError("Refuse candidate marked as operator validated")
    if audit.get("2025_as_built_snapshot_verified") is not False:
        raise ValueError("Refuse candidate marked as as-built 2025")
    evidence = audit.get("original_source_verified", {})
    names = {"buses.csv", "lines.csv", "transformers.csv", "links.csv", "converters.csv"}
    if set(evidence) != names or any(not e.get("source_md5_verified") or
            len(e.get("sha256", "")) != 64 for e in evidence.values()):
        raise ValueError("Source original checksum record missing")
    tables = {name: load_rows(directory / ("fi_" + name + ".csv"), key)
              for name, key in (("buses", "bus_id"), ("lines", "line_id"),
                                ("transformers", "transformer_id"))}
    ac_ids = {b["bus_id"] for b in tables["buses"]
              if b.get("dc", "").lower() in ("f", "false", "0")}
    if not ac_ids:
        raise ValueError("No source AC buses")
    for kind in ("lines", "transformers"):
        for e in tables[kind]:
            if (e.get("bus0") not in ac_ids or e.get("bus1") not in ac_ids
                    or e["bus0"] == e["bus1"]):
                raise ValueError(f"Dangling or self-connected source {kind}")
    return audit, tables


def electrical_template_audit(lines: list[dict]) -> dict:
    groups: dict[str, list[dict]] = {}
    for row in lines:
        key = row["line_id"]
        v = finite_positive(row.get("voltage"), key + ".voltage")
        if v not in (220, 400):
            raise ValueError("Source nominal voltage outside audited proxy scope")
        circuits = finite_positive(row.get("circuits"), key + ".circuits")
        if circuits != int(circuits):
            raise ValueError("Non-integral circuit count")
        length_km = finite_positive(row.get("length"), key + ".length_m") / 1000
        r = finite_positive(row.get("r"), key + ".r")
        x = finite_positive(row.get("x"), key + ".x")
        b = finite_positive(row.get("b"), key + ".b")
        i_nom = finite_positive(row.get("i_nom"), key + ".i_nom")
        s_nom = finite_positive(row.get("s_nom"), key + ".s_nom")
        computed = math.sqrt(3) * v * i_nom * circuits
        if abs(computed - s_nom) > max(0.1, computed * 1e-4):
            raise ValueError("Source S_nom inconsistent with current/circuit template")
        groups.setdefault(str(int(v)), []).append({
            "r_per_km_per_circuit": r * circuits / length_km,
            "x_per_km_per_circuit": x * circuits / length_km,
            "b_per_km_per_circuit": b / circuits / length_km,
            "source_type": row.get("type", ""),
            "source_nominal_current": i_nom,
            "circuits": int(circuits),
        })
    result = {}
    for voltage, members in sorted(groups.items()):
        params = {}
        for parameter in ("r_per_km_per_circuit", "x_per_km_per_circuit",
                          "b_per_km_per_circuit"):
            values = [m[parameter] for m in members]
            center = median(values)
            deviation = max(abs(v-center)/center for v in values)
            params[parameter] = {
                "median_source_parameter": round(center, 12),
                "maximum_relative_deviation": round(deviation, 8),
                "fits_common_voltage_template_0p1pct": deviation <= 0.001
            }
        result[voltage] = {
            "count": len(members),
            "source_types": sorted({m["source_type"] for m in members}),
            "source_currents": sorted({m["source_nominal_current"] for m in members}),
            "source_circuit_counts": sorted({m["circuits"] for m in members}),
            "templates": params,
            "all_fields_fit": all(p["fits_common_voltage_template_0p1pct"]
                                  for p in params.values())
        }
    return {
        "classification": "authentic_OSM_source_values_THIRD_PARTY_STANDARD_LINE_ASSUMPTIONS",
        "total_ac_lines": len(lines),
        "s_nom_matches_sqrt3_voltage_current_circuits": True,
        "by_voltage": result,
        "all_137_source_lines_fit_voltage_templates": all(g["all_fields_fit"] for g in result.values()),
        "operator_verified_per_line_impedance_or_thermal_rating": False
    }


def components(nodes: set[str], edges: list[dict]) -> list[set[str]]:
    neighbours = {name: set() for name in nodes}
    for e in edges:
        a, b = e.get("bus0"), e.get("bus1")
        if a not in neighbours or b not in neighbours or a == b:
            raise ValueError("Unknown source graph branch endpoint")
        neighbours[a].add(b)
        neighbours[b].add(a)
    visited = set()
    result = []
    for root in sorted(nodes):
        if root in visited:
            continue
        stack, comp = [root], set()
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            comp.add(node)
            stack.extend(neighbours[node] - visited)
        result.append(comp)
    return sorted(result, key=lambda c: (-len(c), min(c)))


def n1_structural_audit(tables: dict) -> dict:
    ac_ids = {row["bus_id"] for row in tables["buses"]
              if row.get("dc", "").lower() in ("f", "false", "0")}
    lines = [{"kind": "AC_line", "id": x["line_id"], "bus0": x["bus0"],
              "bus1": x["bus1"]} for x in tables["lines"]]
    transforms = [{"kind": "transformer", "id": x["transformer_id"],
                   "bus0": x["bus0"], "bus1": x["bus1"]}
                  for x in tables["transformers"]]
    edges = lines + transforms
    if len({(e["kind"], e["id"]) for e in edges}) != len(edges):
        raise ValueError("Duplicate source graph edge")
    if len(components(ac_ids, edges)) != 1:
        raise ValueError("Original Finnish 2024 extracted source graph disconnected")
    critical = []
    for index, edge in enumerate(edges):
        # Remove exactly one source edge, not ALL edges between its endpoint
        # pair. A parallel edge is not a topological bridge.
        partitions = components(ac_ids, edges[:index] + edges[index+1:])
        if len(partitions) > 1:
            critical.append({
                "source_id": edge["id"], "asset_kind": edge["kind"],
                "component_sizes_after_single_edge_removal":
                    sorted((len(x) for x in partitions), reverse=True),
                "smaller_partition_bus_count": min(len(x) for x in partitions)
            })
    return {
        "classification": "single_source_edge_GRAPH_REMOVAL_ONLY_NOT_electricity_security_N_minus_one",
        "ac_bus_count": len(ac_ids), "ac_line_count": len(lines),
        "transformer_count": len(transforms),
        "edges_tested_individually": len(edges),
        "ac_only_component_sizes": [len(c) for c in components(ac_ids, lines)],
        "source_ac_plus_transformer_component_sizes": [len(c) for c in components(ac_ids, edges)],
        "single_edge_removals_causing_graph_disconnection": len(critical),
        "breakdown_by_kind": dict(Counter(x["asset_kind"] for x in critical)),
        "critical_source_edge_records": sorted(critical, key=lambda x: (x["asset_kind"], x["source_id"])),
        "important_limitations": [
            "Missing 110-kV and excluded cross-border electrical paths can create artificial apparent bridges.",
            "2024 OSM reconstructed connectivity is not Fingrid switching or 2025 operating topology.",
            "Graph severance is NOT a predicted power outage, real N-1 violation or project connection refusal.",
            "No AC/DC power flow, voltage, thermal rating, injections or actual security constraints are solved."
        ]
    }


def run(input_dir: Path, output_dir: Path) -> dict:
    original, tables = verify_archive(input_dir)
    result = {
        "dataset_licence": "ODbL-1.0",
        "source_record": RECORD,
        "original_zenodo_version": "0.6",
        "source_archive_manifest_sha256":
            hashlib.sha256((input_dir/"audit.json").read_bytes()).hexdigest(),
        "original_file_sha256": {name: proof["sha256"] for name, proof
                                in sorted(original["original_source_verified"].items())},
        "operator_verified_network": False, "2025_actual_security_compliance": None,
        "validated_project_connection_headroom": None,
        "electrical_templates": electrical_template_audit(tables["lines"]),
        "source_topology_n1": n1_structural_audit(tables)
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/"2024_finland_osm_proxy_n1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    (output_dir/"DATA_LICENSE_ODBL.txt").write_text(
        "ODbL-1.0 adapted derived source: © OpenStreetMap contributors and "
        "Xiong et al., PyPSA-Eur OSM v0.6 (2024).\n"+RECORD+"\n"
        "Topology-only research, not Fingrid engineering validation.\n", encoding="utf-8")
    print("FI_PROXY_STAGE2_JSON="+json.dumps({
        "source_lines":result["electrical_templates"]["total_ac_lines"],
        "voltage_templates_fit":result["electrical_templates"]["all_137_source_lines_fit_voltage_templates"],
        "single_edge_disconnections":result["source_topology_n1"]["single_edge_removals_causing_graph_disconnection"],
        "by_kind":result["source_topology_n1"]["breakdown_by_kind"],
        "actual_grid_security_verified": False
    }, sort_keys=True))
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--extracted-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args(argv)
    run(args.extracted_dir, args.output_dir)


if __name__ == "__main__":
    main()
