"""Artificial graphs and fake line records; none represent Finnish grid assets."""
from copy import deepcopy
import pytest
from src.models.fi_proxy_n1_audit import components, electrical_template_audit, n1_structural_audit


def fixture():
    return {
        "buses": [{"bus_id": x, "dc": "f"} for x in "ABCD"],
        "lines": [dict(line_id="SYNTHETIC_"+name, bus0=left, bus1=right,
                       voltage="400", circuits="1", length="100000",
                       r="3.0", x="24.6", b="0.0004335",
                       i_nom="2.58", s_nom="1787.476", type="FAKE_TYPE")
                  for name,left,right in [("AB","A","B"), ("BC","B","C"),
                                          ("CA","C","A"), ("CD","C","D")]],
        "transformers": []
    }


def test_single_edge_bridge_and_ring_edges():
    result = n1_structural_audit(fixture())
    assert result["source_ac_plus_transformer_component_sizes"] == [4]
    assert result["single_edge_removals_causing_graph_disconnection"] == 1
    assert result["critical_source_edge_records"][0]["source_id"] == "SYNTHETIC_CD"
    assert result["critical_source_edge_records"][0]["component_sizes_after_single_edge_removal"] == [3,1]


def test_parallel_source_edges_are_not_bridges():
    data=fixture()
    data["lines"].append({**data["lines"][-1], "line_id": "SYNTHETIC_CD_TWO"})
    assert n1_structural_audit(data)["single_edge_removals_causing_graph_disconnection"] == 0


def test_identical_source_conductor_templates_and_derived_nominal_rating():
    out = electrical_template_audit(fixture()["lines"])
    assert out["s_nom_matches_sqrt3_voltage_current_circuits"]
    assert out["all_137_source_lines_fit_voltage_templates"]
    assert abs(out["by_voltage"]["400"]["templates"]["x_per_km_per_circuit"]["median_source_parameter"]-0.246)<1e-9


def test_double_circuit_normalization_keeps_single_template():
    data=fixture()
    line=deepcopy(data["lines"][0])
    line.update(line_id="SYNTHETIC_2C", circuits="2", r="1.5", x="12.3",
                b="0.000867", s_nom="3574.953")
    data["lines"].append(line)
    assert electrical_template_audit(data["lines"])["all_137_source_lines_fit_voltage_templates"]


@pytest.mark.parametrize("field,value",[
    ("length","0"),("x","nan"),("r",""),("circuits","1.5"),
    ("s_nom","100"),("voltage","110"),("b","-0.2")
])
def test_unverified_or_invalid_electrical_parameter_rejected(field,value):
    data=fixture()
    data["lines"][0][field]=value
    with pytest.raises(ValueError):
        electrical_template_audit(data["lines"])


def test_dangling_unknown_source_ids_fail():
    with pytest.raises(ValueError,match="Unknown source"):
        components({"A","B"},[{"bus0":"A","bus1":"Z"}])
    data=fixture()
    data["lines"][0]["bus0"]="UNKNOWN"
    with pytest.raises(ValueError,match="Unknown source"):
        n1_structural_audit(data)
