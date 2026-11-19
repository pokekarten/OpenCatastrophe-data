#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed offline transport-receipt consistency for Eurostat V3 ZIP.

This cannot download anything. It only compares a small, externally produced
HTTP receipt to the separately authorized, locally available exact V3 ZIP.
A self-authored receipt NEVER proves the provider delivered or signed the file,
nor constitutes legal permission. Keep acquisition evidence separate from
content SHA, same-release cell parity, and scientific model admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

from research_runners.eurostat_census_v3_offline_complete_zip_parity_v0 import (
    ORIGINAL_ZIP_BYTES,
    ZIP_NAMES,
)
from research_runners.eurostat_census_v3_full_csv_member_parity_v0 import (
    CSVParityBlocked,
    PROVIDER_ARCHIVE,
)

RECEIPT_SCHEMA = "eurostat-gisco-census-2021-v3-offline-http-receipt-v0"
MAX_RECEIPT_BYTES = 4096
DIGEST_CHUNK = 1_048_576
EXPECTED_KEYS = frozenset({
    "schema", "source_url", "requested_url", "final_url",
    "http_method", "http_status", "redirect_count",
    "content_encoding", "content_type", "content_length_bytes",
    "saved_bytes", "local_file_sha256", "retrieved_at_utc",
    "source_access_review_reference",
})
ALLOWED_TYPES = frozenset({
    "application/zip", "application/octet-stream",
    "application/x-zip-compressed",
})


def _reject_if(condition: bool, explanation: str) -> None:
    if condition:
        raise CSVParityBlocked(explanation)


def _strict_object(pairs):
    v = {}
    for key, item in pairs:
        if key in v:
            raise CSVParityBlocked("duplicate HTTP receipt key")
        v[key] = item
    return v


def verify_local_zip_http_receipt(
    receipt_bytes: bytes,
    *,
    expected_zip_sha256: str,
    local_zip_bytes: int,
) -> dict:
    """Check receipt and locally computed file digest, not remote authenticity."""
    _reject_if(not isinstance(receipt_bytes, bytes)
               or not 2 <= len(receipt_bytes) <= MAX_RECEIPT_BYTES,
               "receipt is absent or outside bounded JSON size")
    try:
        receipt = json.loads(
            receipt_bytes.decode("utf-8"), object_pairs_hook=_strict_object)
    except CSVParityBlocked:
        raise
    except (UnicodeDecodeError, ValueError) as exc:
        raise CSVParityBlocked("invalid source receipt JSON") from exc
    _reject_if(not isinstance(receipt, dict)
               or set(receipt) != EXPECTED_KEYS,
               "unexpected HTTP receipt schema fields")
    _reject_if(receipt["schema"] != RECEIPT_SCHEMA,
               "HTTP receipt version drift")
    for key in ("source_url", "requested_url", "final_url"):
        _reject_if(receipt[key] != PROVIDER_ARCHIVE,
                   "HTTP receipt wrong exact Eurostat V3 provider URL: " + key)
    _reject_if(receipt["http_method"] != "GET"
               or type(receipt["http_status"]) is not int
               or receipt["http_status"] != 200,
               "HTTP receipt is not an exact completed full-object GET")
    _reject_if(type(receipt["redirect_count"]) is not int
               or receipt["redirect_count"] != 0,
               "HTTP source redirects are not independently reviewed")
    _reject_if(receipt["content_encoding"] != "identity",
               "unexpected gzip, Brotli or transformed source representation")
    _reject_if(not isinstance(receipt["content_type"], str)
               or receipt["content_type"] not in ALLOWED_TYPES,
               "unexpected provider ZIP content type")
    for k in ("content_length_bytes", "saved_bytes"):
        _reject_if(type(receipt[k]) is not int or receipt[k] != ORIGINAL_ZIP_BYTES
                   or receipt[k] != local_zip_bytes,
                   "HTTP receipt wrong full ZIP content length: " + k)
    sha = receipt["local_file_sha256"]
    _reject_if(not isinstance(sha, str)
               or re.fullmatch("[a-f0-9]{64}", sha) is None
               or sha != expected_zip_sha256,
               "HTTP receipt original ZIP SHA256 disagrees with local file")
    stamp = receipt["retrieved_at_utc"]
    _reject_if(not isinstance(stamp, str)
               or re.fullmatch(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z",
                               stamp) is None,
               "HTTP receipt retrieval timestamp is not canonical UTC")
    try:
        actual_time = datetime.fromisoformat(stamp[:-1] + "+00:00")
    except ValueError as exc:
        raise CSVParityBlocked("invalid UTC receipt timestamp") from exc
    _reject_if(actual_time > datetime.now(timezone.utc),
               "source retrieval timestamp is in the future")
    _reject_if(actual_time < datetime(2026, 5, 30, tzinfo=timezone.utc),
               "source receipt predates the V3 publication")
    review = receipt["source_access_review_reference"]
    _reject_if(not isinstance(review, str)
               or re.fullmatch("[A-Za-z0-9_./#-]{8,150}", review) is None,
               "source-specific manual service review reference absent")
    return {
        "source_archive": PROVIDER_ARCHIVE,
        "schema": RECEIPT_SCHEMA,
        "receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
        "local_zip_sha256": sha,
        "local_zip_bytes": local_zip_bytes,
        "source_access_review_reference": review,
        "transport_receipt_consistent_with_local_zip": True,
        "strict_full_get_no_redirect": True,
        "source_original_9_members_expected": len(ZIP_NAMES),
        "independently_signed_provider_origin_verified": False,
        "access_review_approval_verified_by_this_script": False,
        "same_release_csv_tiff_14_band_parity_verified_by_this_script": False,
        "cat_model_input_approved": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt-json", type=Path, required=True)
    parser.add_argument("--preapproved-v3-zip", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt_path = args.receipt_json
        zip_path = args.preapproved_v3_zip
        if (receipt_path.is_symlink() or not receipt_path.is_file()
                or not 2 <= receipt_path.stat().st_size <= MAX_RECEIPT_BYTES):
            raise CSVParityBlocked("local provider HTTP receipt absent or oversized")
        if (zip_path.is_symlink() or not zip_path.is_file()
                or zip_path.stat().st_size != ORIGINAL_ZIP_BYTES):
            raise CSVParityBlocked("exact original V3 local ZIP missing")
        digest = hashlib.sha256()
        with zip_path.open("rb") as stream:
            while chunk := stream.read(DIGEST_CHUNK):
                digest.update(chunk)
        evidence = verify_local_zip_http_receipt(
            receipt_path.read_bytes(), expected_zip_sha256=digest.hexdigest(),
            local_zip_bytes=zip_path.stat().st_size)
        print(json.dumps(evidence,sort_keys=True))
        return 0
    except (CSVParityBlocked, OSError) as exc:
        print(json.dumps({"status":"BLOCKED","reason":str(exc),
                          "cat_model_input_approved":False}),file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
