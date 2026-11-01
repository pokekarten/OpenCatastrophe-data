#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""GDAL/Fiona interpretation cross-check for publisher-byte-verified HANZE 2024.

Original administrative region ZIP stays in memory. Independently GDAL/Fiona
constructs the polygon (and holes) semantics, Shapely/GEOS reports only
aggregate validity. Compare with pinned pyshp interpretation, not source IDs,
raw coordinates, region names or per-geometry error locations.

An invalid geometry in two readers is stronger evidence, but still not
permission to auto-repair, assume regional inundation, redistribute proprietary
geodata or attribute catastrophe losses to insurers.
"""
from __future__ import annotations

from collections import Counter
import math
import re

if __package__:
    from .hanze_2024_original_polygon_integrity_v0 import inspect_polygon_records
    from .hanze_2024_independent_crs_geos_audit_v0 import _invalid_family
    from .hanze_regions2024_geometry_zip_audit_v0 import RegionArchiveError
else:
    from hanze_2024_original_polygon_integrity_v0 import inspect_polygon_records
    from hanze_2024_independent_crs_geos_audit_v0 import _invalid_family
    from hanze_regions2024_geometry_zip_audit_v0 import RegionArchiveError

MAX_FEATURES = 3000


def validate_original_with_gdal_fiona(archive: bytes, *, expected_sha256: str) -> dict:
    prior = inspect_polygon_records(archive, expected_sha256=expected_sha256)
    try:
        import fiona
        from fiona.io import ZipMemoryFile
        import shapely
        from shapely.geometry import shape as shapely_shape
        from shapely.validation import explain_validity
    except ImportError as exc:
        raise RegionArchiveError("Fiona/GDAL independent geometry audit not installed") from exc
    counts = Counter()
    invalid_reason_families = Counter()
    geo_types = Counter()
    gdal_crs_available = False
    try:
        with ZipMemoryFile(archive) as zipped:
            with zipped.open() as source:
                if source.driver != "ESRI Shapefile":
                    raise RegionArchiveError("unexpected original GDAL source vector driver")
                n = len(source)
                if n != prior["polygon_records"]+prior["null_shape_records"] or n > MAX_FEATURES:
                    raise RegionArchiveError("GDAL original feature count is inconsistent or oversized")
                gdal_crs_available = bool(source.crs_wkt)
                schema_fields = set(source.schema.get("properties", {}))
                if not {"Code", "Name"} <= schema_fields:
                    raise RegionArchiveError("GDAL did not expose original region Code/Name fields")
                for feature in source:
                    counts["features"] += 1
                    raw_geom = feature.geometry
                    if raw_geom is None:
                        counts["null_geometries"] += 1
                        continue
                    geom = shapely_shape(raw_geom)
                    if geom.geom_type not in ("Polygon", "MultiPolygon"):
                        raise RegionArchiveError("GDAL interpreted non-polygon source geometry")
                    geo_types[geom.geom_type] += 1
                    if geom.is_empty:
                        counts["empty_geometries"] += 1
                    if not math.isfinite(geom.area) or geom.area <= 0:
                        counts["nonpositive_area"] += 1
                    if geom.is_valid:
                        counts["geos_valid"] += 1
                    else:
                        counts["geos_invalid"] += 1
                        invalid_reason_families[_invalid_family(explain_validity(geom))] += 1
                        if len(invalid_reason_families) > 30:
                            raise RegionArchiveError("unbounded original GDAL geometry error classes")
    except RegionArchiveError:
        raise
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        raise RegionArchiveError("independent GDAL/Fiona source geometry read failed") from exc
    if (counts["features"] != n
        or counts["geos_valid"]+counts["geos_invalid"]+counts["null_geometries"] != n):
        raise RegionArchiveError("GDAL original geometry coverage did not reconcile")
    return {
        "evidence_stage": "HANZE_2024_ORIGINAL_GDAL_FIONA_GEOS_AGGREGATE_REVIEW_ONLY",
        "original_zip_sha256_verified": prior["original_zip_sha256_verified"],
        "gdal_version": ".".join(str(v) for v in fiona.gdal_version),
        "fiona_version": fiona.__version__,
        "shapely_version": shapely.__version__,
        "driver": "ESRI Shapefile",
        "source_wkt_readable_by_gdal": gdal_crs_available,
        "read_feature_count": counts["features"],
        "type_counts": {name: geo_types[name] for name in ("Polygon","MultiPolygon")},
        "validity_counts": {name: counts[name] for name in (
            "geos_valid", "geos_invalid", "empty_geometries",
            "null_geometries", "nonpositive_area",
        )},
        "invalid_reason_family_counts": dict(sorted(invalid_reason_families.items())),
        "original_geometry_bytes_or_region_ids_exported": False,
        "automatic_geometry_makevalid_performed": False,
        "peril_hazard_footprints_observed": False,
        "cross_feature_polygon_coverage_or_gap_validated": False,
        "underlying_polygon_commercial_rights_approved": False,
        "model_input_admitted": False,
    }
