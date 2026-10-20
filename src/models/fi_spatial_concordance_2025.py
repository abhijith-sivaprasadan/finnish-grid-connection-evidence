"""Licence-cautious comparison of two NON-AUTHORITATIVE Finnish grid geometries.

Uses ODbL-labelled PyPSA-Eur OSM v0.6 (September 2024) locally and a
public third-party FCG ArcGIS feature service collected 22 February 2025.
The FCG ArcGIS item has blank 'licenseInfo'; this module NEVER writes
or redistributes any of its raw geometries or individual feature IDs.
Outputs ONLY aggregated statistics and provenance/rights warnings.

Even high geographic agreement is NOT Fingrid topology certification, 2025
commissioning proof, electrical branch validation, or connectability.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request

ITEM_ID = "c24608cc5f5943469d04821c77954e95"
ITEM_URL = "https://www.arcgis.com/sharing/rest/content/items/" + ITEM_ID
SERVICE = "https://services2.arcgis.com/uh3cDCipmuPcmxmx/arcgis/rest/services/Suomen_s%C3%A4hk%C3%B6verkko/FeatureServer/0"
SVC_OWNER = "henri.korhonen_fcg"
SOURCE_OSM = "https://doi.org/10.5281/zenodo.14144752"
VOLTAGES = (220, 400)
QUERY_LIMIT = 5000
PAGE = 500


def get_json(url: str, params: dict, *, timeout=45) -> dict:
    query = urlencode(params)
    request = Request(url + "?" + query, headers={"User-Agent": "FinnishGridAtlas/1.0 spatial-research provenance audit"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read(12 * 1024 * 1024 + 1)
    if len(body) > 12 * 1024 * 1024:
        raise ValueError("ArcGIS single response exceeds bounded size")
    data = json.loads(body)
    if not isinstance(data, dict) or "error" in data:
        raise ValueError("Invalid/rejected ArcGIS response: "+str(data.get("error") if isinstance(data,dict) else "non-object"))
    return data


def check_metadata(item: dict, layer: dict) -> dict:
    """Check identity, source date and rights, NOT the truth of the source attribution."""
    if item.get("id") != ITEM_ID or item.get("owner") != SVC_OWNER:
        raise ValueError("Unrecognised FCG source item ID/owner")
    if "22.2.2025" not in (item.get("snippet") or ""):
        raise ValueError("Missing source collection date: 22 Feb 2025")
    if item.get("access") != "public":
        raise ValueError("Source is not publicly accessible")
    if layer.get("geometryType") != "esriGeometryPolyline":
        raise ValueError("Wrong feature geometry type")
    fields = {f.get("name") for f in layer.get("fields", [])}
    if not {"FID", "Tyyppi"}.issubset(fields):
        raise ValueError("Unknown hosted copy line-voltage schema")
    license_text = (item.get("licenseInfo") or "").strip()
    return {
        "hosted_item_url": "https://www.arcgis.com/home/item.html?id="+ITEM_ID,
        "hosted_feature_url": SERVICE,
        "hosted_owner": SVC_OWNER,
        "hosted_copy_2025_02_22": True,
        "hosted_original_claimed_source": "Fingrid map feedback service, asserted by third-party FCG description",
        "license_info_present": bool(license_text),
        "rights_status": "UNKNOWN_HOLD_ALL_RAW_FCG_GEOMETRY" if not license_text else
            "RIGHTS_REQUIRE_INDEPENDENT_MANUAL_REVIEW",
        "permission_to_redistribute_FCG_geometry": False,
        "confirmed_Fingrid_equipment_database": False,
    }


def acquire_fc_geometry(*, item: dict | None = None, layer: dict | None = None) -> tuple[dict, list[dict]]:
    if item is None: item = get_json(ITEM_URL, {"f": "json"})
    if layer is None: layer = get_json(SERVICE, {"f": "json"})
    provenance = check_metadata(item,layer)
    where = "Tyyppi IN ('220','400')"
    count = get_json(SERVICE+"/query", {"where":where,"returnCountOnly":"true","f":"json"}).get("count")
    if not isinstance(count,int) or not (1 <= count <= QUERY_LIMIT):
        raise ValueError(f"Unexpected/unbounded hosted layer feature count: {count}")
    features = []
    for offset in range(0,count,PAGE):
        data = get_json(SERVICE+"/query", {
            "where":where, "outFields":"FID,Tyyppi", "returnGeometry":"true",
            "outSR":"4326","f":"geojson", "resultOffset":str(offset),
            "resultRecordCount":str(min(PAGE,count-offset)), "orderByFields":"FID ASC"})
        if data.get("type") != "FeatureCollection":
            raise ValueError("Hosted comparison did not return GeoJSON FeatureCollection")
        batch = data.get("features")
        if not isinstance(batch,list) or len(batch)!=min(PAGE,count-offset):
            raise ValueError("GeoJSON pagination incomplete; never treat partial dataset as coverage")
        features.extend(batch)
    ids = [x.get("properties",{}).get("FID") for x in features]
    if len(ids)!=len(set(ids)) or any(x is None for x in ids):
        raise ValueError("Missing/duplicate third-party feature IDs")
    provenance["hosted_400_220_feature_count"] = count
    return provenance, features


def load_osm_lines(csv_path: Path, audit_path: Path) -> list[dict]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if (audit.get("record") != SOURCE_OSM or audit.get("dataset_licence") != "ODbL-1.0"
          or audit.get("source_release") != "0.6"
          or audit.get("operator_verified_physical_network") is not False):
        raise ValueError("OSM original/licence evidence invalid")
    originals = audit.get("original_source_verified",{})
    if "lines.csv" not in originals or not originals["lines.csv"].get("source_md5_verified"):
        raise ValueError("No original Zenodo line CSV checksum proof")
    with csv_path.open(encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or not {"line_id","voltage","geometry"}.issubset(reader.fieldnames):
            raise ValueError("Missing required ODbL original geometry fields")
        lines=list(reader)
    if not lines or len({x["line_id"] for x in lines}) != len(lines):
        raise ValueError("Missing/duplicate OSM original line IDs")
    if any(int(row["voltage"]) not in VOLTAGES for row in lines):
        raise ValueError("Unsupported 2024 OSM AC source voltage")
    return lines


def to_projected(geom, transformer):
    from shapely.ops import transform
    return transform(transformer.transform,geom)


def prepare_pairs(osm_rows: list[dict], fcg_features: list[dict]):
    from pyproj import Transformer
    from shapely import wkt
    from shapely.geometry import shape
    crs = Transformer.from_crs("EPSG:4326","EPSG:3067",always_xy=True)
    osm = {voltage: [] for voltage in VOLTAGES}
    comparison = {voltage: [] for voltage in VOLTAGES}
    for line in osm_rows:
        voltage = int(line["voltage"])
        geometry = to_projected(wkt.loads(line["geometry"]),crs)
        if geometry.geom_type not in ("LineString","MultiLineString") or geometry.is_empty or geometry.length < 100:
            raise ValueError("Invalid original OSM route geometry")
        osm[voltage].append(geometry)
    for feature in fcg_features:
        properties = feature.get("properties") or {}
        voltage = int(properties.get("Tyyppi") or 0)
        if voltage not in VOLTAGES:
            raise ValueError("Unexpected 110 or 500 kV feature in 220/400-only query")
        geometry = to_projected(shape(feature.get("geometry")),crs)
        if geometry.geom_type not in ("LineString","MultiLineString") or geometry.is_empty or geometry.length <= 0:
            raise ValueError(f"Invalid hosted feature geometry: type={geometry.geom_type}, empty={geometry.is_empty}, length_nonpositive={geometry.length<=0}")
        comparison[voltage].append(geometry)
    if any(not osm[x] or not comparison[x] for x in VOLTAGES):
        raise ValueError("Both 220/400kV source types must have valid features")
    return osm, comparison


def sample_distances(osm_lines:list, comparator_lines:list, *, spacing_m:float=2000) -> list[list[float]]:
    """Per-OSM-line midpoint samples; nearest SAME-VOLTAGE hosted polyline.

    Does not output cross-provider feature IDs or joined geometry.
    """
    from shapely.strtree import STRtree
    tree=STRtree(comparator_lines)
    readings=[]
    for geometry in osm_lines:
        n=max(1,min(250,math.ceil(geometry.length/spacing_m)))
        distances=[]
        for k in range(n):
            point=geometry.interpolate((k+0.5)/n,normalized=True)
            index=int(tree.nearest(point))
            distances.append(round(point.distance(comparator_lines[index]),5))
        readings.append(distances)
    return readings


def audit_spatial(osm:dict,comparison:dict) -> dict:
    from statistics import median
    result={}
    for voltage in VOLTAGES:
        readings=sample_distances(osm[voltage],comparison[voltage])
        all_d=[d for values in readings for d in values]
        counts={str(limit):sum(d<=limit for d in all_d) for limit in (250,1000,5000)}
        result[str(voltage)] = {
            "OSM_source_route_rows":len(osm[voltage]),
            "hosted_comparator_feature_rows":len(comparison[voltage]),
            "route_midpoint_samples":len(all_d),
            "sample_share_within_250m":round(counts["250"]/len(all_d),5),
            "sample_share_within_1000m":round(counts["1000"]/len(all_d),5),
            "sample_share_within_5000m":round(counts["5000"]/len(all_d),5),
            "median_nearest_same_voltage_line_m":round(median(all_d),1),
            "source_routes_at_least_80pct_within_1000m":sum(
                sum(d<=1000 for d in values)/len(values)>=0.8 for values in readings),
            "source_routes_at_least_80pct_within_5000m":sum(
                sum(d<=5000 for d in values)/len(values)>=0.8 for values in readings)
        }
    return result


def run(osm_dir:Path,output:Path)->dict:
    lines=load_osm_lines(osm_dir/"fi_lines.csv",osm_dir/"audit.json")
    provenance,fcg_features=acquire_fc_geometry()
    source,hosted=prepare_pairs(lines,fcg_features)
    aggregates=audit_spatial(source,hosted)
    result={
        "type":"NON_AUTHORITATIVE_GEOGRAPHIC_CONCORDANCE_TWO_PROXY_SOURCES",
        "study_reference_OSM_september_2024":SOURCE_OSM,
        "OSM_derived_network_data_licence":"ODbL-1.0",
        "comparator":provenance,
        "observations":aggregates,
        "dated_2025_as_built_Fingrid_grid_verified":False,
        "individual_Fingrid_substations_or_line_ids_reconciled":0,
        "operator_confirmed_physical_r_x_b_or_thermal_rating_count":0,
        "raw_2025_FCG_features_published":False,
        "published_cross_provider_individual_asset_mappings":False,
        "cannot_imply":[
            "A public third-party FCG Feb-2025 copy is NOT a licence-granted Fingrid certified 2025 network",
            "The two route maps could share upstream source lineage or simplification and are NOT independent engineering verification",
            "Proximity does not identify an individual conductor or actual connected bus/switch",
            "The 2025-02-22 layer pre-dates Q3 2025 Huittinen-Forssa and Nov 2025 Aurora commissioning",
            "No per-asset impedance, thermal rating, N-1 actual compliance, or grid connection headroom",
            "Comparisons omit the FCG source's 110kV routes because the OSM >=220kV network does not include them"
        ]
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("FI_2025_SPATIAL_SUMMARY="+json.dumps({
        "has_rights_to_redistribute_fcg":False,
        "operator_verified":False,
        "aggregate":aggregates},sort_keys=True))
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--osm-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args(argv)
    run(a.osm_dir,a.out)


if __name__=="__main__":
    main()
