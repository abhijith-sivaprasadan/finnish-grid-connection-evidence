"""Read-only NLS OGC API Features *metadata discovery* for future inventory sourcing.

The service has many collections; this module does NOT assume any of them
represents Fingrid substations. No feature is ingested, mapped or published.
The API key is sent as HTTP Basic auth, never as a URL query parameter.
"""
from __future__ import annotations
import argparse
import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

PRODUCTION = "https://avoin-paikkatieto.maanmittauslaitos.fi/maastotiedot/features/v1"
BETA = "https://open-api-geospatial.nls.fi/api/topodb/open-data/features/v1"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("NLS API redirected; inspect the service separately before using credentials")


def normalize_collections(document: dict) -> list[dict[str, str]]:
    """Return only human-readable metadata; do not infer substations from titles."""
    if not isinstance(document, dict) or not isinstance(document.get("collections"), list):
        raise ValueError("Unexpected OGC collections document")
    output = []
    for item in document["collections"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("Malformed OGC collection")
        output.append({
            "id": item["id"],
            "title": item.get("title", "") if isinstance(item.get("title", ""), str) else "",
            "description": item.get("description", "")[:500]
                if isinstance(item.get("description", ""), str) else "",
        })
    return output


def discover(key: str, *, beta: bool = False, opener=None) -> list[dict[str,str]]:
    if not key or any(ch.isspace() for ch in key):
        raise ValueError("Set the NLS_API_KEY environment variable to a valid key")
    root = BETA if beta else PRODUCTION
    authorization = base64.b64encode((key + ":").encode("utf-8")).decode("ascii")
    request = Request(root + "/collections", headers={
        "Accept": "application/json",
        "Authorization": "Basic " + authorization,
        "User-Agent": "FinnishGridAtlasResearch/1.0"
    })
    handler = opener or build_opener(NoRedirect)
    try:
        with handler.open(request, timeout=25) as response:
            if response.status != 200:
                raise ValueError("NLS metadata request did not succeed")
            payload = response.read(4_000_001)
        if len(payload) > 4_000_000:
            raise ValueError("NLS metadata response too large")
        return normalize_collections(json.loads(payload))
    except (HTTPError, URLError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        # Do not interpolate exceptions; they may include headers, URL or secrets.
        raise ValueError("NLS metadata retrieval failed; check API key, service version and network") from None


def main(argv=None):
    parser=argparse.ArgumentParser(description="List NLS geospatial collection metadata; no data import")
    parser.add_argument("--beta", action="store_true", help="Use 2026 beta endpoint (not refreshed during beta)")
    parser.add_argument("--output", help="Optional local metadata output JSON (public descriptors only)")
    args=parser.parse_args(argv)
    try:
        rows=discover(os.environ.get("NLS_API_KEY", ""), beta=args.beta)
        result={"endpoint":"beta" if args.beta else "production", "collections":rows,
                "warning":"Metadata discovery only. No collection has been certified as a Fingrid substation inventory."}
        text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            from pathlib import Path
            Path(args.output).write_text(text,encoding="utf-8")
        print(text,end="")
    except ValueError as error:
        parser.exit(2,str(error)+"\n")


if __name__ == "__main__":
    main()
