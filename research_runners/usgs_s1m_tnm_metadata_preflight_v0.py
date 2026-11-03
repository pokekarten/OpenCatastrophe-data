# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed USGS TNMAccess S1M metadata evidence preflight.

No network requests, asset downloads, sampling or admission. It reads an
externally supplied ORIGINAL bounded JSON body, binds its SHA-256 and checks
that S1M has not been confused with the legacy project 1-m DEM product.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

DATASET_TAG = "Seamless 1-m DEM (S1M)"
LEGACY_TAG = "Digital Elevation Model (DEM) 1 meter"
MAX_BYTES = 131072
DOWNLOAD_HOST = "prd-tnm.s3.amazonaws.com"
# One externally verified bounded TNM S1M example, not an admitted source asset.
# The TNM API may return "datasets": [] even with the exact S1M filter;
# do not accept that absence for any other product.
PILOT_SOURCE_ID = "6a9785801ba49b050c166274"
PILOT_TITLE = "S1M n0450e1510 20260821"
PILOT_DOWNLOAD_URL = (
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/"
    "S1M/n04e15/n0450e1510/S1M_n0450e1510_20260821.tif"
)
PILOT_BBOX = (-81.00, 25.95, -80.95, 26.00)
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")


class Blocked(ValueError):
    """Reject rather than infer an unverified dataset identity."""


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for k, v in pairs:
        if k in result:
            raise Blocked("duplicate JSON key")
        result[k] = v
    return result


def _constant(_value: str) -> object:
    raise Blocked("non-finite JSON value")


def load_receipt(path: Path, expected_sha256: str) -> tuple[object, str, int]:
    if not SHA_RE.fullmatch(expected_sha256):
        raise Blocked("expected SHA-256 must be 64 lowercase hex digits")
    with path.open("rb") as stream:
        original = stream.read(MAX_BYTES + 1)
    if not original or len(original) > MAX_BYTES:
        raise Blocked("empty or oversized original metadata body")
    digest = hashlib.sha256(original).hexdigest()
    if digest != expected_sha256:
        raise Blocked("original metadata SHA-256 mismatch")
    try:
        value = json.loads(original.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
    except (ValueError, UnicodeError) as e:
        raise Blocked("invalid strict JSON") from e
    return value, digest, len(original)


def check_catalog(value: object) -> dict[str, object]:
    if type(value) is not list or not value or len(value) > 100:
        raise Blocked("unexpected TNM datasets catalogue shape or size")
    matches: list[dict[str, object]] = []
    for parent in value:
        if type(parent) is not dict:
            raise Blocked("dataset parent not an object")
        tags = parent.get("tags", [])
        if type(tags) is not list:
            raise Blocked("dataset tags not a list")
        for tag in tags:
            if type(tag) is not dict:
                raise Blocked("dataset tag not an object")
            if tag.get("sbDatasetTag") == DATASET_TAG:
                if parent.get("parentCategory") != "Data" or tag.get("id") != "seamless-1m-dem":
                    raise Blocked("S1M tag has unexpected parent or identifier")
                matches.append(tag)
    if len(matches) != 1:
        raise Blocked("exact S1M tag absent, duplicate or ambiguous")
    if matches[0].get("sbDatasetTag") == LEGACY_TAG:
        raise Blocked("legacy project DEM selected")
    return {"mode": "catalogue_identity", "dataset_tag": DATASET_TAG, "catalogue_count": len(value)}


def check_products(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise Blocked("TNM product response not an object")
    if value.get("errors") not in (None, []):
        raise Blocked("provider reported errors")
    total = value.get("total")
    items = value.get("items")
    if type(total) is not int or total < 0 or type(items) is not list or len(items) != 1 or total < 1:
        raise Blocked("not exactly one bounded matching product")
    item = items[0]
    if type(item) is not dict:
        raise Blocked("product not an object")
    declared = item.get("datasets")
    if type(declared) is not list:
        raise Blocked("product dataset identity missing or malformed")
    if declared == [DATASET_TAG]:
        identity_evidence = "per_product_dataset_tag"
    elif (declared == [] and item.get("sourceId") == PILOT_SOURCE_ID
          and item.get("title") == PILOT_TITLE and item.get("downloadURL") == PILOT_DOWNLOAD_URL):
        # This exception is for ONE externally inspected public record;
        # it is not a general bypass for empty TNM datasets arrays.
        identity_evidence = "frozen_florida_s1m_record"
    else:
        raise Blocked("product dataset identity not attested for exact S1M")
    if item.get("format") != "GeoTIFF":
        raise Blocked("not a GeoTIFF metadata record")
    if type(item.get("sourceId")) is not str or not re.fullmatch(r"[a-f0-9]{24}", item["sourceId"]):
        raise Blocked("missing immutable provider source ID")
    url = item.get("downloadURL")
    if type(url) is not str:
        raise Blocked("missing product URL")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != DOWNLOAD_HOST or parsed.username or parsed.password
            or parsed.query or parsed.fragment or not parsed.path.startswith("/StagedProducts/Elevation/")
            or not parsed.path.lower().endswith(".tif")):
        raise Blocked("untrusted external or non-TIFF product URL")
    bounds = item.get("boundingBox")
    if type(bounds) is not dict:
        raise Blocked("no product bounding box")
    vals = [bounds.get(k) for k in ("minX", "minY", "maxX", "maxY")]
    if any(type(x) not in (int, float) for x in vals):
        raise Blocked("invalid product bbox")
    minx, miny, maxx, maxy = vals
    if not (-180 <= minx < maxx <= 180 and -90 <= miny < maxy <= 90):
        raise Blocked("invalid product bbox extent")
    if identity_evidence == "frozen_florida_s1m_record":
        bx0, by0, bx1, by1 = PILOT_BBOX
        if not (minx <= bx0 < bx1 <= maxx and miny <= by0 < by1 <= maxy):
            raise Blocked("frozen S1M pilot extent does not cover the recorded AOI")
    return {"mode": "product_metadata_only", "dataset_tag": DATASET_TAG, "source_id": item["sourceId"],
            "identity_evidence": identity_evidence, "admission": "not_admitted",
            "external_bytes_persisted": False, "provider_request_receipt_verified": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("catalogue", "products"), required=True)
    parser.add_argument("--original-json", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        value, digest, count = load_receipt(args.original_json, args.expected_sha256)
        result = check_catalog(value) if args.mode == "catalogue" else check_products(value)
    except (Blocked, OSError) as exc:
        print("BLOCKED: " + str(exc))
        return 2
    print(json.dumps({"status": "offline_verified_metadata_only", "original_sha256": digest,
                      "original_bytes": count, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
