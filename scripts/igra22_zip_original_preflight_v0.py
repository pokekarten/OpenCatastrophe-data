# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline preflight of an independently authorized, original IGRA 2.2 station ZIP.

No network, implicit downloads, archive extraction to disk, source authorization,
Neon write, or CAT model admission. Only the first <=12 complete soundings can
receive a scientific text-format screen; the rest is not claimed to be screened.
"""

from __future__ import annotations

import hashlib
import io
import re
import stat
import zipfile

from scripts.igra22_sounding_preflight_v0 import (
    MAX_LEVELS,
    MAX_SOUNDINGS,
    MAX_TEXT_BYTES,
    STATION_ID,
    Igra22FormatError,
    screen_igra22_unzipped_text_bytes,
)

MAX_ZIP_BYTES = 5_242_880
MAX_UNCOMPRESSED_MEMBER_BYTES = 12_582_912


def screen_igra22_original_station_zip(original_zip: bytes, *, station_id: str) -> dict[str, object]:
    """Hash exact ZIP bytes then challenge one same-station text member and its prefix.

    A source ZIP might contain hundreds or thousands of soundings. The first
    bounded prefix is a *format challenge*, not a representative sample or
    complete station-series scientific validation. Scientific status remains
    blocked even when the ZIP checksum and preflight pass.
    """
    if not isinstance(station_id, str) or not STATION_ID.fullmatch(station_id):
        raise Igra22FormatError("invalid IGRA station identifier")
    if (not isinstance(original_zip, bytes) or
            not 0 < len(original_zip) <= MAX_ZIP_BYTES or
            not original_zip.startswith(b"PK\x03\x04")):
        raise Igra22FormatError("invalid, unsupported, or oversized original station ZIP")

    expected_member = f"{station_id}-data.txt"
    try:
        with zipfile.ZipFile(io.BytesIO(original_zip), mode="r") as archive:
            members = archive.infolist()
            if len(members) != 1 or members[0].filename != expected_member:
                raise Igra22FormatError("ZIP requires one exact same-station data member")
            info = members[0]
            mode = (info.external_attr >> 16) & 0xFFFF
            if (info.is_dir() or stat.S_ISLNK(mode) or info.flag_bits & 1 or
                    info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED} or
                    not 0 < info.file_size <= MAX_UNCOMPRESSED_MEMBER_BYTES or
                    not 0 < info.compress_size <= MAX_ZIP_BYTES):
                raise Igra22FormatError("unsupported or unsafe ZIP member flags or size")
            with archive.open(info, mode="r") as stream:
                text_bytes = stream.read(MAX_UNCOMPRESSED_MEMBER_BYTES + 1)
            if len(text_bytes) != info.file_size:
                raise Igra22FormatError("ZIP uncompressed size mismatch or oversized data")
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError, RuntimeError, ValueError) as exc:
        if isinstance(exc, Igra22FormatError):
            raise
        raise Igra22FormatError("malformed or unverifiable IGRA station ZIP") from exc

    # Sample *whole*, unchanged records; do not rewrite lines or hash them as
    # though they were the complete provider ZIP/member.
    cursor = io.BytesIO(text_bytes)
    selected_parts: list[bytes] = []
    selected_bytes = 0
    selected_soundings = 0
    while cursor.tell() < len(text_bytes) and selected_soundings < MAX_SOUNDINGS:
        first = cursor.readline()
        if len(first) < 36 or not first.startswith(b"#"):
            raise Igra22FormatError("malformed sounding header in original ZIP prefix")
        declared = first[32:36].strip()
        if not re.fullmatch(rb"[0-9]{1,4}", declared):
            raise Igra22FormatError("invalid sounding level count in ZIP prefix")
        nlevels = int(declared)
        if not 1 <= nlevels <= MAX_LEVELS:
            raise Igra22FormatError("unsafe sounding level count in ZIP prefix")
        parts = [first]
        for _ in range(nlevels):
            line = cursor.readline()
            if not line:
                raise Igra22FormatError("truncated sounding in original ZIP prefix")
            parts.append(line)
        candidate = b"".join(parts)
        if selected_bytes + len(candidate) > MAX_TEXT_BYTES:
            if not selected_parts:
                raise Igra22FormatError("first complete sounding exceeds bounded text screen")
            break
        selected_parts.append(candidate)
        selected_bytes += len(candidate)
        selected_soundings += 1
    if not selected_parts:
        raise Igra22FormatError("no complete sounding in original ZIP")
    screen = screen_igra22_unzipped_text_bytes(b"".join(selected_parts), station_id=station_id)
    return {
        "source_id": "noaa.ncei.igra.v2.2",
        "station_id": station_id,
        "product": "NOAA IGRA 2.2 same-station sounding ZIP",
        "original_zip_sha256": hashlib.sha256(original_zip).hexdigest(),
        "original_zip_bytes": len(original_zip),
        "unzipped_member_name": expected_member,
        "unzipped_member_bytes": len(text_bytes),
        "unzipped_member_sha256": hashlib.sha256(text_bytes).hexdigest(),
        "screened_prefix_bytes": selected_bytes,
        "screened_prefix_sha256": hashlib.sha256(b"".join(selected_parts)).hexdigest(),
        "screened_prefix_soundings": screen["soundings"],
        "screened_prefix_levels": screen["levels"],
        "full_member_scientifically_screened": selected_bytes == len(text_bytes),
        "science_screen_scope": "first_bounded_complete_soundings_only",
        "external_provider_acquisition": "not_performed_by_this_code",
        "download_service_rights": "not_verified_by_this_code",
        "commercial_cat_model_admission": "not_admitted",
        "neon_storage": "storage_not_verified",
    }
