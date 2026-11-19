#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed original-byte preflight for JMA RSMC Tokyo best-track text.

Offline only. Accept an independently obtained exact archive member, plus a
separately pinned SHA-256. No network access, raw event exports, rights approval
or insurer model input is provided. Format: official JMA Best Track (Text).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

PROFILE = "jma-rsmc-besttrack-ascii-metadata-preflight-v0"
SOURCE_ID = "jp.jma.rsmc-tokyo.best-track"
FORMAT_URL = "https://www.jma.go.jp/jma/jma-eng/jma-center/rsmc-hp-pub-eg/Besttracks/e_format_bst.html"
MAX_BYTES = 8_000_000
MAX_LINES = 120_000
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
DIGITS = re.compile(r"[0-9]+\Z")


class JMABestTrackError(ValueError):
    """Original source format, identity or scientific interpretation is uncertain."""


def _digits(fragment: str, field: str, *, blank_ok: bool = False) -> int | None:
    raw = fragment.strip()
    if not raw and blank_ok:
        return None
    if not DIGITS.fullmatch(raw):
        raise JMABestTrackError(field + " must be ASCII decimal")
    return int(raw)


def _date8(raw: str) -> str:
    if not re.fullmatch(r"[0-9]{8}", raw):
        raise JMABestTrackError("header revision must be YYYYMMDD")
    try:
        return datetime.strptime(raw, "%Y%m%d").date().isoformat()
    except ValueError as exc:
        raise JMABestTrackError("invalid header revision calendar date") from exc


def _observation_time(raw: str) -> datetime:
    if not re.fullmatch(r"[0-9]{8}", raw):
        raise JMABestTrackError("observation timestamp must be YYMMDDHH")
    year2 = int(raw[:2])
    if year2 <= 26:
        year = 2000 + year2
    elif year2 >= 51:
        year = 1900 + year2
    else:
        raise JMABestTrackError("ambiguous two-digit analysis year outside 1951-2026")
    try:
        return datetime(year, int(raw[2:4]), int(raw[4:6]), int(raw[6:8]), tzinfo=timezone.utc)
    except ValueError as exc:
        raise JMABestTrackError("invalid observation calendar time") from exc


def inspect_besttrack_bytes(blob: bytes, expected_sha256: str) -> dict:
    """Return aggregate source-integrity evidence, never track points or storm IDs."""
    if type(expected_sha256) is not str or not DIGEST.fullmatch(expected_sha256):
        raise JMABestTrackError("independent expected sha256 must be 64 lowercase hex digits")
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise JMABestTrackError("original JMA text must be nonempty and within byte cap")
    actual = hashlib.sha256(blob).hexdigest()
    if actual != expected_sha256:
        raise JMABestTrackError("original source SHA256 mismatch")
    try:
        text = blob.decode("ascii")
    except UnicodeError as exc:
        raise JMABestTrackError("JMA original best track text must be ASCII") from exc
    rows = text.splitlines()
    if len(rows) > MAX_LINES or not rows or any(not row or "\t" in row for row in rows):
        raise JMABestTrackError("invalid empty/tabbed/oversized JMA text lines")
    idx = 0
    seen = set()
    storms = 0
    observations = 0
    windy = 0
    pressure_known = 0
    first = last = None
    revision_latest = None
    while idx < len(rows):
        h = rows[idx]
        idx += 1
        if len(h) < 72 or h[:5] != "66666":
            raise JMABestTrackError("expected 72-column JMA cyclone header")
        sid = h[6:10]
        repeat = h[21:25]
        if not re.fullmatch(r"[0-9]{4}", sid) or sid != repeat:
            raise JMABestTrackError("header international number does not match repeat")
        year2 = int(sid[:2])
        if year2 not in set(range(0, 27)) | set(range(51, 100)):
            raise JMABestTrackError("invalid international year range")
        count = _digits(h[12:15], "header data-line count")
        if not count or count > 500 or idx + count > len(rows):
            raise JMABestTrackError("header count does not match remaining lines")
        if h[26] not in "01" or h[28] not in "0123456789":
            raise JMABestTrackError("invalid header terminal flag")
        rev = _date8(h[64:72])
        if revision_latest is None or rev > revision_latest:
            revision_latest = rev
        if sid != "0000":
            if sid in seen:
                raise JMABestTrackError("duplicate international storm identifier")
            seen.add(sid)
        prev = None
        for row in rows[idx:idx + count]:
            if len(row) < 36 or row[9:12] != "002":
                raise JMABestTrackError("invalid JMA analysis record indicator")
            timestamp = _observation_time(row[:8])
            if prev is not None and timestamp <= prev:
                raise JMABestTrackError("nonincreasing track analysis times")
            prev = timestamp
            if first is None or timestamp < first:
                first = timestamp
            if last is None or timestamp > last:
                last = timestamp
            grade = _digits(row[13:14], "intensity grade")
            if grade not in {2, 3, 4, 5, 6, 7, 9}:
                raise JMABestTrackError("unrecognized JMA intensity grade")
            lat = _digits(row[15:18], "latitude tenths")
            lon = _digits(row[19:23], "longitude tenths")
            pressure = _digits(row[24:28], "central pressure", blank_ok=True)
            wind = _digits(row[33:36], "max wind knots", blank_ok=True)
            if not (0 <= lat <= 900 and 0 <= lon <= 3600):
                raise JMABestTrackError("location outside possible geographic bounds")
            if pressure not in (None, 0) and not 800 <= pressure <= 1100:
                raise JMABestTrackError("central pressure outside plausibility bounds")
            if wind not in (None, 0) and not 1 <= wind <= 200:
                raise JMABestTrackError("max wind outside plausibility bounds")
            # Blank and provider zero placeholders are UNKNOWN, not zero wind.
            windy += int(wind not in (None, 0))
            pressure_known += int(pressure not in (None, 0))
            observations += 1
        idx += count
        storms += 1
    return {
        "profile": PROFILE,
        "source_id": SOURCE_ID,
        "provider_format_documentation": FORMAT_URL,
        "source_sha256": actual,
        "original_byte_count": len(blob),
        "cyclone_header_count": storms,
        "analysis_record_count": observations,
        "records_with_positive_reported_max_wind": windy,
        "records_with_positive_reported_central_pressure": pressure_known,
        "source_first_analysis_utc": first.isoformat() if first else None,
        "source_last_analysis_utc": last.isoformat() if last else None,
        "latest_provider_header_revision": revision_latest,
        "zero_wind_or_blank_is_unknown_not_no_wind": True,
        "track_geometry_exported": False,
        "raw_event_rows_or_identifiers_exported": False,
        "observed_wind_footprint_available": False,
        "observed_insured_losses_available": False,
        "source_rights_reviewed": False,
        "model_input_admitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_text", type=Path)
    p.add_argument("--expected-sha256", required=True)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args(argv)
    if args.original_text.resolve() == args.out.resolve():
        p.error("refusing to overwrite provider source bytes")
    try:
        report = inspect_besttrack_bytes(args.original_text.read_bytes(), args.expected_sha256)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    except (JMABestTrackError, OSError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
