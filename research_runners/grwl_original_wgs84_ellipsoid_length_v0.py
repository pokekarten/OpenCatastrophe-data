# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only GRWL 2026 original WGS84 ellipsoid-length source experiment.

Uses the shortest Karney geodesic between consecutive original vertices,
handling antimeridian transitions. This does NOT prove river feature identity,
hydrologic validity, or the publisher's original SHAPE_LENG algorithm.
Only aggregate results are printed. No original data are stored in Git.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct
import tempfile
import zipfile

from research_runners.grwl_original_aggregate_semantic_diff_v0 import (
    OriginalZipError, PINNED_SOURCE_SHA256, SOURCE_FILES, read_dbf_semantics,
)
from research_runners.grwl_original_oriented_vertex_metric_v0 import (
    read_original_polylines,
)
from research_runners.grwl_original_shape_leng_audit_v0 import (
    _distribution,
    has_original_longitude_jump_across_dateline,
    read_keyed_source_lengths,
    spherical_centerline_length_km,
)
from research_runners.grwl_original_zip_structure_preflight_v0 import inspect_original_zip
from research_runners.grwl_trusted_original_byte_proof_v0 import download_fixed

SCHEMA = "opencatastrophe-grwl-2026-original-wgs84-ellipsoid-length-v0"
EXPECTED_SOURCE_FEATURES = 42_077
ORIGINAL_RELEASE = "2026"
GEODESIC_VERSION_PIN = "2.1"
RELATIVE_ERROR_THRESHOLDS = (0.0001, 0.001, 0.01, 0.05, 0.10)


def _wgs84_geodesic():
    """The dependency is deliberately isolated from normal repository CI."""
    try:
        from geographiclib import __version__
        from geographiclib.geodesic import Geodesic
    except ImportError as exc:
        raise OriginalZipError(
            "geographiclib dependency required for reviewed ellipsoid audit") from exc
    if __version__ != GEODESIC_VERSION_PIN:
        raise OriginalZipError("unexpected GeographicLib version")
    return Geodesic.WGS84


def ellipsoid_centerline_length_km(shape, geodesic):
    """Sum shortest WGS84 ellipsoid geodesics within each original SHP part."""
    parts, xy = shape
    if not parts:
        return 0.0
    if len(xy) != 16 * sum(parts):
        raise OriginalZipError("inconsistent original XY byte extent")
    total_m = 0.0
    offset = 0
    for part_points in parts:
        if part_points < 2:
            raise OriginalZipError("one original SHP part has fewer than two vertices")
        lon1, lat1 = struct.unpack_from("<dd", xy, offset * 16)
        for i in range(offset + 1, offset + part_points):
            lon2, lat2 = struct.unpack_from("<dd", xy, i * 16)
            distance_m = geodesic.Inverse(
                lat1, lon1, lat2, lon2, geodesic.DISTANCE)["s12"]
            if not math.isfinite(distance_m) or distance_m < 0:
                raise OriginalZipError("invalid WGS84 ellipsoid inverse distance")
            total_m += distance_m
            lon1, lat1 = lon2, lat2
        offset += part_points
    result = total_m / 1000.0
    if not math.isfinite(result):
        raise OriginalZipError("nonfinite original ellipsoid length")
    return result


def compare_ellipsoid_reference(ids, source_lengths, source_shapes, geodesic):
    """Only anonymous counts/distributions; never source keys, values or points."""
    if (len(ids) != EXPECTED_SOURCE_FEATURES
            or len(source_lengths) != len(ids)
            or len(source_shapes) != len(ids)
            or len(set(ids)) != len(ids)):
        raise OriginalZipError("original GRWL row count or OBJECTID uniqueness gate")
    all_ratios = []
    all_relative_errors = []
    all_spherical_vs_ellipsoid = []
    by_dateline = {False: [], True: []}
    threshold_counts = Counter()
    threshold_crossing = Counter()
    threshold_other = Counter()
    dateline_count = 0
    no_ellipsoid_length_count = 0
    for source_km, geometry in zip(source_lengths, source_shapes):
        if not math.isfinite(source_km) or source_km < 0:
            raise OriginalZipError("invalid original SHAPE_LENG value")
        crossing = has_original_longitude_jump_across_dateline(geometry)
        if crossing:
            dateline_count += 1
        exact_km = ellipsoid_centerline_length_km(geometry, geodesic)
        if exact_km <= 0:
            no_ellipsoid_length_count += 1
            continue
        ratio = source_km / exact_km
        if not math.isfinite(ratio):
            raise OriginalZipError("nonfinite original source-to-ellipsoid ratio")
        error = abs(ratio - 1)
        all_ratios.append(ratio)
        all_relative_errors.append(error)
        by_dateline[crossing].append(ratio)
        for threshold in RELATIVE_ERROR_THRESHOLDS:
            name = str(threshold)
            if error > threshold:
                threshold_counts[name] += 1
                (threshold_crossing if crossing else threshold_other)[name] += 1
        spherical = spherical_centerline_length_km(geometry)
        if spherical > 0:
            all_spherical_vs_ellipsoid.append(spherical / exact_km)
    return {
        "schema": SCHEMA,
        "original_release": ORIGINAL_RELEASE,
        "verified_unique_original_objectid_candidates": len(ids),
        "source_shape_leng_over_wgs84_ellipsoid_km": _distribution(all_ratios),
        "abs_relative_source_vs_wgs84_ellipsoid": _distribution(all_relative_errors),
        "spherical_haversine_over_wgs84_ellipsoid": _distribution(
            all_spherical_vs_ellipsoid),
        "source_over_ellipsoid_ratio_dateline": _distribution(by_dateline[True]),
        "source_over_ellipsoid_ratio_non_dateline": _distribution(by_dateline[False]),
        "original_features_with_longitude_jump_above_180_degrees": dateline_count,
        "original_features_with_zero_ellipsoid_length": no_ellipsoid_length_count,
        "features_with_relative_error_above": {
            str(t): threshold_counts[str(t)] for t in RELATIVE_ERROR_THRESHOLDS
        },
        "dateline_features_with_relative_error_above": {
            str(t): threshold_crossing[str(t)] for t in RELATIVE_ERROR_THRESHOLDS
        },
        "other_features_with_relative_error_above": {
            str(t): threshold_other[str(t)] for t in RELATIVE_ERROR_THRESHOLDS
        },
        "geodesic_method": "GeographicLib_2.1_Karney_shortest_WGS84_ellipsoid_inverse_per_original_segment",
        "geodesic_ellipsoid_semiaxis_a_metres": 6378137.0,
        "geodesic_ellipsoid_flattening": "1/298.257223563",
        "source_method_or_original_units_independently_certified": False,
        "source_geographic_feature_identity_verified": False,
        "antimeridian_source_length_cause_proven": False,
        "flood_stage_or_insured_loss_calculated": False,
        "model_input_admitted": False,
        "production_database_modified": False,
        "original_objectids_or_coordinates_published": False,
    }


def original_ellipsoid_audit():
    # The 2018 angular-degree proof is already supported by a separate
    # independently SHA-pinned original run. Re-fetch only the 2026 original
    # for this distinct geodesic test: avoid unnecessary provider requests.
    geodesic = _wgs84_geodesic()
    with tempfile.TemporaryDirectory(prefix="grwl-original-wgs84-geodesic-") as scratch:
        path = Path(scratch) / SOURCE_FILES[ORIGINAL_RELEASE][0]
        downloaded = download_fixed(ORIGINAL_RELEASE, path)
        receipt = inspect_original_zip(path, ORIGINAL_RELEASE)
        required_sha = PINNED_SOURCE_SHA256[ORIGINAL_RELEASE]
        if (downloaded["independent_original_zip_sha256"] != required_sha
                or receipt["independently_computed_original_zip_sha256"] != required_sha):
            raise OriginalZipError("source 2026 original ZIP SHA-256 does not match trusted pin")
        with zipfile.ZipFile(path) as archive:
            fields = read_dbf_semantics(archive)
            ids, source_lengths = read_keyed_source_lengths(archive, fields)
            shapes, total_points = read_original_polylines(archive)
        return {
            "original_source_release": ORIGINAL_RELEASE,
            "verified_original_zip_sha256": required_sha,
            "original_point_count": total_points,
            "comparison": compare_ellipsoid_reference(
                ids, source_lengths, shapes, geodesic),
            "source_bytes_in_output": False,
            "source_data_admitted": False,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="explicit original fixed-Zenodo-source request (trusted main only)")
    args = parser.parse_args(argv)
    if not args.live:
        parser.print_help()
        return 2
    try:
        data = original_ellipsoid_audit()
    except OriginalZipError as exc:
        parser.error(str(exc))
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
