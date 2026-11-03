# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Aggregate-only matching of exact-author GTSM CSV to fixed Zenodo station rows.

No original catalogue entries, station IDs, names or coordinates leave memory.
A join can prove *observed* identity for this pair of files; it does not prove
same-run input history, flood model fitness, data rights or coast proximity.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from io import StringIO

EXPECTED_STATS_ROWS = 38_957
MAX_AUTHOR_CATALOGUE_ROWS = 60_000
SCALE = Decimal("1000")


class AuthorCatalogueAuditBlocked(ValueError):
    """Author catalogue or fixed source row schema cannot be safely compared."""


def _packed_coordinate(value: str, *, longitude: bool) -> int:
    try:
        if not isinstance(value, str) or len(value) > 32:
            raise AuthorCatalogueAuditBlocked("source coordinate is not a bounded text scalar")
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise AuthorCatalogueAuditBlocked("source coordinate cannot be represented as decimal") from exc
    limit = 180 if longitude else 90
    if not number.is_finite() or not -limit <= number <= limit:
        raise AuthorCatalogueAuditBlocked("source coordinate is outside Earth bounds")
    # Source-original lon/lat are packed 0.001 degree int32; the public author
    # CSV may contain more precision. Quantization is a comparison, not a join key.
    return int((number * SCALE).to_integral_value(rounding=ROUND_HALF_EVEN))


def _station_family(name: str) -> str:
    if not isinstance(name, str) or len(name) > 256:
        raise AuthorCatalogueAuditBlocked("unbounded catalogue station-name metadata")
    if name.startswith("id_coast_"):
        return "coast_name_prefix"
    if name.startswith("id_reg_grid_"):
        return "regular_grid_name_prefix"
    if name.startswith("id_obs_"):
        return "observation_name_prefix"
    return "other_name_prefix"


def parse_author_catalogue(
    contents: str, *, limit: int = MAX_AUTHOR_CATALOGUE_ROWS,
) -> dict[int, tuple[int, int, str]]:
    """Strict tab-separated supplier text; caller verifies pinned Git blob first."""
    if type(contents) is not str or not 1 <= limit <= MAX_AUTHOR_CATALOGUE_ROWS:
        raise AuthorCatalogueAuditBlocked("unexpected catalogue stream or bounded row budget")
    reader = csv.DictReader(StringIO(contents), delimiter="\t")
    required = {"station_id", "station_name", "lon", "lat"}
    columns = reader.fieldnames or []
    if (len(columns) > 16 or len(set(columns)) != len(columns)
            or not required.issubset(set(columns))):
        raise AuthorCatalogueAuditBlocked("author GTSM station catalogue header changed")
    catalogue: dict[int, tuple[int, int, str]] = {}
    for row in reader:
        if len(catalogue) >= limit:
            raise AuthorCatalogueAuditBlocked("supplier catalogue exceeds fixed row budget")
        if None in row or any(row.get(key) is None for key in required):
            raise AuthorCatalogueAuditBlocked("malformed supplier station catalogue record")
        value = row["station_id"]
        if (not isinstance(value, str) or not value.isascii()
                or not value.isdecimal() or len(value) > 5):
            raise AuthorCatalogueAuditBlocked("author station identifier is not bounded uint16 text")
        station_id = int(value)
        if not 0 <= station_id <= 65_535:
            raise AuthorCatalogueAuditBlocked("author station identifier outside uint16")
        if station_id in catalogue:
            raise AuthorCatalogueAuditBlocked("author station catalogue includes duplicated station IDs")
        catalogue[station_id] = (
            _packed_coordinate(row["lon"], longitude=True),
            _packed_coordinate(row["lat"], longitude=False),
            _station_family(row["station_name"]),
        )
    if not catalogue:
        raise AuthorCatalogueAuditBlocked("author station catalogue is empty")
    return catalogue


def compare_original_to_author_catalogue(
    original_station_ids: list[int],
    original_raw_lons: list[int],
    original_raw_lats: list[int],
    catalogue: dict[int, tuple[int, int, str]],
    *, expected_rows: int = EXPECTED_STATS_ROWS,
) -> dict[str, object]:
    """Exact ID and packed coordinate crosscheck, aggregate-only outputs."""
    if type(expected_rows) is not int or not 1 <= expected_rows <= EXPECTED_STATS_ROWS:
        raise AuthorCatalogueAuditBlocked("unexpected source station-row budget")
    if any(
        type(arr) is not list or len(arr) != expected_rows
        for arr in (original_station_ids, original_raw_lons, original_raw_lats)
    ):
        raise AuthorCatalogueAuditBlocked("original source station/coordinate axes do not agree")
    if type(catalogue) is not dict or not catalogue:
        raise AuthorCatalogueAuditBlocked("author catalogue not verified and parsed")
    seen: set[int] = set()
    absent_ids = 0
    exact_packed_coordinate_matches = 0
    within_one_packed_unit = 0
    coordinate_conflicts = 0
    prefix_counts = {
        "coast_name_prefix": 0,
        "regular_grid_name_prefix": 0,
        "observation_name_prefix": 0,
        "other_name_prefix": 0,
    }
    for station, lon, lat in zip(original_station_ids, original_raw_lons, original_raw_lats):
        if (type(station) is not int or not 0 <= station <= 65_535
                or type(lon) is not int or type(lat) is not int
                or not -180_000 <= lon <= 180_000
                or not -90_000 <= lat <= 90_000):
            raise AuthorCatalogueAuditBlocked("original source packed station representation changed")
        if station in seen:
            raise AuthorCatalogueAuditBlocked("original source station-ID row duplicate")
        seen.add(station)
        row = catalogue.get(station)
        if row is None:
            absent_ids += 1
            continue
        ref_lon, ref_lat, category = row
        if category not in prefix_counts:
            raise AuthorCatalogueAuditBlocked("author station-name family is not recognized")
        prefix_counts[category] += 1
        if (lon, lat) == (ref_lon, ref_lat):
            exact_packed_coordinate_matches += 1
        elif abs(lon - ref_lon) <= 1 and abs(lat - ref_lat) <= 1:
            within_one_packed_unit += 1
        else:
            coordinate_conflicts += 1
    matched_ids = expected_rows - absent_ids
    if (sum(prefix_counts.values()) != matched_ids
            or exact_packed_coordinate_matches + within_one_packed_unit
            + coordinate_conflicts != matched_ids):
        raise AuthorCatalogueAuditBlocked("author/source catalogue overlap counts do not reconcile")

    # No original rows emitted: aggregate only the publisher catalogue's
    # name-family prefixes for IDs *not* represented in the Zenodo statistics.
    author_prefix_counts = dict.fromkeys(prefix_counts, 0)
    not_in_statistics_prefix_counts = dict.fromkeys(prefix_counts, 0)
    not_in_statistics_inside_source_id_span = 0
    not_in_statistics_outside_source_id_span = 0
    source_min = min(seen)
    source_max = max(seen)
    for catalogue_id, (_, _, family) in catalogue.items():
        if family not in author_prefix_counts:
            raise AuthorCatalogueAuditBlocked("supplier catalogue name-family drift")
        author_prefix_counts[family] += 1
        if catalogue_id not in seen:
            not_in_statistics_prefix_counts[family] += 1
            if source_min <= catalogue_id <= source_max:
                not_in_statistics_inside_source_id_span += 1
            else:
                not_in_statistics_outside_source_id_span += 1
    remaining = len(catalogue) - matched_ids
    occupied_original_id_span = source_max - source_min + 1
    missing_original_ids_within_its_span = occupied_original_id_span - len(seen)
    missing_in_both_within_source_span = (
        missing_original_ids_within_its_span
        - not_in_statistics_inside_source_id_span
    )
    if missing_in_both_within_source_span < 0:
        raise AuthorCatalogueAuditBlocked("original/author occupied-ID span reconciliation failed")
    if (sum(author_prefix_counts.values()) != len(catalogue)
            or sum(not_in_statistics_prefix_counts.values()) != remaining
            or not_in_statistics_inside_source_id_span
               + not_in_statistics_outside_source_id_span != remaining):
        raise AuthorCatalogueAuditBlocked("supplier-only ID counts do not reconcile")

    return {
        "schema_version": "gtsm-zenodo-author-station-catalogue-overlap-v0",
        "original_zenodo_statistical_rows": expected_rows,
        "author_catalogue_rows": len(catalogue),
        "matching_native_station_ids": matched_ids,
        "original_native_station_ids_absent_in_author_catalogue": absent_ids,
        "author_catalogue_ids_not_in_original_statistics": remaining,
        "author_catalogue_name_family_by_prefix": author_prefix_counts,
        "author_catalogue_not_in_statistics_by_prefix": not_in_statistics_prefix_counts,
        "original_native_id_span_width": occupied_original_id_span,
        "integer_id_labels_absent_in_both_files_inside_original_span": (
            missing_in_both_within_source_span
        ),
        "parent_paper_44734_model_positions_same_catalogue_release_proven": False,
        "author_catalogue_not_in_statistics_inside_occupied_original_id_span": (
            not_in_statistics_inside_source_id_span
        ),
        "author_catalogue_not_in_statistics_outside_occupied_original_id_span": (
            not_in_statistics_outside_source_id_span
        ),
        "matching_ids_with_exact_quantized_coordinates": exact_packed_coordinate_matches,
        "matching_ids_within_one_0p001_degree_packed_unit": within_one_packed_unit,
        "matching_ids_with_coordinate_conflict_larger_than_0p001_degree": coordinate_conflicts,
        "source_station_family_by_author_prefix": prefix_counts,
        "source_family_is_name_heuristic_not_geographic_coast_validation": True,
        "same_processing_run_inputs_proven": False,
        "source_source_parent_catalogue_join_for_all_rows_proven": (
            absent_ids == 0 and coordinate_conflicts == 0
            and exact_packed_coordinate_matches + within_one_packed_unit == expected_rows
        ),
        "vertical_datum_alignment_proven": False,
        "source_original_rows_or_provider_coordinates_emitted": False,
        "source_original_data_persisted": False,
        "commercial_rights_approved": False,
        "cat_model_admitted": False,
    }
