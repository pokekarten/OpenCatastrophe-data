#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent CRS and interpreted polygon-validity checks on original HANZE 2024.

Requires independently version-pinned optional libraries pyproj, shapely and
pyshp in the source-only CI job. Prior exact original SHA and safe ZIP/polygon
record preflight is mandatory. Return only aggregate metadata: no polygons,
vertices, region codes, names, or per-feature geometry/diagnostic details.

Pyshp's shape-to-GeoJSON interpretation and GEOS is_valid test diagnose
self-intersections and ring arrangement. This does NOT verify inter-feature
topological coverage/gaps, hazard footprints, commercial geodata rights,
insurance properties, TIV or observed flood damage.
"""
from __future__ import annotations

from collections import Counter
import io
import math
import re
import zipfile

if __package__:
    from .hanze_2024_original_polygon_integrity_v0 import inspect_polygon_records
    from .hanze_regions2024_geometry_zip_audit_v0 import RegionArchiveError
else:
    from hanze_2024_original_polygon_integrity_v0 import inspect_polygon_records
    from hanze_regions2024_geometry_zip_audit_v0 import RegionArchiveError

EPSG_REFERENCE = 3035
MAX_GEOMETRIES = 3000
MAX_INVALID_FAMILIES = 20


def _library():
    try:
        import pyproj
        import shapely
        import shapefile
        from shapely.geometry import shape as shapely_shape
        from shapely.validation import explain_validity
    except ImportError as exc:
        raise RegionArchiveError("independent CRS/geometry validation libraries absent") from exc
    return pyproj, shapely, shapefile, shapely_shape, explain_validity


def _invalid_family(reason: str) -> str:
    """Only the reason *class*, never coordinates or feature IDs."""
    if type(reason) is not str or not reason:
        raise RegionArchiveError("unexpected empty geometry validation result")
    stem = reason.split("[", 1)[0].strip()
    if not re.fullmatch(r"[A-Za-z0-9 _().-]{1,80}", stem):
        return "Unclassified reason"
    return stem


def audit_independent_crs_and_topology(
    archive: bytes, *, expected_sha256: str, max_geometries: int = MAX_GEOMETRIES,
) -> dict:
    if type(max_geometries) is not int or not 1 <= max_geometries <= MAX_GEOMETRIES:
        raise RegionArchiveError("bounded geometry review limit invalid")
    original = inspect_polygon_records(archive, expected_sha256=expected_sha256)
    pyproj, shapely, shapefile, shapely_shape, explain_validity = _library()
    with zipfile.ZipFile(io.BytesIO(archive), "r") as zf:
        parts = {}
        for item in zf.infolist():
            ext = item.filename.rsplit(".", 1)[-1].lower()
            if ext in ("shp", "shx", "dbf", "prj"):
                if ext in parts:
                    raise RegionArchiveError("duplicate source regional geometry component")
                parts[ext] = zf.read(item)
    if set(parts) != {"shp", "shx", "dbf", "prj"}:
        raise RegionArchiveError("missing exact source geometry or projection")
    try:
        original_wkt = parts["prj"].decode("utf-8-sig")
        original_crs = pyproj.CRS.from_wkt(original_wkt)
        official = pyproj.CRS.from_epsg(EPSG_REFERENCE)
        # EPSG identification is a result of an independent PROJ parser,
        # not guessed from the name 'ETRS_1989_LAEA'.
        identified = original_crs.to_epsg(min_confidence=70)
        matches_reference = bool(original_crs.equals(official, ignore_axis_order=True))
        # Legacy ESRI WKT1 may use a named ETRS89 datum whereas modern
        # EPSG:3035 uses a datum ensemble. A strict full-object CRS.equals
        # can be False even if PROJ independently identifies EPSG:3035.
        # Match the original projection method, numerical parameters,
        # GRS80 ellipsoid and axis units against the official CRS.
        def parameter_signature(crs):
            op = crs.coordinate_operation
            return (
                op.method_name,
                tuple(sorted((p.name, round(float(p.value), 8), p.unit_name.lower())
                             for p in op.params)),
                round(float(crs.ellipsoid.semi_major_metre), 7),
                round(float(crs.ellipsoid.inverse_flattening), 9),
                tuple(x.unit_name.lower() for x in crs.axis_info),
            )
        epsg3035_parameter_ellipsoid_match = (
            parameter_signature(original_crs) == parameter_signature(official))
        axes = [info.unit_name for info in original_crs.axis_info]
    except (ValueError, UnicodeError, RuntimeError) as exc:
        raise RegionArchiveError("independent source CRS cannot be parsed") from exc
    if not original_crs.is_projected or not axes:
        raise RegionArchiveError("original regional coordinate system is not projected")
    declared = original["projection_declaration"]
    if declared["wkt_header_family"] != "PROJCS" or "Meter" not in declared["declared_unit_names_unverified"]:
        raise RegionArchiveError("WKT structural declaration disagrees with independent interpretation")
    try:
        reader = shapefile.Reader(shp=io.BytesIO(parts["shp"]),
                                  shx=io.BytesIO(parts["shx"]),
                                  dbf=io.BytesIO(parts["dbf"]))
        feature_count = len(reader)
        if feature_count != original["polygon_records"] + original["null_shape_records"]:
            raise RegionArchiveError("pyshp independently read different original feature count")
        if feature_count > max_geometries:
            raise RegionArchiveError("independent geometry validation exceeds bound")
        stats = Counter()
        invalid_reasons = Counter()
        for i in range(feature_count):
            geometry = reader.shape(i)
            stats["source_features"] += 1
            if geometry.shapeType == 0:
                stats["null_shapes"] += 1
                continue
            if geometry.shapeType != 5:
                raise RegionArchiveError("source region has non-Polygon geometry")
            interpreted = shapely_shape(geometry.__geo_interface__)
            if interpreted.geom_type not in ("Polygon", "MultiPolygon"):
                raise RegionArchiveError("GEOS interpreted incompatible original source shape")
            stats["polygons" if interpreted.geom_type == "Polygon" else "multipolygons"] += 1
            if interpreted.is_empty:
                stats["empty_geometries"] += 1
            elif not math.isfinite(interpreted.area) or interpreted.area <= 0:
                stats["nonpositive_or_nonfinite_areas"] += 1
            if interpreted.is_valid:
                stats["geos_valid_geometries"] += 1
            else:
                stats["geos_invalid_geometries"] += 1
                invalid_reasons[_invalid_family(explain_validity(interpreted))] += 1
                if len(invalid_reasons) > MAX_INVALID_FAMILIES:
                    raise RegionArchiveError("unexpected number of geometry error classes")
        reader.close()
    except (OSError, IndexError, ValueError, TypeError, RuntimeError) as exc:
        raise RegionArchiveError("independent original polygon geometry parser failed") from exc
    if stats["source_features"] != feature_count:
        raise RegionArchiveError("source geometry integrity count drift")
    if stats["geos_valid_geometries"] + stats["geos_invalid_geometries"] + stats["null_shapes"] != feature_count:
        raise RegionArchiveError("incomplete interpreted source geometry validation")
    return {
        "evidence_stage": "ORIGINAL_HANZE_2024_INDEPENDENT_CRS_GEOMETRY_VALIDITY_ONLY",
        "original_source_sha256_verified": original["original_zip_sha256_verified"],
        "independent_crs_library": "pyproj",
        "independent_geometric_library": "shapely-GEOS",
        "source_shape_interpretation_library": "pyshp",
        "versions": {"pyproj": pyproj.__version__, "shapely": shapely.__version__,
                     "pyshp": shapefile.__version__},
        "source_projected_crs": bool(original_crs.is_projected),
        "epsg_code_identified_by_pyproj": identified,
        "equals_official_epsg3035_ignoring_axis_order": matches_reference,
        "epsg3035_projection_parameters_ellipsoid_axes_match":
            epsg3035_parameter_ellipsoid_match,
        "legacy_wkt_datum_and_modern_epsg_ensemble_equivalence_not_proven":
            not matches_reference,
        "coordinate_axis_unit_names": axes,
        "source_feature_count": feature_count,
        "validity": {
            key: stats[key] for key in (
                "polygons", "multipolygons", "null_shapes", "empty_geometries",
                "nonpositive_or_nonfinite_areas", "geos_valid_geometries",
                "geos_invalid_geometries",
            )
        },
        "invalid_reason_family_counts": dict(sorted(invalid_reasons.items())),
        "cross_feature_topology_or_spatial_gaps_verified": False,
        "verified_inundation_extent_or_depth": False,
        "dfo_hanze_common_event_identity_proven": False,
        "original_coordinates_or_region_id_exported": False,
        "any_insured_risk_or_loss_calculated": False,
        "commercial_geometry_rights_approved": False,
        "model_input_admitted": False,
    }
