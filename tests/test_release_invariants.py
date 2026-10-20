"""Adversarial mutations: publication/source drift MUST fail, not only happy path."""
import json
from pathlib import Path
import shutil
import pytest
from src.db import ROOT
from src.audit_release_invariants import run

FILES=[
 "data/manual/connection_points.csv",
 "data/manual/grid_scope_observations.csv",
 "docs/audits/GRID_SCOPE_18_ROW_SCREENSHOT_RECHECK_2026_10_19.csv",
 "data/model_inputs/fingrid_20261015_20261016_15min.csv",
 "website/src/lib/snapshot.ts",
 "website/src/lib/grid-scope-audit.json",
 "website/src/lib/finland-observed.json",
 "website/src/lib/pypsa-scenario-results.json",
 "website/src/lib/krios-engineering-verified-2026.json",
 "website/src/lib/fingrid-archive-coverage-2025.json",
 "website/src/lib/netherlands-official-source-summary-2026.json",
]

@pytest.fixture
def copied(tmp_path):
    for name in FILES:
        target=tmp_path/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,target)
    return tmp_path

def edited(root,name,old,new):
    file=root/name
    s=file.read_text(encoding="utf8")
    assert old in s
    file.write_text(s.replace(old,new,1),encoding="utf8")

def test_dated_release_publication_is_internally_reproducible(copied):
    report=run(copied)
    assert report["historical_indicative_records"]==18
    assert report["source_original_2026_native_intervals"]==192
    assert report["operator_confirmed_site_connectable_mw"] is None
    assert report["original_screenshot_image_bytes_independently_reverified"] is False

@pytest.mark.parametrize("filename,original,tampered",[
 ("data/manual/grid_scope_observations.csv",",2026,500,MW",",2026,501,MW"),
 ("website/src/lib/snapshot.ts",'["VUOLIJOKI", "production", 2026, 500]','["VUOLIJOKI", "production", 2026, 600]'),
 ("website/src/lib/grid-scope-audit.json",'"shown_value": 500','"shown_value": 501'),
 ("website/src/lib/finland-observed.json",'"consumption_mw": 8531.23','"consumption_mw": 8532.23'),
 ("website/src/lib/pypsa-scenario-results.json",'"observed_input_sha256": "ab0316','"observed_input_sha256": "bb0316'),
 ("website/src/lib/krios-engineering-verified-2026.json",'"real_network": false','"real_network": true'),
 ("website/src/lib/netherlands-official-source-summary-2026.json",'"row_count": 271','"row_count": 272'),
])
def test_source_and_claim_tampering_blocks_release(copied,filename,original,tampered):
    edited(copied,filename,original,tampered)
    with pytest.raises(AssertionError):
        run(copied)
