"""Fingrid operator-border source contracts; simulated values only inside tests."""
from datetime import datetime,timedelta,timezone
from src.schema import OperationalRecord
import pytest
from src.models.verified_border_market import IDS,parse_source,START,END

def obs(i,ts,val):
    stamp=datetime.fromisoformat(ts.replace("Z","+00:00"))
    from src.ingest.fingrid import DATASETS
    return OperationalRecord(source="fingrid",area="FI",dataset_id=str(i),
       metric=DATASETS[i][0],unit="MW",value=val,timestamp_utc=ts,
       interval_end_utc=(stamp+timedelta(minutes=15)).isoformat().replace("+00:00","Z"),
       retrieved_at="2026-10-20T13:00:00Z",
       source_url=f"https://data.fingrid.fi/en/datasets/{i}")

def test_correct_operator_border_source_contract_and_sign():
    assert IDS==(31,32,38,39)
    a=datetime(2025,9,15,tzinfo=timezone.utc)
    b=a+timedelta(days=1)
    x=parse_source([obs(31,"2025-09-15T00:00:00Z",-250.)],31,a,b)
    assert list(x.values())[0]["value"]==-250
    with pytest.raises(ValueError,match="negative unused intraday capacity"):
        parse_source([obs(38,"2025-09-15T00:00:00Z",-1.)],38,a,b)

def test_reject_timestamp_duplicate_or_bad_frequency():
    a=datetime(2025,9,15,tzinfo=timezone.utc)
    b=a+timedelta(days=1)
    r=obs(39,"2025-09-15T00:00:00Z",150)
    with pytest.raises(ValueError,match="Repeated"):
        parse_source([r,r],39,a,b)
    with pytest.raises(ValueError,match="Incompatible"):
        parse_source([obs(39,"2025-09-16T00:00:00Z",1)],39,a,b)
