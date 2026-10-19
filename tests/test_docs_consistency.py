"""Canonical status, audit boundaries and immutable original capture."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]

def test_original_grid_scope_source_has_pinned_git_blob():
    data=(ROOT/"data/manual/grid_scope_observations.csv").read_bytes()
    actual=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    assert actual=="a37421a80d79c0005702fb80136827b490d2d9fa"

def test_active_docs_do_not_claim_disconnected_production_or_unchecked_original():
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    web=(ROOT/"website/README.md").read_text(encoding="utf-8")
    status=(ROOT/"docs/STATUS.md").read_text(encoding="utf-8")
    legacy=(ROOT/"web/README.md").read_text(encoding="utf-8")
    for text in (readme,web,status):
        assert "Vercel remains disconnected" not in text
        assert "No background schedule is enabled yet" not in text
    assert "18" in status and "screenshots" in status
    assert "not" in status.lower() and "headroom" in status.lower()
    assert "archived" in legacy.lower() and "website/" in legacy
    assert "docs/STATUS.md" in readme

def test_private_screenshot_files_not_in_public_audit():
    audit=ROOT/"docs/audits"
    assert not list(audit.rglob("*.png"))
    assert not list(audit.rglob("*.jpg"))
