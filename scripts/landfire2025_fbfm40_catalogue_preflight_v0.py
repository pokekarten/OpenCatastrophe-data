# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strictly offline LANDFIRE 2025 CONUS FBFM40 catalogue-snapshot gate.

This checks inconsistencies among separately collected *public metadata claims*.
It neither fetches nor authenticates the referenced archive, and cannot clear
rights, original bytes, raster classification, or CAT-model admissibility.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

SOURCE_ID = "us.landfire.fuel-vegetation.2025"
PRODUCT = "FBFM40"
VERSION = "LF 2025"
REGION = "CONUS"
THEME = "Fuel"
ARCHIVE_PATH = "/data-downloads/CONUS_LF2025/LF2025_FBFM40_CONUS.zip"
PAGE_URLS = frozenset({"https://landfire.gov/node/6145", "https://www.landfire.gov/node/6145"})
MAX_EVIDENCE_BYTES = 16_384
MIN_SNAPSHOTS = 2
MAX_SNAPSHOTS = 8
CHECKSUM_32 = re.compile(r"[0-9a-f]{32}\Z")
SIZE_LABEL = re.compile(r"(?:[1-9][0-9]{0,3})(?:\.[0-9]{1,2})? (?:MB|GB)\Z")
CAPTURE_ID = re.compile(r"[a-z][a-z0-9_-]{2,47}\Z")
UTC_TS = re.compile(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z\Z")
SNAPSHOT_KEYS = frozenset({
    "capture_id", "captured_at_utc", "product_page_url", "product", "version",
    "region", "theme", "archive_relative_path", "published_checksum_32hex",
    "published_size_label",
})


class LandfireCatalogueError(ValueError):
    """Unexpected evidence identity, encoding, or unsupported product metadata."""


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise LandfireCatalogueError("duplicate evidence JSON key")
        result[key] = value
    return result


def _no_nonfinite(_: str) -> None:
    raise LandfireCatalogueError("nonfinite evidence JSON constant")


def _check_snapshot(item: Any) -> tuple[str, str, str]:
    if not isinstance(item, dict) or set(item) != SNAPSHOT_KEYS:
        raise LandfireCatalogueError("snapshot fields absent, extra or malformed")
    if any(not isinstance(v, str) for v in item.values()):
        raise LandfireCatalogueError("snapshot fields must be strings")
    if (item["product_page_url"] not in PAGE_URLS or
            item["product"] != PRODUCT or item["version"] != VERSION or
            item["region"] != REGION or item["theme"] != THEME or
            item["archive_relative_path"] != ARCHIVE_PATH):
        raise LandfireCatalogueError("wrong product, season, release, region or provider route")
    capture = item["capture_id"]
    if not CAPTURE_ID.fullmatch(capture):
        raise LandfireCatalogueError("unsafe or duplicate-prone capture identifier")
    at = item["captured_at_utc"]
    if not UTC_TS.fullmatch(at):
        raise LandfireCatalogueError("captured_at_utc requires second-precision UTC Z time")
    try:
        timestamp = datetime.fromisoformat(at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LandfireCatalogueError("invalid UTC calendar timestamp") from exc
    if timestamp.utcoffset() != timezone.utc.utcoffset(None):
        raise LandfireCatalogueError("non-UTC metadata capture")
    checksum = item["published_checksum_32hex"]
    if not CHECKSUM_32.fullmatch(checksum):
        raise LandfireCatalogueError("publisher checksum is not exactly 32 lowercase hex")
    size = item["published_size_label"]
    if not SIZE_LABEL.fullmatch(size):
        raise LandfireCatalogueError("unsupported or ambiguous publisher size label")
    return capture, checksum, size


def screen_landfire2025_fbfm40_catalogue_claims(original_json: bytes) -> dict[str, Any]:
    """Classify conflicting catalogue claims without treating agreement as admission.

    Both www and apex URLs are the same upstream provider, *not* independently
    corroborated sources. A 32-hex provider value is not asserted to be MD5 or
    SHA-256; the published algorithm has not been verified by this tool.
    """
    if not isinstance(original_json, bytes) or not 0 < len(original_json) <= MAX_EVIDENCE_BYTES:
        raise LandfireCatalogueError("evidence JSON empty, nonbytes or oversized")
    try:
        doc = json.loads(original_json.decode("utf-8", errors="strict"),
                         object_pairs_hook=_unique_pairs, parse_constant=_no_nonfinite)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise LandfireCatalogueError("invalid evidence JSON encoding or syntax") from exc
    if not isinstance(doc, dict) or set(doc) != {"snapshots"}:
        raise LandfireCatalogueError("expected only snapshots evidence array")
    snapshots = doc["snapshots"]
    if not isinstance(snapshots, list) or not MIN_SNAPSHOTS <= len(snapshots) <= MAX_SNAPSHOTS:
        raise LandfireCatalogueError("requires two to eight bounded metadata snapshots")
    captures: set[str] = set()
    checksums: set[str] = set()
    sizes: set[str] = set()
    for item in snapshots:
        capture, checksum, size = _check_snapshot(item)
        if capture in captures:
            raise LandfireCatalogueError("duplicate capture identifiers")
        captures.add(capture)
        checksums.add(checksum)
        sizes.add(size)
    is_conflicting = len(checksums) != 1 or len(sizes) != 1
    return {
        "source_id": SOURCE_ID,
        "source_product_identity": f"{VERSION}:{PRODUCT}:{REGION}:nonseasonal",
        "archive_relative_path": ARCHIVE_PATH,
        "catalogue_snapshot_count": len(snapshots),
        "distinct_publisher_32hex_claims": len(checksums),
        "distinct_publisher_size_labels": len(sizes),
        "catalogue_claim_status": (
            "conflicting_blocked" if is_conflicting else "agreeing_claims_not_original_verified"
        ),
        "provider_checksum_algorithm_confirmed": False,
        "independent_provider_page_byte_provenance_verified": False,
        "original_archive_bytes_observed": False,
        "original_archive_sha256_verified": False,
        "raster_crs_resolution_and_categories_verified": False,
        "archive_is_seasonal_fuels_product": False,
        "commercial_rights_and_automation_verified": False,
        "insurer_cat_model_input_approved": False,
        "neon_storage": "not_performed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-json", type=Path, required=True,
                        help="local synthetic/review metadata snapshots; no external archive")
    args = parser.parse_args()
    with args.evidence_json.open("rb") as stream:
        content = stream.read(MAX_EVIDENCE_BYTES + 1)
    report = screen_landfire2025_fbfm40_catalogue_claims(content)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if report["catalogue_claim_status"] == "conflicting_blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
