# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed metadata-only receipt for Hazard Plain release 2026-10.

No underlying CSV, Parquet, claims, insurer data or source observations are
read, emitted or admitted. Publisher-provided file hashes remain unverified
claims until exact provider data bytes are acquired and checked separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

MANIFEST_URL = "https://files.hazardplain.org/r/2026-10/bulk/manifest.json"
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
EXPECTED_RELEASE = "2026-10"
EXPECTED_AS_OF = "2026-09-30"
EXPECTED_BUILT_AT = "2026-10-17T19:57:41+00:00"
EXPECTED_FILES = {
    "national/nri_county_hazard.csv": {
        "table": "nri_county_hazard", "rows": 58176, "bytes": 23764594,
        "sha256": "262d0dbc42dfc123408f28d3723bde49c6249c8f734adb2fafb720bb4f770eae",
        "sources": {"nri", "storm_events"},
        "columns": {"stcofips", "hazard", "eal_total", "eal_b", "exp_b", "afreq"},
    },
    "national/eal_outliers.csv": {
        "table": "eal_outliers", "rows": 45853, "bytes": 10265835,
        "sha256": "47c50202b0c6b57fd0c75624e51d3b7b87bb11ae2951ac7b4f5e299882525815",
        "sources": {"nri", "storm_events", "census_adjacency"},
        "columns": {"stcofips", "hazard", "eal_total", "neighbor_median_eal", "outlier", "caveat"},
    },
    "national/b2c_county.csv": {
        "table": "b2c_county", "rows": 3232, "bytes": 352674,
        "sha256": "4d891f4fce8b0f5ae1c4d6119be74b217e302e5cd8f17e3a6b8e43c2c0c7ffc5",
        "sources": {"nfip_mlp"},
        "columns": {"stcofips", "fma_rl", "nfip_rl", "single_family_insured", "as_of_date"},
    },
}


class HazardPlainMetadataError(ValueError):
    """Provider release metadata does not match the reviewed discovery contract."""


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise HazardPlainMetadataError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value):
    raise HazardPlainMetadataError("nonfinite JSON numeric literal")


def inspect_manifest(original: bytes) -> dict:
    if type(original) is not bytes or not 100 <= len(original) <= MAX_MANIFEST_BYTES:
        raise HazardPlainMetadataError("bounded original manifest bytes required")
    try:
        payload = json.loads(original.decode("utf-8"), object_pairs_hook=_strict_object,
                             parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HazardPlainMetadataError("invalid UTF-8 JSON source manifest") from exc
    if type(payload) is not dict or any(payload.get(k) != v for k, v in {
            "manifest_version": "1.0", "kind": "bulk", "product": "Hazard Plain",
            "release": EXPECTED_RELEASE, "as_of": EXPECTED_AS_OF,
            "built_at": EXPECTED_BUILT_AT}.items()):
        raise HazardPlainMetadataError("unexpected provider release identity or vintage")
    if type(payload.get("files")) is not list or type(payload.get("tables")) is not list:
        raise HazardPlainMetadataError("manifest files and tables must be arrays")
    files = payload["files"]
    tables = payload["tables"]
    if len(files) > 10000 or len(tables) > 200:
        raise HazardPlainMetadataError("excessive table/file count")
    indexed_files = {}
    for record in files:
        if type(record) is not dict or type(record.get("path")) is not str:
            raise HazardPlainMetadataError("invalid manifest file record")
        path = record["path"]
        if (path in indexed_files or path.startswith("/") or "\\" in path
                or any(segment in {"", ".", ".."} for segment in path.split("/"))):
            raise HazardPlainMetadataError("unsafe or duplicate manifest path")
        indexed_files[path] = record
    indexed_tables = {}
    for table in tables:
        if type(table) is not dict or type(table.get("name")) is not str:
            raise HazardPlainMetadataError("invalid manifest table record")
        if table["name"] in indexed_tables:
            raise HazardPlainMetadataError("duplicate table identity")
        indexed_tables[table["name"]] = table

    receipts = []
    for path, expected in sorted(EXPECTED_FILES.items()):
        record = indexed_files.get(path)
        table = indexed_tables.get(expected["table"])
        if not record or not table:
            raise HazardPlainMetadataError("selected provider table/file missing")
        if (record.get("table") != expected["table"]
                or record.get("kind") != "national_csv"
                or type(record.get("rows")) is not int
                or record["rows"] != expected["rows"]
                or type(record.get("bytes")) is not int
                or record["bytes"] != expected["bytes"]
                or record.get("sha256") != expected["sha256"]
                or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("sha256", "")))):
            raise HazardPlainMetadataError("publisher table file identity changed")
        if (type(table.get("rows")) is not int
                or table["rows"] != expected["rows"]
                or type(table.get("columns")) is not list
                or not all(type(c) is str for c in table["columns"])
                or not expected["columns"].issubset(set(table["columns"]))
                or type(table.get("sources")) is not list
                or set(table["sources"]) != expected["sources"]):
            raise HazardPlainMetadataError("publisher table schema or source lineage changed")
        receipts.append({
            "path": path, "table": expected["table"], "rows": record["rows"],
            "provider_claimed_file_bytes": record["bytes"],
            "provider_claimed_file_sha256": record["sha256"],
            "derived_from": sorted(expected["sources"]),
            "source_file_bytes_inspected": False,
        })
    return {
        "status": "PROVIDER_MANIFEST_METADATA_CHECKED_ONLY",
        "source_manifest_url": MANIFEST_URL,
        "original_manifest_bytes": len(original),
        "original_manifest_sha256": hashlib.sha256(original).hexdigest(),
        "release": EXPECTED_RELEASE,
        "as_of": EXPECTED_AS_OF,
        "built_at": EXPECTED_BUILT_AT,
        "selected_files": receipts,
        "provider_data_file_hashes_independently_verified": False,
        "nri_noaa_source_lineage_independent": False,
        "commercial_rights_reviewed": False,
        "model_input_admitted": False,
        "insurance_losses_or_aep_oep_generated": False,
    }


class SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if target.scheme != "https" or target.hostname != "files.hazardplain.org":
            raise HazardPlainMetadataError("provider manifest redirected outside source host")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def fetch_official_manifest(*, opener=None) -> bytes:
    if opener is None:
        opener = urllib.request.build_opener(SameHostRedirect()).open
    request = urllib.request.Request(MANIFEST_URL, headers={
        "User-Agent": "OpenCatastrophe-manifest-metadata-audit/0.1",
    })
    with opener(request, timeout=25) as response:
        target = urlsplit(response.geturl())
        if target.scheme != "https" or target.hostname != "files.hazardplain.org":
            raise HazardPlainMetadataError("manifest final host is not provider")
        size = 0
        chunks = []
        while True:
            part = response.read(64 * 1024)
            if not part:
                break
            size += len(part)
            if size > MAX_MANIFEST_BYTES:
                raise HazardPlainMetadataError("provider manifest exceeds byte budget")
            chunks.append(part)
        return b"".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--official-live", action="store_true", help="fetch ONLY official manifest JSON")
    group.add_argument("--manifest", type=Path, help="local original manifest JSON; no data CSV")
    args = parser.parse_args()
    try:
        if args.official_live:
            original = fetch_official_manifest()
        else:
            path = args.manifest
            if path.is_symlink() or not path.is_file() or not 100 <= path.stat().st_size <= MAX_MANIFEST_BYTES:
                raise HazardPlainMetadataError("bounded regular manifest file required")
            original = path.read_bytes()
        print(json.dumps(inspect_manifest(original), sort_keys=True, indent=2))
    except (OSError, TimeoutError, HazardPlainMetadataError) as exc:
        print("BLOCKED: " + str(exc)[:140], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
