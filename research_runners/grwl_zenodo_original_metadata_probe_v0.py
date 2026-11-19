# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fixed, bounded Zenodo API GRWL publication/file metadata reconciliation.

Opt-in original-provider metadata GET only. Never requests ZIP or source GIS bytes;
does not establish source-file SHA-256, model admission, or commercial rights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from urllib.request import Request, HTTPRedirectHandler, ProxyHandler, HTTPSHandler, build_opener

SCHEMA = "opencatastrophe-grwl-zenodo-original-metadata-v0"
HOST = "https://zenodo.org/api/records/"
MAX_BYTES = 131072
CONCEPT_ID = "1269594"
LICENSE = "cc-by-4.0"
FULL_VECTOR = ("GRWL_vector_V01.01.zip", "md5:40171f15c0fccd470db32446dda0480e", 3104998836)
MASK = ("GRWL_mask_V01.01.zip", "md5:4bd15bcd9cdcce7b620cd02f776749fa", 393801516)
RECORDS = {
    1297434: ("GRWL_summaryStats_V01.01.zip", "md5:c37021e144fbff19ae3fc4e701d85d38", 43194162),
    18624542: ("GRWL_summaryStats_V01.02.zip", "md5:cac403c1a59bce7a74432085d3f5bd3a", 43282861),
}


class MetadataError(ValueError):
    """Original provider metadata or access violates the fixed contract."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _decode_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MetadataError("duplicate provider JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise MetadataError("non-finite JSON constant")


def default_fetch(url, max_bytes):
    if url not in {HOST + str(i) for i in RECORDS} or max_bytes != MAX_BYTES:
        raise MetadataError("non-allowlisted original URL or size")
    request = Request(url, method="GET", headers={
        "Accept": "application/json", "Accept-Encoding": "identity",
        "User-Agent": "OpenCatastrophe-GRWL-original-metadata-probe/0",
    })
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), NoRedirects())
    with opener.open(request, timeout=12) as response:
        if response.status != 200:
            raise MetadataError("unexpected original provider HTTP status")
        if not response.headers.get("Content-Type", "").lower().startswith("application/json"):
            raise MetadataError("original provider content-type is not JSON")
        size = response.headers.get("Content-Length")
        if size is not None and (not re.fullmatch(r"[0-9]+", size) or int(size) > max_bytes):
            raise MetadataError("oversized original provider metadata")
        body = response.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise MetadataError("original provider metadata exceeds byte limit")
    return body


def validate_original_record(blob, expected_id):
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise MetadataError("metadata response is missing or oversized")
    try:
        record = json.loads(blob.decode("utf-8"), object_pairs_hook=_decode_pairs, parse_constant=_reject_constant)
    except (UnicodeError, ValueError) as exc:
        raise MetadataError("invalid original provider JSON") from exc
    if not isinstance(record, dict) or type(record.get("id")) is not int or record["id"] != expected_id:
        raise MetadataError("original record ID mismatch")
    if record.get("doi") != f"10.5281/zenodo.{expected_id}" or str(record.get("conceptrecid")) != CONCEPT_ID:
        raise MetadataError("original record DOI / concept identity mismatch")
    meta = record.get("metadata")
    if not isinstance(meta, dict) or meta.get("title") != "Global River Widths from Landsat (GRWL) Database":
        raise MetadataError("unexpected original GRWL publication")
    lic = meta.get("license")
    if not isinstance(lic, dict) or lic.get("id") != LICENSE:
        raise MetadataError("unexpected provider licence claim")
    if meta.get("version") != "V01.01":
        raise MetadataError("provider description version changed: re-review needed")
    files = record.get("files")
    if not isinstance(files, list) or len(files) != 3:
        raise MetadataError("original provider file list must contain exactly three assets")
    expected = (RECORDS[expected_id], FULL_VECTOR, MASK)
    by_name = {}
    for entry in files:
        if not isinstance(entry, dict):
            raise MetadataError("non-object provider file entry")
        name, checksum, size = entry.get("key"), entry.get("checksum"), entry.get("size")
        if type(name) is not str or name in by_name or type(checksum) is not str or type(size) is not int:
            raise MetadataError("duplicate or malformed provider file record")
        if size <= 0 or not re.fullmatch(r"md5:[a-f0-9]{32}", checksum):
            raise MetadataError("malformed provider size or checksum")
        by_name[name] = (name, checksum, size)
    if set(by_name) != {item[0] for item in expected}:
        raise MetadataError("unexpected GRWL original asset name")
    for item in expected:
        if by_name[item[0]] != item:
            raise MetadataError("original provider archive checksum/size mismatch")
    return {
        "record_id": expected_id,
        "concept_record_id": CONCEPT_ID,
        "doi": record["doi"],
        "provider_displayed_version": meta["version"],
        "provider_license_claim": lic["id"],
        "metadata_json_sha256": hashlib.sha256(blob).hexdigest(),
        "original_files_metadata": [
            {"archive": item[0], "provider_md5_unverified": item[1][4:],
             "provider_file_bytes_unverified": item[2]} for item in sorted(expected)
        ],
    }


def reconcile(*, fetch=default_fetch):
    records = [validate_original_record(fetch(HOST + str(rid), MAX_BYTES), rid) for rid in sorted(RECORDS)]
    early, late = records
    by_release = [{entry["archive"]: entry for entry in r["original_files_metadata"]} for r in records]
    def unchanged_common_file(filename):
        return (by_release[0][filename]["provider_md5_unverified"] == by_release[1][filename]["provider_md5_unverified"]
                and by_release[0][filename]["provider_file_bytes_unverified"] == by_release[1][filename]["provider_file_bytes_unverified"])
    return {
        "schema": SCHEMA,
        "records": records,
        "simplified_archive_size_difference_bytes": RECORDS[18624542][2] - RECORDS[1297434][2],
        "same_provider_claim_for_full_vector": unchanged_common_file(FULL_VECTOR[0]),
        "same_provider_claim_for_mask": unchanged_common_file(MASK[0]),
        "same_provider_displayed_version_but_different_simplified_filenames": True,
        "original_source_zip_bytes_downloaded": False,
        "original_source_file_sha256_verified": False,
        "licensed_for_production_use": False,
        "scientific_validation_completed": False,
        "model_input_approved": False,
        "neon_modified": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="opt-in two bounded original Zenodo JSON GETs")
    args = parser.parse_args(argv)
    if not args.live:
        parser.print_help()
        return 2
    try:
        print(json.dumps(reconcile(), indent=2, sort_keys=True))
    except (MetadataError, OSError, TimeoutError) as exc:
        parser.error("original metadata check blocked: " + str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
