#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict, metadata-only receipt for all 46 Insurers Global public name-index pages.

The CLI is offline by default. --live explicitly enables bounded, exact-origin
GETs; the utility never writes third-party bytes, credentials or Neon rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import time

from scripts.insurer_directory_source_receipt_v0 import (
    EXPECTED_VERSION, SOURCE_URL, PROVIDER_STATES,
)

PAGE_SIZE = 400
TOTAL_COUNT = 18180
PAGE_COUNT = 46
MAX_PAGE_BYTES = 300000
PAGE_URL_PREFIX = "https://insurers.global/api/v1/insurers/names/pages/"


class PageReceiptError(ValueError):
    """Original source identity or publication/size boundary failed."""


def page_url(page: int) -> str:
    if type(page) is not int or page < 1 or page > PAGE_COUNT:
        raise PageReceiptError("invalid fixed source page number")
    return f"{PAGE_URL_PREFIX}{page}.json"


def _unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise PageReceiptError("duplicate JSON object key")
        obj[key] = value
    return obj


def _reject_constant(value):
    raise PageReceiptError("non-finite JSON value")


def inspect_page(raw: bytes, page: int, *, total_count=TOTAL_COUNT,
                 page_size=PAGE_SIZE, page_count=PAGE_COUNT) -> tuple[dict, list]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_PAGE_BYTES:
        raise PageReceiptError("page input missing or unbounded")
    if type(page) is not int or not 1 <= page <= page_count:
        raise PageReceiptError("invalid page")
    if type(total_count) is not int or type(page_size) is not int or type(page_count) is not int:
        raise PageReceiptError("invalid count profile")
    if total_count < 1 or page_size < 1 or page_count != (total_count + page_size - 1) // page_size:
        raise PageReceiptError("inconsistent fixed page-count profile")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                         parse_constant=_reject_constant)
    except (ValueError, UnicodeError) as exc:
        raise PageReceiptError("invalid original page JSON") from exc
    if type(obj) is not dict:
        raise PageReceiptError("original page is not an object")
    checks = {
        "version": EXPECTED_VERSION, "count": total_count, "page": page,
        "pageSize": page_size, "pageCount": page_count, "all": SOURCE_URL,
        "first": page_url(1), "last": page_url(page_count),
        "prev": page_url(page - 1) if page > 1 else None,
        "next": page_url(page + 1) if page < page_count else None,
    }
    for key, expected in checks.items():
        actual = obj.get(key)
        if type(actual) is not type(expected) or actual != expected:
            raise PageReceiptError(f"original page {key} mismatch")
    licence = obj.get("licence")
    if type(licence) is not str or "CC BY 4.0" not in licence or "KAFS North America" not in licence:
        raise PageReceiptError("unreviewed licence/attribution")
    rows = obj.get("data")
    expected_len = min(page_size, total_count - (page - 1) * page_size)
    if type(rows) is not list or len(rows) != expected_len:
        raise PageReceiptError("missing, incomplete or duplicate-count page")
    slugs = set()
    for row in rows:
        if type(row) is not dict:
            raise PageReceiptError("page record not an object")
        for key in ("slug", "name", "country", "classCode", "verification"):
            if type(row.get(key)) is not str or not row[key].strip():
                raise PageReceiptError("invalid source row identity")
        if row["verification"] not in PROVIDER_STATES:
            raise PageReceiptError("unknown publisher verification state")
        if row["slug"] in slugs:
            raise PageReceiptError("duplicate slug within original page")
        slugs.add(row["slug"])
    return {
        "page": page, "source_url": page_url(page),
        "raw_page_bytes": len(raw),
        "raw_page_sha256": hashlib.sha256(raw).hexdigest(),
        "row_count": len(rows),
    }, rows


def audit_pages(read_page, *, total_count=TOTAL_COUNT, page_size=PAGE_SIZE,
                page_count=PAGE_COUNT) -> dict:
    pages, seen, identities = [], set(), []
    for index in range(1, page_count + 1):
        info, rows = inspect_page(read_page(index), index, total_count=total_count,
                                  page_size=page_size, page_count=page_count)
        for row in rows:
            if row["slug"] in seen:
                raise PageReceiptError("cross-page duplicate source slug")
            seen.add(row["slug"])
            values = (
                row["slug"], row["country"], row["name"],
                row["classCode"], row["verification"],
            )
            if any(chr(30) in value or chr(31) in value for value in values):
                raise PageReceiptError("source value contains reserved digest delimiter")
            identities.append(values)
        pages.append(info)
    if len(seen) != total_count or sum(p["row_count"] for p in pages) != total_count:
        raise PageReceiptError("incomplete global original page enumeration")
    # Stable UTF-8 field digest for direct equality against independently queried
    # Neon columns. A matching digest is NOT a byte-identical original aggregate.
    canonical = chr(30).join(
        chr(31).join(fields)
        for fields in sorted(identities, key=lambda fields: fields[0])
    )
    canonical_row_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "schema_version": "oc-insurer-directory-paged-source-receipt-v0",
        "canonical_field_digest_sha256": canonical_row_sha256,
        "canonical_field_order": [
            "slug", "country", "name", "classCode", "verification",
        ],
        "canonical_record_separator": "0x1e",
        "canonical_field_separator": "0x1f",
        "source_index_url": SOURCE_URL,
        "source_version": EXPECTED_VERSION,
        "total_source_rows": total_count,
        "unique_source_slugs": len(seen),
        "page_count": page_count,
        "pages": pages,
        "source_aggregate_original_sha256": None,
        "original_page_bytes_committed_to_git": False,
        "regulator_identity_verified": False,
        "neon_database_written": False,
        "model_input_approved": False,
    }


def read_live_page(page: int) -> bytes:
    url = page_url(page)
    time.sleep(0.25)  # Publisher fair-use terms: keep request rates reasonable.
    request = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "OpenCatastrophe-data-research/0.1 (+https://github.com/pokekarten/OpenCatastrophe-data; metadata-only)",
    })
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.geturl() != url or response.status != 200:
            raise PageReceiptError("redirected or failed original source request")
        if response.headers.get_content_type() != "application/json":
            raise PageReceiptError("unexpected original content type")
        data = response.read(MAX_PAGE_BYTES + 1)
    if len(data) > MAX_PAGE_BYTES:
        raise PageReceiptError("original page exceeds read limit")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--live", action="store_true", help="explicit bounded public API acquisition")
    group.add_argument("--page-dir", type=Path, help="local page-001.json through page-046.json")
    args = parser.parse_args()
    if args.live:
        reader = read_live_page
    else:
        directory = args.page_dir
        def reader(page):
            path = directory / f"page-{page:03d}.json"
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_PAGE_BYTES:
                raise PageReceiptError("missing or oversized original local page")
            return path.read_bytes()
    receipt = audit_pages(reader)
    print(json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PageReceiptError, OSError, UnicodeError) as exc:
        raise SystemExit(f"BLOCKED: {exc}") from exc
