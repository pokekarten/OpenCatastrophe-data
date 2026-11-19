#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict offline metadata gate for ONE Physrisk-transformed WRI coastal hazard array.

No HTTP access, array chunk decoding, license approval, event synthesis or production import.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SOURCE = "osclimate.physrisk.hazard-indicator-public-bucket"
ORIGINAL = "wri.aqueduct-flood-hazard.v2.2020"
PROFILE = "physrisk-wri-aqueduct-coastal-zarr-metadata-v0"
ROOT = ("https://os-climate-physical-risk.s3.amazonaws.com/"
        "hazard-indicators/hazard.zarr/inundation/wri/v2/"
        "inuncoast_historical_nosub_hist_0")
RETURN_PERIODS = [2, 5, 10, 25, 50, 100, 250, 500, 1000]
TRANSFORM = [1 / 120, 0, -180, 0, -1 / 120, 90, 0, 0, 1]
SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
MAX_META_BYTES = 4096


class SourceGateError(ValueError):
    """The source evidence changed or cannot justify the claimed semantics."""


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SourceGateError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _nonfinite(text):
    raise SourceGateError("nonfinite JSON number: " + text)


def _load(blob: bytes, expected_sha256: str, label: str) -> tuple[dict, str]:
    if not isinstance(expected_sha256, str) or not SHA_PATTERN.fullmatch(expected_sha256):
        raise SourceGateError(label + ": SHA-256 must be independently pinned lowercase hex")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_META_BYTES:
        raise SourceGateError(label + ": invalid or oversized original metadata")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected_sha256:
        raise SourceGateError(label + ": source metadata SHA-256 mismatch")
    try:
        doc = json.loads(blob.decode("utf-8"), object_pairs_hook=_unique_keys,
                         parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SourceGateError(label + ": invalid UTF-8/JSON") from exc
    if type(doc) is not dict:
        raise SourceGateError(label + ": expected JSON object")
    return doc, digest


def _number(value):
    return type(value) in (float, int) and math.isfinite(value)


def inspect_metadata(zarray_blob: bytes, zattrs_blob: bytes,
                     zarray_sha256: str, zattrs_sha256: str) -> dict:
    arr, arr_hash = _load(zarray_blob, zarray_sha256, ".zarray")
    attrs, attrs_hash = _load(zattrs_blob, zattrs_sha256, ".zattrs")
    expected_arr = {
        "zarr_format": 2, "shape": [9, 21600, 43200],
        "chunks": [9, 1000, 1000], "dtype": "<f4", "order": "C",
        "compressor": {"id": "blosc", "cname": "lz4", "clevel": 5,
                       "shuffle": 1, "blocksize": 0},
        "filters": None,
    }
    if (any(type(arr.get(key)) is not type(value) or arr.get(key) != value
            for key, value in expected_arr.items())
            or not _number(arr.get("fill_value")) or arr["fill_value"] != 0):
        raise SourceGateError("unexpected WRI Zarr v2 array encoding, shape or fill value")
    if (attrs.get("crs") != "+init=epsg:4326"
            or attrs.get("dimensions") != ["index", "latitude", "longitude"]
            or attrs.get("index_name") != "return period (years)"
            or attrs.get("index_values") != RETURN_PERIODS
            or any(type(x) is not int for x in attrs["index_values"])):
        raise SourceGateError("return periods, CRS or index dimension changed")
    geotransform = attrs.get("transform_mat3x3")
    if (type(geotransform) is not list or len(geotransform) != 9
            or any(not _number(x) or abs(x - expected) > 1e-12
                   for x, expected in zip(geotransform, TRANSFORM))):
        raise SourceGateError("geographic transform changed or is nonfinite")
    return {
        "profile": PROFILE,
        "source_candidate": SOURCE,
        "original_provider_product": ORIGINAL,
        "zarray_url": ROOT + "/.zarray", "zattrs_url": ROOT + "/.zattrs",
        "zarray_sha256": arr_hash, "zattrs_sha256": attrs_hash,
        "data_type": "float32", "array_shape_return_period_lat_lon": [9, 21600, 43200],
        "crs_native": attrs["crs"], "grid_step_degrees": [1 / 120, -1 / 120],
        "return_period_years": RETURN_PERIODS,
        "peril": "coastal_flood", "baseline": "historical_no_subsidence",
        "intensity_units_from_wri_provider_documentation": "m",
        "flood_protection_modelled": False,
        "return_period_levels_are_independent_events": False,
        "annual_event_catalogue_present": False,
        "physical_loss_or_insured_loss_present": False,
        "array_chunks_read": False,
        "original_wri_geotiff_cellwise_reconciled": False,
        "upstream_rights_and_scientific_review_complete": False,
        "model_input_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zarray_json", type=Path)
    parser.add_argument("zattrs_json", type=Path)
    parser.add_argument("--expected-zarray-sha256", required=True)
    parser.add_argument("--expected-zattrs-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    sources = {args.zarray_json.resolve(), args.zattrs_json.resolve()}
    if len(sources) != 2 or args.out.resolve() in sources:
        parser.error("original inputs must be distinct and never overwritten")
    try:
        report = inspect_metadata(args.zarray_json.read_bytes(), args.zattrs_json.read_bytes(),
                                  args.expected_zarray_sha256, args.expected_zattrs_sha256)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, SourceGateError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
