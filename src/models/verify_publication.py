"""Publication gate: only real solver output matching the attributed site JSON ships."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_PUBLIC=ROOT/"website/src/lib/pypsa-scenario-results.json"


def verify(published:dict, solved:dict)->None:
    if published.get("publication_status")!="verified_solver_output":
        raise ValueError("Unverified model output cannot appear as a published result")
    if published.get("verified_operator_connectability") is not False:
        raise ValueError("No claim of operator-confirmed grid headroom is permitted")
    for key in ("model_version","classification","source","observed_input_sha256",
                "source_window_utc","assumptions","limitations","source_urls"):
        if published.get(key)!=solved.get(key):
            raise ValueError(f"Changed or mismatched model provenance: {key}")
    left=published.get("scenarios",[])
    right=solved.get("scenarios",[])
    if len(left)!=4 or len(right)!=4:
        raise ValueError("Expected exactly four actually solved scenarios")
    for source,actual in zip(left,right):
        if set(source)!=set(actual) or source["scenario"]!=actual["scenario"]:
            raise ValueError("Published schema/scenarios differ from solver")
        for key in actual:
            a,b=source[key],actual[key]
            if isinstance(b,(float,int)) and not isinstance(b,bool):
                if abs(float(a)-float(b))>0.01:
                    raise ValueError(f"Published {source['scenario']} {key} is not solver-derived")
            elif a!=b:
                raise ValueError(f"Published {source['scenario']} {key} differs")
        if source["solver_status"]!="ok" or source["termination"]!="optimal":
            raise ValueError("No unoptimal model output allowed")
        if source["max_model_balance_error_mw"]>1e-5:
            raise ValueError("An unbalanced scenario cannot be reported")
    if len(solved.get("intervals",[]))!=192*4:
        raise ValueError("Solver did not yield every snapshot for all four scenarios")
    if published["model_resolution"]!=solved["model_resolution"]:
        raise ValueError("Published geographic/model scope changed")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--solved",required=True,type=Path)
    p.add_argument("--published",type=Path,default=DEFAULT_PUBLIC)
    a=p.parse_args()
    verify(json.loads(a.published.read_text(encoding="utf-8")),
           json.loads(a.solved.read_text(encoding="utf-8")))
    print("PASS: 4 site-published PyPSA summaries match actual optimal solver output, original input hash and source limitations.")


if __name__=="__main__":
    main()
