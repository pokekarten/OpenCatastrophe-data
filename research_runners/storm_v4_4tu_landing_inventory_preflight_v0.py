#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, fail-closed comparison against 4TU's published STORM v4 file list.

Input is an operator-normalized *listing transcription*, NOT original 4TU API
JSON and NOT source track bytes. Hashes in the listing are provider-published
MD5 labels; this code does not independently verify any downloaded file.
No network access, source admission or Neon writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

DOI = "10.4121/12706085.v4"
PAGE = "https://data.4tu.nl/articles/_/12706085/4"
SOURCE_ID = "storm.ibtracs.present-climate.v4"
SCHEMA = "storm-v4-4tu-publisher-listing-transcription-v0"
PROFILE = "storm-v4-4tu-publisher-listing-preflight-v0"
MAX_BYTES = 32768
EXPECTED_FILES: dict[str, tuple[int, str]] = {
    "README.txt": (2322, "bcffee2371f9f2dacc16905b91f22202"),
    "Basins of STORM IBTrACS dataset.kml": (2612, "e45ddb50b5d9b7007564b77cfe21a34c"),
    "STORMV4.zip": (543251824, "d3e5647fa9c01b1ed33c33c0c930eb30"),
}
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
MD5_PATTERN = re.compile(r"[0-9a-f]{32}\Z")


class Blocked(ValueError):
    """Input metadata or its provenance boundary is not acceptable."""


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise Blocked("duplicate JSON key")
        out[key] = value
    return out


def _constant(value: str) -> None:
    raise Blocked("non-finite JSON constant")


def _float(value: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise Blocked("non-finite JSON number")
    return x


def inspect_listing(raw: bytes, expected_snapshot_sha256: str) -> dict[str, Any]:
    if not isinstance(expected_snapshot_sha256, str) or not SHA256_PATTERN.fullmatch(expected_snapshot_sha256):
        raise Blocked("independent normalized snapshot SHA-256 must be lowercase 64 hex characters")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise Blocked("normalized snapshot must contain between 1 and 32768 bytes")
    body_sha = hashlib.sha256(raw).hexdigest()
    if body_sha != expected_snapshot_sha256:
        raise Blocked("normalized snapshot body SHA-256 mismatch")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                         parse_constant=_constant, parse_float=_float)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise Blocked("invalid strict UTF-8 JSON") from exc
    if not isinstance(obj, dict) or set(obj) != {
        "schema_version", "record_doi", "publisher_page", "version",
        "observation_basis", "files",
    }:
        raise Blocked("unexpected normalized listing schema")
    if obj["schema_version"] != SCHEMA or obj["record_doi"] != DOI:
        raise Blocked("source or DOI identity drift")
    if obj["publisher_page"] != PAGE or type(obj["version"]) is not int or obj["version"] != 4:
        raise Blocked("wrong publisher landing page or STORM version")
    if obj["observation_basis"] != "manual_transcription_of_provider_landing_listing":
        raise Blocked("source observation basis must not masquerade as original API bytes")
    files = obj["files"]
    if type(files) is not list or len(files) != len(EXPECTED_FILES):
        raise Blocked("wrong STORM v4 publisher file count")
    seen: set[str] = set()
    total = 0
    for idx, entry in enumerate(files):
        if not isinstance(entry, dict) or set(entry) != {"name", "size_bytes", "publisher_md5"}:
            raise Blocked(f"invalid file listing entry {idx}")
        name = entry["name"]
        if not isinstance(name, str) or name not in EXPECTED_FILES:
            raise Blocked("unknown, unsafe or non-v4 file name")
        if name in seen:
            raise Blocked("duplicate provider file name")
        seen.add(name)
        size = entry["size_bytes"]
        checksum = entry["publisher_md5"]
        if type(size) is not int or size <= 0:
            raise Blocked("source file size must be a positive integer")
        if not isinstance(checksum, str) or not MD5_PATTERN.fullmatch(checksum):
            raise Blocked("malformed provider-published MD5 label")
        if (size, checksum) != EXPECTED_FILES[name]:
            raise Blocked("publisher-listed STORM v4 size or MD5 mismatch")
        total += size
    if seen != set(EXPECTED_FILES):
        raise Blocked("missing original STORM v4 file")
    return {
        "profile": PROFILE,
        "source_id": SOURCE_ID,
        "doi": DOI,
        "publisher_page": PAGE,
        "observation_basis": "manual_transcription_of_provider_landing_listing",
        "snapshot_bytes": len(raw),
        "normalized_snapshot_sha256": body_sha,
        "published_file_count": len(seen),
        "published_file_total_bytes": total,
        "file_metadata_labels_match_frozen_publisher_listing": True,
        "original_provider_api_response_retrieved": False,
        "original_api_uuid_verified": False,
        "provider_original_file_bytes_downloaded": False,
        "independent_file_sha256_verified": False,
        "commercial_asset_rights_reviewed": False,
        "synthetic_year_semantics_verified": False,
        "wind_hazard_footprints_verified": False,
        "model_input_approved": False,
        "neon_write_performed": False,
        "admission_status": "not_admitted",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", required=True, type=Path,
                   help="locally created manual transcription JSON (not a provider API response)")
    p.add_argument("--expected-sha256", required=True,
                   help="separately computed SHA-256 of this normalized transcription")
    args = p.parse_args()
    try:
        with args.snapshot.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        result = inspect_listing(raw, args.expected_sha256)
    except (Blocked, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
