#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read only ZIP EOCD + central-directory ranges of three pinned Berlin SRGK ZIPs.

Never fetch an entire archive, local TIFF member, raster pixel, insured
asset or peril model. A server ignoring HTTP Range fails before body read.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import ssl
import struct
import sys
from urllib import error, request

SOURCE_BASE = "https://gdi.berlin.de/data/ua_srgk/atom/"
SOURCES = (
    ("selten", "wasserstand_seltenes_ereignis.zip", 132_689_382),
    ("aussergewoehnlich", "wasserstand_aussergewoehnliches_ereignis.zip", 136_928_247),
    ("extrem", "wasserstand_extrem.zip", 93_562_670),
)
SOURCE_URLS = {SOURCE_BASE + filename: (scenario, size) for scenario, filename, size in SOURCES}
TAIL = 65_557  # EOCD can have <=65535 comment bytes + 22 fixed bytes
MAX_CENTRAL_BYTES = 262_144
MAX_MEMBERS = 2048
MAX_FILENAME_BYTES = 400
MAX_TOTAL_INDEX_BYTES = 3 * (TAIL + MAX_CENTRAL_BYTES)
CONTENT_RANGE = re.compile(r"bytes (\d+)-(\d+)/(\d+)\Z")
PROFILE = "berlin-srgk-three-depth-zip-central-index-range-v0"
TIMEOUT = 35


class ZipIndexBlocked(ValueError):
    """Original ZIP metadata cannot be source-validated without excess bytes."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ZipIndexBlocked("original official provider redirected")


def _open(req, timeout):
    return request.build_opener(
        request.ProxyHandler({}), NoRedirect(),
        request.HTTPSHandler(context=ssl.create_default_context()),
    ).open(req, timeout=timeout)


def fetch_range(url: str, start: int, end: int, opener=_open) -> bytes:
    if url not in SOURCE_URLS:
        raise ZipIndexBlocked("unapproved source archive URL")
    size = SOURCE_URLS[url][1]
    if (type(start) is not int or type(end) is not int
            or not 0 <= start <= end < size
            or end - start + 1 > MAX_CENTRAL_BYTES):
        raise ZipIndexBlocked("requested byte interval not safe or bounded")
    req = request.Request(
        url, method="GET",
        headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
    )
    try:
        with opener(req, TIMEOUT) as response:
            # Fail on 200 before a byte is read. Prevent whole-ZIP download.
            if response.status != 206 or response.geturl() != url:
                raise ZipIndexBlocked("provider did not honor exact 206 Range request")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise ZipIndexBlocked("unexpected encoded Range response")
            declared = response.headers.get("Content-Range", "")
            match = CONTENT_RANGE.fullmatch(declared)
            if not match or tuple(map(int, match.groups())) != (start, end, size):
                raise ZipIndexBlocked("original size or byte range changed")
            payload = response.read(end - start + 2)
    except ZipIndexBlocked:
        raise
    except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
        raise ZipIndexBlocked("official ZIP HTTP Range unavailable") from exc
    if len(payload) != end - start + 1:
        raise ZipIndexBlocked("partial or excessive ZIP Range body")
    return payload


def locate_eocd(tail: bytes, full_size: int) -> tuple[int, int, int]:
    if not isinstance(tail, bytes) or len(tail) != min(TAIL, full_size):
        raise ZipIndexBlocked("wrong original bounded tail length")
    signature = b"PK\x05\x06"
    for pos in range(len(tail) - 22, -1, -1):
        if tail[pos:pos+4] != signature:
            continue
        (_, disk, cd_disk, on_disk, members, cd_size, cd_offset, comment) = (
            struct.unpack_from("<4s4H2IH", tail, pos)
        )
        if pos + 22 + comment != len(tail):
            continue
        if disk != 0 or cd_disk != 0 or on_disk != members:
            raise ZipIndexBlocked("spanned or multi-volume archive forbidden")
        if any(x in (0xFFFF, 0xFFFFFFFF) for x in (members, cd_size, cd_offset)):
            raise ZipIndexBlocked("ZIP64 requires separately reviewed source protocol")
        if not 0 < members <= MAX_MEMBERS or not 0 < cd_size <= MAX_CENTRAL_BYTES:
            raise ZipIndexBlocked("absent or overlarge ZIP central directory")
        absolute_eocd = full_size - len(tail) + pos
        if cd_offset + cd_size != absolute_eocd:
            raise ZipIndexBlocked("ZIP central offsets do not align with EOCD")
        return cd_offset, cd_size, members
    raise ZipIndexBlocked("complete original ZIP EOCD not found")


def parse_directory(raw: bytes, members: int) -> dict:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_CENTRAL_BYTES:
        raise ZipIndexBlocked("invalid bounded original ZIP directory")
    pos, filenames, formats = 0, set(), Counter()
    tiff_samples = []
    for i in range(members):
        if pos + 46 > len(raw):
            raise ZipIndexBlocked("truncated original central entry")
        fields = struct.unpack_from("<4s6H3I5H2I", raw, pos)
        (magic, _made, _need, flags, method, _clock, _date,
         _crc, comp_size, uncomp_size, fnlen, extralen, commentlen,
         disk, _internal, _external, local_offset) = fields
        if magic != b"PK\x01\x02":
            raise ZipIndexBlocked("unexpected original central ZIP signature")
        if flags & 1 or disk or any(v == 0xFFFFFFFF for v in (comp_size, uncomp_size, local_offset)):
            raise ZipIndexBlocked("encrypted, split or ZIP64 member unreviewed")
        if method not in (0, 8):
            raise ZipIndexBlocked("unreviewed compression method")
        if not 0 < fnlen <= MAX_FILENAME_BYTES:
            raise ZipIndexBlocked("empty/oversized original ZIP member name")
        end = pos + 46 + fnlen + extralen + commentlen
        if end > len(raw):
            raise ZipIndexBlocked("original ZIP central entry exceeds bounded index")
        namebytes = raw[pos+46:pos+46+fnlen]
        try:
            name = namebytes.decode("utf-8" if flags & (1 << 11) else "cp437")
        except UnicodeError as exc:
            raise ZipIndexBlocked("invalid original ZIP member encoding") from exc
        if ("\x00" in name or "\\" in name or name.startswith("/")
                or any(piece in (".", "..", "") for piece in name.rstrip("/").split("/"))
                or ":" in name):
            raise ZipIndexBlocked("unsafe provider member path")
        if name in filenames:
            raise ZipIndexBlocked("duplicate original ZIP member")
        filenames.add(name)
        suffix = ".tif" if name.lower().endswith(".tif") else (
            ".tiff" if name.lower().endswith(".tiff") else "other"
        )
        formats[suffix] += 1
        if suffix != "other" and len(tiff_samples) < 12:
            # Only safe public source filename metadata, not member payloads.
            tiff_samples.append({
                "name": name, "compressed_size_bytes": comp_size,
                "uncompressed_size_bytes": uncomp_size,
            })
        pos = end
    if pos != len(raw):
        raise ZipIndexBlocked("central directory has unparsed trailing bytes")
    return {
        "central_member_count": members,
        "central_suffix_counts": dict(sorted(formats.items())),
        "bounded_tiff_name_samples": tiff_samples,
        "all_original_tiff_member_pixels_unread": True,
        "all_original_member_bodies_unread": True,
    }


def inspect_one(url: str, opener) -> dict:
    if url not in SOURCE_URLS:
        raise ZipIndexBlocked("unexpected official source")
    scenario, size = SOURCE_URLS[url]
    tail_start = size - min(TAIL, size)
    tail = fetch_range(url, tail_start, size - 1, opener)
    offset, count, members = locate_eocd(tail, size)
    cd = fetch_range(url, offset, offset + count - 1, opener)
    parsed = parse_directory(cd, members)
    return {
        "scenario": scenario,
        "source_original_zip_url": url,
        "source_head_verified_zip_bytes_pinned": size,
        "source_bounded_tail_sha256": sha256(tail).hexdigest(),
        "source_bounded_central_directory_sha256": sha256(cd).hexdigest(),
        "source_central_directory_offset": offset,
        "source_central_directory_bytes": count,
        "source_get_requests": 2,
        "source_bytes_transferred": len(tail) + len(cd),
        **parsed,
    }


def probe(*, opener=_open, clock=lambda: datetime.now(timezone.utc)) -> dict:
    records = [inspect_one(url, opener) for url in SOURCE_URLS]
    total = sum(r["source_bytes_transferred"] for r in records)
    if total > MAX_TOTAL_INDEX_BYTES:
        raise ZipIndexBlocked("aggregate original index bytes exceeded")
    now = clock()
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ZipIndexBlocked("timestamp must have timezone")
    return {
        "profile": PROFILE,
        "original_source_checked_utc": now.astimezone(timezone.utc).isoformat(),
        "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "official_source_scenarios": records,
        "total_source_range_get_requests": 6,
        "total_original_zip_index_bytes_transferred": total,
        "any_complete_source_zip_downloaded": False,
        "any_original_tiff_or_raster_pixel_decoded": False,
        "raster_crs_or_depth_units_verified": False,
        "verified_second_pilot_raster_coverage": False,
        "mixed_geographic_licence_rights_resolved": False,
        "insurer_exposure_or_cat_model_admitted": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.error("explicit --live required for six bounded original ZIP index requests")
    try:
        print(json.dumps(probe(), ensure_ascii=False, sort_keys=True, allow_nan=False))
    except (ZipIndexBlocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
