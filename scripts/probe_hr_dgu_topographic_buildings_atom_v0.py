#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded original DGU topographic Buildings ATOM *metadata* receipt.

Distinct product from DGU's cadastral Buildings WFS. No bulk ZIP download,
geometry extraction, source admission or licence inference from public access.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib import error, request
import xml.etree.ElementTree as ET

ATOM = "{http://www.w3.org/2005/Atom}"
FEED_URL = "https://geoportal.dgu.hr/services/atom/bu-core2d/xml"
ZIP_URL = "https://geoportal.dgu.hr/services/atom/INSPIRE_Building_(BU-CORE2D).zip"
RIGHTS_TEXT = (
    "ograničenje javnog pristupa prema članku 13 stavku 1 točki (e) "
    "INSPIRE Direktive"
)
REVIEWED_ATOM_UPDATED = "2024-03-07T17:05:52.000000+01:00"
REVIEWED_ZIP_ADVERTISED_BYTES = 285995484
REVIEWED_ATOM_SHA256 = "ef9b09a02579fd101b8015466f069482ff24ea7781850773a5795b324aabcd8f"
MAX_XML_BYTES = 64 * 1024
TIMEOUT_SECONDS = 15


class AtomMetadataError(ValueError):
    """An original provider response differs from the reviewed contract."""


def inspect_atom(raw: bytes) -> dict:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_XML_BYTES:
        raise AtomMetadataError("original ATOM feed is missing or oversized")
    if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", raw, flags=re.IGNORECASE):
        raise AtomMetadataError("DOCTYPE/ENTITY forbidden in provider XML")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise AtomMetadataError("invalid original ATOM XML") from exc
    if root.tag != ATOM + "feed":
        raise AtomMetadataError("not an ATOM feed")
    if root.findtext(ATOM + "id") != FEED_URL:
        raise AtomMetadataError("wrong ATOM feed product identity")
    entries = root.findall(ATOM + "entry")
    if len(entries) != 1:
        raise AtomMetadataError("exactly one reviewed topographic entry required")
    rights = root.findall(ATOM + "rights")
    if len(rights) != 1 or rights[0].text != RIGHTS_TEXT:
        raise AtomMetadataError("restriction text missing or changed: fresh rights review required")
    updated = root.findtext(ATOM + "updated")
    entry_updated = entries[0].findtext(ATOM + "updated")
    if not updated or updated != entry_updated:
        raise AtomMetadataError("missing or inconsistent ATOM update timestamp")
    try:
        dt = datetime.fromisoformat(updated)
    except ValueError as exc:
        raise AtomMetadataError("invalid ATOM update timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise AtomMetadataError("provider update timestamp lacks timezone")
    if updated != REVIEWED_ATOM_UPDATED:
        raise AtomMetadataError("unreviewed ATOM release timestamp drift")
    # This title is source-format evidence, not proof of the ZIP contents.
    entry_title = entries[0].findtext(ATOM + "title") or ""
    if "GML 3.2.1" not in entry_title or "ETRS89/LAEA" not in entry_title:
        raise AtomMetadataError("advertised GML/CRS product description changed")
    downloads = [
        link for link in entries[0].findall(ATOM + "link")
        if link.get("rel") == "alternate" and link.get("href") == ZIP_URL
    ]
    if len(downloads) != 1:
        raise AtomMetadataError("missing or duplicated exact DGU topographic ZIP link")
    link = downloads[0]
    if link.get("type") != "application/x-gmz":
        raise AtomMetadataError("publisher ZIP MIME declaration changed")
    size_text = link.get("length")
    if size_text is None or not re.fullmatch(r"[1-9][0-9]{0,11}", size_text):
        raise AtomMetadataError("missing or invalid publisher advertised byte count")
    zip_size = int(size_text)
    if zip_size != REVIEWED_ZIP_ADVERTISED_BYTES:
        raise AtomMetadataError("unreviewed advertised ZIP byte-size drift")
    xml_sha = hashlib.sha256(raw).hexdigest()
    return {
        "receipt_profile": "hr-dgu-topographic-buildings-atom-metadata-v0",
        "source_product": "DGU Basic Topographic Database INSPIRE Buildings ATOM",
        "atom_feed_url": FEED_URL,
        "atom_updated_as_declared": updated,
        "feed_original_bytes": len(raw),
        "feed_original_sha256": xml_sha,
        "reviewed_original_feed_sha256": REVIEWED_ATOM_SHA256,
        "matches_reviewed_original_feed_bytes": xml_sha == REVIEWED_ATOM_SHA256,
        "advertised_zip_url": ZIP_URL,
        "advertised_zip_bytes_not_verified": zip_size,
        "advertised_format": "GML 3.2.1 / ETRS89-LAEA / ZIP",
        "rights_notice_verbatim": RIGHTS_TEXT,
        "rights_reconciliation_required": True,
        "distinct_product_identity_from_cadastral_wfs": True,
        "zip_downloaded": False,
        "raw_geometry_verified": False,
        "public_redistribution_approved": False,
        "model_input_admitted": False,
    }


def validate_feed_content_length(declared: object, actual_bytes: int) -> None:
    """Reject unbounded or ambiguous HTTP Content-Length before parsing it."""
    if declared is None:
        return
    if (
        type(declared) is not str
        or not (1 <= len(declared) <= 10)
        or not declared.isascii()
        or not declared.isdecimal()
    ):
        raise AtomMetadataError("invalid ATOM Content-Length")
    value = int(declared)
    if value == 0 or value > MAX_XML_BYTES or value != actual_bytes:
        raise AtomMetadataError("incomplete or oversized ATOM Content-Length")


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AtomMetadataError("ATOM metadata redirect denied")


def live_feed() -> bytes:
    # Pin direct provider transport; do not inherit ambient proxy routing.
    opener = request.build_opener(request.ProxyHandler({}), _NoRedirect())
    req = request.Request(
        FEED_URL,
        headers={"Accept": "application/atom+xml, application/xml"},
        method="GET",
    )
    try:
        with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.geturl() != FEED_URL:
                raise AtomMetadataError("unexpected ATOM URL/status")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise AtomMetadataError("unexpected compressed transfer")
            raw = response.read(MAX_XML_BYTES + 1)
            declared = response.headers.get("Content-Length")
            validate_feed_content_length(declared, len(raw))
    except (error.URLError, TimeoutError) as exc:
        raise AtomMetadataError("original ATOM metadata unavailable") from exc
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="Only metadata, one official GET")
    mode.add_argument("--offline-file", type=Path, help="Original or synthetic ATOM XML")
    args = parser.parse_args(argv)
    try:
        if args.live:
            raw = live_feed()
        else:
            if args.offline_file.is_symlink() or not args.offline_file.is_file():
                raise AtomMetadataError("offline XML must be a regular file")
            with args.offline_file.open("rb") as src:
                raw = src.read(MAX_XML_BYTES + 1)
        receipt = inspect_atom(raw)
        # Exact-byte pin applies only to an actual network fetch. Offline mode
        # deliberately permits synthetic fixtures and never proves origin.
        if args.live and not receipt["matches_reviewed_original_feed_bytes"]:
            raise AtomMetadataError(
                "live feed bytes differ from reviewed SHA-256; fresh source review required"
            )
        receipt["live_original_fetch_in_this_run"] = bool(args.live)
    except (AtomMetadataError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
