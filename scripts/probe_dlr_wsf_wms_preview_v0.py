#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Three exact, anonymous DLR WSF WMS visual-preview probes.

Never accept caller URLs, coordinates, layer names, output dimensions, or times.
The service returns *rendered PNG*, not native GeoTIFF class values. This probes
the 32x32 public WMS contract only: no provider pixels committed to Git, no
commercial CAT-model input, no insurance exposure/individual address.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, parse_qsl
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import zlib

SERVICE = "https://geoservice.dlr.de/eoc/land/wms"
BBOX = "11.52,48.10,11.60,48.18"  # one fixed bounded location, WMS 1.1.1 lon/lat
SIZE = 32
MAX_RESPONSE = 16_384
MAX_DECODED = 65_536
LAYER_BY_SOURCE = {
    "dlr.wsf.2019": "WSF_2019",
    "dlr.eoc.wsf-tracker.2016-2026": "WSF_TRACKER",
    "dlr.wsf.evolution.1985-2015": "WSF_Evolution",
}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class WSFPreviewBlocked(ValueError):
    """Contract, HTTP response, or small PNG evidence was rejected."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise WSFPreviewBlocked("redirect is not allowed for frozen WMS source")


def frozen_url(source: str) -> str:
    if source not in LAYER_BY_SOURCE:
        raise WSFPreviewBlocked("source is not approved for this exact GetMap operation")
    params = [
        ("SERVICE", "WMS"),
        ("VERSION", "1.1.1"),
        ("REQUEST", "GetMap"),
        ("LAYERS", LAYER_BY_SOURCE[source]),
        ("STYLES", ""),
        ("SRS", "EPSG:4326"),
        ("BBOX", BBOX),
        ("WIDTH", str(SIZE)),
        ("HEIGHT", str(SIZE)),
        ("FORMAT", "image/png"),
        ("TRANSPARENT", "TRUE"),
    ]
    url = SERVICE + "?" + urlencode(params)
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "geoservice.dlr.de"
            or parsed.path != "/eoc/land/wms" or parsed.fragment
            or parse_qsl(parsed.query, keep_blank_values=True) != params):
        raise WSFPreviewBlocked("unexpected WMS host, path or parameters")
    return url


def inspect_png(data: bytes, media_type: str) -> dict:
    """Require one complete, CRC-valid 32x32 PNG with bounded inflated bytes."""
    if not isinstance(data, bytes) or not 65 <= len(data) <= MAX_RESPONSE:
        raise WSFPreviewBlocked("image outside bounded 32x32 response size")
    if media_type.split(";", 1)[0].strip().lower() != "image/png":
        raise WSFPreviewBlocked("WMS did not return image/png")
    if not data.startswith(PNG_SIGNATURE):
        raise WSFPreviewBlocked("not a PNG response")
    offset, ihdr_seen, iend_seen = 8, False, False
    image_parts = []
    while offset < len(data):
        if offset + 12 > len(data):
            raise WSFPreviewBlocked("truncated PNG chunk header")
        size = struct.unpack_from(">I", data, offset)[0]
        tag = data[offset + 4:offset + 8]
        stop = offset + 12 + size
        if size > MAX_RESPONSE or stop > len(data):
            raise WSFPreviewBlocked("invalid PNG chunk size")
        payload = data[offset + 8:offset + 8 + size]
        expected_crc = struct.unpack_from(">I", data, offset + 8 + size)[0]
        actual_crc = zlib.crc32(tag + payload) & 0xffffffff
        if actual_crc != expected_crc:
            raise WSFPreviewBlocked("invalid PNG CRC")
        if not ihdr_seen:
            if tag != b"IHDR" or size != 13:
                raise WSFPreviewBlocked("PNG IHDR not first")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if (width, height) != (SIZE, SIZE) or depth not in (1, 2, 4, 8)
                    or color not in (0, 2, 3, 4, 6) or (compression, filtering, interlace) != (0, 0, 0):
                raise WSFPreviewBlocked("wrong PNG dimension, format or interlacing")
            ihdr_seen = True
        elif tag == b"IDAT":
            image_parts.append(payload)
        elif tag == b"IEND":
            if size != 0 or stop != len(data):
                raise WSFPreviewBlocked("invalid PNG IEND or trailing bytes")
            iend_seen = True
            break
        offset = stop
    if not ihdr_seen or not iend_seen or not image_parts:
        raise WSFPreviewBlocked("incomplete or empty PNG")
    decoder = zlib.decompressobj()
    decoded = decoder.decompress(b"".join(image_parts), MAX_DECODED + 1)
    if len(decoded) > MAX_DECODED or decoder.unconsumed_tail or not decoder.eof:
        raise WSFPreviewBlocked("unbounded or incomplete PNG compressed pixels")
    return {
        "width": SIZE,
        "height": SIZE,
        "format": "image/png",
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "rendered_preview_only": True,
        "native_raster_values_verified": False,
        "model_input_approved": False,
    }


def run_probe(source: str) -> dict:
    url = frozen_url(source)
    opener = build_opener(ProxyHandler({}), NoRedirect())
    request = Request(
        url,
        headers={"Accept": "image/png", "User-Agent": "OpenCatastrophe-WSF-Probe/0.1"},
        method="GET",
    )
    try:
        with opener.open(request, timeout=25) as response:
            if response.status != 200 or response.geturl() != url:
                raise WSFPreviewBlocked("unexpected HTTP status or redirect")
            media = response.headers.get("Content-Type", "")
            raw = response.read(MAX_RESPONSE + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise WSFPreviewBlocked("official DLR WMS access failed") from exc
    result = inspect_png(raw, media)
    return {
        "source_id": source,
        "operation": "frozen_32px_wms_1_1_1_preview",
        "layer": LAYER_BY_SOURCE[source],
        "bbox_lonlat": [11.52, 48.10, 11.60, 48.18],
        "srs": "EPSG:4326",
        "request_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
        "response_sha256": result["sha256"],
        "response_bytes": result["bytes"],
        "width": result["width"],
        "height": result["height"],
        "rendered_preview_only": result["rendered_preview_only"],
        "native_raster_values_verified": result["native_raster_values_verified"],
        "provider_bytes_persisted": False,
        "model_input_approved": False,
        "license": "CC BY 4.0",
        "license_evidence": "https://geoservice.dlr.de/web/datasets/",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, choices=sorted(LAYER_BY_SOURCE))
    args = parser.parse_args()
    try:
        print(json.dumps(run_probe(args.source), sort_keys=True))
        return 0
    except WSFPreviewBlocked as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
