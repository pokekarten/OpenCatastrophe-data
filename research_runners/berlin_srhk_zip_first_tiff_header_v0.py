#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded original Berlin ZIP prefix -> TIFF HEADER research, not flood pixels.

The actual Berlin water-depth ZIP HEAD, first-512 SHA and single-TIFF member
were already independently verified. Fetch only bytes 0..65535, then use a
strict decompressed byte cap to inspect TIFF magic and optional first-IFD
GeoKeyDirectory. No full ZIP, no TIFF tile values, no risk/loss admission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import ssl
import struct
import sys
from typing import Callable
from urllib import error, request
import zlib

from research_runners.berlin_srhk_depth_zip_eocd_tail_v0 import (
    OBJECTS, ROOT, LAST_MODIFIED, MIME,
)

from research_runners.berlin_srhk_tiff_grid_affine_v0 import (
    BerlinTiffGridError, inspect_berlin_tiff_header_grid,
)

READ_BYTES = 65_536
MAX_DECOMPRESSED_PREFIX = 1_048_576
TIMEOUT = 40
PROFILE = "berlin-srhk-original-zip-bounded-tiff-first-ifd-v0"
FIRST_512_SHA = {
    "extreme": "49c954a118d834e33dac1902c4df3f7df47e9022c963bd966451f9a20b3ee30f",
    "extraordinary": "0486e017feaf9a74b56a351f53e238ed72d45cfe23cdeeda4464fc8f774cd9c8",
}
FIRST_MEMBER_NAME_LENGTH = {"extreme": 38, "extraordinary": 39}


class TiffHeaderError(ValueError):
    """Source changed or unsafe source TIFF-header profile."""


def decode_tiff_metadata(prefix: bytes) -> dict:
    if type(prefix) is not bytes or len(prefix) < 8:
        raise TiffHeaderError("TIFF prefix lacks header")
    if prefix[:2] == b"II":
        order, byteorder = "<", "little"
    elif prefix[:2] == b"MM":
        order, byteorder = ">", "big"
    else:
        raise TiffHeaderError("original decompressed member is not TIFF byte order")
    magic = struct.unpack_from(order + "H", prefix, 2)[0]
    if magic == 42:  # classic TIFF
        ifd = struct.unpack_from(order + "I", prefix, 4)[0]
        variant = "classic_tiff"
    elif magic == 43:  # BigTIFF
        if len(prefix) < 16:
            raise TiffHeaderError("incomplete BigTIFF first header")
        bytesize, reserved = struct.unpack_from(order + "HH", prefix, 4)
        if bytesize != 8 or reserved != 0:
            raise TiffHeaderError("invalid BigTIFF pointer format")
        ifd = struct.unpack_from(order + "Q", prefix, 8)[0]
        variant = "bigtiff"
    else:
        raise TiffHeaderError("unsupported original TIFF magic")
    if ifd < (16 if magic == 43 else 8):
        raise TiffHeaderError("invalid original TIFF first IFD offset")
    result = {
        "original_member_tiff_header_confirmed": True,
        "tiff_variant": variant,
        "tiff_byte_order": byteorder,
        "tiff_first_ifd_offset_bytes": ifd,
        "tiff_first_ifd_fully_available_in_prefix": False,
        "geokey_directory_tag_available_in_prefix": False,
        "geokey_directory_values_available_in_prefix": False,
        "projected_epsg_from_first_geokey": None,
        "geographic_epsg_from_first_geokey": None,
        "tiff_pixel_data_interpreted": False,
    }
    if variant == "bigtiff" or ifd + 2 > len(prefix):
        return result
    count = struct.unpack_from(order + "H", prefix, ifd)[0]
    if count > 512:
        raise TiffHeaderError("unbounded first TIFF IFD entry count")
    end = ifd + 2 + 12 * count + 4
    if end > len(prefix):
        return result
    result["tiff_first_ifd_fully_available_in_prefix"] = True
    geotags = []
    for i in range(count):
        entry = ifd + 2 + 12*i
        tag, data_type, length, val_or_offset = struct.unpack_from(
            order + "HHII", prefix, entry
        )
        if tag == 34735:
            geotags.append((entry, data_type, length, val_or_offset))
    if len(geotags) > 1:
        raise TiffHeaderError("duplicated GeoKeyDirectory first IFD tag")
    if not geotags:
        return result
    result["geokey_directory_tag_available_in_prefix"] = True
    entry, dtype, length, ptr = geotags[0]
    if dtype != 3 or not 4 <= length <= 2048 or length % 4:
        raise TiffHeaderError("unsafe GeoTIFF GeoKeyDirectory type/count")
    payload_len = 2*length
    if payload_len <= 4:
        data = prefix[entry+8:entry+8+payload_len]
    else:
        if ptr + payload_len > len(prefix):
            return result
        data = prefix[ptr:ptr+payload_len]
    shorts = struct.unpack(order + str(length) + "H", data)
    version, revision, minor, nkeys = shorts[:4]
    if (version != 1 or revision > 10 or minor > 10
            or nkeys > 500 or 4+nkeys*4 != length):
        raise TiffHeaderError("unreviewed original GeoTIFF GeoKeyDirectory structure")
    codes = {}
    for i in range(nkeys):
        key, tiff_tag_location, key_count, value = shorts[4+i*4:8+i*4]
        if key in (3072, 2048):
            if key in codes or tiff_tag_location != 0 or key_count != 1 or value <= 0:
                raise TiffHeaderError("ambiguous original projected/geographic GeoKey")
            codes[key] = value
    result["geokey_directory_values_available_in_prefix"] = True
    result["projected_epsg_from_first_geokey"] = codes.get(3072)
    result["geographic_epsg_from_first_geokey"] = codes.get(2048)
    return result


def inspect_prefix(raw: bytes, *, scenario: str, expected_512_sha: str) -> dict:
    if scenario not in OBJECTS or type(raw) is not bytes or len(raw) != READ_BYTES:
        raise TiffHeaderError("wrong source scenario or bounded original byte count")
    if sha256(raw[:512]).hexdigest() != expected_512_sha:
        raise TiffHeaderError("first source ZIP bytes differ from original pinned 512-byte receipt")
    if raw[:4] != b"PK\x03\x04":
        raise TiffHeaderError("source ZIP local file magic changed")
    (_, version, flags, method, _, _, _, _, _, name_len, extra_len) = (
        struct.unpack_from("<IHHHHHIIIHH", raw)
    )
    if (version != 20 or flags & 1 or method != 8
            or name_len != FIRST_MEMBER_NAME_LENGTH[scenario] or extra_len != 0):
        raise TiffHeaderError("original ZIP member compression or header contract changed")
    start = 30 + name_len + extra_len
    try:
        decompressor = zlib.decompressobj(wbits=-15)
        decoded = decompressor.decompress(raw[start:], MAX_DECOMPRESSED_PREFIX)
    except zlib.error as exc:
        raise TiffHeaderError("original ZIP Deflate prefix cannot be decoded safely") from exc
    if len(decoded) < 16:
        raise TiffHeaderError("source TIFF prefix too short after bounded Deflate")
    metadata = decode_tiff_metadata(decoded)
    try:
        projected_grid = inspect_berlin_tiff_header_grid(decoded)
    except BerlinTiffGridError as exc:
        raise TiffHeaderError("unsafe original GeoTIFF affine-grid metadata") from exc
    return {
        "exact_source_scenario": scenario,
        "original_zip_prefix_http_bytes": READ_BYTES,
        "original_zip_prefix_sha256_only": sha256(raw).hexdigest(),
        "prior_exact_512_byte_sha256_same": True,
        "first_zip_member_deflate_method_verified": True,
        "decompressed_original_tiff_prefix_bytes": len(decoded),
        "bounded_decompression_limit_bytes": MAX_DECOMPRESSED_PREFIX,
        "decompression_output_cap_reached": len(decoded) >= MAX_DECOMPRESSED_PREFIX,
        "original_tiff_prefix_or_zip_bytes_persisted": False,
        "not_full_original_tiff_or_zip_sha256": True,
        "geotiff_full_crs_and_affine_grid_validated": False,
        "original_depth_units_or_nodata_validated": False,
        "hazard_raster_pixels_or_buildings_sampled": False,
        "original_scenario_not_historical_insurance_event": True,
        "source_rights_and_cat_model_admission_pending": True,
        **metadata,
        **projected_grid,
    }


def validate_response(headers, *, scenario: str):
    total = OBJECTS[scenario][1]
    if headers.get("Content-Range", "").strip() != f"bytes 0-{READ_BYTES-1}/{total}":
        raise TiffHeaderError("provider range changed from original HEAD source")
    if headers.get("Content-Length", "").strip() != str(READ_BYTES):
        raise TiffHeaderError("provider did not supply exact bounded byte count")
    media = headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if media not in MIME or headers.get("Content-Encoding", "identity").strip().lower() != "identity":
        raise TiffHeaderError("provider ZIP media/encoding changed")
    lm = headers.get("Last-Modified")
    if lm is not None and lm.strip() != LAST_MODIFIED[scenario]:
        raise TiffHeaderError("source changed since independent HEAD receipt")
    return {"last_modified_same_as_original_head_when_sent": lm is not None}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TiffHeaderError("fixed official ZIP prefix GET redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context())
    ).open(req, timeout=timeout)


def probe(scenario: str, *, opener: Callable = _fetch,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    if scenario not in OBJECTS:
        raise TiffHeaderError("unknown immutable original Berlin ZIP source")
    url = ROOT + OBJECTS[scenario][0]
    req = request.Request(
        url, method="GET",
        headers={"Range": f"bytes=0-{READ_BYTES-1}",
                 "If-Range": LAST_MODIFIED[scenario],
                 "Accept": "application/zip",
                 "Accept-Encoding": "identity"}
    )
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 206 or resp.geturl() != url:
                raise TiffHeaderError("provider refused fixed 65536-byte original range")
            checked = validate_response(resp.headers, scenario=scenario)
            raw = resp.read(READ_BYTES + 1)
            fields = inspect_prefix(
                raw, scenario=scenario,
                expected_512_sha=FIRST_512_SHA[scenario]
            )
    except TiffHeaderError:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise TiffHeaderError("original source TIFF-prefix read unavailable") from exc
    now = clock()
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise TiffHeaderError("source UTC clock invalid")
    return {
        "profile": PROFILE,
        "fixed_original_url": url,
        "retrieved_utc": now.astimezone(timezone.utc).isoformat(),
        "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_get_status_206_verified": True,
        **checked,
        **fields,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario", required=True, choices=sorted(OBJECTS))
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required; synthetic tests are default")
    try:
        print(json.dumps(probe(args.scenario), sort_keys=True, allow_nan=False))
    except (TiffHeaderError, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
