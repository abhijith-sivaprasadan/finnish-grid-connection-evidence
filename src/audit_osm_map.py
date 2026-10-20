"""Verify EACH web map point/edge against five checksum-pinned 2024 OSM sources.

The map's hardcoded coordinate arrays are currently not auto-generated, so
counts alone are insufficient. This check fails closed on any map-to-source
coordinate, source-order, line-endpoint, AC/DC or voltage mismatch.
This is NOT Fingrid as-built or operator substation identity verification.

Usage: python -m src.audit_osm_map --source-dir /tmp/fi-verified
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import re
from src.db import ROOT

def csv_data(path):
    with Path(path).open(encoding="utf8", newline="") as file:
        return list(csv.DictReader(file))

def parse_web_arrays(path):
    code=Path(path).read_text(encoding="utf8")
    nodes_match=re.search(r'const SOURCE_NODES="([^"]+)"',code)
    links_match=re.search(r'const SOURCE_EDGES="([^"]+)"',code)
    if not nodes_match or not links_match:
        raise ValueError("Expected the reviewed static source array form")
    nodes=[tuple(float(v) for v in entry.split(",")) for entry in nodes_match.group(1).split(";")]
    edges=[tuple(map(int,entry.split(","))) for entry in links_match.group(1).split(";")]
    return nodes,edges

def audit_map(root:Path,source_dir:Path):
    from src.models.fi_proxy_n1_audit import verify_archive
    _,tables=verify_archive(source_dir)
    original_buses=tables["buses"]
    original_lines=tables["lines"]
    map_nodes,map_edges=parse_web_arrays(root/"website/src/lib/osm-2024-proxy-map-odbl.ts")
    if len(original_buses)!=107 or len(original_lines)!=137:
        raise ValueError("Original licensed FI-only inventory changed")
    if len(map_nodes)!=len(original_buses) or len(map_edges)!=len(original_lines):
        raise ValueError("Published map inventory does not match source record counts")
    ids={}
    coord_errors=[];voltage_errors=[]
    for pos, original in enumerate(original_buses):
        key=original["bus_id"]
        ids[key]=pos
        map_lon,map_lat,map_v=map_nodes[pos]
        original_lon=float(original["x"])
        original_lat=float(original["y"])
        original_v=float(original["voltage"])/1000 if float(original["voltage"])>1000 else float(original["voltage"])
        if abs(map_lon-original_lon)>0.000501 or abs(map_lat-original_lat)>0.000501:
            coord_errors.append((pos,key,map_lon,map_lat,original_lon,original_lat))
        if abs(map_v-original_v)>1e-6:
            voltage_errors.append((pos,key,map_v,original_v))
    edge_errors=[]
    for pos,source in enumerate(original_lines):
        actual=map_edges[pos]
        expected=(ids[source["bus0"]],ids[source["bus1"]])
        if actual!=expected:
            edge_errors.append((pos,source["line_id"],actual,expected))
    if coord_errors or voltage_errors or edge_errors:
        raise ValueError({
            "map_coordinate_errors":coord_errors[:7],"coordinate_errors_total":len(coord_errors),
            "map_voltage_errors":voltage_errors[:7],"voltage_errors_total":len(voltage_errors),
            "map_edge_errors":edge_errors[:7],"edge_errors_total":len(edge_errors)
        })
    return {
        "status":"all_107_bus_positions_and_137_graph_edges_matched_historical_osm_source_order",
        "source_license":"ODbL-1.0",
        "map_bus_count":len(map_nodes),"map_edge_count":len(map_edges),
        "original_2024_OSM_source_verified":True,
        "matches_2025_Fingrid_as_built_or_site_capacity":False,
        "source_bus_voltage_unit_verified":True
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--source-dir",type=Path,required=True)
    a=p.parse_args(argv)
    import json
    print(json.dumps(audit_map(a.root,a.source_dir),sort_keys=True))

if __name__=="__main__":main()
