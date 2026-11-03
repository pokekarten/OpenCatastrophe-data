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


def audit_hypothetical_100_id_batches(
    original_station_ids: list[int],
    author_catalogue: dict[int, tuple[int, int, str]],
) -> dict[str, object]:
    """Classify *aggregate* numeric-ID coverage in the author's 100-ID blocks.

    Only full 0..99, 100..199, ... bins completely contained within the
    original statistical ID span are considered. The author's p01 SLURM
    script uses 100 stations per batch, but no production run manifest or
    source-file completeness guarantee has been obtained.
    """
    if type(original_station_ids) is not list or not original_station_ids:
        raise AuthorCatalogueAuditBlocked("original statistical station ID list unavailable")
    if len(original_station_ids) > EXPECTED_STATS_ROWS:
        raise AuthorCatalogueAuditBlocked("source station IDs exceed exact original budget")
    if type(author_catalogue) is not dict or not author_catalogue:
        raise AuthorCatalogueAuditBlocked("original author catalogue unavailable")
    original_ids = set()
    for key in original_station_ids:
        if type(key) is not int or not 0 <= key <= 65_535:
            raise AuthorCatalogueAuditBlocked("unexpected native uint16 identifier")
        if key in original_ids:
            raise AuthorCatalogueAuditBlocked("original native station ID duplicated")
        if key not in author_catalogue:
            raise AuthorCatalogueAuditBlocked("author station catalogue does not contain original native ID")
        original_ids.add(key)
    for key, record in author_catalogue.items():
        if (type(key) is not int or not 0 <= key <= 65_535
                or type(record) is not tuple or len(record) != 3
                or record[2] not in ("coast_name_prefix", "regular_grid_name_prefix",
                                     "observation_name_prefix", "other_name_prefix")):
            raise AuthorCatalogueAuditBlocked("author original station catalogue entry invalid")

    width = 100
    low, high = min(original_ids), max(original_ids)
    first_full_start = ((low + width - 1) // width) * width
    # Note: exclude terminal partial 100-ID bin rather than make it appear
    # incomplete due only to being outside the published statistics ID span.
    last_full_start = (high - (width - 1)) // width * width
    states = {
        "full_100_of_100_statistics": 0,
        "partial_1_to_99_statistics": 0,
        "zero_statistics_all_100_author_rows": 0,
        "zero_statistics_some_author_rows": 0,
        "zero_statistics_zero_author_rows": 0,
    }
    author_only_in_zero_stat_by_prefix = {
        name: 0 for name in (
            "coast_name_prefix", "regular_grid_name_prefix",
            "observation_name_prefix", "other_name_prefix"
        )
    }
    total_stat_in_full_bins = 0
    total_author_in_full_bins = 0
    complete_bins = 0
    author_only_in_source_nonempty_bins = 0
    bins_with_any_stat_and_additional_author_ids = 0

    if first_full_start <= last_full_start:
        for start in range(first_full_start, last_full_start + 1, width):
            stat = 0
            author = 0
            for key in range(start, start + width):
                if key in original_ids:
                    stat += 1
                if key in author_catalogue:
                    author += 1
            total_stat_in_full_bins += stat
            total_author_in_full_bins += author
            complete_bins += 1
            if stat == width:
                states["full_100_of_100_statistics"] += 1
            elif stat:
                states["partial_1_to_99_statistics"] += 1
            elif author == width:
                states["zero_statistics_all_100_author_rows"] += 1
            elif author:
                states["zero_statistics_some_author_rows"] += 1
            else:
                states["zero_statistics_zero_author_rows"] += 1
            if stat == 0:
                for key in range(start, start + width):
                    row = author_catalogue.get(key)
                    if row is not None:
                        author_only_in_zero_stat_by_prefix[row[2]] += 1
            else:
                difference = author - stat
                if difference > 0:
                    bins_with_any_stat_and_additional_author_ids += 1
                    author_only_in_source_nonempty_bins += difference

    if sum(states.values()) != complete_bins:
        raise AuthorCatalogueAuditBlocked("author 100-ID batch classes do not reconcile")
    if total_stat_in_full_bins > total_author_in_full_bins:
        raise AuthorCatalogueAuditBlocked("author original ID subset invariant failed")
    catalogue_only_in_complete_bins = total_author_in_full_bins - total_stat_in_full_bins
    if (sum(author_only_in_zero_stat_by_prefix.values())
            + author_only_in_source_nonempty_bins != catalogue_only_in_complete_bins):
        raise AuthorCatalogueAuditBlocked("author-only coverage across 100-ID bins does not reconcile")

    author_rows_within_original_id_span = sum(
        low <= station_id <= high for station_id in author_catalogue
    )
    author_outside_original_id_span = len(author_catalogue) - author_rows_within_original_id_span
    original_rows_in_partial_boundary_bins = len(original_ids) - total_stat_in_full_bins
    author_rows_in_partial_boundary_bins = (
        author_rows_within_original_id_span - total_author_in_full_bins
    )
    if (original_rows_in_partial_boundary_bins < 0
            or author_rows_in_partial_boundary_bins < original_rows_in_partial_boundary_bins
            or author_outside_original_id_span < 0
            or author_rows_in_partial_boundary_bins + total_author_in_full_bins
               + author_outside_original_id_span != len(author_catalogue)):
        raise AuthorCatalogueAuditBlocked("source/author terminal partial-bin rows do not reconcile")

    gap_runs_multiple_of_100 = 0
    gap_runs_100_aligned = 0
    omitted_aligned_ids = 0
    ordered = sorted(original_ids)
    for left, right in zip(ordered, ordered[1:]):
        missing = right - left - 1
        if missing > 0 and missing % width == 0:
            gap_runs_multiple_of_100 += 1
            if (left + 1) % width == 0 and right % width == 0:
                gap_runs_100_aligned += 1
                omitted_aligned_ids += missing
    return {
        "schema_version": "gtsm-author-station-id-batch100-coverage-v0",
        "batch_origin": "numeric_zero_based_hypothesis",
        "batch_width_ids": width,
        "complete_100_id_bins_within_original_native_id_span": complete_bins,
        "source_statistic_rows_in_complete_bins": total_stat_in_full_bins,
        "author_catalogue_rows_in_complete_bins": total_author_in_full_bins,
        "source_rows_in_omitted_partial_boundary_bins": original_rows_in_partial_boundary_bins,
        "author_rows_in_omitted_partial_boundary_bins": author_rows_in_partial_boundary_bins,
        "author_catalogue_rows_outside_original_source_native_id_span": (
            author_outside_original_id_span
        ),
        "complete_bin_coverage_classes": states,
        "author_name_families_in_100_id_bins_with_zero_statistics": author_only_in_zero_stat_by_prefix,
        "author_catalogue_only_ids_in_100_id_bins_with_any_statistics": (
            author_only_in_source_nonempty_bins
        ),
        "number_of_100_id_bins_with_statistics_and_extra_catalogue_ids": (
            bins_with_any_stat_and_additional_author_ids
        ),
        "all_author_only_ids_within_complete_bins_are_in_zero_statistic_bins": (
            author_only_in_source_nonempty_bins == 0
        ),
        "original_missing_id_runs_length_multiple_of_100": gap_runs_multiple_of_100,
        "original_missing_id_runs_exactly_aligned_to_hypothetical_100_id_boundaries": (
            gap_runs_100_aligned
        ),
        "missing_integer_ids_in_100_boundary_aligned_gap_runs": omitted_aligned_ids,
        "actual_producer_batch_file_manifest_verified": False,
        "same_source_release_and_processing_run_proven": False,
        "any_missing_batches_proven": False,
        "author_name_prefix_is_not_coast_model_fitness_proof": True,
        "individual_station_ids_coordinates_or_batch_start_ids_emitted": False,
        "source_original_data_persisted": False,
        "commercial_rights_approved": False,
        "cat_model_admitted": False,
    }
