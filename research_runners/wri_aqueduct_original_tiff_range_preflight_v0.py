#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact original-WRI GeoTIFF header/IFD/georeference safety gate (read-only/offline).

Checks three small, independently SHA-pinned HTTP byte-range response bodies
for one WRI v2 2-year historical coastal/no-subsidence TIFF, never raster
samples, never complete TIFFs, and never implies insurance-model admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

PROFILE = "wri-aqueduct-v2-coastal-2yr-original-tiff-range-v0"
SOURCE_URL = ("https://aqueduct.wridata.org/AqueductFloods20/"
              "inuncoast_historical_nosub_hist_rp0002_0.tif")
HEADER_RANGE = (0, 1023)
IFD_RANGE = (44820220, 44822267)
GEO_RANGE = (44993200, 44993711)
EXPECTED_BYTES = (1024, 2048, 208)
SHA_PATTERN = re.compile(r"[a-f0-9]{64}\Z")


class TiffGateError(ValueError):
    """Original TIFF range identity or physical interpretation changed."""


def _check_blob(blob, supplied_sha, expected_length, label):
    if type(blob) is not bytes or len(blob) != expected_length:
        raise TiffGateError(label + ": incomplete or oversized exact original HTTP response range")
    if type(supplied_sha) is not str or not SHA_PATTERN.fullmatch(supplied_sha):
        raise TiffGateError(label + ": independently recorded SHA256 required")
    if hashlib.sha256(blob).hexdigest() != supplied_sha:
        raise TiffGateError(label + ": original-range SHA256 mismatch")


def _read_original_value(geodata: bytes, absolute_offset: int, length: int) -> bytes:
    start = absolute_offset - GEO_RANGE[0]
    if start < 0 or start + length > len(geodata):
        raise TiffGateError("GeoTIFF tag target outside pinned small original metadata range")
    return geodata[start:start + length]


def inspect_original_tiff_ranges(header: bytes, ifd: bytes, geo: bytes,
                                 header_sha: str, ifd_sha: str, geo_sha: str) -> dict:
    for b, digest, length, label in zip(
            (header, ifd, geo),
            (header_sha, ifd_sha, geo_sha),
            EXPECTED_BYTES, ("header", "IFD", "GeoTIFF auxiliary")):
        _check_blob(b, digest, length, label)
    if header[:4] != b"II*\x00":
        raise TiffGateError("expected classic little-endian TIFF, not BigTIFF/other")
    if struct.unpack_from("<I", header, 4)[0] != IFD_RANGE[0]:
        raise TiffGateError("changed TIFF first-IFD offset; re-acquire bounded ranges")
    count = struct.unpack_from("<H", ifd, 0)[0]
    if count != 18:
        raise TiffGateError("unexpected TIFF IFD entry count")
    tags = {}
    for n in range(count):
        tag, typ, num, value = struct.unpack_from("<HHII", ifd, 2 + 12 * n)
        if tag in tags:
            raise TiffGateError("duplicate TIFF IFD tag")
        tags[tag] = (typ, num, value)

    required_inline = {
        256: (3, 1, 43200), 257: (3, 1, 21600),
        258: (3, 1, 32), 259: (3, 1, 5),
        277: (3, 1, 1), 278: (3, 1, 1),
        339: (3, 1, 3),
    }
    if any(tags.get(k) != v for k, v in required_inline.items()):
        raise TiffGateError("original size, Float32 sample, LZW compression or strip count contract drift")
    required_external = {
        33550: (12, 3, 44993248),
        33922: (12, 6, 44993272),
        34735: (3, 32, 44993320),
        42113: (2, 6, 44993242),
    }
    if any(tags.get(k) != v for k, v in required_external.items()):
        raise TiffGateError("original georeference/NoData tag type or pointer drift")
    px_scale = struct.unpack("<3d", _read_original_value(geo, 44993248, 24))
    tiepoint = struct.unpack("<6d", _read_original_value(geo, 44993272, 48))
    geo_keys = struct.unpack("<32H", _read_original_value(geo, 44993320, 64))
    nodata = _read_original_value(geo, 44993242, 6)
    if any(abs(v - expected) > 1e-12
           for v, expected in zip(px_scale, (1 / 120, 1 / 120, 0))):
        raise TiffGateError("source GeoTIFF pixel size differs from nominal 30 arcsecond grid")
    if any(abs(v - expected) > 1e-12
           for v, expected in zip(tiepoint, (0, 0, 0, -180, 90, 0))):
        raise TiffGateError("source GeoTIFF tiepoint differs from Physrisk metadata")
    if (geo_keys[:4] != (1, 1, 0, 7)
            or (2048, 0, 1, 4326) not in [tuple(geo_keys[i:i+4])
                                           for i in range(4, len(geo_keys), 4)]):
        raise TiffGateError("source GeoTIFF WGS84/EPSG:4326 tag not present")
    if nodata != b"-9999\x00":
        raise TiffGateError("source nodata unexpected; cannot infer source/derived missing values")
    return {
        "profile": PROFILE, "original_provider_tiff": SOURCE_URL,
        "original_response_byte_ranges": [list(HEADER_RANGE), list(IFD_RANGE), list(GEO_RANGE)],
        "original_range_sha256s": [header_sha, ifd_sha, geo_sha],
        "tiff_width": 43200, "tiff_height": 21600,
        "sample_format": "Float32", "compression": "LZW",
        "geo_crs": "EPSG:4326", "pixel_scale_degrees": [1 / 120, -1 / 120],
        "upper_left_tiepoint_longitude_latitude": [-180, 90],
        "original_nodata": -9999,
        "physrisk_zarr_fill_value_separately_observed": 0.0,
        "nodata_to_zarr_fill_transformation_verified": False,
        "pixel_values_read": False,
        "source_geotiff_cellwise_reconciled": False,
        "annual_occurrence_catalogue_provided": False,
        "rights_and_scientific_review_complete": False,
        "model_input_admitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tiff_header", type=Path)
    parser.add_argument("tiff_ifd", type=Path)
    parser.add_argument("tiff_geo", type=Path)
    parser.add_argument("--expected-header-sha256", required=True)
    parser.add_argument("--expected-ifd-sha256", required=True)
    parser.add_argument("--expected-geo-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    paths = [p.resolve() for p in (args.tiff_header, args.tiff_ifd, args.tiff_geo)]
    if len(set(paths)) != 3 or args.out.resolve() in paths:
        parser.error("each provider response must be independent; never overwrite original bytes")
    try:
        result = inspect_original_tiff_ranges(
            *(p.read_bytes() for p in (args.tiff_header, args.tiff_ifd, args.tiff_geo)),
            args.expected_header_sha256, args.expected_ifd_sha256, args.expected_geo_sha256,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, TiffGateError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
