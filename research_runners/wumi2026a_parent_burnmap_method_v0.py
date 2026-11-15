#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline WUMI2026a *publisher method* audit for parent-only burn-area maps.

Not a verification of per-event MTBS raster bytes, agency polygons, historical
completeness, legal reuse or hazard-model admission. Exact Dryad asset SHA and
ZIP CRC are required before reading even the original parent event list.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from io import BytesIO, StringIO
import json
from pathlib import Path
from zipfile import ZipFile

try:
    from .wumi2026a_dryad_original_asset_receipt_v0 import (
        ASSET_BYTES, ASSET_SHA256, DryadReceiptBlocked, inspect_original_zip_pinned,
    )
    from .wumi2026a_parent_subfire_partition_v0 import (
        NO_NAME, PartitionBlocked, _read_list,
    )
except ImportError:
    from wumi2026a_dryad_original_asset_receipt_v0 import (
        ASSET_BYTES, ASSET_SHA256, DryadReceiptBlocked, inspect_original_zip_pinned,
    )
    from wumi2026a_parent_subfire_partition_v0 import (
        NO_NAME, PartitionBlocked, _read_list,
    )

MTBS = "MTBS_LANDSAT_CLASSIFICATION_METHOD"
BOUNDARY = "AGENCY_PERIMETER_UNIFORM_BURN_ASSUMPTION"
CIRCLE = "HYPOTHETICAL_CIRCLE_UNIFORM_BURN_ASSUMPTION"
TIER = (MTBS, BOUNDARY, CIRCLE)
PRIMARY_DATASETS = frozenset(("mtbs", "calfire", "wfigs", "wfaip", "fpa_fod"))
EXTRA_COLS = frozenset((
    "mtbs_id", "object_id_calfire", "object_id_wfigs",
    "object_id_usgs", "object_id_iafph",
))
MISSING = frozenset(("", "na", "n/a", "null", "nan", "unknown"))


class FootprintMethodBlocked(ValueError):
    """Cannot safely assign the author's declared original burn-map method."""


def _is_missing(value: str) -> bool:
    return value.strip().casefold() in MISSING


def _source_method(record: dict[str, str]) -> tuple[str, str]:
    """Replicate the original author's 19_make_final_lists lines 565–580.

    Priority is primary MTBS/Calfire/WFIGS, then linked WFIGS, USGS,
    IAFPH and finally the synthetic circle. No independent map is claimed.
    """
    dataset = record["dataset"].strip().casefold()
    if dataset not in PRIMARY_DATASETS:
        raise FootprintMethodBlocked("unknown primary fire dataset; method attribution blocked")
    if dataset == "mtbs":
        return "mtbs", MTBS
    if dataset == "calfire":
        return "calfire", BOUNDARY
    if dataset == "wfigs":
        return "wfigs", BOUNDARY
    for link_field, provider in (
        ("object_id_wfigs", "wfigs"),
        ("object_id_usgs", "usgs"),
        ("object_id_iafph", "iafph"),
    ):
        if not _is_missing(record[link_field]):
            return provider, BOUNDARY
    return "circle", CIRCLE


def summarize_publisher_parent_burnmap_methods(parent_list: bytes) -> dict:
    """Emit only source-method and annual aggregate counts, not original rows."""
    native_header, checked, _ = _read_list(parent_list, "WUMI2026a_parent_only")
    header_set = set(native_header)
    if not EXTRA_COLS.issubset(header_set):
        raise FootprintMethodBlocked("required original WUMI linked perimeter source columns missing")
    try:
        stream = StringIO(parent_list.decode("utf-8-sig"), newline="")
        reader = csv.DictReader(stream, delimiter=",", strict=True)
        header = reader.fieldnames
        if header is None or tuple(v.strip().casefold() for v in header) != native_header:
            raise FootprintMethodBlocked("inconsistent original source header")
        name_map = {v: header[i] for i, v in enumerate(native_header)}
        source_counts = Counter()
        by_year = defaultdict(Counter)
        by_tier = Counter()
        source_identity_gaps = Counter()
        burn_area_missing_by_tier = Counter()
        records_seen = 0
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise FootprintMethodBlocked("unexpected original source row shape")
            fields = {key: row[name_map[key]] for key in EXTRA_COLS | {"dataset", "year", "burn_area_ha"}}
            method, tier = _source_method(fields)
            year = fields["year"].strip()
            if year not in {str(y) for y in range(1984, 2027)}:
                raise FootprintMethodBlocked("unbounded original source year")
            records_seen += 1
            source_counts[method] += 1
            by_year[year][tier] += 1
            by_tier[tier] += 1
            identity_column = {
                "mtbs": "mtbs_id",
                "calfire": "object_id_calfire",
                "wfigs": "object_id_wfigs",
                "usgs": "object_id_usgs",
                "iafph": "object_id_iafph",
            }.get(method)
            if identity_column and _is_missing(fields[identity_column]):
                source_identity_gaps[method] += 1
            if fields["burn_area_ha"].strip().casefold() in MISSING:
                burn_area_missing_by_tier[tier] += 1
    except (csv.Error, UnicodeError) as exc:
        raise FootprintMethodBlocked("unreadable original WUMI CSV") from exc
    if records_seen != len(checked) or records_seen != sum(by_tier.values()):
        raise FootprintMethodBlocked("source count mismatches validated original ID population")
    return {
        "audit": "wumi2026a-original-parent-map-method-provenance-v0",
        "state": (
            "REVIEW_PUBLISHER_LINK_IDENTITIES"
            if sum(source_identity_gaps.values())
            else "PUBLISHER_METHOD_COUNTS_ONLY_NO_ADMISSION"
        ),
        "view": "no_subfires_only",
        "fire_events_in_parent_view": records_seen,
        "publisher_burn_map_methods": dict(sorted(source_counts.items())),
        "evidence_method_tiers": {k: by_tier[k] for k in TIER},
        "publisher_method_by_year": {
            year: {k: counts[k] for k in TIER}
            for year, counts in sorted(by_year.items())
        },
        "missing_publisher_source_identity_by_method": dict(sorted(source_identity_gaps.items())),
        "missing_publisher_burn_area_by_tier": dict(sorted(burn_area_missing_by_tier.items())),
        "author_selection_precedence": [
            "primary_mtbs", "primary_calfire", "primary_wfigs",
            "linked_wfigs", "linked_usgs", "linked_iafph", "synthetic_circle",
        ],
        "agency_perimeter_does_not_prove_observed_burned_pixels": True,
        "hypothetical_circle_is_not_observed_wildfire_perimeter": True,
        "mtbs_method_label_is_not_original_raster_byte_validation": True,
        "subfire_members_not_counted_as_additional_occurrences": True,
        "event_frequency_hazard_footprint_and_insured_loss_admitted": False,
        "source_rights_and_original_burn_maps_reviewed": False,
        "original_event_identifiers_geometries_or_individual_areas_emitted": False,
    }


def inspect_exact_original_parent_map_methods_zip(raw: bytes) -> dict:
    receipt = inspect_original_zip_pinned(raw)
    parent = None
    with ZipFile(BytesIO(raw), "r") as archive:
        for member in archive.infolist():
            if member.filename.rsplit("/", 1)[-1] == NO_NAME:
                if parent is not None:
                    raise FootprintMethodBlocked("ambiguous duplicate original no-subfires parent list")
                if member.file_size > 40_000_000:
                    raise FootprintMethodBlocked("original parent list exceeds bounded size")
                parent = archive.read(member)
    if parent is None:
        raise FootprintMethodBlocked("exact original parent list not found in pinned ZIP")
    out = summarize_publisher_parent_burnmap_methods(parent)
    out.update({
        "dryad_original_dataset_version_declared": 458442,
        "publisher_original_zip_sha256": ASSET_SHA256,
        "original_zip_exact_sha_verified": receipt["target_original_file_sha256_verified"],
        "original_zip_structure_crc_verified": receipt["zip_structure_crc_checked"],
        "actual_per_fire_burnmap_original_bytes_tested": False,
        "CAT_model_or_source_licensing_admitted": False,
    })
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if not args.original_zip.is_file() or args.original_zip.stat().st_size != ASSET_BYTES:
            raise FootprintMethodBlocked("original publisher WUMI ZIP missing or wrong size")
        report = inspect_exact_original_parent_map_methods_zip(args.original_zip.read_bytes())
    except (DryadReceiptBlocked, PartitionBlocked, FootprintMethodBlocked, OSError) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 1 if report["state"] == "REVIEW_PUBLISHER_LINK_IDENTITIES" else 0


if __name__ == "__main__":
    raise SystemExit(main())
