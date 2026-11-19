#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Exact 512-byte original HTTP Range ZIP-prefix canary, not ZIP acquisition.

Original official Berlin SRHK water-depth ZIP HEADs were verified on
2026-11-01. Size, ZIP prefix bytes and local-header metadata only.
No archive directory, tile contents, GeoTIFF, geographic raster, loss or CAT
input is acquired or admitted. No provider bytes are persisted.
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
from urllib import request, error

ROOT = "https://gdi.berlin.de/data/ua_srhk/atom/"
OBJECTS = {
    "extreme": ("wasserstand_extrem2022.zip", 619_211_977),
    "extraordinary": ("wasserstand_aussergewoehnliches_ereignis2022.zip", 563_115_763),
}
PROFILE = "berlin-srhk-bounded-512-byte-zip-local-header-v0"
RANGE = "bytes=0-511"
BYTE_COUNT = 512
TIMEOUT = 40
ZIP_LOCAL_HEADER = b"PK\x03\x04"
MEDIA = {"application/zip", "application/x-zip-compressed",
         "application/octet-stream", "binary/octet-stream"}


class PrefixError(ValueError):
    """Partial source object, ZIP prefix or HTTP range is not independently verified."""


def inspect(raw: bytes, headers, *, scenario: str) -> dict:
    if scenario not in OBJECTS:
        raise PrefixError("unknown fixed official Berlin depth scenario")
    if type(raw) is not bytes or len(raw) != BYTE_COUNT:
        raise PrefixError("ZIP prefix must be exactly 512 original bytes")
    filename, full_size = OBJECTS[scenario]
    content_range = headers.get("Content-Range", "").strip()
    if content_range != f"bytes 0-511/{full_size}":
        raise PrefixError("ZIP range reply differs from original HEAD source length")
    declared_length = headers.get("Content-Length", "")
    if declared_length != str(BYTE_COUNT):
        raise PrefixError("ZIP range response has unexpected Content-Length")
    mime = headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if mime not in MEDIA:
        raise PrefixError("ZIP response has unsupported MIME")
    if headers.get("Content-Encoding", "identity").strip().lower() != "identity":
        raise PrefixError("ZIP response was encoded over the wire")
    if raw[:4] != ZIP_LOCAL_HEADER:
        raise PrefixError("ZIP original local-file header signature missing")
    if len(raw) < 30:
        raise PrefixError("incomplete ZIP local header")
    # ZIP local file header: sig, version, flags, method, time, date,
    # CRC-32, comp size, uncomp size, filename length, extra length.
    (_, version, flags, method, _, _, _, _, _, name_len, extra_len) = (
        struct.unpack_from("<IHHHHHIIIHH", raw, 0)
    )
    if version > 99 or flags & 1:
        raise PrefixError("unsupported ZIP version or encrypted first file")
    if name_len == 0 or name_len > BYTE_COUNT - 30 or extra_len > 65_535:
        raise PrefixError("unbounded/incomplete first ZIP member filename")
    if b"\x00" in raw[30:30 + name_len]:
        raise PrefixError("invalid first ZIP member filename bytes")
    return {
        "source_scenario": scenario,
        "exact_official_zip_filename": filename,
        "original_head_declared_object_bytes": full_size,
        "http_partial_content_range_confirmed": True,
        "zip_first_file_local_signature_confirmed": True,
        "zip_first_file_header_version_needed": version,
        "zip_first_file_compression_method_code": method,
        "zip_first_file_name_length_bytes": name_len,
        "zip_first_file_extra_length_bytes": extra_len,
        "first_zip_filename_or_tile_id_exported": False,
        "original_sample_bytes": BYTE_COUNT,
        "original_sample_sha256_only": sha256(raw).hexdigest(),
        "not_full_archive_sha256": True,
        "zip_central_directory_or_entry_count_verified": False,
        "zip_decompression_or_tiff_bytes_performed": False,
        "true_source_crs_and_depth_values_verified": False,
        "source_scenario_not_observed_cat_event": True,
        "source_rights_and_model_admission_pending": True,
        "building_or_insurer_database_modified": False,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PrefixError("fixed official source ZIP Range request redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(scenario: str, *, opener: Callable = _fetch,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    if scenario not in OBJECTS:
        raise PrefixError("unknown fixed official Berlin depth scenario")
    url = ROOT + OBJECTS[scenario][0]
    req = request.Request(
        url, method="GET",
        headers={"Range": RANGE, "Accept": "application/zip",
                 "Accept-Encoding": "identity"}
    )
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 206 or resp.geturl() != url:
                raise PrefixError("original ZIP server did not honor exact fixed range")
            raw = resp.read(BYTE_COUNT + 1)
            data = inspect(raw, resp.headers, scenario=scenario)
    except PrefixError:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise PrefixError("bounded original ZIP prefix GET failed") from exc
    when = clock()
    if not isinstance(when, datetime) or when.tzinfo is None or when.utcoffset() is None:
        raise PrefixError("UTC source receipt clock invalid")
    return {
        "profile": PROFILE,
        "fixed_original_url": url,
        "requested_http_range": RANGE,
        "retrieved_utc": when.astimezone(timezone.utc).isoformat(),
        "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "original_provider_prefix_bytes_persisted": False,
        **data,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario", choices=sorted(OBJECTS), required=True)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required for the exact 512-byte GET")
    try:
        print(json.dumps(probe(args.scenario), sort_keys=True, allow_nan=False))
    except (PrefixError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
