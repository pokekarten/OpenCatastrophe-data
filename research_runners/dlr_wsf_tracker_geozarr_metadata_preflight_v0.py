#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline original-byte metadata gate for MindEarth/DLR WSF Tracker GeoZarr v3.

The two inputs must be exact independently retrieved zarr.json response bodies:
native level 0 and overview level 12. This preflight never accesses network or
raster chunks, reports no geospatial cells and cannot grant source admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SOURCE_ID = "dlr.eoc.wsf-tracker.2016-2026"
PROFILE = "dlr-wsf-tracker-geozarr-original-metadata-preflight-v0"
ROOT_URL = "https://data.source.coop/mindearth/wsf/World_WSF_20160701-20260101.zarr"
LEVELS = ("0", "12")
EXPECTED_SHAPES = {"0": [1536433, 4007502], "12": [375, 978]}
MAX_METADATA_BYTES = 32768
DIGEST = re.compile(r"[a-f0-9]{64}\Z")


class WSFGateError(ValueError):
    """A source identity or geometry/temporal representation assumption changed."""


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise WSFGateError("duplicate original Zarr JSON key")
        result[key] = value
    return result


def _nonfinite(value):
    raise WSFGateError("nonfinite original Zarr JSON value " + value)


def _read_metadata(blob: bytes, expected_sha: str, level: str) -> tuple[dict, str]:
    if type(expected_sha) is not str or not DIGEST.fullmatch(expected_sha):
        raise WSFGateError("independently pinned sha256 must be 64 lowercase hexadecimal characters")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_METADATA_BYTES:
        raise WSFGateError("original Zarr metadata missing or above strict byte cap")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected_sha:
        raise WSFGateError("source SHA256 mismatch for level " + level)
    try:
        doc = json.loads(blob.decode("utf-8"), object_pairs_hook=_strict_object,
                         parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise WSFGateError("invalid strict UTF-8 Zarr JSON at level " + level) from exc
    if type(doc) is not dict:
        raise WSFGateError("Zarr metadata must be a JSON object")
    return doc, digest


def _validate_array(doc: dict, level: str):
    if (type(doc.get("zarr_format")) is not int or doc["zarr_format"] != 3
            or doc.get("node_type") != "array"
            or doc.get("data_type") != "int8"
            or type(doc.get("fill_value")) is not int or doc["fill_value"] != 0):
        raise WSFGateError("unexpected Zarr v3, int8, or fill-value contract")
    shape = doc.get("shape")
    if (type(shape) is not list or len(shape) != 2
            or any(type(x) is not int for x in shape)
            or shape != EXPECTED_SHAPES[level]):
        raise WSFGateError("original source array shape differs from pinned level " + level)
    if doc.get("dimension_names") != ["y", "x"]:
        raise WSFGateError("unexpected source dimension order")
    attrs = doc.get("attributes")
    if (type(attrs) is not dict
            or attrs.get("_ARRAY_DIMENSIONS") != ["y", "x"]
            or attrs.get("grid_mapping") != "spatial_ref"
            or type(attrs.get("valid_min")) is not int or attrs["valid_min"] != 0
            or type(attrs.get("valid_max")) is not int or attrs["valid_max"] != 20):
        raise WSFGateError("unexpected index domain or coordinates metadata")
    description = attrs.get("description")
    if (type(description) is not str
            or "earliest" not in description.lower()
            or "min aggregation" not in description.lower()
            or "1-20" not in description):
        raise WSFGateError("source does not document earliest-event index and overview reducer")
    grid = doc.get("chunk_grid")
    if (type(grid) is not dict or grid.get("name") != "regular"
            or type(grid.get("configuration")) is not dict
            or grid["configuration"].get("chunk_shape") != [8192, 8192]):
        raise WSFGateError("unexpected storage shard grid; bounded sampling must be redesigned")
    codecs = doc.get("codecs")
    if (type(codecs) is not list or len(codecs) != 1
            or type(codecs[0]) is not dict or codecs[0].get("name") != "sharding_indexed"):
        raise WSFGateError("unexpected Zarr sharding codec")
    cfg = codecs[0].get("configuration")
    if type(cfg) is not dict or cfg.get("chunk_shape") != [256, 256]:
        raise WSFGateError("unexpected internal chunk granularity")
    if doc.get("storage_transformers") not in ([], None):
        raise WSFGateError("unreviewed storage transformer")


def earliest_detection_epoch(index: int) -> str | None:
    """Source raster code to first observed built-up epoch, NOT building age.

    Code 1 means built-up was ALREADY observed by 2016-07-01, not that a
    building was constructed in 2016. Zero conflates no-built-up and nodata.
    """
    if type(index) is not int or not 0 <= index <= 20:
        raise WSFGateError("WSF emergence index must be a source int8 code from 0 to 20")
    if index == 0:
        return None
    year = 2016 + index // 2
    month = 7 if index % 2 else 1
    return f"{year:04d}-{month:02d}-01"


def inspect_wsf_metadata_bytes(
    native_blob: bytes, overview_blob: bytes,
    native_sha256: str, overview_sha256: str,
) -> dict:
    native, native_hash = _read_metadata(native_blob, native_sha256, "0")
    overview, overview_hash = _read_metadata(overview_blob, overview_sha256, "12")
    _validate_array(native, "0")
    _validate_array(overview, "12")
    if native_hash == overview_hash:
        raise WSFGateError("native and overview metadata identities must differ")
    return {
        "profile": PROFILE,
        "candidate_id": SOURCE_ID,
        "original_native_metadata_url": ROOT_URL + "/0/wsf_tracker/zarr.json",
        "original_overview_metadata_url": ROOT_URL + "/12/wsf_tracker/zarr.json",
        "native_metadata_sha256": native_hash,
        "overview_metadata_sha256": overview_hash,
        "source_zarr_format": 3,
        "source_variable": "wsf_tracker",
        "source_data_type": "int8",
        "native_group": "0",
        "overview_group": "12",
        "native_shape_yx": EXPECTED_SHAPES["0"],
        "overview_shape_yx": EXPECTED_SHAPES["12"],
        "source_index_min": 0,
        "source_index_max": 20,
        "source_index_zero_meaning": "NO_SETTLEMENT_OR_NODATA_NOT_A_BUILDING_COUNT",
        "first_emergence_epoch": "2016-07-01",
        "last_emergence_epoch": "2026-01-01",
        "one_epoch_every_six_months": True,
        "overview_aggregates_with_minimum": True,
        "overview_valid_for_area_count_or_vintage_statistics": False,
        "index_one_preexisting_by_2016_07_not_construction_date": True,
        "direct_geozarr_to_dlr_stac_cog_pixel_alignment_verified": False,
        "native_raster_required_for_exact_built_up_area_statistics": True,
        "native_raster_chunks_acquired": False,
        "building_footprints_observed": False,
        "building_values_observed": False,
        "demolition_events_observed": False,
        "scientific_uncertainty_and_licence_review_complete": False,
        "model_input_admitted": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("level0_metadata_json", type=Path)
    ap.add_argument("level12_metadata_json", type=Path)
    ap.add_argument("--expected-level0-sha256", required=True)
    ap.add_argument("--expected-level12-sha256", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    src_paths = {args.level0_metadata_json.resolve(), args.level12_metadata_json.resolve()}
    if len(src_paths) != 2 or args.out.resolve() in src_paths:
        ap.error("refusing to use the same source twice or overwrite original provider bytes")
    try:
        receipt = inspect_wsf_metadata_bytes(
            args.level0_metadata_json.read_bytes(),
            args.level12_metadata_json.read_bytes(),
            args.expected_level0_sha256, args.expected_level12_sha256,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, WSFGateError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
