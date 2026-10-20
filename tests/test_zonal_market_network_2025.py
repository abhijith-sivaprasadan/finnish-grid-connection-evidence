"""No generated original observations: network model has strict source fingerprint gates."""
from pathlib import Path
import pytest
from src.models.zonal_market_network_2025 import (
    load_pinned_sources,CORRIDORS,FLEX_SPANS,STORAGE_HOURS,ORIGINAL_INTERVALS)

def test_corridors_and_model_dimensions():
    assert CORRIDORS==("SE1+SE3","SE1_only","SE3_only")
    assert len(CORRIDORS)*len(FLEX_SPANS)*len(STORAGE_HOURS)==24
    assert ORIGINAL_INTERVALS==30*96

def test_missing_unverified_inputs_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_pinned_sources(tmp_path/"operator-border.csv",tmp_path/"operator-national.csv")

def test_false_original_source_checksum_rejected(tmp_path):
    p=tmp_path/"fake.csv"
    p.write_text("timestamp_utc,garbage\n2025-09-15T00:00Z,0\n")
    with pytest.raises(ValueError,match="SHA-256"):
        load_pinned_sources(p,p)
