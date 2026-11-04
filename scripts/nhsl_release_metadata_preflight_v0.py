# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline, bounded NHSL v1.0 GitHub release asset metadata preflight.

Never downloads NHSL asset bytes. A passing receipt is NOT data admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = "OpenDRR/national-human-settlement"
TAG = "v1.0"
RELEASE_URL = f"https://github.com/{REPO}/releases/tag/{TAG}"
API_URL = f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}"
ASSET_PREFIX = f"https://github.com/{REPO}/releases/download/{TAG}/"
# Names published on Canada's official NHSL Physical Exposure resource page.
REQUIRED_ASSETS = (
    "nhsl_physical_exposure_attributes_en.xlsx",
    "nhsl_physical_exposure_indicators_b.zip",
    "nhsl_physical_exposure_indicators_s.zip",
)
MAX_METADATA_BYTES = 2_000_000
MAX_ASSET_SIZE = 1_000_000_000
SHA256 = re.compile(r"[0-9a-f]{64}")


class NHSLPreflightError(ValueError):
    """Expected metadata does not identify the exact public release."""


def audit_release(metadata: dict[str, Any], original_metadata_sha256: str) -> dict[str, Any]:
    """Validate release identity, intended asset names and their declared metadata."""
    if not isinstance(metadata, dict):
        raise NHSLPreflightError("release must be an object")
    if not isinstance(original_metadata_sha256, str) or not SHA256.fullmatch(original_metadata_sha256):
        raise NHSLPreflightError("metadata SHA-256 must be 64 lowercase hex characters")
    if metadata.get("tag_name") != TAG or metadata.get("html_url") != RELEASE_URL:
        raise NHSLPreflightError("unexpected release tag or release URL")
    if metadata.get("draft") is not False or metadata.get("prerelease") is not False:
        raise NHSLPreflightError("draft or prerelease cannot be accepted")
    assets = metadata.get("assets")
    if not isinstance(assets, list) or len(assets) > 500:
        raise NHSLPreflightError("invalid or unbounded release assets list")

    found: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise NHSLPreflightError("asset metadata must be objects")
        name = asset.get("name")
        if name not in REQUIRED_ASSETS:
            continue
        if name in found:
            raise NHSLPreflightError(f"duplicate release asset: {name}")
        size = asset.get("size")
        if type(size) is not int or not 0 < size <= MAX_ASSET_SIZE:
            raise NHSLPreflightError(f"invalid asset byte count: {name}")
        if asset.get("browser_download_url") != ASSET_PREFIX + name:
            raise NHSLPreflightError(f"wrong asset origin / URL: {name}")
        declared_digest = asset.get("digest")
        if declared_digest is not None and (
            not isinstance(declared_digest, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", declared_digest)
        ):
            raise NHSLPreflightError(f"invalid publisher-declared digest: {name}")
        found[name] = {
            "filename": name,
            "publisher_reported_bytes": size,
            "publisher_reported_digest": declared_digest,
            "asset_url": ASSET_PREFIX + name,
            "downloaded": False,
            "checksum_independently_verified": False,
        }

    missing = set(REQUIRED_ASSETS) - set(found)
    if missing:
        raise NHSLPreflightError(f"missing original release assets: {', '.join(sorted(missing))}")

    return {
        "source_candidate_id": "can.nrcan.nhsl.physical-exposure.2016-2020",
        "repository": REPO,
        "release_tag": TAG,
        "metadata_source_url": API_URL,
        "release_url": RELEASE_URL,
        "original_metadata_sha256": original_metadata_sha256,
        "assets": [found[name] for name in REQUIRED_ASSETS],
        "spatial_semantics": "building_archetype_points_at_settlement_centroids_not_individual_rooftops",
        "cost_semantics": "modeled_2019_CAD_replacement_cost_not_insured_TIV",
        "data_dictionary_read": False,
        "source_asset_bytes_acquired": False,
        "dataset_rights_reviewed": False,
        "scientific_fitness_reviewed": False,
        "model_input_approved": False,
        "admission_status": "not_admitted",
    }


def inspect_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise NHSLPreflightError("release metadata file does not exist")
    if path.stat().st_size > MAX_METADATA_BYTES:
        raise NHSLPreflightError("metadata JSON exceeds allowed byte limit")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_METADATA_BYTES:
        raise NHSLPreflightError("empty or oversized metadata JSON")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise NHSLPreflightError("invalid UTF-8 release JSON") from exc
    return audit_release(payload, hashlib.sha256(raw).hexdigest())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-json", required=True, type=Path, help="Local, externally acquired GitHub release metadata JSON only")
    args = parser.parse_args(argv)
    try:
        receipt = inspect_file(args.release_json)
    except (NHSLPreflightError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
