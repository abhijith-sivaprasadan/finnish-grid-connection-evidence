"""Synthetic contracts only. None of these IDs, values, or lines describe Finland."""
from copy import deepcopy
import pytest
from src.models.physical_grid_evidence_gate import audit

BASE = {
    "country": "FI", "study_year": 2025,
    "buses": [
        {"id": "SYNTHETIC_A", "voltage_kv": 400, "parameter_evidence": "proxy_estimate",
         "evidence_url": "https://example.org/imaginary-source-a", "captured_utc": "2026-10-20T15:00:00Z"},
        {"id": "SYNTHETIC_B", "voltage_kv": 400, "parameter_evidence": "proxy_estimate",
         "evidence_url": "https://example.org/imaginary-source-b", "captured_utc": "2026-10-20T15:00:00Z"}
    ],
    "ac_lines": [{
        "id": "SYNTHETIC_TEST_LINE_ONLY", "bus0": "SYNTHETIC_A", "bus1": "SYNTHETIC_B",
        "kind": "AC_overhead_or_cable", "voltage_kv": 400,
        "r_ohm": 1.0, "x_ohm": 10.0, "b_siemens": 0.0001,
        "length_km": 20.0, "thermal_rating_mva": 1500.0,
        "parameter_evidence": "proxy_estimate",
        "evidence_url": "https://example.org/imaginary-line-source",
        "captured_utc": "2026-10-20T15:00:00Z"
    }]
}


def test_complete_synthetic_data_are_never_claimed_operator_validated():
    out = audit(deepcopy(BASE))
    assert out["structurally_screenable"]
    assert out["proxy_parameter_line_count"] == 1
    assert out["operator_verified_physical_network"] is False
    assert out["validated_site_connection_headroom_mw"] is None


@pytest.mark.parametrize("field,value,match", [
    ("x_ohm", None, "finite number"),
    ("x_ohm", 0, "invalid nonnegative"),
    ("x_ohm", float("nan"), "invalid nonnegative"),
    ("thermal_rating_mva", -1, "invalid nonnegative"),
    ("r_ohm", -1, "invalid nonnegative"),
    ("market_capacity_mw", 1000, "market capacity"),
    ("kind", "HVDC", "do not model DC"),
    ("voltage_kv", 110, "voltage mismatch"),
    ("evidence_url", "", "specific HTTPS")
])
def test_rejects_unsourced_or_nonphysical_branch_fields(field, value, match):
    data = deepcopy(BASE)
    data["ac_lines"][0][field] = value
    with pytest.raises(ValueError, match=match):
        audit(data)


def test_rejects_invented_site_approval_and_bus_identity():
    data = deepcopy(BASE)
    data["site_connection_approved"] = True
    with pytest.raises(ValueError, match="Site connection approval"):
        audit(data)
    data = deepcopy(BASE)
    data["buses"][1]["id"] = data["buses"][0]["id"]
    with pytest.raises(ValueError, match="unique nonempty"):
        audit(data)


def test_rejects_unregistered_branch_and_cross_voltage_transformer():
    data = deepcopy(BASE)
    data["ac_lines"][0]["bus1"] = "UNVERIFIED_NODE"
    with pytest.raises(ValueError, match="registered buses"):
        audit(data)
    data = deepcopy(BASE)
    data["buses"][1]["voltage_kv"] = 220
    with pytest.raises(ValueError, match="transformers need"):
        audit(data)


def test_no_empty_study_can_be_marked_complete():
    data = deepcopy(BASE)
    data["ac_lines"] = []
    with pytest.raises(ValueError, match="nonempty"):
        audit(data)
