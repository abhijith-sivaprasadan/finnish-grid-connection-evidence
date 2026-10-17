"""Run from repo root with python -m src.cli."""
import argparse
import json
from pathlib import Path
import sqlite3
from src.db import ROOT, connect, insert
from src.ingest.manual_grid_scope import ingest
from src.ingest.http import HttpClient, SourceError
from src.quality import report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, help="SQLite path (default data/evidence.sqlite)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    manual = commands.add_parser("import-manual")
    manual.add_argument("--directory", type=Path, default=ROOT / "data" / "manual")
    commands.add_parser("quality")
    for name in ("fingrid", "entsoe"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--start", required=True, help="ISO 8601 timestamp with timezone")
        cmd.add_argument("--end", required=True, help="Exclusive ISO 8601 end timestamp")
        if name == "fingrid":
            cmd.add_argument("--datasets", nargs="+", type=int, default=[124, 74])
        else:
            cmd.add_argument("--kind", choices=["load", "generation"], default="load")
    args = parser.parse_args(argv)
    try:
        if args.command == "import-manual":
            result = ingest(args.directory, args.db)
        elif args.command in {"init", "quality"}:
            with connect(args.db) as conn:
                result = report(conn)
        else:
            client = HttpClient()
            if args.command == "fingrid":
                from src.ingest.fingrid import fetch
                records = [r for dataset in args.datasets for r in fetch(dataset, args.start, args.end, client=client)]
            else:
                from src.ingest.entsoe import fetch
                records = fetch(args.kind, args.start, args.end, client=client)
            if not records:
                raise ValueError("No source records returned; database left unchanged")
            with connect(args.db) as conn:
                result = {"inserted": sum(insert(conn, row) for row in records), "category": "operational_context"}
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error, SourceError) as exc:
        parser.exit(2, f"Import stopped: {exc}\n")


if __name__ == "__main__":
    main()
