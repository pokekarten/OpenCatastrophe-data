# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Original-byte EU paired-event -> hazard index ID crosswalk, receipt only.

Three fixed public publisher CSVs; no raw rows saved or emitted, no exposure,
loss or model admission. Upstream events are derived from common hazard inputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from scripts.zenodo_eu_wind_flood_pairs_preflight_v0 import (
    HEADER as PAIR_HEADER,
    ORIGINAL_URL as PAIR_URL,
    parse_pair_csv,
    NoRedirect,
)

RECORD_ID = 22080546
SOURCE_ID = "nl.vu.european-multihazard-sparse-events.v1"
URL_PREFIX = "https://zenodo.org/api/records/22080546/files/"
# Original file sizes / publisher checksums from fixed official Zenodo record.
SOURCES = {
    "wind": ("hazardinfows.csv", 32210, "e58a511d83da230931b57cb9822d8841"),
    "flood": ("hazardinfofl.csv", 477845, "01ee8e21e7844e1335767bd40ea3f836"),
    "pairs": ("fl_ws.csv", 801138, "4b88bee853013fa40095b555620f0852"),
}
# Independent original source SHA-256 from the completed bounded provider run.
EXPECTED_SHA256 = {
    "wind": "35f10da966ad8b6f0bc5fd9dba904bb8251ae11a9f52fe7e10f4f6ff9e2bf787",
    "flood": "0d4d24baf9839b43559a7c3a3abca781ad2626ee19dbdde6d741be2f5db5a431",
    "pairs": "087a0db2f6cfde6e952f5944040019ec32f956297487b1f6e429f91c82b6225f",
}
INDEX_HEADER = [
    "hazardtype", "groupname", "start_date", "end_date",
    "minlon", "maxlon", "minlat", "maxlat", "intensity",
    "intensity unit",
]
UNITS = {"ws": "Mean wind speed (m/s)", "fl": "Mean flood depth (cm)"}


class CrosswalkError(ValueError):
    """Original byte identity or scientific schema failed validation."""


def original_file_receipt(kind: str, raw: bytes) -> dict:
    name, size, publisher_md5 = SOURCES[kind]
    if len(raw) != size or hashlib.md5(raw).hexdigest() != publisher_md5:
        raise CrosswalkError(f"{kind}: exact original size/MD5 mismatch")
    independent_sha256 = hashlib.sha256(raw).hexdigest()
    if independent_sha256 != EXPECTED_SHA256[kind]:
        raise CrosswalkError(f"{kind}: original SHA-256 differs from independently pinned bytes")
    return {
        "file_key": name, "original_size_bytes": size,
        "publisher_md5_recomputed": publisher_md5,
        "original_sha256_recomputed": independent_sha256,
    }


def fetch_original(kind: str) -> bytes:
    name, size, _md5 = SOURCES[kind]
    url = URL_PREFIX + name + "/content"
    if kind == "pairs" and url != PAIR_URL:
        raise CrosswalkError("original pair URL changed")
    req = urllib.request.Request(url, headers={
        "Accept": "*/*",
        "User-Agent": "OpenCatastrophe-data/1.0 bounded-crosswalk-proof",
    })
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=30) as response:
            if response.status != 200:
                raise CrosswalkError(f"{kind}: original HTTP status is not 200")
            declared = response.headers.get("Content-Length")
            if declared is not None and int(declared) != size:
                raise CrosswalkError(f"{kind}: HTTP length differs from original")
            raw = response.read(size + 1)
    except (OSError, urllib.error.URLError, ValueError) as exc:
        raise CrosswalkError(f"{kind}: fixed original HTTPS read failed: {exc}") from exc
    original_file_receipt(kind, raw)
    return raw


def parse_index(raw: bytes, expected_peril: str) -> dict[str, tuple]:
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        if reader.fieldnames != INDEX_HEADER:
            raise CrosswalkError("original hazard index header changed")
        records = {}
        for line, row in enumerate(reader, 2):
            if len(records) >= 50000:
                raise CrosswalkError("index exceeds explicit 50000-event cap")
            if None in row or any(value is None for value in row.values()):
                raise CrosswalkError(f"line {line}: wrong field count")
            event_id = row["groupname"]
            if row["hazardtype"] != expected_peril or not re.fullmatch(expected_peril + r"[0-9]+", event_id):
                raise CrosswalkError(f"line {line}: peril/ID mismatch")
            if event_id in records:
                raise CrosswalkError(f"line {line}: duplicate event ID")
            if row["intensity unit"] != UNITS[expected_peril]:
                raise CrosswalkError(f"line {line}: unexpected source unit")
            try:
                start = date.fromisoformat(row["start_date"])
                end = date.fromisoformat(row["end_date"])
                bbox = tuple(float(row[k]) for k in ("minlon", "maxlon", "minlat", "maxlat"))
                intensity = float(row["intensity"])
            except ValueError as exc:
                raise CrosswalkError(f"line {line}: invalid source date/numeric field") from exc
            if not (re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["start_date"])
                    and re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["end_date"])):
                raise CrosswalkError(f"line {line}: noncanonical date")
            if start > end:
                raise CrosswalkError(f"line {line}: reversed event interval")
            w, e, s, n = bbox
            if not (all(map(math.isfinite, (*bbox, intensity)))
                    and -180 <= w < e <= 180 and -90 <= s < n <= 90 and intensity > 0):
                raise CrosswalkError(f"line {line}: invalid source geometry/intensity")
            records[event_id] = (
                row["start_date"], row["end_date"], bbox,
                intensity, row["intensity unit"],
            )
    except (UnicodeError, csv.Error) as exc:
        raise CrosswalkError(f"invalid UTF-8/CSV: {exc}") from exc
    if not records:
        raise CrosswalkError("empty original hazard index")
    return records


def reconcile(wind: bytes, flood: bytes, pairs: bytes) -> dict:
    wind_index = parse_index(wind, "ws")
    flood_index = parse_index(flood, "fl")
    pair_profile = parse_pair_csv(pairs)
    sources = {"ws": wind_index, "fl": flood_index}

    missing_ids: set[str] = set()
    date_differences: set[str] = set()
    extent_differences: set[str] = set()
    intensity_differences: set[str] = set()
    source_unit_differences: set[str] = set()
    internally_conflicting_ids: set[str] = set()
    observed: dict[str, tuple] = {}
    seen_pair_refs: set[str] = set()

    reader = csv.DictReader(io.StringIO(pairs.decode("utf-8-sig"), newline=""), strict=True)
    if reader.fieldnames != PAIR_HEADER:
        raise CrosswalkError("pair header does not match original schema")
    for line, row in enumerate(reader, 2):
        for side in ("1", "2"):
            event_id = row["groupname_" + side]
            peril = row["hazardtype_" + side]
            if peril not in sources:
                raise CrosswalkError(f"line {line}: unknown event peril")
            seen_pair_refs.add(event_id)
            current = (
                row["start_date_" + side], row["end_date_" + side],
                tuple(float(row[k + "_" + side])
                      for k in ("minlon", "maxlon", "minlat", "maxlat")),
                float(row["intensity_" + side]),
                row["intensity unit_" + side],
            )
            if event_id in observed and observed[event_id] != current:
                internally_conflicting_ids.add(event_id)
            observed[event_id] = current
            source_event = sources[peril].get(event_id)
            if source_event is None:
                missing_ids.add(event_id)
                continue
            if source_event[:2] != current[:2]:
                date_differences.add(event_id)
            if any(not math.isclose(a, b, rel_tol=0, abs_tol=1e-6)
                   for a, b in zip(source_event[2], current[2])):
                extent_differences.add(event_id)
            if not math.isclose(source_event[3], current[3], rel_tol=1e-6, abs_tol=1e-5):
                intensity_differences.add(event_id)
            if source_event[4] != current[4]:
                source_unit_differences.add(event_id)

    # Counts are *catalogue coverage*, not insurer exposures or event rates.
    wind_refs = {item for item in seen_pair_refs if item.startswith("ws")}
    flood_refs = {item for item in seen_pair_refs if item.startswith("fl")}
    unpaired_wind = len(set(wind_index) - wind_refs)
    unpaired_flood = len(set(flood_index) - flood_refs)

    discrepancy_ids = (
        missing_ids | date_differences | extent_differences |
        intensity_differences | source_unit_differences |
        internally_conflicting_ids
    )
    report = {
        "schema_version": "oc-eu-original-event-id-crosswalk-v0",
        "original_record_id": RECORD_ID,
        "source_candidate_id": SOURCE_ID,
        "original_wind_catalogue_events": len(wind_index),
        "original_flood_catalogue_events": len(flood_index),
        "original_wind_events_not_in_pair_index": unpaired_wind,
        "original_flood_events_not_in_pair_index": unpaired_flood,
        "wind_catalogue_pair_reference_coverage_pct": round(100 * (len(wind_index) - unpaired_wind) / len(wind_index), 3),
        "flood_catalogue_pair_reference_coverage_pct": round(100 * (len(flood_index) - unpaired_flood) / len(flood_index), 3),
        "unique_event_ids_referenced_by_pairs": len(seen_pair_refs),
        "unique_missing_index_ids": len(missing_ids),
        "unique_event_date_mismatches": len(date_differences),
        "unique_event_bbox_mismatches": len(extent_differences),
        "unique_event_intensity_mismatches": len(intensity_differences),
        "unique_event_unit_mismatches": len(source_unit_differences),
        "unique_ids_with_conflicting_pair_rows": len(internally_conflicting_ids),
        "total_unique_crosswalk_discrepancy_ids": len(discrepancy_ids),
        "exact_event_id_crosswalk_complete": len(discrepancy_ids) == 0,
        "source_event_rows_persisted": False,
        "pixel_overlap_proven": False,
        "insured_loss_generated": False,
        "model_input_admitted": False,
        "source_rights_scientifically_admitted": False,
        "pair_source_diagnostic": pair_profile,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fetch", action="store_true", help="three fixed official HTTPS GETs, bounded")
    group.add_argument("--local-dir", type=Path, help="directory of the three original files")
    args = parser.parse_args()
    try:
        if args.fetch:
            raw = {kind: fetch_original(kind) for kind in SOURCES}
        else:
            raw = {}
            for kind, (name, size, _md5) in SOURCES.items():
                path = args.local_dir / name
                if not path.is_file() or path.stat().st_size != size:
                    raise CrosswalkError(f"{kind}: original file missing or wrong length")
                raw[kind] = path.read_bytes()
        receipts = {kind: original_file_receipt(kind, payload)
                    for kind, payload in raw.items()}
        report = reconcile(raw["wind"], raw["flood"], raw["pairs"])
        report["original_file_receipts"] = receipts
        print(json.dumps(report, indent=2, sort_keys=True))
    except (OSError, UnicodeError, ValueError, CrosswalkError) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
