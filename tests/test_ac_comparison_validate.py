"""No solver needed: validate the comparison gate itself without invented claims."""
import pytest
from src.models.ac_comparison_validate import compare

def fixture(solver):
 return {"solver":solver,"reference":"3bus",
         "source_parameters":{"x":1.2},
         "actual_full_AC_PF":{"bus_v_pu":{"A":1.0,"B":.99},
                              "line_from_p_mw":{"A-B":10.}}}

def test_independent_outputs_must_agree_and_models_equal():
 a,b=fixture("pandapower"),fixture("pypsa")
 assert compare(a,b)["within_predeclared_tolerance"]
 b["actual_full_AC_PF"]["bus_v_pu"]["B"]=.8
 assert not compare(a,b)["within_predeclared_tolerance"]
 b["source_parameters"]={"x":2.2}
 with pytest.raises(ValueError,match="identical"):compare(a,b)
