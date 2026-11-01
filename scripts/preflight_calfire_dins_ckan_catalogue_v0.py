# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline metadata-only check for the exact public CAL FIRE DINS CKAN package.

No HTTP requests. The caller supplies original saved CKAN response bytes
obtained independently under the provider's documented public read-only API.
This validates catalogue identity only, not individual inspection records,
access to resource URLs, authenticity of submitted bytes, or model admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_BYTES = 65_536
DATASET_UUID = "1fdaea07-4bcd-4795-aa88-cd72b98e8a03"
PACKAGE_SLUG = "cal-fire-damage-inspection-dins-data"
METADATA_MODIFIED = "2026-10-21T20:55:50.264159"
OBSERVED_METADATA_SHA256 = "1998a87aff518a059162d9c4faff3ce3c2e145f007323c6a91cf3fb3617927f8"
ENDPOINT = (
    "https://publish.data.ca.gov/api/3/action/package_show"
    "?id=1fdaea07-4bcd-4795-aa88-cd72b98e8a03"
)
FROZEN_RESOURCES = {
    "bcb68c2c-fdb6-40f4-9c67-5dfb96efc9f9": "HTML",
    "547d5d5e-1093-415d-acc1-0fa1f1aeec9f": "ArcGIS GeoServices REST API",
    "b8aeb030-140d-43d2-aa29-1a80862e3d62": "CSV",
    "ebd354c6-f5ff-40bf-8164-56fa4e20a533": "ZIP",
    "1e583984-5262-4623-b079-8babf3b0c056": "GeoJSON",
    "3c233d0c-6c92-43af-b650-4fa49176c8b4": "KML",
    "917490df-8758-48ae-aaba-b92e8ab63be9": "ZIP",
    "0931300a-bb71-4f6d-9dfa-eb3bb5acdee3": "TXT",
    "fd2ee9be-8555-43e2-92d7-13a454d0a89c": "XLSX",
    "b449c656-e1f8-4204-9cde-d0ac0b54515f": "GPKG",
    "ed3313e9-06f7-4855-809e-8f484e84d43d": "GDB",
}


class CkanMetadataError(ValueError):
    """Wrong package identity, metadata version drift or unsafe input."""


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CkanMetadataError("duplicate JSON key in provider response")
        out[key] = value
    return out


def _reject_constant(value: str) -> None:
    raise CkanMetadataError("nonfinite JSON value")


def inspect_ckan_metadata(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_BYTES):
        raise CkanMetadataError("CKAN metadata response outside bounded byte size")
    try:
        data = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CkanMetadataError("invalid UTF-8 JSON provider response") from exc
    if type(data) is not dict or data.get("success") is not True:
        raise CkanMetadataError("CKAN action success=true required")
    result = data.get("result")
    if type(result) is not dict:
        raise CkanMetadataError("CKAN package_show result object missing")
    if (
        result.get("id") != DATASET_UUID
        or result.get("name") != PACKAGE_SLUG
        or result.get("license_id") != "cc-by"
        or result.get("metadata_modified") != METADATA_MODIFIED
        or result.get("accessLevel") != "public"
        or result.get("isopen") is not True
    ):
        raise CkanMetadataError("dataset identity, rights label or vintage drift")
    resources = result.get("resources")
    if type(resources) is not list or len(resources) != len(FROZEN_RESOURCES):
        raise CkanMetadataError("CKAN resource list missing or changed")
    found: dict[str, str] = {}
    for resource in resources:
        if type(resource) is not dict:
            raise CkanMetadataError("malformed package resource")
        rid, fmt = resource.get("id"), resource.get("format")
        if type(rid) is not str or type(fmt) is not str or rid in found:
            raise CkanMetadataError("invalid or duplicate resource identity")
        found[rid] = fmt
    if found != FROZEN_RESOURCES:
        raise CkanMetadataError("resource IDs, formats or count differ from pinned source")
    digest = hashlib.sha256(raw).hexdigest()
    return {
        "contract": "CALFIRE-DINS-CKAN-METADATA-RECEIPT-v0",
        "expected_provider_request": ENDPOINT,
        "dataset_id": DATASET_UUID,
        "dataset_name": PACKAGE_SLUG,
        "dataset_catalogue_license_label": "cc-by",
        "dataset_metadata_modified": METADATA_MODIFIED,
        "resource_count": len(found),
        "resource_formats": sorted(found.values()),
        "source_response_bytes": len(raw),
        "source_response_sha256": digest,
        "matches_recorded_original_provider_response_sha256": digest == OBSERVED_METADATA_SHA256,
        "input_bytes_provenance_authenticated_by_this_checker": False,
        "provider_asset_downloads_performed": 0,
        "provider_feature_rows_read": 0,
        "resource_url_execution_allowed": False,
        "personal_data_emitted": False,
        "model_data_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        report = inspect_ckan_metadata(raw)
    except (OSError, CkanMetadataError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
