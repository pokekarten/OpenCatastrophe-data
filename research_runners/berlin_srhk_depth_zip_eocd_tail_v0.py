#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read an exact 65,557-byte suffix of official Berlin depth ZIPs, NOT ZIPs.

One fixed no-redirect original HTTP 206 request per chosen scenario.
The returned original ZIP EOCD/central-directory metadata is research only.
Do not export original filenames, bytes, coordinates or insured risk.
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

from research_runners.berlin_srhk_depth_zip_prefix_v0 import OBJECTS, ROOT

TAIL_BYTES = 65_557
MAX_DIRECTORY_BYTES = 1_048_576
MAX_MEMBERS = 10_000
TIMEOUT = 40
PROFILE = "berlin-srhk-two-water-depth-original-zip-eocd-tail-v0"
LAST_MODIFIED = {
    "extreme": "Wed, 12 Feb 2025 06:54:20 GMT",
    "extraordinary": "Wed, 12 Feb 2025 06:55:33 GMT",
}
MIME = {"application/zip", "application/octet-stream",
        "application/x-zip-compressed", "binary/octet-stream"}


class EocdSourceError(ValueError):
    """Changed source, unsafe ZIP directory, or unsupported archive feature."""


def inspect_tail(raw: bytes, *, scenario: str) -> dict:
    if scenario not in OBJECTS or type(raw) is not bytes or len(raw) != TAIL_BYTES:
        raise EocdSourceError("wrong scenario or original tail length")
    filename, file_bytes = OBJECTS[scenario]
    absolute_tail_start = file_bytes - TAIL_BYTES
    # The signature may also appear in a ZIP comment. It must end at EOF
    # with the exact 16-bit comment-length field to be an EOCD candidate.
    candidates = []
    start = 0
    while True:
        at = raw.find(b"PK\x05\x06", start)
        if at < 0:
            break
        if at + 22 <= len(raw):
            comment_len = struct.unpack_from("<H", raw, at + 20)[0]
            if at + 22 + comment_len == len(raw):
                candidates.append(at)
        start = at + 1
    if len(candidates) != 1:
        raise EocdSourceError("missing, ambiguous or invalid end-of-central-directory")
    at = candidates[0]
    (sig, disk, cd_disk, on_disk, entries, size, offset, comment_len) = (
        struct.unpack_from("<IHHHHIIH", raw, at)
    )
    if (sig != 0x06054B50 or disk != 0 or cd_disk != 0 or on_disk != entries
            or not 1 <= entries <= MAX_MEMBERS):
        raise EocdSourceError("multi-disk, empty or unsupported ZIP member count")
    if (entries == 0xFFFF or size == 0xFFFFFFFF or offset == 0xFFFFFFFF):
        raise EocdSourceError("ZIP64 directory requires separate scientific review")
    absolute_eocd = absolute_tail_start + at
    if (not 1 <= size <= MAX_DIRECTORY_BYTES or offset < 30
            or offset + size != absolute_eocd):
        raise EocdSourceError("directory size/offset does not lead exactly to EOCD")
    in_tail = offset >= absolute_tail_start
    report = {
        "source_scenario": scenario,
        "exact_official_zip_filename": filename,
        "whole_zip_size_from_independent_head": file_bytes,
        "original_tail_bytes_received": TAIL_BYTES,
        "original_tail_sha256_only": sha256(raw).hexdigest(),
        "eocd_signature_and_source_offset_verified": True,
        "archive_requires_zip64_for_directory": False,
        "single_disk_zip_classic_eocd": True,
        "zip_member_count_declared": entries,
        "central_directory_offset_bytes": offset,
        "central_directory_size_bytes": size,
        "zip_archive_comment_bytes": comment_len,
        "central_directory_fully_present_within_original_tail": in_tail,
        "individual_member_names_emitted": False,
        "full_zip_sha256_or_archive_integrity_proven": False,
        "full_zip_bytes_or_geotiff_pixels_downloaded": False,
        "true_tiff_crs_units_or_nodata_verified": False,
        "model_input_or_insurer_loss_admitted": False,
    }
    if in_tail:
        directory = raw[offset-absolute_tail_start:at]
        report.update(inspect_directory(directory, members=entries,
                                        source_total_bytes=file_bytes,
                                        central_offset=offset))
    else:
        report.update({
            "central_directory_members_independently_parsed": False,
            "tiff_named_member_count": None,
            "other_named_member_count": None,
            "central_directory_separate_range_needed": True,
        })
    return report


def inspect_directory(raw: bytes, *, members: int, source_total_bytes: int,
                      central_offset: int) -> dict:
    if (type(raw) is not bytes or not 1 <= len(raw) <= MAX_DIRECTORY_BYTES
            or not 1 <= members <= MAX_MEMBERS):
        raise EocdSourceError("invalid bounded original central directory")
    pos, tiffs, other, seen = 0, 0, 0, set()
    for _ in range(members):
        if pos + 46 > len(raw):
            raise EocdSourceError("truncated ZIP central-directory member")
        parts = struct.unpack_from("<IHHHHHHIIIHHHHHII", raw, pos)
        if parts[0] != 0x02014B50:
            raise EocdSourceError("unexpected ZIP member header signature")
        flags, method = parts[3], parts[4]
        comp_size, uncomp_size = parts[8], parts[9]
        namelen, extralen, commentlen, disk_start = parts[10:14]
        local_offset = parts[16]
        stop = pos + 46 + namelen + extralen + commentlen
        if (stop > len(raw) or not 1 <= namelen <= 512
                or flags & 1 or method not in (0, 8)
                or disk_start != 0
                or any(v == 0xFFFFFFFF for v in (comp_size, uncomp_size, local_offset))
                or local_offset >= central_offset):
            raise EocdSourceError("unsafe, encrypted, ZIP64 or truncated ZIP member")
        namebytes = raw[pos+46:pos+46+namelen]
        try:
            name = namebytes.decode("utf-8" if flags & 0x800 else "cp437")
        except UnicodeError as exc:
            raise EocdSourceError("invalid ZIP member filename encoding") from exc
        if (not name or name.startswith("/") or "\\" in name or ":" in name
                or "\x00" in name or any(p in ("", ".", "..") for p in name.rstrip("/").split("/"))
                or name in seen):
            raise EocdSourceError("unsafe or duplicate ZIP member name")
        seen.add(name)
        if name.lower().endswith((".tif", ".tiff")):
            tiffs += 1
        else:
            other += 1
        pos = stop
    if pos != len(raw):
        raise EocdSourceError("unparsed trailing ZIP central-directory bytes")
    return {
        "central_directory_members_independently_parsed": True,
        "tiff_named_member_count": tiffs,
        "other_named_member_count": other,
        "central_directory_separate_range_needed": False,
        "source_member_names_not_persisted": True,
    }


def validate_range(headers, *, scenario: str):
    if scenario not in OBJECTS:
        raise EocdSourceError("unknown scenario")
    total = OBJECTS[scenario][1]
    start, end = total - TAIL_BYTES, total - 1
    if headers.get("Content-Range", "").strip() != f"bytes {start}-{end}/{total}":
        raise EocdSourceError("original ZIP tail Content-Range does not match source HEAD")
    if headers.get("Content-Length", "").strip() != str(TAIL_BYTES):
        raise EocdSourceError("original ZIP tail Content-Length not exact")
    media = headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if media not in MIME or headers.get("Content-Encoding", "identity").strip().lower() != "identity":
        raise EocdSourceError("unverified response MIME or transfer encoding")
    modified = headers.get("Last-Modified")
    if modified is not None and modified.strip() != LAST_MODIFIED[scenario]:
        raise EocdSourceError("source ZIP Last-Modified changed since original HEAD")
    return {
        "range_start": start,
        "range_end": end,
        "last_modified_same_as_prior_head_when_sent": modified is not None,
    }


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise EocdSourceError("original source ZIP tail redirected")


def _fetch(req: request.Request, timeout: int):
    return request.build_opener(
        request.ProxyHandler({}),
        NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def probe(scenario: str, *, opener: Callable = _fetch,
          clock: Callable = lambda: datetime.now(timezone.utc)) -> dict:
    if scenario not in OBJECTS:
        raise EocdSourceError("unknown Berlin water-depth ZIP scenario")
    name, full_size = OBJECTS[scenario]
    start, end = full_size - TAIL_BYTES, full_size - 1
    url = ROOT + name
    req = request.Request(
        url, method="GET",
        headers={"Range": f"bytes={start}-{end}",
                 "Accept": "application/zip",
                 "Accept-Encoding": "identity",
                 "If-Range": LAST_MODIFIED[scenario]}
    )
    try:
        with opener(req, TIMEOUT) as resp:
            if resp.status != 206 or resp.geturl() != url:
                raise EocdSourceError("provider did not honor immutable original ZIP tail range")
            header = validate_range(resp.headers, scenario=scenario)
            raw = resp.read(TAIL_BYTES + 1)
            details = inspect_tail(raw, scenario=scenario)
    except EocdSourceError:
        raise
    except (OSError, error.URLError, TimeoutError) as exc:
        raise EocdSourceError("original Berlin ZIP tail metadata fetch blocked") from exc
    now = clock()
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise EocdSourceError("receipt must have timezone offset")
    return {
        "profile": PROFILE,
        "original_source_url": url,
        "utc": now.astimezone(timezone.utc).isoformat(),
        "source_code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "http_range_status_206_verified": True,
        "no_original_source_bytes_persisted": True,
        **header,
        **details,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scenario", required=True, choices=sorted(OBJECTS))
    p.add_argument("--live", action="store_true")
    a = p.parse_args(argv)
    if not a.live:
        p.error("explicit --live required; synthetic unit tests are default")
    try:
        print(json.dumps(probe(a.scenario), sort_keys=True, allow_nan=False))
    except (EocdSourceError, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
