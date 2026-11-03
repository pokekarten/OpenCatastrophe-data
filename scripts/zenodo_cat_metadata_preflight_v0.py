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
    "nl.deltares.gtsm-era5-e.extreme-sea-level-stats.v2": 14671593,
    "waleedgeo.gfsm.global-flood-susceptibility.v1": 20568218,
    "emdat.llm-geodis.2026.v7": 18935447,
}

LLM_GEODIS_SOURCE = "emdat.llm-geodis.2026.v7"
LLM_GEODIS_V7_FILES = frozenset({
    "241204_emdat_archive.xlsx",
    "emdat_geocoding-zenodo.zip",
    "gdis_disnos.csv",
    "geoemdat_gaul.gpkg",
    "input_emdat.csv",
    "Instructions_LLM-GeoDis.pdf",
    "LLMGeoDis_part1.zip",
    "LLMGeoDis_part2.zip",
    "LLMGeoDis_part3.zip",
    "LLMGeoDis_part4.zip",
    "LLMGeoDis_part5.zip",
    "pend-gdis-1960-2018-disasterlocations.csv",
    "reliability_db.csv",
    "synthetic_EMDAT_locations.csv",
})


LLM_GEODIS_V7_PUBLISHED_MD5 = {
    "241204_emdat_archive.xlsx": "e78b986f8234a48de376b8026017d1dc",
    "Instructions_LLM-GeoDis.pdf": "2e8cb9f813877cd10dcbaa326b9ed01f",
    "LLMGeoDis_part1.zip": "e0b90fa7ffff0ca9a4ef102118db8056",
    "LLMGeoDis_part2.zip": "e8137895a92159c6d9b19f21a4559709",
    "LLMGeoDis_part3.zip": "817e75737a4834b782568e6a079e3dc5",
    "LLMGeoDis_part4.zip": "667f69347acd41261bf397cadd8f11a3",
    "LLMGeoDis_part5.zip": "be427a1290f6eea5eb88a7bf87b2141d",
    "emdat_geocoding-zenodo.zip": "6d177d89cc6ceacf790068213974b5b7",
    "gdis_disnos.csv": "41e6a666c7e26323ae6853ef753f960d",
    "geoemdat_gaul.gpkg": "79b9e864059c19e6bf76b084a4aba9ee",
    "input_emdat.csv": "97384f5817103569d2b1b18de5be4ea4",
    "pend-gdis-1960-2018-disasterlocations.csv": "c6a669466c815a0882deb5b4cc648acb",
    "reliability_db.csv": "fbb290425afbb64a3de62d8373fb839d",
    "synthetic_EMDAT_locations.csv": "391085a505a50c948b95ffdb257ab058",
}
# Published digests do NOT independently verify the original data bytes.

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


def normalize_llm_geodis_v7(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Accept the exact current InvenioRDM metadata shape, never data files.

    Preserve the other historical Zenodo candidates' original parser contract.
    This shape conversion is not evidence of original download or upstream
    commercial rights.
    """
    record = dict(require_dict(payload, "Zenodo v7 record"))
    shape = "legacy_compatibility"
    raw_id = record.get("id")
    if type(raw_id) is str:
        if raw_id != str(RECORDS[LLM_GEODIS_SOURCE]):
            raise MetadataPreflightError("LLM-GeoDis v7 source record ID mismatch")
        record["id"] = RECORDS[LLM_GEODIS_SOURCE]
    metadata = dict(require_dict(record.get("metadata"), "metadata"))

    pids = record.get("pids")
    if pids is not None:
        doi_entry = require_dict(require_dict(pids, "pids").get("doi"), "pids.doi")
        doi = require_text(doi_entry.get("identifier"), "pids.doi.identifier")
        if "doi" in record and record["doi"].casefold() != doi.casefold():
            raise MetadataPreflightError("conflicting legacy DOI and version DOI")
        record["doi"] = doi
        shape = "inveniordm"

    access = record.get("access")
    if isinstance(access, dict) and ("record" in access or "files" in access):
        if access.get("record") != "public" or access.get("files") != "public":
            raise MetadataPreflightError("record or original file access not public")
        if "access_right" in metadata and metadata["access_right"] != "open":
            raise MetadataPreflightError("conflicting access statements")
        metadata["access_right"] = "open"
        shape = "inveniordm"

    if "rights" in metadata:
        rights = metadata["rights"]
        if not isinstance(rights, list) or len(rights) != 1:
            raise MetadataPreflightError("expected exactly one version-pinned record license")
        declared = require_text(require_dict(rights[0], "metadata.rights[0]").get("id"), "rights.id")
        previous = metadata.get("license")
        if previous is not None:
            old_id = previous.get("id") if isinstance(previous, dict) else previous
            if old_id != declared:
                raise MetadataPreflightError("contradictory record license statements")
        metadata["license"] = {"id": declared}
        shape = "inveniordm"

    raw_files = record.get("files")
    if isinstance(raw_files, dict):
        if raw_files.get("enabled") is not True:
            raise MetadataPreflightError("Zenodo v7 files are not enabled")
        entries = raw_files.get("entries")
        if not isinstance(entries, list):
            raise MetadataPreflightError("InvenioRDM files.entries must be an array")
        count = raw_files.get("count")
        if count is not None and (type(count) is not int or count != len(entries)):
            raise MetadataPreflightError("InvenioRDM file count mismatch")
        for position, item in enumerate(entries):
            links = require_dict(require_dict(item, f"files.entries[{position}]").get("links"), "file links")
            content = require_text(links.get("content"), "original file content URL")
            key = require_text(item.get("key"), "source file key")
            check_download_url(content, RECORDS[LLM_GEODIS_SOURCE])
            if not content.endswith(f"/files/{key}/content"):
                raise MetadataPreflightError("file content link does not match exact key")
        record["files"] = entries
        shape = "inveniordm"

    record["metadata"] = metadata
    return record, shape


def audit_record(payload: dict[str, Any], source_id: str, raw_sha256: str) -> dict[str, Any]:
    if source_id == "ihcantabria.transclima.tropical-cyclone-data-catalogue.v1":
        raise MetadataPreflightError("catalogue latest record 23736380 is restricted; no public files")
    if source_id not in RECORDS:
        raise MetadataPreflightError("unknown source candidate; no unreviewed dynamic IDs")
    record = require_dict(payload, "record")
    metadata_api_shape = "legacy_compatibility"
    if source_id == LLM_GEODIS_SOURCE:
        record, metadata_api_shape = normalize_llm_geodis_v7(record)
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

    if source_id == LLM_GEODIS_SOURCE:
        if metadata.get("version") != "v7":
            raise MetadataPreflightError("LLM-GeoDis record version is not pinned v7")
        if license_id.casefold() != "cc-by-4.0":
            raise MetadataPreflightError("LLM-GeoDis declared record license differs from pinned CC BY 4.0")
        if seen != LLM_GEODIS_V7_FILES:
            raise MetadataPreflightError("LLM-GeoDis v7 original file inventory mismatch")
        for item in inventory:
            published = "md5:" + LLM_GEODIS_V7_PUBLISHED_MD5[item["key"]]
            if item["publisher_checksum"] != published:
                raise MetadataPreflightError("LLM-GeoDis v7 published source checksum mismatch")

    return {
        "schema_version": "zenodo-cat-metadata-preflight-v0",
        "metadata_api_shape": metadata_api_shape,
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


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MetadataPreflightError(f"duplicate metadata JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise MetadataPreflightError(f"nonfinite metadata JSON value: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True, choices=sorted(RECORDS))
    parser.add_argument("--metadata", required=True, type=Path, help="local JSON, not a URL")
    args = parser.parse_args()
    try:
        if not args.metadata.is_file() or args.metadata.stat().st_size > MAX_METADATA_BYTES:
            raise MetadataPreflightError("metadata file missing or exceeds 5 MiB cap")
        raw = args.metadata.read_bytes()
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_nonfinite)
        receipt = audit_record(payload, args.source_id, hashlib.sha256(raw).hexdigest())
    except (OSError, UnicodeError, json.JSONDecodeError, MetadataPreflightError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
