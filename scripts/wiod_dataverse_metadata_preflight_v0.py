# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed offline check of WIOD 2016's original Dataverse release metadata.

The metadata check does not fetch WIOT archive bytes or establish 2011 tables.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

API_URL = "https://dataverse.nl/api/datasets/:persistentId/?persistentId=doi%3A10.34894%2FPJ2M1C"
SOURCE_DOI = "https://doi.org/10.34894/PJ2M1C"
DATASET_ID = 199086
RELEASE_TIME = "2025-10-09T08:23:27Z"
# Provider-reported values read from the original Dataverse release metadata.
# Format: Dataverse file ID, bytes, publisher SHA-1 (NOT independently verified).
PINNED_FILES = {
    "WIOTS_in_R.zip": (199101, 641578409, "51efc2a6c0358cff485e24d6b4b96ffe27f4e23a"),
    "Exchange_Rates.xlsx": (199097, 19308, "06952426dc6fdac6ecf5b4c71bf40239167864e7"),
}
MAX_METADATA_BYTES = 4_000_000


class WIODPreflightError(ValueError):
    """Provided metadata cannot prove the required release and file identities."""


def audit_dataset(metadata: dict[str, Any], raw_metadata_sha256: str) -> dict[str, Any]:
    if not isinstance(metadata, dict) or metadata.get("status") != "OK":
        raise WIODPreflightError("Dataverse response status must be OK")
    if not isinstance(raw_metadata_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", raw_metadata_sha256):
        raise WIODPreflightError("invalid metadata SHA-256")
    data = metadata.get("data")
    if not isinstance(data, dict) or (
        data.get("id") != DATASET_ID
        or data.get("persistentUrl") != SOURCE_DOI
        or data.get("authority") != "10.34894"
        or data.get("identifier") != "PJ2M1C"
        or data.get("protocol") != "doi"
    ):
        raise WIODPreflightError("WIOD original dataset identity drift")
    version = data.get("latestVersion")
    if not isinstance(version, dict) or (
        version.get("versionNumber") != 2 or version.get("versionMinorNumber") != 1
        or version.get("versionState") != "RELEASED"
        or version.get("releaseTime") != RELEASE_TIME
    ):
        raise WIODPreflightError("WIOD dataset release/version drift")
    if "Creative Commons Attribution 4.0" not in version.get("termsOfUse", ""):
        raise WIODPreflightError("WIOD Dataverse terms changed")
    files = version.get("files")
    if not isinstance(files, list) or len(files) > 10000:
        raise WIODPreflightError("invalid or unbounded Dataverse file list")
    found: dict[str, dict[str, Any]] = {}
    for record in files:
        if not isinstance(record, dict) or not isinstance(record.get("dataFile"), dict):
            raise WIODPreflightError("invalid dataset file entry")
        file = record["dataFile"]
        name = file.get("filename")
        if name not in PINNED_FILES:
            continue
        if name in found:
            raise WIODPreflightError(f"duplicate Dataverse file name: {name}")
        expected_id, expected_size, expected_sha1 = PINNED_FILES[name]
        checksum = file.get("checksum")
        if (file.get("id") != expected_id or type(file.get("filesize")) is not int
            or file["filesize"] != expected_size or record.get("restricted") is not False
            or not isinstance(checksum, dict) or checksum.get("type") != "SHA-1"
            or checksum.get("value") != expected_sha1):
            raise WIODPreflightError(f"file ID/size/checksum/restriction drift: {name}")
        found[name] = {
            "name": name,
            "publisher_file_id": expected_id,
            "publisher_reported_bytes": expected_size,
            "publisher_reported_sha1": expected_sha1,
            "original_download_url": f"https://dataverse.nl/api/access/datafile/{expected_id}",
            "archive_bytes_acquired": False,
            "publisher_checksum_independently_verified": False,
        }
    if set(found) != set(PINNED_FILES):
        raise WIODPreflightError("missing WIOD source archives: " + ", ".join(sorted(set(PINNED_FILES) - set(found))))
    return {
        "source_candidate_id": "rug.wiod2016.world-input-output-tables",
        "metadata_endpoint": API_URL,
        "original_metadata_sha256": raw_metadata_sha256,
        "dataverse_dataset_id": DATASET_ID,
        "dataset_version": "2.1",
        "dataset_release_time": RELEASE_TIME,
        "files": [found[name] for name in PINNED_FILES],
        "selected_model_year_2011_verified_within_archive": False,
        "original_archive_bytes_acquired": False,
        "licensed_use_independently_reviewed": False,
        "scientific_fitness_reviewed": False,
        "model_input_approved": False,
        "admission_status": "not_admitted",
    }


def inspect_file(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size > MAX_METADATA_BYTES:
        raise WIODPreflightError("missing or oversized metadata file")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_METADATA_BYTES:
        raise WIODPreflightError("empty or oversized metadata file")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise WIODPreflightError("invalid UTF-8 metadata JSON") from exc
    return audit_dataset(data, hashlib.sha256(raw).hexdigest())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-json", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = inspect_file(args.dataset_json)
    except (WIODPreflightError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
