# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline preflight of metadata only for fixed public Zenodo CAT products.

Does not fetch any network or source data bytes, admit a dataset, verify an
original file digest, or authorize downstream model use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

MAX_METADATA_BYTES = 5 * 1024 * 1024
MAX_FILES = 2000
RECORDS = {
    "nl.vu.european-multihazard-sparse-events.v1": 22080546,
    "ihcantabria.ih-storm.enso-synthetic-tracks.v2": 15097665,
    "ihcantabria.transclima.tc-surge-hydrographs.2026": 18170693,
    "ihcantabria.transclima.tropical-cyclone-data-catalogue.v1": 23736379,
    "nl.deltares.gtsm-era5-e.extreme-sea-level-stats.v2": 14671593,
    "waleedgeo.gfsm.global-flood-susceptibility.v1": 20568218,
}


class MetadataPreflightError(ValueError):
    """Fail-closed source metadata or identity error."""


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MetadataPreflightError(f"{label} must be an object")
    return value


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MetadataPreflightError(f"{label} must be non-empty text")
    return value


def check_download_url(value: Any, record_id: int) -> None:
    url = require_text(value, "file content URL")
    try:
        parts = urlsplit(url)
        hostname = parts.hostname
        parts.port
    except ValueError as exc:
        raise MetadataPreflightError("malformed file content URL") from exc
    if parts.scheme != "https" or hostname != "zenodo.org":
        raise MetadataPreflightError("file content URL must use original zenodo.org HTTPS")
    if parts.username or parts.password or parts.fragment or parts.query:
        raise MetadataPreflightError("signed, credentialed or non-canonical file URL rejected")
    prefixes = (f"/api/records/{record_id}/files/", f"/records/{record_id}/files/")
    if not any(parts.path.startswith(p) for p in prefixes):
        raise MetadataPreflightError("file content URL record identity mismatch")


def audit_record(payload: dict[str, Any], source_id: str, raw_sha256: str) -> dict[str, Any]:
    if source_id not in RECORDS:
        raise MetadataPreflightError("unknown source candidate; no unreviewed dynamic IDs")
    record = require_dict(payload, "record")
    record_id = RECORDS[source_id]
    if type(record.get("id")) is not int or record["id"] != record_id:
        raise MetadataPreflightError("original Zenodo record ID mismatch")
    doi = require_text(record.get("doi"), "record DOI")
    if doi.casefold() != f"10.5281/zenodo.{record_id}":
        raise MetadataPreflightError("record DOI/version identity mismatch")
    metadata = require_dict(record.get("metadata"), "metadata")
    title = require_text(metadata.get("title"), "metadata.title")
    access = metadata.get("access_right")
    if access is None:
        access = require_dict(record.get("access"), "access").get("status")
    if access != "open":
        raise MetadataPreflightError("record is not verified open-access metadata")
    license_raw = metadata.get("license")
    if isinstance(license_raw, dict):
        license_id = require_text(license_raw.get("id"), "metadata.license.id")
    else:
        license_id = require_text(license_raw, "metadata.license")
    if not re.fullmatch(r"[a-zA-Z0-9._+-]{2,90}", license_id):
        raise MetadataPreflightError("invalid license identifier")
    files = record.get("files")
    if not isinstance(files, list) or not 0 < len(files) <= MAX_FILES:
        raise MetadataPreflightError("files must be a bounded non-empty list")

    seen: set[str] = set()
    inventory = []
    total_bytes = 0
    for position, entry in enumerate(files):
        obj = require_dict(entry, f"files[{position}]")
        key = require_text(obj.get("key"), f"files[{position}].key")
        if (key.startswith("/") or "\\" in key or "\x00" in key
                or any(part in ("", ".", "..") for part in key.split("/"))):
            raise MetadataPreflightError("unsafe source file path")
        if key in seen:
            raise MetadataPreflightError("duplicate original file path")
        seen.add(key)
        size = obj.get("size")
        if type(size) is not int or size <= 0:
            raise MetadataPreflightError("source file size must be a positive integer")
        checksum = require_text(obj.get("checksum"), "publisher checksum")
        m = re.fullmatch(r"(md5|sha256):([0-9a-fA-F]+)", checksum)
        if not m or len(m.group(2)) != {"md5": 32, "sha256": 64}[m.group(1)]:
            raise MetadataPreflightError("unsupported or malformed publisher checksum")
        links = require_dict(obj.get("links"), "file links")
        check_download_url(links.get("self") or links.get("content") or links.get("download"), record_id)
        total_bytes += size
        inventory.append({
            "key": key,
            "size_bytes": size,
            "publisher_checksum": f"{m.group(1)}:{m.group(2).lower()}",
            "file_bytes_downloaded": False,
            "original_checksum_independently_verified": False,
        })

    return {
        "schema_version": "zenodo-cat-metadata-preflight-v0",
        "source_candidate_id": source_id,
        "original_zenodo_record_id": record_id,
        "original_doi": doi,
        "record_title": title,
        "record_version": metadata.get("version") if isinstance(metadata.get("version"), str) else None,
        "declared_record_license": license_id,
        "record_access_status": access,
        "metadata_body_sha256": raw_sha256,
        "file_count": len(inventory),
        "listed_source_bytes": total_bytes,
        "files": inventory,
        "source_bytes_acquired": False,
        "rights_and_science_reviewed": False,
        "model_input_approved": False,
        "admission_status": "not_admitted",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True, choices=sorted(RECORDS))
    parser.add_argument("--metadata", required=True, type=Path, help="local JSON, not a URL")
    args = parser.parse_args()
    try:
        if not args.metadata.is_file() or args.metadata.stat().st_size > MAX_METADATA_BYTES:
            raise MetadataPreflightError("metadata file missing or exceeds 5 MiB cap")
        raw = args.metadata.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        receipt = audit_record(payload, args.source_id, hashlib.sha256(raw).hexdigest())
    except (OSError, UnicodeError, json.JSONDecodeError, MetadataPreflightError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
