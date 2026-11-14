#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, pinned WUMI2026a source genealogy vs alternative final-event views.

Original Dryad ZIP bytes and ZIP CRC are checked upstream. The subfires notes
describe candidate source children, not an admitted physical event genealogy.
No source identifiers, geographic locations or individual areas are printed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

try:
    from .wumi2026a_dryad_original_asset_receipt_v0 import (
        ASSET_BYTES, ASSET_SHA256, DryadReceiptBlocked, inspect_original_zip_pinned,
    )
    from .wumi2026a_parent_subfire_partition_v0 import (
        NO_NAME, WITH_NAME, PartitionBlocked, _read_list, compare_alternative_list_views,
    )
except ImportError:
    from wumi2026a_dryad_original_asset_receipt_v0 import (
        ASSET_BYTES, ASSET_SHA256, DryadReceiptBlocked, inspect_original_zip_pinned,
    )
    from wumi2026a_parent_subfire_partition_v0 import (
        NO_NAME, WITH_NAME, PartitionBlocked, _read_list, compare_alternative_list_views,
    )

MAX_NOTES = 10_000
MAX_NOTE_BYTES = 250_000
MAX_NOTES_TOTAL_BYTES = 30_000_000
MAX_CANDIDATES = 100_000


class GenealogyBlocked(ValueError):
    """Source geometry, identity or genealogy contract is not auditable."""


def _parse_original_note(blob: bytes, parent_id: str, native_header: tuple[str, ...]):
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_NOTE_BYTES or b"\x00" in blob:
        raise GenealogyBlocked("missing/oversized/invalid source genealogy text")
    try:
        lines = blob.decode("utf-8-sig").splitlines()
    except UnicodeError as exc:
        raise GenealogyBlocked("invalid original note encoding") from exc
    # Original MATLAB writes: header, parent record, blank line, candidate
    # child rows; blank before a new top-level child, no blank for sub-subfires.
    if not 5 <= len(lines) <= 2_500 or lines[2].strip():
        raise GenealogyBlocked("unexpected parent plus grouped children source layout")
    child_lines = [line for line in lines[3:] if line.strip()]
    if len(child_lines) < 2:
        raise GenealogyBlocked("source note lacks at least two candidate child rows")
    aligned = "\n".join([lines[0], lines[1]] + child_lines) + "\n"
    try:
        header, records, _ = _read_list(aligned.encode("utf8"), "source_genealogy_note")
    except PartitionBlocked as exc:
        raise GenealogyBlocked("invalid native child/parent field or event identity") from exc
    if header != native_header or parent_id not in records:
        raise GenealogyBlocked("subfires file does not match source header/parent ID")
    children = set(records) - {parent_id}
    if len(children) != len(child_lines):
        raise GenealogyBlocked("genealogy note repeats parent as child")
    groups = nested = 0
    group_start = False
    for line in lines[2:]:
        if not line.strip():
            group_start = True
        elif group_start:
            groups += 1
            group_start = False
        else:
            nested += 1
    if groups < 1 or groups + nested != len(children):
        raise GenealogyBlocked("ambiguous nested source-note grouping")
    return records[parent_id], children, groups, nested


def audit_original_genealogy_notes(
    no_subfires: bytes, with_subfires: bytes, original_notes: dict[str, bytes],
) -> dict:
    """Source-only, aggregate original parent-candidate graph evidence."""
    report = compare_alternative_list_views(no_subfires, with_subfires)
    header, parents, _ = _read_list(no_subfires, "original_parent_view")
    _, final, _ = _read_list(with_subfires, "original_child_view")
    if (not isinstance(original_notes, dict)
            or not 0 < len(original_notes) <= MAX_NOTES):
        raise GenealogyBlocked("missing or out-of-bounds original genealogy notes")
    removed, added = set(parents) - set(final), set(final) - set(parents)
    owned = {}
    by_parent = {}
    stats = Counter()
    for parent_id, raw in original_notes.items():
        if parent_id not in parents or parent_id in by_parent:
            raise GenealogyBlocked("note filename parent not in original no-subfires view")
        original_parent, children, groups, nested = _parse_original_note(raw, parent_id, header)
        if original_parent != parents[parent_id]:
            raise GenealogyBlocked("note parent row conflicts with original parent view")
        for child_id in children:
            if child_id in owned or child_id == parent_id:
                raise GenealogyBlocked("source candidate child assigned to several parents")
            owned[child_id] = parent_id
        by_parent[parent_id] = children
        stats["candidate_child_rows"] += len(children)
        stats["top_level_child_groups"] += groups
        stats["nested_candidate_rows"] += nested
        if stats["candidate_child_rows"] > MAX_CANDIDATES:
            raise GenealogyBlocked("original genealogy candidate count over limit")
    if set(by_parent) & set(owned):
        raise GenealogyBlocked("ambiguous cyclic/nested parent identity across source files")

    for parent_id in removed:
        if parent_id not in by_parent:
            stats["removed_parent_missing_note"] += 1
            continue
        final_child_ids = by_parent[parent_id] & added
        if len(final_child_ids) < 2:
            stats["removed_parent_fewer_than_two_children"] += 1
            continue
        parent_area = parents[parent_id][4]
        child_areas = [final[c][4] for c in final_child_ids]
        if parent_area is None or any(area is None for area in child_areas):
            stats["polygon_area_not_comparable"] += 1
            continue
        # The publisher's MATLAB code rounds scaled polygon child area to
        # four decimal places; this checks numerical metadata only, NOT
        # geometric conservation, satellite-burn-area, or insured losses.
        tolerance = Decimal("0.0001") * (len(final_child_ids) + 1)
        if abs(parent_area - sum(child_areas, Decimal(0))) <= tolerance:
            stats["polygon_area_parent_sum_within_rounding"] += 1
        else:
            stats["polygon_area_parent_sum_disagrees"] += 1

    missing_child_link = len(added - set(owned))
    review = bool(
        missing_child_link or stats["removed_parent_missing_note"]
        or stats["removed_parent_fewer_than_two_children"]
        or stats["polygon_area_parent_sum_disagrees"]
    )
    report.update({
        "audit": "wumi2026a-original-subfires-parent-genealogy-v0",
        "state": "REVIEW_GENEALOGY_COVERAGE_OR_AREA" if review else "BOUNDED_SOURCE_GENEALOGY_ONLY",
        "source_subfires_note_count": len(by_parent),
        "source_candidate_child_records": stats["candidate_child_rows"],
        "source_top_level_child_groups": stats["top_level_child_groups"],
        "source_nested_sub_sub_fire_records": stats["nested_candidate_rows"],
        "removed_parents_missing_source_genealogy_file": stats["removed_parent_missing_note"],
        "final_added_ids_absent_from_all_source_notes": missing_child_link,
        "source_notes_for_parent_retained_in_final_view": len(set(by_parent) - removed),
        "removed_parents_with_fewer_than_two_final_children": stats["removed_parent_fewer_than_two_children"],
        "parent_polygon_area_sums_within_publisher_rounding_tolerance": stats["polygon_area_parent_sum_within_rounding"],
        "parent_polygon_area_sums_disagree": stats["polygon_area_parent_sum_disagrees"],
        "parent_polygon_area_sums_not_comparable": stats["polygon_area_not_comparable"],
        "candidate_notes_not_treated_as_final_event_count": True,
        "native_source_parent_child_physical_identity_proven": False,
        "parent_summed_satellite_burn_area_proven": False,
        "two_final_views_additive": False,
        "source_reuse_rights_or_CAT_admission_granted": False,
        "insurance_occurrence_or_loss_proven": False,
        "original_source_ids_coordinates_and_areas_emitted": False,
    })
    return report


def inspect_pinned_genealogy_zip(raw: bytes) -> dict:
    validated = inspect_original_zip_pinned(raw)
    views, notes = {}, {}
    size_total = 0
    with ZipFile(BytesIO(raw), "r") as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            path = member.filename.strip("/")
            name = path.rsplit("/", 1)[-1]
            if name in (NO_NAME, WITH_NAME):
                if name in views:
                    raise GenealogyBlocked("duplicate alternative-list basename")
                views[name] = archive.read(member)
            elif "/subfires/" in "/" + path and path.endswith(".txt"):
                parts = path.split("/")
                if parts[-2] != "subfires":
                    raise GenealogyBlocked("unsupported nested original-note path")
                parent_id = name[:-4]
                if parent_id in notes or member.file_size > MAX_NOTE_BYTES:
                    raise GenealogyBlocked("duplicate/oversized original note")
                size_total += member.file_size
                if size_total > MAX_NOTES_TOTAL_BYTES or len(notes) >= MAX_NOTES:
                    raise GenealogyBlocked("original genealogy exceeds total member bounds")
                notes[parent_id] = archive.read(member)
    if set(views) != {NO_NAME, WITH_NAME} or not notes:
        raise GenealogyBlocked("no verifiable original two-list + subfires-note structure")
    out = audit_original_genealogy_notes(views[NO_NAME], views[WITH_NAME], notes)
    out.update({
        "dryad_version_declared": 458442,
        "publisher_original_zip_sha256": ASSET_SHA256,
        "original_zip_bytes_verified": validated["target_original_file_sha256_verified"],
        "original_zip_crc_verified": validated["zip_structure_crc_checked"],
        "rights_or_insured_loss_admitted": False,
    })
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if not args.original_zip.is_file() or args.original_zip.stat().st_size != ASSET_BYTES:
            raise GenealogyBlocked("original Dryad ZIP missing or has wrong length")
        result = inspect_pinned_genealogy_zip(args.original_zip.read_bytes())
    except (OSError, DryadReceiptBlocked, PartitionBlocked, GenealogyBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 1 if result["state"] == "REVIEW_GENEALOGY_COVERAGE_OR_AREA" else 0


if __name__ == "__main__":
    raise SystemExit(main())
