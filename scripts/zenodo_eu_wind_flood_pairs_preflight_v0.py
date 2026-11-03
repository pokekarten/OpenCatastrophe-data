# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Bounded original Zenodo wind/flood paired-event CSV research preflight.

No source observations are committed, retained, emitted, or promoted to
insurance data. The public dataset is upstream-derived and not an independent
damage/loss observation. This standalone runner uses Python's standard library.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

SOURCE_ID = "nl.vu.european-multihazard-sparse-events.v1"
RECORD_ID = 22080546
FILE_KEY = "fl_ws.csv"
ORIGINAL_URL = (
    "https://zenodo.org/api/records/22080546/files/fl_ws.csv/content"
)
EXPECTED_BYTES = 801138
EXPECTED_MD5 = "4b88bee853013fa40095b555620f0852"
HEADER = [
    "groupname_1", "groupname_2", "start_date_1", "end_date_1",
    "start_date_2", "end_date_2", "hazardtype_1",
    "minlon_1", "maxlon_1", "minlat_1", "maxlat_1",
    "intensity_1", "intensity unit_1", "hazardtype_2",
    "minlon_2", "maxlon_2", "minlat_2", "maxlat_2",
    "intensity_2", "intensity unit_2",
]
UNITS = {"ws": "Mean wind speed (m/s)", "fl": "Mean flood depth (cm)"}


class OriginalPairError(ValueError):
    """Original source identity or semantics cannot be established."""


def _safe_date(value: str, line: int) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise OriginalPairError(f"line {line}: invalid date form")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise OriginalPairError(f"line {line}: impossible event date") from exc


def _one_event(row: dict[str, str], suffix: str, line: int):
    hazard = row["hazardtype_" + suffix]
    event_id = row["groupname_" + suffix]
    if hazard not in UNITS or not re.fullmatch(hazard + r"[0-9]+", event_id):
        raise OriginalPairError(f"line {line}: invalid hazard/event ID")
    if row["intensity unit_" + suffix] != UNITS[hazard]:
        raise OriginalPairError(f"line {line}: source unit not known or wrong")
    start = _safe_date(row["start_date_" + suffix], line)
    end = _safe_date(row["end_date_" + suffix], line)
    if end < start:
        raise OriginalPairError(f"line {line}: event end precedes start")
    try:
        bbox = tuple(float(row[k + "_" + suffix]) for k in
                     ("minlon", "maxlon", "minlat", "maxlat"))
        intensity = float(row["intensity_" + suffix])
    except (TypeError, ValueError) as exc:
        raise OriginalPairError(f"line {line}: invalid numeric field") from exc
    if not all(map(math.isfinite, (*bbox, intensity))):
        raise OriginalPairError(f"line {line}: non-finite numeric field")
    west, east, south, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise OriginalPairError(f"line {line}: invalid event bounding box")
    if intensity <= 0:
        raise OriginalPairError(f"line {line}: non-positive source intensity")
    return hazard, event_id, start, end, bbox


def parse_pair_csv(raw: bytes) -> dict[str, object]:
    try:
        contents = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(contents, newline=""), strict=True)
        if reader.fieldnames != HEADER:
            raise OriginalPairError("unexpected original pair CSV header")
        counts = {"wind_flood": 0, "other": 0}
        all_pairs: set[tuple[str, str]] = set()
        distinct = {"ws": set(), "fl": set()}
        nonoverlap_time = 0
        nonoverlap_bbox = 0
        start_dates: list[date] = []
        end_dates: list[date] = []
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise OriginalPairError(f"line {line}: invalid number of CSV fields")
            a = _one_event(row, "1", line)
            b = _one_event(row, "2", line)
            distinct[a[0]].add(a[1])
            distinct[b[0]].add(b[1])
            pair_key = tuple(sorted((a[1], b[1])))
            if pair_key in all_pairs:
                raise OriginalPairError(f"line {line}: duplicate event pair")
            all_pairs.add(pair_key)
            if {a[0], b[0]} == {"ws", "fl"}:
                counts["wind_flood"] += 1
            else:
                counts["other"] += 1
            if a[3] < b[2] or b[3] < a[2]:
                nonoverlap_time += 1
            # Bounding-box overlap is necessary, but not sufficient, for
            # true sparse-pixel physical overlap; never claim physical match.
            x, y = a[4], b[4]
            if x[1] < y[0] or y[1] < x[0] or x[3] < y[2] or y[3] < x[2]:
                nonoverlap_bbox += 1
            start_dates.extend((a[2], b[2]))
            end_dates.extend((a[3], b[3]))
    except (UnicodeError, csv.Error) as exc:
        raise OriginalPairError(f"malformed UTF-8/CSV: {exc}") from exc

    if not all_pairs or not counts["wind_flood"]:
        raise OriginalPairError("no valid wind/flood pairs found")
    return {
        "pair_rows": len(all_pairs),
        "wind_flood_pair_rows": counts["wind_flood"],
        "other_pair_rows_requires_scientific_review": counts["other"],
        "wind_event_ids_referenced": len(distinct["ws"]),
        "flood_event_ids_referenced": len(distinct["fl"]),
        "pair_rows_without_calendar_overlap": nonoverlap_time,
        "pair_rows_without_bbox_overlap": nonoverlap_bbox,
        "first_source_event_start": min(start_dates).isoformat(),
        "last_source_event_end": max(end_dates).isoformat(),
        "original_event_ids_not_insured_losses": True,
        "bbox_overlap_not_sparse_pixel_overlap": True,
    }


def original_receipt(raw: bytes) -> dict[str, object]:
    if len(raw) != EXPECTED_BYTES:
        raise OriginalPairError("source data truncated or unexpected original byte length")
    actual_md5 = hashlib.md5(raw).hexdigest()
    if actual_md5 != EXPECTED_MD5:
        raise OriginalPairError("original publisher MD5 does not match")
    stats = parse_pair_csv(raw)
    return {
        "schema_version": "oc-eu-wind-flood-pair-original-byte-proof-v0",
        "source_candidate_id": SOURCE_ID,
        "zenodo_record_id": RECORD_ID,
        "file_key": FILE_KEY,
        "original_byte_count": len(raw),
        "original_md5_recomputed": actual_md5,
        "original_sha256_recomputed": hashlib.sha256(raw).hexdigest(),
        **stats,
        "raw_source_bytes_persisted": False,
        "source_admitted": False,
        "derived_loss_computed": False,
        "model_input_approved": False,
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise OriginalPairError("original URL redirect forbidden")


def retrieve_original() -> bytes:
    req = urllib.request.Request(
        ORIGINAL_URL,
        headers={"Accept": "*/*",
                 "User-Agent": "OpenCatastrophe-data/1.0 bounded-source-proof"},
    )
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=25) as response:
            if response.status != 200:
                raise OriginalPairError("original provider did not return HTTP 200")
            if response.headers.get("Content-Length"):
                size = int(response.headers["Content-Length"])
                if size != EXPECTED_BYTES:
                    raise OriginalPairError("provider content-length/version mismatch")
            raw = response.read(EXPECTED_BYTES + 1)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise OriginalPairError(f"original provider HTTPS read failed: {exc}") from exc
    if len(raw) != EXPECTED_BYTES:
        raise OriginalPairError("source missing, truncated or exceeds fixed byte cap")
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fetch", action="store_true", help="one exact bounded official HTTPS GET")
    source.add_argument("--local", type=Path, help="existing exact original local CSV")
    args = parser.parse_args()
    try:
        if args.fetch:
            raw = retrieve_original()
        else:
            if not args.local.is_file() or args.local.stat().st_size != EXPECTED_BYTES:
                raise OriginalPairError("local original file missing or wrong size")
            raw = args.local.read_bytes()
        print(json.dumps(original_receipt(raw), sort_keys=True, indent=2))
    except OriginalPairError as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
