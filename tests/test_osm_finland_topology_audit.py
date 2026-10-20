"""Synthetic topology fixtures only; no asset below describes Finland."""
import pytest
from src.models.osm_finland_topology_audit import summarize,load_csv


def fixture():
    cols = {
        "buses": ["bus_id", "voltage", "country", "x", "y", "dc", "under_construction"],
        "lines": ["line_id", "bus0", "bus1", "voltage", "r", "x", "b", "length", "circuits", "under_construction"],
        "transformers": ["transformer_id", "bus0", "bus1"],
        "links": ["link_id", "bus0", "bus1"],
        "converters": ["converter_id", "bus0", "bus1"]
    }
    rows = {
        "buses": [dict(bus_id="FI_FAKE_A", country="FI", voltage="400", x="25", y="62", dc="f", under_construction="f"),
                  dict(bus_id="FI_FAKE_B", country="FI", voltage="400", x="26", y="63", dc="f", under_construction="f"),
                  dict(bus_id="SE_FAKE_A", country="SE", voltage="400", x="24", y="62", dc="f", under_construction="f")],
        "lines": [dict(line_id="SYNTHETIC_INTERNAL", bus0="FI_FAKE_A", bus1="FI_FAKE_B", voltage="400", r="1.2", x="5.1", b="0.003", length="55", circuits="1", under_construction="f"),
                  dict(line_id="SYNTHETIC_BORDER", bus0="FI_FAKE_A", bus1="SE_FAKE_A", voltage="400", r="1.5", x="4.3", b="", length="35", circuits="1", under_construction="f")],
        "transformers": [], "links": [], "converters": []
    }
    return {name: (rows[name], cols[name]) for name in cols}


def test_source_boundary_inventory_no_invented_thermal_ratings():
    report, extracted = summarize(fixture(), {"example": {"source_md5_verified": True}})
    assert report["geographic_inventory"]["fi_all_buses_including_dc"] == 2
    assert report["geographic_inventory"]["domestic_edge_counts"]["lines"] == 1
    assert report["geographic_inventory"]["cross_border_edge_counts"]["lines"] == 1
    assert extracted["lines"][0]["line_id"] == "SYNTHETIC_INTERNAL"
    assert report["electrical_parameter_inventory_ac_lines"]["x"]["populated_and_finite"] == 1
    assert report["electrical_parameter_inventory_ac_lines"]["s_nom"]["missing"] == 1
    assert report["operator_verified_physical_network"] is False
    assert report["approved_site_connection_headroom_mw"] is None


def test_missing_or_invalid_impedance_remains_missing():
    t = fixture()
    t["lines"][0][0]["x"] = ""
    t["lines"][0][0]["b"] = "NaN"
    report, _ = summarize(t, {})
    assert report["electrical_parameter_inventory_ac_lines"]["x"]["missing"] == 1
    assert report["electrical_parameter_inventory_ac_lines"]["b"]["invalid"] == 1
    assert not report["all_domestic_ac_lines_have_source_r_x_b"]


def test_fail_closed_without_finland_or_geo_coordinates():
    t = fixture()
    for row in t["buses"][0]:
        row["country"] = "SE"
    with pytest.raises(ValueError, match="No Finland"):
        summarize(t, {})
    t = fixture()
    t["buses"][0][0]["x"] = ""
    with pytest.raises(ValueError, match="geocoordinates"):
        summarize(t, {})


def test_csv_original_quote_convention_and_duplicate_ids(tmp_path):
    p = tmp_path / "buses.csv"
    p.write_text("bus_id,voltage,country,tags\nFAKE_1,400,FI,'line, with comma'\n", encoding="utf-8")
    rows, _ = load_csv(p, "bus_id")
    assert rows[0]["tags"] == "line, with comma"
    p.write_text("bus_id,voltage,country\nX,400,FI\nX,220,FI\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate original ID"):
        load_csv(p, "bus_id")
