# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline fail-closed PDOK parcel OGC cursor-page assembly.

Use only after obtaining a legally permitted, bounded set of original provider
GeoJSON pages. The exact URL self/next chain is checked with canonical query
parsing, as are strict safe fields, unique source IDs, page counts, CRS84
geometries, query bounds, and timestamp gaps. Only the private combined
FeatureCollection may contain original feature bytes; NEVER commit it to Git.

Paging does not freeze a mutable provider's snapshot: preserve first/last
request timestamps, and do NOT assert a common transactional data vintage.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit

if __package__:
    from .audit_pdok_brk_bag_centroid_v0 import (
        _bbox, _collection, ParcelBagError, load,
    )
else:
    from audit_pdok_brk_bag_centroid_v0 import (
        _bbox, _collection, ParcelBagError, load,
    )

ROOT = Path(__file__).resolve().parents[1]
PATH = "/kadaster/brk-kadastrale-kaart/ogc/v1/collections/perceel/items"
MAX_PAGES = 50
MAX_FEATURES = 500
MAX_PAGE_LIMIT = 50
MAX_TOTAL_BYTES = 3_000_000
MAX_ELAPSED_SECONDS = 3600


def _private_file(path):
    p = Path(path).resolve()
    if p == ROOT or ROOT in p.parents:
        raise ParcelBagError("original PDOK bytes may not be saved inside Git checkout")
    return p


def _pdok_query(url, bbox, limit):
    if not isinstance(url, str):
        raise ParcelBagError("missing provider self/next URL")
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "api.pdok.nl" or parts.path != PATH or parts.fragment:
        raise ParcelBagError("untrusted OGC pagination URL")
    try:
        q = parse_qs(parts.query, keep_blank_values=True, strict_parsing=True)
        if set(q) - {"bbox", "limit", "f", "cursor"}:
            raise ParcelBagError("unexpected OGC pagination query field")
        if any(len(v) != 1 for v in q.values()) or not {"bbox", "limit", "f"} <= q.keys():
            raise ParcelBagError("missing or duplicate OGC pagination parameter")
        if int(q["limit"][0]) != limit or q["f"][0] != "json":
            raise ParcelBagError("incorrect page limit or JSON format")
        vals = _bbox([float(v) for v in q["bbox"][0].split(",")])
        if any(abs(a - b) > 1e-9 for a, b in zip(vals, bbox)):
            raise ParcelBagError("page bbox changed during pagination")
    except (KeyError, TypeError, ValueError) as exc:
        raise ParcelBagError("invalid OGC pagination query parameters") from exc
    cursor = q.get("cursor", [None])[0]
    if cursor is not None and (not cursor or len(cursor) > 256):
        raise ParcelBagError("invalid OGC cursor")
    return cursor


def _link(page, rel):
    links = page.get("links")
    if not isinstance(links, list):
        raise ParcelBagError("OGC page links missing")
    hits = [row.get("href") for row in links
            if isinstance(row, dict) and row.get("rel") == rel]
    if len(hits) > 1 or any(not isinstance(url, str) for url in hits):
        raise ParcelBagError("ambiguous OGC page link")
    if rel == "self" and len(hits) != 1:
        raise ParcelBagError("missing OGC self link")
    return hits[0] if hits else None


def assemble(pages, *, bbox, limit):
    bounds = _bbox(bbox)
    if type(limit) is not int or not 1 <= limit <= MAX_PAGE_LIMIT:
        raise ParcelBagError("invalid bounded OGC page limit")
    if not isinstance(pages, list) or not 1 <= len(pages) <= MAX_PAGES:
        raise ParcelBagError("invalid page count")
    output, ids, expected_cursor, stamps = [], set(), None, []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ParcelBagError("page must be an object")
        cursor = _pdok_query(_link(page, "self"), bounds, limit)
        if index == 0 and cursor is not None:
            raise ParcelBagError("first page contains a cursor")
        if index and cursor != expected_cursor:
            raise ParcelBagError("broken OGC next/self cursor chain")
        if index and expected_cursor is None:
            raise ParcelBagError("previous page did not advertise continuation")
        next_url = _link(page, "next")
        next_cursor = _pdok_query(next_url, bounds, limit) if next_url else None
        if index < len(pages) - 1 and next_cursor is None:
            raise ParcelBagError("truncated OGC pagination")
        if index == len(pages) - 1 and next_cursor is not None:
            raise ParcelBagError("last OGC page still has next link")
        if next_cursor is not None and next_cursor == cursor:
            raise ParcelBagError("OGC page repeats its cursor")

        # Reuse strict CRS84, ID, forbidden owner/address-field and size gates.
        # _collection rightly rejects incomplete pages, so remove only
        # the original next relation in a LOCAL validation copy.
        checked = {**page, "links": [x for x in page["links"]
                                    if not (isinstance(x, dict) and x.get("rel") == "next")]}
        stamp, rows = _collection(checked, "parcel", bounds)
        if len(rows) > limit:
            raise ParcelBagError("OGC page exceeds declared limit")
        for object_id, _properties, _polygons in rows:
            if object_id in ids:
                raise ParcelBagError("duplicate parcel ID across pages")
            ids.add(object_id)
        output.extend(page["features"])
        stamps.append(stamp)
        expected_cursor = next_cursor
        if len(output) > MAX_FEATURES:
            raise ParcelBagError("combined feature budget exceeded")
    gap = (max(stamps) - min(stamps)).total_seconds()
    if gap > MAX_ELAPSED_SECONDS:
        raise ParcelBagError("pagination spans more than one hour")
    final_time = max(stamps).isoformat().replace("+00:00", "Z")
    first_time = min(stamps).isoformat().replace("+00:00", "Z")
    combined = {
        "type": "FeatureCollection",
        "timeStamp": final_time,
        "links": [],
        "numberReturned": len(output),
        "features": output,
        "_research_assembly_receipt": {
            "original_page_count": len(pages),
            "distinct_parcel_features": len(output),
            "first_provider_timestamp": first_time,
            "last_provider_timestamp": final_time,
            "timestamp_gap_seconds": int(gap),
            "page_limit": limit,
            "bbox_crs": "OGC:CRS84",
            "bbox": list(bounds),
            "complete_link_chain_observed": True,
            "atomic_provider_snapshot_verified": False,
            "data_rights_or_model_admission_verified": False,
        },
    }
    return combined


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", nargs="+", type=Path, required=True,
                        help="Ordered original PDOK GeoJSON page files, PRIVATE paths only")
    parser.add_argument("--bbox", required=True)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True,
                        help="Private assembled GeoJSON outside Git checkout")
    args = parser.parse_args(argv)
    try:
        if len(args.pages) > MAX_PAGES:
            raise ParcelBagError("too many pages")
        dest = _private_file(args.out)
        source_paths = [_private_file(p) for p in args.pages]
        if dest in source_paths:
            raise ParcelBagError("source and destination may not be identical")
        if sum(p.stat().st_size for p in source_paths) > MAX_TOTAL_BYTES:
            raise ParcelBagError("input page bytes exceed 3 MB budget")
        result = assemble([load(p) for p in source_paths],
                          bbox=[float(x) for x in args.bbox.split(",")],
                          limit=args.limit)
        data = json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n"
        if len(data.encode("utf-8")) > MAX_TOTAL_BYTES:
            raise ParcelBagError("output exceeds 3 MB research budget")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(data, encoding="utf-8")
        dest.chmod(0o600)
    except (ValueError, OSError, UnicodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    receipt = result["_research_assembly_receipt"]
    print(json.dumps({
        **receipt, "analysis_only": True,
        "output_sha256": hashlib.sha256(data.encode()).hexdigest(),
        "source_admitted": False, "model_input_approved": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
