"""No secret is required to test NLS metadata discovery. Never fetch in CI."""
import io
import pytest
from src.ingest.nls_catalogue import discover, normalize_collections, PRODUCTION, BETA


def test_normalize_metadata_never_labels_assets_as_fingrid():
    result=normalize_collections({"collections":[{"id":"other_structure","title":"Other structures","description":"Cartographic classification"}]})
    assert result==[{"id":"other_structure","title":"Other structures","description":"Cartographic classification"}]
    assert "substation" not in str(result).lower()
    with pytest.raises(ValueError):
        normalize_collections({"not_collections":[]})


class FakeResponse:
    status=200
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self, n): return b'{"collections":[{"id":"sample","title":"Not a station"}]}'


class FakeOpener:
    def __init__(self): self.url=None;self.auth=None
    def open(self,req,timeout):
        self.url=req.full_url
        self.auth=req.get_header("Authorization")
        return FakeResponse()


def test_uses_basic_auth_header_not_url_query():
    fake=FakeOpener()
    rows=discover("SYNTHETIC-TEST-KEY",opener=fake)
    assert rows[0]["id"]=="sample"
    assert fake.url==PRODUCTION+"/collections"
    assert "SYNTHETIC" not in fake.url
    assert fake.auth.startswith("Basic ")


def test_api_key_required_and_no_public_data_assumed():
    with pytest.raises(ValueError, match="NLS_API_KEY"):
        discover("")
    with pytest.raises(ValueError):
        normalize_collections({"collections":[{"missing_id":"x"}]})
