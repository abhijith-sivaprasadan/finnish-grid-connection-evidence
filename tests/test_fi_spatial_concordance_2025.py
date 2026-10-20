"""Synthetic geometries only: NOT actual Finnish transmission lines."""
from pathlib import Path
import json
import pytest
from src.models.fi_spatial_concordance_2025 import (
    check_metadata, prepare_pairs, sample_distances, audit_spatial,
    load_osm_lines, ITEM_ID, SVC_OWNER
)


def meta():
    return ({"id":ITEM_ID,"owner":SVC_OWNER,"snippet":"Keräyspäivä 22.2.2025",
             "access":"public","licenseInfo":""},
            {"geometryType":"esriGeometryPolyline","fields":[
                {"name":"FID"},{"name":"Tyyppi"}]})


def test_unknown_hosted_data_licence_forces_no_redistribution():
    item,layer=meta()
    evidence=check_metadata(item,layer)
    assert evidence["permission_to_redistribute_FCG_geometry"] is False
    assert evidence["rights_status"]=="UNKNOWN_HOLD_ALL_RAW_FCG_GEOMETRY"
    assert not evidence["confirmed_Fingrid_equipment_database"]


def test_changed_source_owner_or_collection_date_must_fail():
    item,layer=meta()
    item["owner"]="UNRECOGNIZED_THIRD_PARTY"
    with pytest.raises(ValueError,match="ID/owner"):
        check_metadata(item,layer)
    item,layer=meta()
    item["snippet"]="unknown scrape time"
    with pytest.raises(ValueError,match="collection date"):
        check_metadata(item,layer)


def test_voltage_specific_spatial_comparison():
    pytest.importorskip("shapely")
    pytest.importorskip("pyproj")
    # Two tiny invented lines in WGS84 Helsinki-like range. Zero operator source.
    osm=[{"line_id":"SYNTHETIC400","voltage":"400",
          "geometry":"LINESTRING (25 61,25 61.04)"},
         {"line_id":"SYNTHETIC220","voltage":"220",
          "geometry":"LINESTRING (27 65,27 65.04)"}]
    mirror=[
        {"properties":{"FID":1,"Tyyppi":"400"},
         "geometry":{"type":"LineString","coordinates":[[25.0005,61],[25.0005,61.04]]}},
        {"properties":{"FID":2,"Tyyppi":"220"},
         "geometry":{"type":"LineString","coordinates":[[27.01,65],[27.01,65.04]]}}]
    source,comp=prepare_pairs(osm,mirror)
    summary=audit_spatial(source,comp)
    assert summary["400"]["sample_share_within_1000m"] == 1
    assert summary["220"]["sample_share_within_5000m"] == 1
    assert summary["400"]["route_midpoint_samples"]>1
    assert summary["400"]["source_routes_at_least_80pct_within_1000m"]==1


def test_false_spatial_match_and_duplicate_hosted_voltage_guard():
    pytest.importorskip("pyproj")
    LineString = pytest.importorskip("shapely.geometry").LineString
    near=LineString([(0,0),(10000,0)])
    far=LineString([(0,50000),(10000,50000)])
    assert min(sample_distances([near],[far])[0]) > 49000
    osm=[{"voltage":"400","geometry":"LINESTRING (25 61,25 61.05)"},
         {"voltage":"220","geometry":"LINESTRING (24 62,24 62.05)"}]
    hosted=[{"properties":{"FID":1,"Tyyppi":"400"},
             "geometry":{"type":"LineString","coordinates":[[25,61],[25,61.05]]}},
            {"properties":{"FID":2,"Tyyppi":"110"},
             "geometry":{"type":"LineString","coordinates":[[24,62],[24,62.05]]}}]
    with pytest.raises(ValueError,match="Unexpected 110"):
        prepare_pairs(osm,hosted)


def test_source_osm_audit_requires_odbl_and_checksums(tmp_path):
    source=tmp_path/"fi_lines.csv"
    source.write_text("line_id,voltage,geometry\nFAKE_1,400,\"LINESTRING (25 61,25 61.01)\"\n",encoding="utf-8")
    audit=tmp_path/"audit.json"
    proof={"record":"https://doi.org/10.5281/zenodo.14144752",
           "dataset_licence":"ODbL-1.0","source_release":"0.6",
           "operator_verified_physical_network":False,
           "original_source_verified":{"lines.csv":{"source_md5_verified":True}}}
    audit.write_text(json.dumps(proof))
    assert len(load_osm_lines(source,audit))==1
    proof["dataset_licence"]="MIT"
    audit.write_text(json.dumps(proof))
    with pytest.raises(ValueError,match="original/licence"):
        load_osm_lines(source,audit)
