#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, bounded EuroCropsV2.02 original GeoParquet preflight.

No network, no source rows in output, no model admission.
Requires optional pyarrow and shapely for original Parquet inspection.
"""
from __future__ import annotations

if __package__:
    from .eurocrops_codebook_qc_v0 import (
        Blocked as CodebookBlocked, _read_local, _read_rows, audit,
        MAP_HEADER, HCAT_HEADER, sample_mapping_coverage,
    )
else:
    from eurocrops_codebook_qc_v0 import (
        Blocked as CodebookBlocked, _read_local, _read_rows, audit,
        MAP_HEADER, HCAT_HEADER, sample_mapping_coverage,
    )

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
import re
import sys

JRC_BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv202/"
NUTS = frozenset("at be2 be3 bg cz de4 dea dk ee es fi fr ie iti1 nl pt si sk".split())
NAME = re.compile(r"([a-z][a-z0-9]*)_(20\d\d)\.parquet\Z")
REQUIRED = ("cropfield", "original_code", "area_ha")
GEOMETRY_COLUMNS = ("geometry", "geom")
MAX_FILE_BYTES = 2_500_000_000

class Blocked(ValueError):
    """Fail closed if source or schema evidence is absent."""


def asset_identity(path: Path) -> tuple[str, int, str]:
    match = NAME.fullmatch(path.name)
    if match is None or match[1] not in NUTS or not (2008 <= int(match[2]) <= 2023):
        raise Blocked("expected a listed gpqtv202 NUTS/year parquet, not stack/arbitrary file")
    if path.is_symlink() or not path.is_file():
        raise Blocked("original input absent or symlink")
    size = path.stat().st_size
    if size <= 8 or size > MAX_FILE_BYTES:
        raise Blocked("original input empty or over explicit size cap")
    with path.open("rb") as f:
        if f.read(4) != b"PAR1":
            raise Blocked("Parquet header missing")
        f.seek(-4, 2)
        if f.read(4) != b"PAR1":
            raise Blocked("Parquet footer missing")
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return match[1], int(match[2]), digest.hexdigest()


def geo_metadata(metadata: dict | None, names: list[str]) -> dict:
    if any(col not in names for col in REQUIRED):
        raise Blocked("required original fields missing")
    if not metadata or b"geo" not in metadata:
        raise Blocked("GeoParquet metadata missing, cannot assume EPSG")
    try:
        geo = json.loads(metadata[b"geo"].decode("utf-8"))
        primary = geo["primary_column"]
        if primary not in GEOMETRY_COLUMNS or primary not in names:
            raise Blocked("unexpected or absent original GeoParquet geometry column")
        geometry_details = geo["columns"][primary]
        if geometry_details.get("encoding") != "WKB":
            raise Blocked("original GeoParquet geometry is not explicitly WKB")
        crs = geometry_details["crs"]
        if isinstance(crs, str):
            is_3035 = crs.upper() == "EPSG:3035"
        elif isinstance(crs, dict):
            identity = crs.get("id", {})
            is_3035 = (str(identity.get("authority", "")).upper() == "EPSG"
                       and str(identity.get("code", "")) == "3035")
        else:
            is_3035 = False
    except (KeyError, TypeError, AttributeError, ValueError, UnicodeError) as exc:
        raise Blocked("invalid GeoParquet metadata") from exc
    if not is_3035:
        raise Blocked("not independently evidenced as EPSG:3035")
    return {"primary_geometry_column": primary, "geometry_encoding": "WKB",
            "crs": "EPSG:3035"}


def audit_rows(rows: list[dict], geometry_column: str = "geom") -> dict:
    if geometry_column not in GEOMETRY_COLUMNS:
        raise Blocked("unexpected original geometry column")
    try:
        from shapely import wkb
        from shapely.errors import GEOSException
    except ImportError as exc:
        raise Blocked("shapely required") from exc
    stats = {"sampled": 0, "missing_crop_code": 0, "duplicate_cropfield_in_sample": 0,
             "invalid_area_ha": 0, "invalid_or_empty_geometry": 0,
             "non_polygon_geometry": 0, "area_disagreement_over_5pct": 0}
    seen: set[str] = set()
    for row in rows:
        stats["sampled"] += 1
        field = row.get("cropfield")
        if field is None or str(field) in seen:
            stats["duplicate_cropfield_in_sample"] += 1
        else:
            seen.add(str(field))
        code = row.get("original_code")
        if not isinstance(code, str) or not code.strip():
            stats["missing_crop_code"] += 1
        area = row.get("area_ha")
        valid_area = (not isinstance(area, bool) and isinstance(area, (int, float))
                      and math.isfinite(area) and area > 0)
        if not valid_area:
            stats["invalid_area_ha"] += 1
        try:
            binary = row.get(geometry_column)
            geom = wkb.loads(bytes(binary)) if isinstance(binary, (bytes, bytearray, memoryview)) else None
            if geom is None or geom.is_empty or not geom.is_valid:
                stats["invalid_or_empty_geometry"] += 1
                continue
            if geom.geom_type not in ("Polygon", "MultiPolygon"):
                stats["non_polygon_geometry"] += 1
                continue
            if valid_area and abs(geom.area / 10000 - float(area)) / float(area) > 0.05:
                stats["area_disagreement_over_5pct"] += 1
        except (ValueError, TypeError, OverflowError, GEOSException):
            stats["invalid_or_empty_geometry"] += 1
    return stats


def sampled_row_positions(total_rows: int, max_rows: int, source_sha256: str) -> list[int]:
    """A reproducible bounded uniform sample across the WHOLE original file.

    The validated full-file SHA fixes the seed. Positions are neither returned
    in the public report nor treated as independent crop-area observations.
    This is a QA sample and does NOT establish full-source completeness.
    """
    if (type(total_rows) is not int or total_rows < 1 or
            type(max_rows) is not int or not 1 <= max_rows <= 5000 or
            not isinstance(source_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None):
        raise Blocked("invalid original row count, sample limit or source hash")
    n = min(total_rows, max_rows)
    rng = random.Random(int.from_bytes(
        hashlib.sha256(("EuroCropsV202-uniform-QA|" + source_sha256).encode("ascii")
                       ).digest(), "big"))
    return sorted(rng.sample(range(total_rows), n))


def read_spread_sample(
    parquet, positions: list[int], geometry_column: str = "geom"
) -> tuple[list[dict], int]:
    if geometry_column not in GEOMETRY_COLUMNS:
        raise Blocked("invalid source geometry column")
    """Retrieve selected global rows without loading any entire row group.

    Iterate only sampled row groups, reading batches capped at 512 rows.
    Metadata row-group counts MUST sum to the complete footer row count.
    """
    if not positions or len(positions) > 5000 or any(
        type(p) is not int or p < 0 for p in positions
    ) or positions != sorted(set(positions)):
        raise Blocked("invalid selected source sample positions")
    meta = parquet.metadata
    if not 1 <= meta.num_row_groups <= 20000 or meta.num_rows <= 0:
        raise Blocked("invalid or unbounded Parquet footer row groups")
    rows: list[dict] = []
    checked_start = 0
    selected_ptr = 0
    visited = 0
    for group_no in range(meta.num_row_groups):
        size = meta.row_group(group_no).num_rows
        if type(size) is not int or size < 0:
            raise Blocked("invalid original row-group length")
        next_start = checked_start + size
        local: list[int] = []
        while selected_ptr < len(positions) and positions[selected_ptr] < next_start:
            if positions[selected_ptr] < checked_start:
                raise Blocked("source sample offset moved backward")
            local.append(positions[selected_ptr] - checked_start)
            selected_ptr += 1
        if local:
            visited += 1
            batch_start = 0
            local_ptr = 0
            for batch in parquet.iter_batches(
                batch_size=512, columns=[*REQUIRED, geometry_column], row_groups=[group_no]
            ):
                if not 0 < batch.num_rows <= 512:
                    raise Blocked("invalid or oversized Parquet sample batch")
                stop = batch_start + batch.num_rows
                while local_ptr < len(local) and local[local_ptr] < stop:
                    row_offset = local[local_ptr] - batch_start
                    selected = batch.slice(row_offset, 1).to_pylist()
                    if len(selected) != 1 or not isinstance(selected[0], dict):
                        raise Blocked("incomplete original Parquet sample row")
                    rows.append(selected[0])
                    local_ptr += 1
                batch_start = stop
                if local_ptr == len(local):
                    break
            if local_ptr != len(local):
                raise Blocked("original Parquet row group shorter than footer claims")
        checked_start = next_start
    if (checked_start != meta.num_rows or selected_ptr != len(positions) or
            len(rows) != len(positions)):
        raise Blocked("Parquet row group totals or sampled rows inconsistent")
    return rows, visited


def footer_statistics_quality(parquet, geometry_column: str) -> dict:
    """Original-source Parquet footer QA only: statistics are not row proofs.

    In particular, one zero minimum area can hide in a large source even if a
    sample of 512 is clean. Distinguish missing footer stats from clean stats.
    """
    if geometry_column not in GEOMETRY_COLUMNS:
        raise Blocked("footer cannot select an unreviewed geometry field")
    wanted = ("cropfield", "original_code", geometry_column, "area_ha")
    meta = parquet.metadata
    if not 1 <= meta.num_row_groups <= 20000:
        raise Blocked("invalid row group count for footer statistics")
    nulls: dict[str, int | None] = {name: 0 for name in wanted}
    areas_min: list[float] = []
    areas_max: list[float] = []
    complete_areas = True
    for group_no in range(meta.num_row_groups):
        group = meta.row_group(group_no)
        columns = {}
        for index in range(group.num_columns):
            col = group.column(index)
            name = col.path_in_schema
            if name in wanted:
                if name in columns:
                    raise Blocked("duplicate original Parquet footer column")
                columns[name] = col
        if set(columns) != set(wanted):
            raise Blocked("footer row group lacks required original crop fields")
        for name in wanted:
            statistics = columns[name].statistics
            reported = None if statistics is None else statistics.null_count
            if reported is None:
                nulls[name] = None
            elif type(reported) is not int or reported < 0:
                raise Blocked("malformed original footer null statistic")
            elif nulls[name] is not None:
                nulls[name] += reported
        area_stats = columns["area_ha"].statistics
        if area_stats is None or not area_stats.has_min_max:
            complete_areas = False
            continue
        try:
            minimum = float(area_stats.min)
            maximum = float(area_stats.max)
        except (ValueError, TypeError, OverflowError) as exc:
            raise Blocked("invalid original footer area min/max types") from exc
        if not (math.isfinite(minimum) and math.isfinite(maximum)) or minimum > maximum:
            raise Blocked("invalid original footer area min/max values")
        areas_min.append(minimum)
        areas_max.append(maximum)
    return {
        "footer_area_ha_minimum_if_all_groups_have_stats":
            min(areas_min) if complete_areas and areas_min else None,
        "footer_area_ha_maximum_if_all_groups_have_stats":
            max(areas_max) if complete_areas and areas_max else None,
        "footer_area_statistics_complete": complete_areas,
        "any_row_group_footer_min_area_nonpositive": any(x <= 0 for x in areas_min),
        "footer_null_counts_if_all_groups_have_stats": nulls,
        "footer_stats_are_original_provider_claims_not_row_validation": True,
        "footer_quality_does_not_establish_real_polygon_area_or_geometry_validity": True,
    }


def scan_full_area_column(parquet) -> dict:
    """Exact-value audit of one original DOUBLE column, without field identities.

    Optional because a real source file must first have a pinned full SHA-256.
    The area column is read in small batches, never the geometry or whole row
    group; this does NOT check overlaps, actual polygons or insured exposure.
    """
    total_rows = parquet.metadata.num_rows
    if type(total_rows) is not int or not 1 <= total_rows <= 50000000:
        raise Blocked("full area scan exceeds reviewed row budget")
    count = 0
    zero_count = 0
    negative_count = 0
    nonfinite_count = 0
    null_count = 0
    wrong_type_count = 0
    positive_min = None
    max_area = None
    for batch in parquet.iter_batches(batch_size=4096, columns=["area_ha"]):
        if not 0 < batch.num_rows <= 4096:
            raise Blocked("full area scan produced an invalid batch size")
        values = batch.column(0).to_pylist()
        if len(values) != batch.num_rows:
            raise Blocked("area column batch length drift")
        for raw in values:
            count += 1
            if raw is None:
                null_count += 1
            elif isinstance(raw, bool) or not isinstance(raw, (int, float)):
                wrong_type_count += 1
            else:
                try:
                    area = float(raw)
                except (ValueError, TypeError, OverflowError):
                    wrong_type_count += 1
                    continue
                if not math.isfinite(area):
                    nonfinite_count += 1
                elif area < 0:
                    negative_count += 1
                elif area == 0:
                    zero_count += 1
                else:
                    positive_min = (
                        area if positive_min is None else min(positive_min, area)
                    )
                    max_area = area if max_area is None else max(max_area, area)
            if count > total_rows:
                raise Blocked("full area scan exceeds Parquet footer row count")
    if count != total_rows:
        raise Blocked("full area scan shorter than Parquet footer row count")
    return {
        "scan_scope": "original full area_ha attribute only",
        "original_area_rows_scanned": count,
        "original_area_ha_zero_count": zero_count,
        "original_area_ha_negative_count": negative_count,
        "original_area_ha_nonfinite_count": nonfinite_count,
        "original_area_ha_null_count": null_count,
        "original_area_ha_wrong_type_count": wrong_type_count,
        "original_area_ha_minimum_positive_value": positive_min,
        "original_area_ha_maximum_positive_value": max_area,
        "all_original_geometry_and_topology_validated": False,
        "sum_of_parcel_areas_is_not_unique_cultivated_area": True,
    }


def inspect_local(
    path: Path, expected_sha256: str, max_rows: int = 512,
    mapping: Path | None = None, mapping_git_blob_sha1: str | None = None,
    hierarchy: Path | None = None, hierarchy_git_blob_sha1: str | None = None,
    scan_full_area: bool = False,
) -> dict:
    if max_rows < 1 or max_rows > 5000:
        raise Blocked("sample size must be 1..5000")
    codebooks = (mapping, mapping_git_blob_sha1, hierarchy, hierarchy_git_blob_sha1)
    if any(value is not None for value in codebooks) and not all(
        value is not None for value in codebooks
    ):
        raise Blocked("both original codebooks and their pinned Git blob SHA1s required")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise Blocked("explicit expected original SHA256 required")
    region, year, actual = asset_identity(path)
    if actual != expected_sha256:
        raise Blocked("original source SHA256 mismatch")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise Blocked("install optional pyarrow to inspect original file") from exc
    parquet = pq.ParquetFile(path)
    geo = geo_metadata(parquet.schema_arrow.metadata, parquet.schema_arrow.names)
    footer_quality = footer_statistics_quality(parquet, geo["primary_geometry_column"])
    positions = sampled_row_positions(parquet.metadata.num_rows, max_rows, actual)
    rows, sampled_groups = read_spread_sample(
        parquet, positions, geo["primary_geometry_column"]
    )
    stats = audit_rows(rows, geo["primary_geometry_column"])
    full_area_scan = scan_full_area_column(parquet) if scan_full_area else None
    mapping_coverage = None
    if mapping is not None and hierarchy is not None:
        try:
            mapping_raw = _read_local(mapping)
            hierarchy_raw = _read_local(hierarchy)
            codebook_report = audit(
                mapping_raw, mapping_git_blob_sha1,
                hierarchy_raw, hierarchy_git_blob_sha1,
            )
            original_mapping_rows = _read_rows(
                mapping_raw, mapping_git_blob_sha1, MAP_HEADER,
            )
            original_hierarchy_rows = _read_rows(
                hierarchy_raw, hierarchy_git_blob_sha1, HCAT_HEADER,
            )
            mapping_coverage = sample_mapping_coverage(
                rows, region, original_mapping_rows, original_hierarchy_rows,
            )
            mapping_coverage["codebook_missing_hcat4_reference_count"] = (
                codebook_report["unresolved_hcat4_reference_count"]
            )
            mapping_coverage["mapping_git_blob_sha1"] = mapping_git_blob_sha1
            mapping_coverage["hierarchy_git_blob_sha1"] = hierarchy_git_blob_sha1
        except CodebookBlocked as exc:
            raise Blocked("original taxonomy preflight failed: " + str(exc)) from exc
    return {
        "profile": "eurocrops-v202-local-source-qc-v0",
        "source_candidate_id": "eu.jrc.eurocropsv2.gsa-parcels",
        "source_url": JRC_BASE + path.name,
        "source_filename": path.name,
        "source_region": region, "source_year": year,
        "source_sha256": actual, "sha256_matched_operator_pin": True,
        "file_bytes": path.stat().st_size,
        "parquet_total_rows_from_footer": parquet.metadata.num_rows,
        "parquet_row_groups": parquet.metadata.num_row_groups,
        "schema_fields": list(parquet.schema_arrow.names),
        "geo": geo, "pyarrow_version": pa.__version__,
        "sample": stats,
        "original_footer_column_quality": footer_quality,
        "full_original_area_ha_scan": full_area_scan,
        "full_original_area_ha_scan_checked": full_area_scan is not None,
        "sample_selection": "source_sha256_seeded_uniform_without_replacement",
        "sampled_row_groups": sampled_groups,
        "sampled_positions_exported": False,
        "sample_is_full_dataset": stats["sampled"] == parquet.metadata.num_rows,
        "sample_represents_independently_verified_source_coverage": False,
        "sample_taxonomy_crosswalk": mapping_coverage,
        "taxonomy_crosswalk_checked": mapping_coverage is not None,
        "research_qc_only": True,
        "rights_and_scientific_admission": "NOT_REVIEWED_NOT_ADMITTED",
        "loss_or_insurer_exposure_model_ready": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--sample-rows", type=int, default=512)
    parser.add_argument("--scan-full-area", action="store_true",
                        help="opt-in exact original area_ha column-only scan")
    parser.add_argument("--mapping", type=Path, help="locally obtained original eurocrops.csv")
    parser.add_argument("--mapping-git-blob-sha1", help="source-pinned Git blob SHA1")
    parser.add_argument("--hierarchy", type=Path, help="locally obtained original hcat4.csv")
    parser.add_argument("--hierarchy-git-blob-sha1", help="source-pinned Git blob SHA1")
    args = parser.parse_args(argv)
    try:
        result = inspect_local(
            args.input, args.expected_sha256, args.sample_rows,
            args.mapping, args.mapping_git_blob_sha1,
            args.hierarchy, args.hierarchy_git_blob_sha1,
            scan_full_area=args.scan_full_area,
        )
    except (Blocked, OSError, RuntimeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
