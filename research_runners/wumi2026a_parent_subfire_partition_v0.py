#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Conservative, offline comparison of two WUMI2026a final-list views.

The original 2026a ZIP must first match its publisher-listed exact SHA-256;
only two expected CSV-ish files are then read in memory. Does not infer parent
to child genealogy, burn-area conservation, independent events or CAT losses.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
import re
from zipfile import ZipFile

try:
    from .wumi2026a_dryad_original_asset_receipt_v0 import (
        ASSET_BYTES, ASSET_SHA256, DryadReceiptBlocked, inspect_original_zip_pinned,
    )
except ImportError:
    from wumi2026a_dryad_original_asset_receipt_v0 import (
        ASSET_BYTES, ASSET_SHA256, DryadReceiptBlocked, inspect_original_zip_pinned,
    )

NO_NAME = "WUMI2026a_wildfires_1984_2026_no_subfires.txt"
WITH_NAME = "WUMI2026a_wildfires_1984_2026_with_subfires.txt"
MAX_CSV_BYTES = 40_000_000
MAX_ROWS_PER_VIEW = 150_000
MIN_NATIVE_FIELDS = 26  # Original 19_make_final_lists uses comma positions through 26.
SOURCE_ID = re.compile(r"[0-9]{8}_[0-9]{1,7}_[0-9]{1,8}\Z")
HEADERS = ("fireid", "dataset", "year", "month", "day", "poly_area_ha", "burn_area_ha")
MISSING = {"", "n/a", "na", "nan", "unknown"}


class PartitionBlocked(ValueError):
    """Unreviewable or contradictory publisher list pair."""


def _area(raw: str, label: str) -> Decimal | None:
    if raw.strip().casefold() in MISSING:
        return None
    if len(raw) > 64:
        raise PartitionBlocked(label + ": overlong area value")
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise PartitionBlocked(label + ": invalid area number") from exc
    if not value.is_finite() or value < 0:
        raise PartitionBlocked(label + ": negative/nonfinite area")
    return value


def _read_list(raw: bytes, label: str):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_CSV_BYTES:
        raise PartitionBlocked(label + ": empty/oversized source list")
    if b"\x00" in raw:
        raise PartitionBlocked(label + ": embedded NUL in text list")
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise PartitionBlocked(label + ": invalid original-list text encoding") from exc
    reader = csv.reader(StringIO(content, newline=""), delimiter=",", strict=True)
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as exc:
        raise PartitionBlocked(label + ": missing header") from exc
    hdr = tuple(x.strip().casefold() for x in header)
    if not MIN_NATIVE_FIELDS <= len(hdr) <= 80 or len(hdr) != len(set(hdr)):
        raise PartitionBlocked(label + ": duplicate/incomplete original header fields")
    if not set(HEADERS).issubset(hdr):
        raise PartitionBlocked(label + ": original WUMI field contract differs")
    indexes = {name: hdr.index(name) for name in HEADERS}
    rows = {}
    mismatched_id_dates = 0
    missing_poly = 0
    missing_burn = 0
    changed_coordinates_uncertified = False
    try:
        for row in reader:
            if not row or (len(row) == 1 and not row[0].strip()):
                raise PartitionBlocked(label + ": unexpected blank event row")
            if len(row) != len(hdr) or len(rows) >= MAX_ROWS_PER_VIEW:
                raise PartitionBlocked(label + ": oversized/misaligned original CSV row")
            rid = row[indexes["fireid"]].strip()
            if not SOURCE_ID.fullmatch(rid) or rid in rows:
                raise PartitionBlocked(label + ": invalid or duplicate original event ID")
            year = row[indexes["year"]].strip()
            month = row[indexes["month"]].strip()
            day = row[indexes["day"]].strip()
            if not (year.isascii() and year.isdigit() and len(year) == 4
                    and month.isascii() and month.isdigit()
                    and day.isascii() and day.isdigit()):
                raise PartitionBlocked(label + ": malformed publisher start-date fields")
            y, m, d = int(year), int(month), int(day)
            if not 1984 <= y <= 2026 or not 1 <= m <= 12 or not 1 <= d <= 31:
                raise PartitionBlocked(label + ": impossible bounded date components")
            if rid[:8] != f"{y:04d}{m:02d}{d:02d}":
                mismatched_id_dates += 1  # identity claim only; metadata can be revised.
            dataset = row[indexes["dataset"]].strip()
            if not dataset or len(dataset) > 90:
                raise PartitionBlocked(label + ": missing source lineage")
            poly = _area(row[indexes["poly_area_ha"]], label)
            burn = _area(row[indexes["burn_area_ha"]], label)
            missing_poly += poly is None
            missing_burn += burn is None
            rows[rid] = (y, m, d, dataset, poly, burn)
    except csv.Error as exc:
        raise PartitionBlocked(label + ": malformed quoted native CSV") from exc
    if not rows:
        raise PartitionBlocked(label + ": no original events")
    stats = {
        "records": len(rows),
        "years": dict(sorted(Counter(v[0] for v in rows.values()).items())),
        "missing_polygon_area_records": missing_poly,
        "missing_satellite_burn_area_records": missing_burn,
        "fireid_date_components_disagree_count": mismatched_id_dates,
        "coordinates_checked_against_fireid": changed_coordinates_uncertified,
    }
    return hdr, rows, stats


def compare_alternative_list_views(no_subfires: bytes, with_subfires: bytes) -> dict:
    """Counts alternate source views; explicitly cannot claim parent-child links."""
    h0, a, sa = _read_list(no_subfires, "no_subfires")
    h1, b, sb = _read_list(with_subfires, "with_subfires")
    if h0 != h1:
        raise PartitionBlocked("original list column header drift between alternate views")
    both = a.keys() & b.keys()
    removed = a.keys() - b.keys()
    added = b.keys() - a.keys()
    mismatched_shared_years = sum(a[rid][0] != b[rid][0] for rid in both)
    if mismatched_shared_years:
        raise PartitionBlocked("same source fireid assigned different years across views")
    shared_area_changes = sum(
        a[rid][4:] != b[rid][4:] for rid in both
    )
    changed_origin = sum(a[rid][3] != b[rid][3] for rid in both)
    if len(both) + len(removed) != len(a) or len(both) + len(added) != len(b):
        raise PartitionBlocked("event-ID set conservation failed")
    # A count comparison alone cannot validate the parent-child links.
    return {
        "audit": "wumi2026a-alternative-event-partitions-v0",
        "state": "REVIEW_SHARED_ROWS" if (shared_area_changes or changed_origin) else "ALTERNATIVE_VIEWS_COUNTED_NOT_ADMITTED",
        "no_subfires": sa,
        "with_subfires": sb,
        "shared_fireids": len(both),
        "parent_view_ids_absent_from_subfire_view": len(removed),
        "subfire_view_ids_absent_from_parent_view": len(added),
        "shared_fireids_with_different_area_fields": shared_area_changes,
        "shared_fireids_with_different_primary_source": changed_origin,
        "rows_conserved_as_two_alternative_sets": True,
        "both_views_disjoint_event_samples": False,
        "two_views_can_be_summed_for_frequency": False,
        "source_fireid_is_immutable_insurance_occurrence_id": False,
        "publisher_fireid_can_be_recomputed_from_modified_coordinates": False,
        "parent_subfire_genealogy_verified": False,
        "child_polygon_area_sums_verifiably_match_parents": False,
        "child_satellite_burn_area_sums_verifiably_match_parents": False,
        "event_frequency_or_insured_loss_model_admitted": False,
        "original_fireids_or_coordinates_emitted": False,
    }


def inspect_original_pinned_partition_zip(raw: bytes) -> dict:
    """Only inspect original Dryad bytes after old ZIP identity/CRC guard succeeds."""
    parent_receipt = inspect_original_zip_pinned(raw)
    selected = {}
    with ZipFile(BytesIO(raw), "r") as z:
        for info in z.infolist():
            basename = info.filename.rsplit("/", 1)[-1]
            if basename in (NO_NAME, WITH_NAME):
                if basename in selected:
                    raise PartitionBlocked("duplicate final-list basenames in original ZIP")
                if info.file_size > MAX_CSV_BYTES:
                    raise PartitionBlocked("original list member exceeds bounded size")
                selected[basename] = z.read(info)
    if set(selected) != {NO_NAME, WITH_NAME}:
        raise PartitionBlocked("publisher ZIP missing exact two alternate event-list members")
    report = compare_alternative_list_views(selected[NO_NAME], selected[WITH_NAME])
    report.update({
        "dryad_version_declared": 458442,
        "original_zip_publisher_sha256": ASSET_SHA256,
        "original_zip_bytes_verified": parent_receipt["target_original_file_sha256_verified"],
        "original_zip_structure_and_crc_verified": parent_receipt["zip_structure_crc_checked"],
        "original_list_member_sha256": {
            "no_subfires": hashlib.sha256(selected[NO_NAME]).hexdigest(),
            "with_subfires": hashlib.sha256(selected[WITH_NAME]).hexdigest(),
        },
        "source_rights_or_CAT_admission_granted": False,
    })
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path, required=True,
                        help="Authorized local exact original WUMI2026a 4.68 MB archive")
    args = parser.parse_args(argv)
    try:
        if not args.original_zip.is_file() or args.original_zip.stat().st_size != ASSET_BYTES:
            raise PartitionBlocked("missing or wrong-sized original publisher ZIP")
        report = inspect_original_pinned_partition_zip(args.original_zip.read_bytes())
    except (DryadReceiptBlocked, PartitionBlocked, OSError) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 1 if report["state"] == "REVIEW_SHARED_ROWS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
