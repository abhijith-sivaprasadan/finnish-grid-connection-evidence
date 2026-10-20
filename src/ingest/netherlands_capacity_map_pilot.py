"""Licence-conservative Netherlands grid-capacity CSV source audit.

Queries official Netbeheer Nederland exports. Writes ONLY schema/field-completeness
and high-level aggregates. Never publishes per-site or per-postcode raw data,
geometry, feature IDs or imagined MW headroom.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT="https://capaciteitskaart.netbeheernederland.nl"
BASE=ROOT+"/api/download/"
FILES={"tennet_hv":"tennetgebieden.csv",
       "tennet_congestion":"tennetcongestie.csv",
       "rnb_feeding_area":"voedingsgebieden.csv"}
MAX_BYTES=70_000_000


def source_bytes(name, *, reader=urlopen):
    if name not in FILES: raise ValueError("Only listed official export assets supported")
    link=BASE+FILES[name]
    req=Request(link, headers={"User-Agent":"FinnishGridAtlas Academic Source Audit/1.0",
                               "Accept":"text/csv,text/plain,*/*"})
    with reader(req, timeout=85) as response:
        data=response.read(MAX_BYTES+1)
    if not data or len(data)>MAX_BYTES: raise ValueError("Official CSV missing or exceeds bounded file size")
    # Refuse HTML redirects to a sign-in or unexpected errors
    head=data[:400].lower()
    if b"<html" in head or b"<!doctype" in head: raise ValueError("Expected raw official CSV, received HTML")
    return link,data


def inspect_csv(name, source, data):
    txt=data.decode("utf-8-sig")
    try:
        delimiter=csv.Sniffer().sniff(txt[:8000], delimiters=";,\\t").delimiter
    except csv.Error as exc:
        raise ValueError("CSV delimiter cannot be verified") from exc
    reader=csv.DictReader(io.StringIO(txt, newline=""), delimiter=delimiter)
    columns=reader.fieldnames
    if not columns or len(columns)!=len(set(columns)) or len(columns)<3:
        raise ValueError("Unknown export schema or delimiter; manual review before claims")
    nonempty=Counter()
    sample_types={name:set() for name in columns}
    count=0
    for row in reader:
        if None in row: raise ValueError("Inconsistent CSV field count")
        count+=1
        for key,val in row.items():
            if val and val.strip():
                nonempty[key]+=1
                # Keep no source values: totals only.
    if count==0: raise ValueError("Official source empty")
    return {
        "source":source,
        "downloaded_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sha256_original_csv":hashlib.sha256(data).hexdigest(),
        "original_bytes":len(data),
        "rows":count,
        "original_columns":columns,
        "delimiter":delimiter,
        "field_nonempty_counts":dict(sorted(nonempty.items())),
        "data_level":"feeding_areas_not_individual_verified_site_connections",
        "original_release_licence":"not_verified_for_raw_redistribution",
        "raw_data_retained_or_published":False,
        "numeric_connectable_MW_claim":None,
        "interpretation":"Official source CSV schema audit only; no licensed derivative raw export nor nodal feasibility.",
    }


def audit(files, reader=urlopen):
    findings={}
    for name in files:
        url,data=source_bytes(name, reader=reader)
        findings[name]=inspect_csv(name,url,data)
    return {
        "status":"SCHEMA_AND_AGGREGATE_COUNTS_ONLY",
        "source_homepage":ROOT+"/info/algemene-info/",
        "source_faq":ROOT+"/info/faq/",
        "source_geography":"Netherlands",
        "operator_provenance":"Netbeheer Nederland national capacity map, not TenneT-approved project request",
        "source_metadata_date":datetime.now(timezone.utc).date().isoformat(),
        "feeds":findings,
        "claims_no_rights_to_connection":True,
        "can_safely_compare_with_fingrid_site_MW":False,
        "no_operator_confirmed_site_headroom":True,
        "raw_data_licence_unresolved":True,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args(argv)
    result=audit(list(FILES))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print("NL_NBN_OFFICIAL_CSV_AUDIT="+json.dumps({
        "feeds":{k:{"rows":v["rows"],"columns":v["original_columns"],
                    "bytes":v["original_bytes"],"sha256":v["sha256_original_csv"]}
                 for k,v in result["feeds"].items()},
        "licensed_raw_export":False,
        "approved_project_capacity":False
    },ensure_ascii=False))


if __name__=="__main__":
    main()
