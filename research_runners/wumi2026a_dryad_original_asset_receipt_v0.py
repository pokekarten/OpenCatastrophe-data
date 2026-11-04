#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed Dryad v458442 WUMI2026a file-metadata gate.

The original file digest reported by Dryad is NOT proof of downloaded bytes.
No network access, source data, original events or licensed content here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

MAX_JSON = 128_000
VERSION = 458442
ASSET_NAME = "WUMI2026a_final_wildfire_lists.zip"
ASSET_ID = "4917545"
ASSET_BYTES = 4_683_571
ASSET_SHA256 = "8d8a59588935b832bf8e382a0c94b8a6705e6a8fa2bed161bacf1d9fe78726d0"
EXPECTED_FILES = frozenset((
    "WUMI2026a_final_wildfire_lists.zip", "README.md", "study_region.zip",
    "projection.zip", "fire_lists.zip", "fire_maps.zip", "original_data.zip",
))
SHA256 = re.compile(r"[a-f0-9]{64}\Z")


class DryadReceiptBlocked(ValueError):
    """Cannot substantiate exact publisher metadata identity."""


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise DryadReceiptBlocked("duplicate JSON key")
        out[key] = value
    return out


def _nonfinite(value):
    raise DryadReceiptBlocked("nonfinite JSON number")


def inspect_dryad_files_metadata(raw: bytes, sha256: str, *, expected_version: int) -> dict:
    """Audit exact v458442 JSON response; never attest response provenance or archive bytes."""
    if type(expected_version) is not int or expected_version != VERSION:
        raise DryadReceiptBlocked("wrong Dryad dataset version; 2024a is not 2026a")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_JSON:
        raise DryadReceiptBlocked("missing or oversized original metadata JSON")
    if type(sha256) is not str or not SHA256.fullmatch(sha256):
        raise DryadReceiptBlocked("lowercase SHA256 of exact metadata JSON required")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != sha256:
        raise DryadReceiptBlocked("metadata original-byte SHA256 mismatch")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as e:
        raise DryadReceiptBlocked("invalid metadata UTF-8/JSON") from e
    if not isinstance(doc, dict) or "error" in doc:
        raise DryadReceiptBlocked("publisher file inventory not a successful response")
    if type(doc.get("count")) is not int or type(doc.get("total")) is not int:
        raise DryadReceiptBlocked("missing original Dryad file-count fields")
    if doc["count"] != 7 or doc["total"] != 7:
        raise DryadReceiptBlocked("expected exactly seven version-458442 files, not paginated/truncated")
    emb = doc.get("_embedded")
    files = emb.get("stash:files") if isinstance(emb, dict) else None
    if not isinstance(files, list) or len(files) != 7:
        raise DryadReceiptBlocked("missing or truncated original file inventory")
    found = {}
    target = None
    for item in files:
        if not isinstance(item, dict) or type(item.get("path")) is not str:
            raise DryadReceiptBlocked("missing exact original file path")
        name = item["path"]
        if name in found or name not in EXPECTED_FILES:
            raise DryadReceiptBlocked("duplicate/unexpected version-specific file entry")
        if type(item.get("size")) is not int or item["size"] <= 0:
            raise DryadReceiptBlocked("invalid original file-size metadata")
        if item.get("digestType") != "sha-256" or type(item.get("digest")) is not str or not SHA256.fullmatch(item["digest"]):
            raise DryadReceiptBlocked("missing SHA-256 original-file digest claim")
        links = item.get("_links")
        href = links.get("self", {}).get("href") if isinstance(links, dict) and isinstance(links.get("self"), dict) else None
        if type(href) is not str or not re.fullmatch(r"/api/v2/files/[0-9]{1,12}", href):
            raise DryadReceiptBlocked("missing Dryad publisher file-ID link")
        version_link = links.get("stash:version", {}).get("href") if isinstance(links.get("stash:version"), dict) else None
        if version_link != "/api/v2/versions/458442":
            raise DryadReceiptBlocked("file does not attest same publisher version")
        download_link = links.get("stash:download", {}).get("href") if isinstance(links.get("stash:download"), dict) else None
        if download_link != href + "/download":
            raise DryadReceiptBlocked("publisher download identity inconsistent with file ID")
        found[name] = (item["size"], item["digest"], href)
        if name == ASSET_NAME:
            target = item
    if set(found) != EXPECTED_FILES:
        raise DryadReceiptBlocked("missing expected version-458442 original files")
    if target is None or found[ASSET_NAME] != (ASSET_BYTES, ASSET_SHA256, "/api/v2/files/" + ASSET_ID):
        raise DryadReceiptBlocked("WUMI2026a small-list publisher file hash/bytes/ID differ")
    return {
        "audit": "dryad-wumi2026a-v458442-small-original-file-receipt-v0",
        "state": "PUBLISHER_METADATA_MATCH_NOT_ASSET_VALIDATED",
        "publisher_dataset_version_declared": VERSION,
        "version_specific_inventory_sha256": actual,
        "version_specific_file_count": len(found),
        "target_asset_name": ASSET_NAME,
        "target_asset_bytes_publisher_claim": ASSET_BYTES,
        "target_asset_sha256_publisher_claim": ASSET_SHA256,
        "target_download_url": "https://datadryad.org/api/v2/files/" + ASSET_ID + "/download",
        "publisher_metadata_origin_authenticated": False,
        "target_file_downloaded": False,
        "target_original_file_sha256_verified": False,
        "target_original_zip_integrity_checked": False,
        "actual_event_list_schema_or_event_count_verified": False,
        "source_rights_or_CAT_model_admission_granted": False,
        "actual_download_observation": "NOT_PERFORMED_BY_THIS_OFFLINE_GATE",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--metadata-json", type=Path, required=True)
    ap.add_argument("--metadata-sha256", required=True)
    ap.add_argument("--dryad-version", type=int, required=True)
    args = ap.parse_args(argv)
    try:
        f = args.metadata_json
        if not f.is_file() or f.stat().st_size > MAX_JSON:
            raise DryadReceiptBlocked("missing/oversized local publisher metadata snapshot")
        result = inspect_dryad_files_metadata(
            f.read_bytes(), args.metadata_sha256, expected_version=args.dryad_version
        )
    except (OSError, DryadReceiptBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
