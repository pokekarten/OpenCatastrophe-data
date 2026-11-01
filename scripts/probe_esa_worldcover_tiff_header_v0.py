#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fixed 4096-byte HTTP Range sample of a reviewed ESA WorldCover TIFF header.

T3 *partial-object* evidence only. Never fetch a full raster, alternate
object, arbitrary URL or a second byte range. Original bytes are transient,
never written to disk, printed or admitted as CAT model input.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import ssl
import struct
import sys
from urllib import error, request

from scripts.validate_source_access import validate_path
from scripts.probe_esa_worldcover_tile_head_v0 import (
    CONTRACT_PATH, EXPECTED_MEDIA, OBJECT_PATH, SERVICE_ROOT, SOURCE, URL,
    NoRedirect,
)

OPERATION = "sample_exact_v200_tile_header_4096"
BYTES = 4096
EXPECTED_TOTAL = 94_851_935  # Recorded from the same fixed object's reviewed HEAD.
CONTENT_RANGE = f"bytes 0-{BYTES - 1}/{EXPECTED_TOTAL}"
MAX_IFD_ENTRIES = 256


class HeaderBlocked(ValueError):
    """One narrowly approved original-byte acquisition is not valid."""


def reviewed_contract(path: Path = CONTRACT_PATH) -> tuple[int, str]:
    contract = validate_path(path)
    if (
        contract["access_id"] != SOURCE
        or contract["source_ids"] != [SOURCE]
        or contract["status"] != "probe_ready"
        or contract["interface_type"] != "object_store"
        or contract["service_root"] != SERVICE_ROOT
        or contract["authentication"]["mode"] != "none"
        or contract["probe_contract"]["operation"] != "probe_exact_v200_tile_head"
        or contract["probe_contract"]["mode"] != "head"
        or contract["request_contract"]["allowed_operations"].count(OPERATION) != 1
        or OBJECT_PATH not in contract["request_contract"]["path_templates"]
        or contract["rights_and_policy"]["dataset_rights_status"] != "verified"
        or contract["rights_and_policy"]["api_terms_status"] != "separate_reviewed"
        or contract["rights_and_policy"]["commercial_automation_status"] != "allowed"
        or not set(EXPECTED_MEDIA).issubset(set(contract["response_contract"]["expected_media_types"]))
        or URL != SERVICE_ROOT + OBJECT_PATH
    ):
        raise HeaderBlocked("reviewed exact WorldCover partial-object contract drift")
    timeout = contract["operational_constraints"]["timeout_seconds"]
    max_bytes = contract["operational_constraints"]["max_probe_bytes"]
    if type(timeout) is not int or timeout <= 0 or timeout > 60:
        raise HeaderBlocked("unsafe timeout in source contract")
    if type(max_bytes) is not int or max_bytes < BYTES or max_bytes > 65536:
        raise HeaderBlocked("reviewed probe size does not permit fixed sample")
    return timeout, hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_tiff_header(raw: bytes) -> dict:
    """Decode only file header and a bounded first-IFD prefix, never pixel data."""
    if type(raw) is not bytes or len(raw) != BYTES:
        raise HeaderBlocked("TIFF sample must be exactly 4096 source bytes")
    if raw[:4] not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
        raise HeaderBlocked("provider original bytes do not start with TIFF/BigTIFF magic")
    endian = "<" if raw[:2] == b"II" else ">"
    big = raw[2:4] in (b"+\x00", b"\x00+")
    if big:
        offset_size, reserved = struct.unpack_from(endian + "HH", raw, 4)
        if offset_size != 8 or reserved != 0:
            raise HeaderBlocked("nonstandard BigTIFF header sizes")
        first_offset = struct.unpack_from(endian + "Q", raw, 8)[0]
        minimum_ifd = 16
        entry_size, count_size = 20, 8
        ifd_type = "BigTIFF"
    else:
        first_offset = struct.unpack_from(endian + "I", raw, 4)[0]
        minimum_ifd = 8
        entry_size, count_size = 12, 2
        ifd_type = "TIFF"
    if first_offset < minimum_ifd:
        raise HeaderBlocked("invalid TIFF first IFD offset")
    # A valid first IFD might lie beyond this tiny range: never infer a
    # missing full-object directory or fabricate CRS/pixel/class metadata.
    in_range = first_offset + count_size <= BYTES
    count = None
    if in_range:
        fmt = endian + ("Q" if big else "H")
        count = struct.unpack_from(fmt, raw, first_offset)[0]
        if count > MAX_IFD_ENTRIES:
            raise HeaderBlocked("implausible TIFF IFD entry count in sampled prefix")
        in_range = first_offset + count_size + count * entry_size <= BYTES
    # Parse only inline scalar metadata in the complete first IFD. Tag values
    # held at offsets elsewhere in the TIFF are deliberately NOT dereferenced:
    # their payload may not be present in the reviewed 4 KiB source sample.
    scalar_tags = {256: "image_width", 257: "image_length",
                   259: "compression", 277: "samples_per_pixel",
                   322: "tile_width", 323: "tile_length"}
    geo_tag_ids = {33550, 33922, 34264, 34735, 34736, 34737}
    observed: dict[int, int] = {}
    geo_tags: list[int] = []
    if in_range:
        seen: set[int] = set()
        for index in range(count):
            off = first_offset + count_size + index * entry_size
            tag, dtype = struct.unpack_from(endian + "HH", raw, off)
            if tag in seen:
                raise HeaderBlocked("duplicate TIFF first-directory tag")
            seen.add(tag)
            if tag in geo_tag_ids:
                geo_tags.append(tag)
            if tag not in scalar_tags:
                continue
            # TIFF type SHORT = 3 (2 bytes), LONG = 4 (4 bytes),
            # BigTIFF LONG8 = 16 (8 bytes); require exactly one inline item.
            n = struct.unpack_from(endian + ("Q" if big else "I"), raw, off + 4)[0]
            if n != 1:
                continue
            start = off + (12 if big else 8)
            spec = {3: ("H", 2), 4: ("I", 4)}
            if big:
                spec[16] = ("Q", 8)
            if dtype not in spec:
                continue
            fmt, width = spec[dtype]
            if width > (8 if big else 4):
                continue
            value = struct.unpack_from(endian + fmt, raw, start)[0]
            if value == 0 or value > 1_000_000:
                raise HeaderBlocked("implausible TIFF inline scalar metadata")
            observed[tag] = value
    return {
        "tiff_flavour": ifd_type,
        "byte_order": "little" if endian == "<" else "big",
        "first_ifd_offset": first_offset,
        "first_ifd_count_if_visible": count if in_range else None,
        "first_ifd_fully_within_sample": bool(in_range),
        "image_width_if_inline": observed.get(256),
        "image_length_if_inline": observed.get(257),
        "compression_code_if_inline": observed.get(259),
        "samples_per_pixel_if_inline": observed.get(277),
        "tile_width_if_inline": observed.get(322),
        "tile_length_if_inline": observed.get(323),
        "geotiff_ifd_tag_ids_present": sorted(geo_tags),
        "raster_dimensions_proven_by_header_only": 256 in observed and 257 in observed,
    }


def _open(req: request.Request, timeout: int):
    client = request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    )
    return client.open(req, timeout=timeout)


def probe(*, open_request=_open, contract_path: Path = CONTRACT_PATH) -> dict:
    timeout, contract_hash = reviewed_contract(contract_path)
    req = request.Request(
        URL, method="GET",
        headers={
            "Range": f"bytes=0-{BYTES - 1}",
            "Accept": "image/tiff,application/octet-stream,binary/octet-stream",
            "Accept-Encoding": "identity",
            "User-Agent": "OpenCatastrophe-WorldCover-Header-Sample/0.1",
        },
    )
    try:
        with open_request(req, timeout) as resp:
            if resp.geturl() != URL or resp.status != 206:
                raise HeaderBlocked("HTTP 206 from the reviewed exact object is mandatory")
            media = resp.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media not in EXPECTED_MEDIA:
                raise HeaderBlocked("unreviewed TIFF sample transport media type")
            if resp.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise HeaderBlocked("compressed HTTP response cannot be an exact raw range")
            if resp.headers.get("Content-Range", "") != CONTENT_RANGE:
                raise HeaderBlocked("Content-Range identity or original object size drift")
            if resp.headers.get("Content-Length", "") != str(BYTES):
                raise HeaderBlocked("bounded sample Content-Length mismatch")
            raw = resp.read(BYTES + 1)
    except HeaderBlocked:
        raise
    except (error.HTTPError, error.URLError, OSError, TimeoutError) as exc:
        raise HeaderBlocked("reviewed WorldCover 4096-byte Range request unavailable") from exc
    shape = inspect_tiff_header(raw)
    return {
        "profile": "oc-esa-worldcover-v200-tiff-header-v0",
        "source_id": SOURCE,
        "tile_id": "N48E009",
        "operation": OPERATION,
        "retrieval_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": 206,
        "response_media_type": media,
        "original_total_bytes_from_content_range": EXPECTED_TOTAL,
        "sample_range": "bytes=0-4095",
        "sample_bytes": len(raw),
        "sample_sha256": hashlib.sha256(raw).hexdigest(),
        "request_sha256": hashlib.sha256(
            ("GET " + URL + " Range:bytes=0-4095").encode("ascii")
        ).hexdigest(),
        "access_contract_sha256": contract_hash,
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        **shape,
        "full_original_sha256_verified": False,
        "cog_layout_verified": False,
        "crs_verified": False,
        "raster_values_inspected": False,
        "external_bytes_persisted": False,
        "model_input_approved": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args(argv)
    if not args.live:
        ap.error("network is disabled by default; explicitly specify --live")
    try:
        print(json.dumps(probe(), sort_keys=True, allow_nan=False))
    except (HeaderBlocked, ValueError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
