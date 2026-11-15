# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed format preflight for one IGRA v2.2 station sounding slice.

Official NOAA format: https://www.ncei.noaa.gov/pub/data/igra/data/igra2-data-format.txt
This parser accepts ONLY *already authorized, separately unzipped* sounding
text bytes. It does not obtain ZIP files, authorize provider access, persist
source rows, or establish a CAT-model admission.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re

MAX_TEXT_BYTES = 262_144
MAX_SOUNDINGS = 12
MAX_LEVELS = 2_000
STATION_ID = re.compile(r"[A-Z0-9]{11}\Z")
MISSING = {-8888, -9999}


class Igra22FormatError(ValueError):
    """Invalid or unsuitable original NOAA IGRA v2.2 sounding text slice."""


def _int_field(record: str, begin: int, end: int, label: str) -> int:
    value = record[begin:end].strip()
    if not re.fullmatch(r"-?[0-9]+", value):
        raise Igra22FormatError(f"invalid {label}")
    return int(value)


def _header(line: str, station_id: str) -> tuple[dt.date, int, int]:
    if len(line) != 71 or line[0] != "#" or line[1:12] != station_id:
        raise Igra22FormatError("IGRA sounding header length/marker/station mismatch")
    try:
        date = dt.date(
            _int_field(line, 13, 17, "year"),
            _int_field(line, 18, 20, "month"),
            _int_field(line, 21, 23, "day"),
        )
    except ValueError as exc:
        raise Igra22FormatError("invalid sounding UTC date") from exc
    hour = _int_field(line, 24, 26, "nominal hour")
    if hour != 99 and not 0 <= hour <= 23:
        raise Igra22FormatError("nominal hour must be UTC 00–23 or 99 missing")
    release_time = _int_field(line, 27, 31, "release time")
    if release_time != 9999 and not (
        0 <= release_time // 100 <= 23 and (0 <= release_time % 100 <= 59 or release_time % 100 == 99)
    ):
        raise Igra22FormatError("invalid release time HHMM, HH99, or 9999")
    levels = _int_field(line, 32, 36, "level count")
    if not 1 <= levels <= MAX_LEVELS:
        raise Igra22FormatError("empty or oversized sounding level count")
    lat = _int_field(line, 55, 62, "latitude")
    lon = _int_field(line, 63, 71, "longitude")
    # NOAA fixed-width station coordinates are encoded in 1/10000 degrees.
    if abs(lat) > 900_000 or abs(lon) > 1_800_000:
        raise Igra22FormatError("station location out of range")
    return date, hour, levels


def _level(line: str) -> tuple[int, int]:
    if len(line) != 51 or line[0] not in "123" or line[1] not in "012":
        raise Igra22FormatError("invalid IGRA level length or type")
    etime = _int_field(line, 3, 8, "elapsed time")
    if etime not in MISSING and (etime < 0 or etime % 100 >= 60):
        raise Igra22FormatError("elapsed time MMMSS malformed")
    pressure = _int_field(line, 9, 15, "pressure")
    if pressure != -9999 and not 0 < pressure <= 110000:
        raise Igra22FormatError("pressure outside Pa bounds")
    _int_field(line, 16, 21, "geopotential height")
    _int_field(line, 22, 27, "temperature")
    rh = _int_field(line, 28, 33, "relative humidity")
    if rh not in MISSING and not 0 <= rh <= 1000:
        raise Igra22FormatError("relative humidity tenths of percent outside range")
    dpdp = _int_field(line, 34, 39, "dewpoint depression")
    if dpdp not in MISSING and dpdp < 0:
        raise Igra22FormatError("negative dewpoint depression")
    wdir = _int_field(line, 40, 45, "wind direction")
    if wdir not in MISSING and not 0 <= wdir <= 360:
        raise Igra22FormatError("wind direction outside degrees")
    wspd = _int_field(line, 46, 51, "wind speed")
    if wspd not in MISSING and wspd < 0:
        raise Igra22FormatError("negative wind speed")
    if any(line[i] not in " AB" for i in (15, 21, 27)):
        raise Igra22FormatError("unknown NOAA pressure/height/temperature quality flag")
    return pressure, wspd


def screen_igra22_unzipped_text_bytes(original_text: bytes, *, station_id: str) -> dict[str, object]:
    """Check an exact station-matched uncompressed text slice; never reformat it.

    SHA-256 here belongs to the *uncompressed text*, not the source ZIP bytes.
    The ZIP has to be separately authorized, size-bounded and hashed on fetch.
    """
    if not isinstance(station_id, str) or not STATION_ID.fullmatch(station_id):
        raise Igra22FormatError("invalid station identifier")
    if not isinstance(original_text, bytes) or not 0 < len(original_text) <= MAX_TEXT_BYTES:
        raise Igra22FormatError("text empty, wrong type or exceeds byte cap")
    try:
        data = original_text.decode("ascii", errors="strict")
    except UnicodeDecodeError as exc:
        raise Igra22FormatError("IGRA sounding text must be ASCII") from exc
    if any(ord(char) < 32 and char not in "\r\n" for char in data):
        raise Igra22FormatError("non-text control byte in sounding")
    if "\r" in data.replace("\r\n", ""):
        raise Igra22FormatError("unexpected carriage return")
    lines = data.splitlines()
    if any(not line for line in lines):
        raise Igra22FormatError("blank line in sounding")
    idx = 0
    soundings = 0
    total_levels = 0
    missing_wind = 0
    first_date = last_date = None
    while idx < len(lines):
        if soundings >= MAX_SOUNDINGS:
            raise Igra22FormatError("too many soundings in research slice")
        date, hour, declared = _header(lines[idx], station_id)
        if idx + declared >= len(lines):
            raise Igra22FormatError("truncated IGRA sounding levels")
        for line in lines[idx + 1:idx + 1 + declared]:
            _, wspd = _level(line)
            missing_wind += wspd in MISSING
        idx += declared + 1
        total_levels += declared
        soundings += 1
        first_date = first_date or date.isoformat()
        last_date = date.isoformat()
    if not soundings:
        raise Igra22FormatError("no sounding")
    return {
        "source_id": "noaa.ncei.igra.v2.2",
        "station_id": station_id,
        "source_scope": "unzipped-bounded-sounding-text-only",
        "uncompressed_text_sha256": hashlib.sha256(original_text).hexdigest(),
        "uncompressed_text_bytes": len(original_text),
        "soundings": soundings,
        "levels": total_levels,
        "levels_without_wind_speed": missing_wind,
        "first_date_utc": first_date,
        "last_date_utc": last_date,
        "zip_original_sha256": "not_tested",
        "source_download_licence_and_service_automation": "not_verified",
        "source_format_screen": "passed_offline_only",
        "scientific_and_model_admission": "not_admitted",
        "neon_storage": "storage_not_verified",
    }
