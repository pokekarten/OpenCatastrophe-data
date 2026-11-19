#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, offline ISIMIP3a ER11 maxrain publisher-metadata preflight.

Input: independently retrieved/pinned original publisher dataset JSON.
No network, external source downloads, NetCDF bytes, model approval or
commercial-rights clearance is performed by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

SOURCE_ID = "isimip3a.tc.er11-wind.historical.maxrain.1950-2021"
DATASET_UUID = "f08ab32e-b3ad-4984-81d1-495235765b6c"
PRODUCT_NAME = "er11-wind_obsclim_historical_maxrain"
VERSION = "20240402"
EXPECTED_YEARS = tuple(range(1950, 2022))
EXPECTED_SIZE_BYTES = 1911545255
MAX_METADATA_BYTES = 1024 * 1024
CC0 = "https://creativecommons.org/publicdomain/zero/1.0/"
FILE_PREFIX = (
    "ISIMIP3a/InputData/climate/tropical_cyclones/obsclim/"
    "global/storm/historical/ER11-wind/"
)
NETCDF_PATTERN = re.compile(r"er11-wind_obsclim_historical_maxrain_([0-9]{4})\.nc\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SHA512 = re.compile(r"[0-9a-f]{128}\Z")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")


class ISIMIPMetadataError(ValueError):
    """Publisher metadata structure, version or rights declaration is uncertain."""


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ISIMIPMetadataError("duplicate JSON key")
        result[key] = value
    return result


def _no_nonfinite(value: str) -> None:
    raise ISIMIPMetadataError("non-finite JSON constant")


def _object(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise ISIMIPMetadataError(field + " must be JSON object")
    return value


def _rights(value: object, field: str) -> None:
    item = _object(value, field)
    if item.get("short") != "CC0 1.0" or item.get("rights_uri") != CC0:
        raise ISIMIPMetadataError(field + " does not declare exact CC0 1.0")


def _provider_url(value: object, expected: str, field: str) -> None:
    if type(value) is not str or value != expected:
        raise ISIMIPMetadataError(field + " provider URL mismatch")
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as exc:
        raise ISIMIPMetadataError(field + " invalid URL") from exc
    if parts.scheme != "https" or not parts.hostname or port is not None or (
        parts.username or parts.password or parts.query or parts.fragment
    ):
        raise ISIMIPMetadataError(field + " unsafe provider URL")


def inspect_metadata_bytes(blob: bytes, expected_sha256: str) -> dict:
    if type(expected_sha256) is not str or not SHA256.fullmatch(expected_sha256):
        raise ISIMIPMetadataError("expected metadata SHA256 must be 64 lowercase hex digits")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_METADATA_BYTES:
        raise ISIMIPMetadataError("metadata JSON must be nonempty and at most 1 MiB")
    actual = hashlib.sha256(blob).hexdigest()
    if actual != expected_sha256:
        raise ISIMIPMetadataError("publisher metadata SHA256 mismatch")
    try:
        payload = json.loads(
            blob.decode("utf-8"),
            object_pairs_hook=_no_duplicates,
            parse_constant=_no_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ISIMIPMetadataError("invalid publisher JSON") from exc
    data = _object(payload, "dataset")
    if data.get("id") != DATASET_UUID or data.get("name") != PRODUCT_NAME:
        raise ISIMIPMetadataError("wrong dataset identity")
    if data.get("version") != VERSION:
        raise ISIMIPMetadataError("wrong publisher product version")
    if data.get("public") is not True or data.get("restricted") is not False:
        raise ISIMIPMetadataError("dataset is not declared public and unrestricted")
    _rights(data.get("rights"), "dataset.rights")
    _provider_url(
        data.get("url"),
        f"https://data.isimip.org/api/v1/datasets/{DATASET_UUID}/",
        "dataset.url",
    )
    _provider_url(
        data.get("filelist_url"),
        f"https://data.isimip.org/api/v1/datasets/{DATASET_UUID}/filelist/",
        "dataset.filelist_url",
    )
    specifiers = _object(data.get("specifiers"), "dataset.specifiers")
    exact = {
        "region": "global",
        "product": "InputData",
        "category": "climate",
        "wind_model": "er11-wind",
        "subcategory": "tropical_cyclones",
        "climate_scenario": "obsclim",
        "climate_variable": "maxrain",
        "simulation_round": "ISIMIP3a",
    }
    if any(specifiers.get(k) != v for k, v in exact.items()):
        raise ISIMIPMetadataError("wrong product specifiers")
    files = data.get("files")
    if not isinstance(files, list) or len(files) != len(EXPECTED_YEARS):
        raise ISIMIPMetadataError("expected exactly 72 annual files")
    years: list[int] = []
    seen_ids: set[str] = set()
    total_bytes = 0
    for f in files:
        item = _object(f, "file")
        filename = item.get("name")
        if not isinstance(filename, str):
            raise ISIMIPMetadataError("file name not text")
        match = NETCDF_PATTERN.fullmatch(filename)
        if match is None:
            raise ISIMIPMetadataError("unexpected file variable/name")
        years.append(int(match.group(1)))
        if item.get("path") != FILE_PREFIX + filename:
            raise ISIMIPMetadataError("file path changed")
        if item.get("version") != VERSION:
            raise ISIMIPMetadataError("file version changed")
        _rights(item.get("rights"), "file.rights")
        if item.get("checksum_type") != "sha512" or type(item.get("checksum")) is not str or not SHA512.fullmatch(item["checksum"]):
            raise ISIMIPMetadataError("missing or invalid publisher SHA512 declaration")
        fid = item.get("id")
        if not isinstance(fid, str) or not UUID.fullmatch(fid) or fid in seen_ids:
            raise ISIMIPMetadataError("invalid or duplicate source file UUID")
        seen_ids.add(fid)
        _provider_url(
            item.get("url"),
            f"https://data.isimip.org/api/v1/files/{fid}/",
            "file.url",
        )
        _provider_url(
            item.get("file_url"),
            "https://files.isimip.org/" + FILE_PREFIX + filename,
            "file.file_url",
        )
        size = item.get("size")
        if type(size) is not int or not 0 < size <= 1_000_000_000:
            raise ISIMIPMetadataError("source file byte count missing/invalid")
        total_bytes += size
    if tuple(years) != EXPECTED_YEARS:
        raise ISIMIPMetadataError("source years are missing, duplicated or unordered")
    declared = data.get("size")
    if type(declared) is not int or declared != EXPECTED_SIZE_BYTES or total_bytes != declared:
        raise ISIMIPMetadataError("dataset published file size sum/version mismatch")
    return {
        "profile": "isimip3a-er11-maxrain-publisher-json-preflight-v0",
        "source_id": SOURCE_ID,
        "dataset_uuid": DATASET_UUID,
        "dataset_version": VERSION,
        "metadata_sha256": actual,
        "metadata_byte_count": len(blob),
        "annual_file_count": len(files),
        "first_year": years[0],
        "last_year": years[-1],
        "declared_total_netcdf_bytes": total_bytes,
        "dataset_and_all_files_declared_cc0_1_0": True,
        "published_sha512_declarations_count": len(files),
        "published_sha512_independently_verified": False,
        "netcdf_source_bytes_acquired": False,
        "terms_and_dependencies_require_independent_review": True,
        "commercial_insurance_rights_cleared": False,
        "scientific_validation_completed": False,
        "admission_status": "not_admitted",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.metadata.resolve() == args.out.resolve():
        parser.error("refusing to overwrite publisher metadata")
    try:
        if args.metadata.stat().st_size > MAX_METADATA_BYTES:
            raise ISIMIPMetadataError("metadata JSON exceeds 1 MiB")
        report = inspect_metadata_bytes(args.metadata.read_bytes(), args.expected_sha256)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (ISIMIPMetadataError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
