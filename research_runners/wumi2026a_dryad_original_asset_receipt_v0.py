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
from io import BytesIO
import json
from pathlib import Path
import re
import stat
from zipfile import BadZipFile, ZipFile, ZIP_STORED, ZIP_DEFLATED

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



def inspect_zip_members_untrusted(raw: bytes) -> dict:
    """Bounded ZIP structural/CRC check on bytes, no extraction or member content output.

    This does NOT establish original asset identity; caller must validate
    exact byte count and publisher digest before using its result.
    """
    if type(raw) is not bytes or not 0 < len(raw) <= 5_000_000:
        raise DryadReceiptBlocked("missing/oversized small WUMI ZIP payload")
    try:
        with ZipFile(BytesIO(raw), "r") as archive:
            infos = archive.infolist()
            if not 0 < len(infos) <= 40:
                raise DryadReceiptBlocked("unexpected empty/overpopulated original ZIP")
            seen = set()
            total = 0
            files = 0
            for info in infos:
                name = info.filename
                if (not isinstance(name, str) or not name or name.startswith("/")
                    or "\\\\" in name or "\\x00" in name
                    or re.match(r"^[A-Za-z]:", name)
                    or any(part in ("", ".", "..") for part in name.rstrip("/").split("/"))):
                    raise DryadReceiptBlocked("unsafe ZIP member path")
                folded = name.rstrip("/").casefold()
                if folded in seen:
                    raise DryadReceiptBlocked("ambiguous duplicate ZIP member path")
                seen.add(folded)
                if info.flag_bits & 0x1:
                    raise DryadReceiptBlocked("encrypted ZIP member not admitted")
                if info.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
                    raise DryadReceiptBlocked("unknown ZIP compression")
                # file system symlinks are not safe payload members.
                if (info.create_system == 3 and
                    stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK):
                    raise DryadReceiptBlocked("ZIP symlink member blocked")
                if info.file_size > 30_000_000:
                    raise DryadReceiptBlocked("unbounded expanded member")
                total += info.file_size
                if total > 80_000_000:
                    raise DryadReceiptBlocked("unbounded ZIP expanded total")
                if not info.is_dir():
                    files += 1
            if files == 0:
                raise DryadReceiptBlocked("ZIP has no ordinary files")
            if archive.testzip() is not None:
                raise DryadReceiptBlocked("ZIP member CRC failed")
    except (BadZipFile, OSError, EOFError, RuntimeError) as exc:
        raise DryadReceiptBlocked("invalid WUMI ZIP container/CRC") from exc
    return {"zip_structure_crc_checked": True, "zip_member_count": len(infos),
            "zip_file_count": files, "zip_total_uncompressed_bytes": total,
            "zip_extraction_performed": False,
            "zip_member_names_or_contents_in_report": False}


def inspect_original_zip_pinned(raw: bytes) -> dict:
    """Require Dryad's exact original bytes before inspecting ZIP structure."""
    if type(raw) is not bytes or len(raw) != ASSET_BYTES:
        raise DryadReceiptBlocked("original ZIP byte count differs from publisher receipt")
    if hashlib.sha256(raw).hexdigest() != ASSET_SHA256:
        raise DryadReceiptBlocked("original ZIP SHA256 differs from publisher receipt")
    result = inspect_zip_members_untrusted(raw)
    return {"target_original_file_sha256_verified": True,
            "target_downloaded_bytes": len(raw), **result}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--metadata-json", type=Path, required=True)
    ap.add_argument("--metadata-sha256", required=True)
    ap.add_argument("--dryad-version", type=int, required=True)
    ap.add_argument("--original-zip", type=Path, help="Optional exact original 4.68 MB ZIP to byte-hash and CRC check")
    args = ap.parse_args(argv)
    try:
        f = args.metadata_json
        if not f.is_file() or f.stat().st_size > MAX_JSON:
            raise DryadReceiptBlocked("missing/oversized local publisher metadata snapshot")
        result = inspect_dryad_files_metadata(
            f.read_bytes(), args.metadata_sha256, expected_version=args.dryad_version
        )
        if args.original_zip is not None:
            zip_path = args.original_zip
            if not zip_path.is_file() or zip_path.stat().st_size != ASSET_BYTES:
                raise DryadReceiptBlocked("missing or wrong-sized original WUMI ZIP")
            result.update(inspect_original_zip_pinned(zip_path.read_bytes()))
            result["state"] = "ORIGINAL_ZIP_BYTES_AND_CRC_MATCH_NO_MODEL_ADMISSION"
    except (OSError, DryadReceiptBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
