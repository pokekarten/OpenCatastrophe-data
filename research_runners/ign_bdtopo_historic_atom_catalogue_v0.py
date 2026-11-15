#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded research-only IGN Géoplateforme historic BD TOPO Atom catalogue preflight.

Reads ORIGINAL *metadata* XML pages provided locally. Does not acquire/redistribute
any actual building archive, infer 2016 building existence, or admit CAT inputs.

For live acquisition, use the documented official GetCapabilities / GetResource
endpoints with zone D077 and editionDateFrom/To; store response bytes outside
Git, then pass each page here. A 403 is an access blocker, not 'zero products'.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

ATOM = "{http://www.w3.org/2005/Atom}"
BASE = "https://data.geopf.fr/telechargement"
MAX_BYTES = 2_000_000
MAX_PAGES = 100
MAX_ENTRIES_PER_PAGE = 50
VALID_ZONES = frozenset({"D077"})
VALID_RESOURCE = frozenset({"BD-TOPO"})
DATE_FROM = "2015-01-01"
DATE_TO = "2016-12-31"


class CatalogueError(ValueError):
    """Missing or unsafe metadata; fail closed."""


def catalogue_url(*, zone: str = "D077", resource: str = "BD-TOPO",
                  page: int = 1, limit: int = 50) -> str:
    if zone not in VALID_ZONES or resource not in VALID_RESOURCE:
        raise CatalogueError("unreviewed geography or product")
    if not isinstance(page, int) or not 1 <= page <= MAX_PAGES:
        raise CatalogueError("invalid catalogue page")
    if not isinstance(limit, int) or not 1 <= limit <= MAX_ENTRIES_PER_PAGE:
        raise CatalogueError("invalid page size")
    query = urlencode({
        "zone": zone, "editionDateFrom": DATE_FROM, "editionDateTo": DATE_TO,
        "page": page, "limit": limit, "lang": "fre",
    })
    return f"{BASE}/resource/{resource}?{query}"


def _text(element: ET.Element, child: str) -> str:
    node = element.find(ATOM + child)
    return (node.text or "").strip() if node is not None else ""


def _local_name(tag: str) -> str:
    return tag.rpartition("}")[2] if "}" in tag else tag


def parse_atom_page(raw: bytes) -> dict[str, Any]:
    if not raw or len(raw) > MAX_BYTES or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise CatalogueError("empty, oversized or entity-bearing Atom XML")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise CatalogueError("invalid XML response") from exc
    if root.tag != ATOM + "feed":
        raise CatalogueError("expected Atom feed, not a download or error page")
    found_total: set[int] = set()
    for el in root:
        if _local_name(el.tag).lower() == "totalentries":
            val = (el.text or "").strip()
            if not re.fullmatch(r"0|[1-9][0-9]*", val):
                raise CatalogueError("invalid totalentries")
            found_total.add(int(val))
    if len(found_total) > 1:
        raise CatalogueError("contradictory totalentries")
    entries = root.findall(ATOM + "entry")
    if len(entries) > MAX_ENTRIES_PER_PAGE:
        raise CatalogueError("feed page exceeds documented 50 records")
    candidates: list[dict[str, str]] = []
    ids: set[str] = set()
    for entry in entries:
        eid, title = _text(entry, "id"), _text(entry, "title")
        if not eid or not title:
            raise CatalogueError("missing Atom entry title or ID")
        if eid in ids:
            raise CatalogueError("duplicate Atom ID on same page")
        ids.add(eid)
        # This is only a *candidate* textual identity, not authenticated data.
        if "BD TOPO" in title.upper() or "BD-TOPO" in title.upper() or "BDTOPO" in title.upper():
            years_in_title = sorted(set(re.findall(r"(?<![0-9])(?:2015|2016)(?![0-9])", title)))
            candidates.append({
                "title": title[:250],
                "candidate_title_years_not_verified_edition_dates": ",".join(years_in_title),
            })
    return {
        "metadata_xml_sha256": hashlib.sha256(raw).hexdigest(),
        "entry_ids": ids,
        "entry_count": len(entries),
        "reported_totalentries": next(iter(found_total)) if found_total else None,
        "candidate_titles": candidates,
    }


def inspect_pages(pages: list[bytes], *, page_size: int = 50) -> dict[str, Any]:
    if not pages or len(pages) > MAX_PAGES or not isinstance(page_size, int) or not 1 <= page_size <= 50:
        raise CatalogueError("invalid number of metadata pages")
    parsed = [parse_atom_page(raw) for raw in pages]
    totals = {p["reported_totalentries"] for p in parsed}
    if None in totals or len(totals) != 1:
        raise CatalogueError("missing/changing totalentries: catalogue completeness not provable")
    expected = next(iter(totals))
    ids: set[str] = set()
    total = 0
    results: list[dict[str, str]] = []
    for index, p in enumerate(parsed):
        if p["entry_ids"] & ids:
            raise CatalogueError("repeated Atom identity across pages")
        ids.update(p["entry_ids"])
        total += p["entry_count"]
        results.extend(p["candidate_titles"])
        if index < len(parsed) - 1 and p["entry_count"] != page_size:
            raise CatalogueError("short page before last page")
    if total > expected:
        raise CatalogueError("more returned entries than declared")
    return {
        "schema": "ign-bdtopo-d077-historical-atom-catalogue-preflight-v0",
        "product_requested": "BD-TOPO",
        "department_requested": "D077",
        "edition_window_requested": [DATE_FROM, DATE_TO],
        "documented_endpoint": f"{BASE}/resource/BD-TOPO",
        "pages_checked": len(pages),
        "response_metadata_sha256": [p["metadata_xml_sha256"] for p in parsed],
        "provider_reported_totalentries": expected,
        "distinct_entries_seen": len(ids),
        "catalogue_pagination_complete": len(ids) == expected,
        "title_matched_candidate_count": len(results),
        "candidate_titles": results[:30],
        "2016_archive_download_verified": False,
        "historical_building_geometry_verified": False,
        "model_input_approved": False,
        "warning": "Metadata titles are discovery-only; validate actual release/version, department, file bytes/hash, original licence and 2016 vintage independently. A title year is NOT a verified edition or building construction date.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", action="append", required=True, type=Path,
                        help="local saved official Atom XML page (repeat in catalogue order)")
    parser.add_argument("--page-size", type=int, default=50)
    args = parser.parse_args()
    result = inspect_pages([path.read_bytes() for path in args.page], page_size=args.page_size)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
