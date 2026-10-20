"""Only invented CSVs. Do not replace official operator results with fixtures."""
from io import BytesIO
import pytest
from src.ingest.netherlands_capacity_map_pilot import inspect_csv,source_bytes,audit


def test_official_csv_schema_stats_do_not_leak_rows_or_fabricate_capacity():
    data=("voedingsgebied;afname;wachtrij;status\n"
          "FAKE_LOCATION_123;9;2;ROOD\n"
          "FAKE_LOCATION_456;;1;GEEL\n").encode()
    out=inspect_csv("rnb_feeding_area","https://capaciteitskaart.netbeheernederland.nl/api/download/voedingsgebieden.csv",data)
    assert out["rows"]==2
    assert out["original_columns"]==["voedingsgebied","afname","wachtrij","status"]
    assert out["field_nonempty_counts"]["afname"]==1
    assert out["raw_data_retained_or_published"] is False
    assert out["numeric_connectable_MW_claim"] is None
    assert "FAKE_LOCATION" not in str(out)
    assert len(out["sha256_original_csv"])==64


def test_comma_separated_export_is_accepted():
    data=b"area,colour,queue\nFAKE,RED,3\n"
    assert inspect_csv("tennet_hv","official",data)["rows"]==1


@pytest.mark.parametrize("data",[b"",b"<html>not csv</html>",b"only_one_field\nx\n"])
def test_missing_non_csv_schema_cannot_be_silently_accepted(data):
    if data.startswith(b"only"):
        with pytest.raises(ValueError):
            inspect_csv("tennet_hv","official",data)
    else:
        class Reader:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,_):return data
        with pytest.raises(ValueError):
            source_bytes("tennet_hv",reader=lambda *_a,**_kw:Reader())


def test_refuse_unlisted_sources_and_malformed_rows():
    with pytest.raises(ValueError,match="official"):
        source_bytes("personal_records",reader=None)
    with pytest.raises(ValueError,match="field count"):
        inspect_csv("rnb","official",b"area;colour;other\n1;red;ok;extra\n")
