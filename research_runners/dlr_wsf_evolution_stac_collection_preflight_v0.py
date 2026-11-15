#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only WSF Evolution STAC Collection identity and science-boundary gate.

No network, item pagination, raster access, database write or admission is possible.
An independently acquired exact original metadata body and independently pinned
SHA-256 are mandatory; generated receipts are metadata evidence only.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl, urlsplit

SOURCE_ID = "dlr.wsf.evolution.1985-2015"
PROFILE = "dlr-wsf-evolution-stac-collection-metadata-preflight-v0"
SOURCE_URL = "https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/WSF_Evolution?f=json"
MAX_BYTES = 131072
HASH_RE = re.compile(r"[a-f0-9]{64}\Z")


class WSFMetadataBlocked(ValueError):
    """Original metadata fails a pinned identity or science safety condition."""


def _no_duplicate_pairs(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise WSFMetadataBlocked("duplicate STAC metadata key")
        result[name] = value
    return result


def _no_nonfinite(value):
    raise WSFMetadataBlocked("non-finite STAC numeric value")


def _datetime_utc(value: object, *, beginning: bool) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise WSFMetadataBlocked("time extent must be an explicit UTC STAC timestamp")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WSFMetadataBlocked("malformed STAC temporal extent") from exc
    if beginning:
        if instant.year != 1985 or instant.month != 1 or instant.day != 1:
            raise WSFMetadataBlocked("unexpected WSF Evolution temporal start")
    elif instant.year != 2015 or instant.month != 12 or instant.day != 31:
        raise WSFMetadataBlocked("unexpected WSF Evolution temporal end")


def _is_fixed_self_link(href: object) -> bool:
    if type(href) is not str:
        return False
    try:
        url = urlsplit(href)
        _ = url.port
    except ValueError:
        return False
    if (url.scheme != "https" or url.hostname != "geoservice.dlr.de"
            or url.username or url.password or url.port is not None or url.fragment
            or url.path != "/eoc/ogc/stac/v1/collections/WSF_Evolution"):
        return False
    return url.query == "" or parse_qsl(url.query, keep_blank_values=True) == [("f", "json")]


def inspect_original_collection(raw: bytes, independently_pinned_sha256: str) -> dict:
    if type(independently_pinned_sha256) is not str or not HASH_RE.fullmatch(independently_pinned_sha256):
        raise WSFMetadataBlocked("expected SHA-256 must be pinned externally as 64 lowercase hex")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise WSFMetadataBlocked("original response is empty or exceeds metadata-only cap")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != independently_pinned_sha256:
        raise WSFMetadataBlocked("independently pinned original SHA-256 mismatch")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
                          parse_constant=_no_nonfinite)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise WSFMetadataBlocked("malformed original STAC JSON") from exc
    if type(data) is not dict or data.get("type") != "Collection" or data.get("id") != "WSF_Evolution":
        raise WSFMetadataBlocked("wrong provider STAC collection identity")
    version = data.get("stac_version")
    if type(version) is not str or not re.fullmatch(r"1\.\d+\.\d+", version):
        raise WSFMetadataBlocked("unsupported or missing STAC v1 version")
    if data.get("license") != "CC-BY-4.0":
        raise WSFMetadataBlocked("no verified product-specific CC BY 4.0 declaration")
    description = data.get("description")
    if type(description) is not str or not all(word in description.lower() for word in ("settlement", "1985", "2015")):
        raise WSFMetadataBlocked("provider temporal/scientific description changed")
    extent = data.get("extent")
    if type(extent) is not dict:
        raise WSFMetadataBlocked("missing STAC extent")
    spatial, temporal = extent.get("spatial"), extent.get("temporal")
    if type(spatial) is not dict or type(temporal) is not dict:
        raise WSFMetadataBlocked("invalid extent metadata")
    bboxes, intervals = spatial.get("bbox"), temporal.get("interval")
    if type(bboxes) is not list or len(bboxes) != 1 or bboxes != [[-180, -90, 180, 90]]:
        raise WSFMetadataBlocked("unexpected global spatial bounding box")
    if type(intervals) is not list or len(intervals) != 1 or type(intervals[0]) is not list or len(intervals[0]) != 2:
        raise WSFMetadataBlocked("temporal coverage is not a single pinned interval")
    _datetime_utc(intervals[0][0], beginning=True)
    _datetime_utc(intervals[0][1], beginning=False)
    providers = data.get("providers")
    if type(providers) is not list or not any(
        type(p) is dict and type(p.get("name")) is str and ("DLR" in p["name"] or "German Aerospace Center" in p["name"])
        for p in providers
    ):
        raise WSFMetadataBlocked("original producer/host attribution missing")
    links = data.get("links")
    if type(links) is not list or not any(
        type(link) is dict and link.get("rel") == "self" and
        _is_fixed_self_link(link.get("href")) for link in links
    ):
        raise WSFMetadataBlocked("missing exact DLR self-link (no external links followed)")
    return {
        "profile": PROFILE,
        "source_id": SOURCE_ID,
        "request_url": SOURCE_URL,
        "original_metadata_bytes": len(raw),
        "original_metadata_sha256": digest,
        "stac_version": version,
        "collection_id": "WSF_Evolution",
        "reported_license": "CC-BY-4.0",
        "dataset_role": "historical_settlement_detection_context_only",
        "historical_years": [1985, 2015],
        "landsat_source": "Landsat-5/7 derived observation/model product",
        "annual_coverage_measured_as_construction_years": False,
        "yearly_input_data_consistency_independently_checked": False,
        "original_raster_bytes_acquired": False,
        "underlying_stac_items_checked": False,
        "model_input_admitted": False,
    }



IDC_QUALITY = {
    1: "very_low", 2: "low", 3: "moderate",
    4: "fair", 5: "good", 6: "very_good",
}


def interpret_detection_and_idc(detection_year: int, idc_score: int | None) -> dict:
    """Interpret paired *synthetic or externally validated* native pixels.

    This deliberately cannot compute building age or an insured location.
    Real pixel use requires independent source asset hashes, paired CRS,
    co-registration, correct IDC year band and a licensed original sample.
    """
    if type(detection_year) is not int or not (detection_year == 0 or 1985 <= detection_year <= 2015):
        raise WSFMetadataBlocked("invalid WSF Evolution year code; 0 is NoData, not no buildings")
    if detection_year == 0:
        if idc_score is not None:
            raise WSFMetadataBlocked("cannot interpret IDC score for a NoData year pixel")
        return {
            "detection_year": None, "pixel_state": "NO_DATA_NOT_NO_SETTLEMENT",
            "idc_quality": None, "construction_year": None,
            "model_input_admitted": False,
        }
    if type(idc_score) is not int or idc_score not in IDC_QUALITY:
        raise WSFMetadataBlocked("paired IDC score 1..6 required for an observed year code")
    return {
        "detection_year": detection_year,
        "pixel_state": "ESTIMATED_FIRST_SETTLEMENT_DETECTION_NOT_CONSTRUCTION",
        "idc_quality": IDC_QUALITY[idc_score],
        "construction_year": None,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("original_collection_json", type=Path)
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    if args.out.resolve() == args.original_collection_json.resolve():
        ap.error("refusing to overwrite original source body")
    try:
        if args.original_collection_json.is_symlink() or args.out.is_symlink():
            raise WSFMetadataBlocked("refusing symlink input or output")
        report = inspect_original_collection(
            args.original_collection_json.read_bytes(), args.expected_sha256
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, WSFMetadataBlocked) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
