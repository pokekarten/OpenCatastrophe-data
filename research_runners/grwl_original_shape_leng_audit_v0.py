# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""GRWL original SHAPE_LENG paired-value and spherical-centerline audit.

Exactly two SHA-256-pinned, provider-verified original ZIPs; temporary bytes only.
No original attribute value, individual OBJECTID or geometry enters the receipt.
Statistics are diagnostic, not a validation of source length calculation method.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import struct
import tempfile
import zipfile

from research_runners.grwl_original_aggregate_semantic_diff_v0 import (
    PINNED_SOURCE_SHA256, OriginalZipError, SOURCE_FILES, _member, _normalized,
    _read_exact, read_dbf_semantics,
)
from research_runners.grwl_original_oriented_vertex_metric_v0 import (
    _haversine_metres, read_original_polylines,
)
from research_runners.grwl_original_zip_structure_preflight_v0 import inspect_original_zip
from research_runners.grwl_trusted_original_byte_proof_v0 import download_fixed

SCHEMA = "opencatastrophe-grwl-shape-leng-source-recalculation-audit-v0"
RELATIVE_DELTA_THRESHOLDS = (1e-9, 1e-6, 1e-4, 0.01, 0.1)
EARTH_LENGTH_APPROXIMATION = "WGS84_vertices_spherical_haversine_km_not_ellipsoidal"
MAX_FEATURES = 60_000


def read_keyed_source_lengths(archive: zipfile.ZipFile, dbf_metadata):
    """Read the two numeric DBF columns; cross-check each OBJECTID hash."""
    fields = dbf_metadata["fields"]
    offsets = {}
    start = 1
    for name, kind, width in fields:
        offsets[name] = (start, width, kind)
        start += width
    if ("OBJECTID" not in offsets or "SHAPE_LENG" not in offsets
            or offsets["OBJECTID"][2] != "N"
            or offsets["SHAPE_LENG"][2] not in ("F", "N")):
        raise OriginalZipError("source DBF requires numeric OBJECTID and SHAPE_LENG")

    info = _member(archive, ".dbf")
    expected = dbf_metadata["field_value_hashes_by_ordinal"]["OBJECTID"]
    n = dbf_metadata["record_count"]
    if not 1 <= n <= MAX_FEATURES:
        raise OriginalZipError("source DBF feature limit")
    ids, lengths = [], []
    with archive.open(info, "r") as stream:
        header = _read_exact(stream, 32)
        header_len, record_len = struct.unpack_from("<HH", header, 8)
        actual_n = struct.unpack_from("<I", header, 4)[0]
        if (actual_n != n or record_len != start
                or header_len < 65 or header_len + n * record_len > info.file_size):
            raise OriginalZipError("original DBF metadata/row bounds disagree")
        _read_exact(stream, header_len - 32)
        for i in range(n):
            row = _read_exact(stream, record_len)
            if row[:1] != b" ":
                raise OriginalZipError("deleted original DBF row rejected")
            key_off, key_width, key_kind = offsets["OBJECTID"]
            val_off, val_width, val_kind = offsets["SHAPE_LENG"]
            raw_key = _normalized(row[key_off:key_off + key_width], key_kind)
            if raw_key == b"<null>":
                raise OriginalZipError("null source OBJECTID")
            key_hash = hashlib.sha256(raw_key).digest()
            if key_hash != expected[i]:
                raise OriginalZipError("DBF OBJECTID mismatch against original semantic gate")
            raw_val = _normalized(row[val_off:val_off + val_width], val_kind)
            if raw_val == b"<null>":
                raise OriginalZipError("null SHAPE_LENG must be reviewed")
            val = float(Decimal(raw_val.decode("ascii")))
            if not math.isfinite(val) or val < 0:
                raise OriginalZipError("negative/non-finite SHAPE_LENG")
            ids.append(key_hash)
            lengths.append(val)
        if stream.read(2) not in (b"", b"\x1a"):
            raise OriginalZipError("unexpected trailing original DBF content")
    if len(set(ids)) != len(ids):
        raise OriginalZipError("ambiguous duplicated source OBJECTID")
    return ids, lengths


def spherical_centerline_length_km(shape):
    """Sum WGS84 vertex-to-vertex spherical distances along each separate part."""
    parts, xy = shape
    if not parts:
        return 0.0
    if len(xy) != 16 * sum(parts):
        raise OriginalZipError("inconsistent SHP part/vertex byte lengths")
    total = 0.0
    offset = 0
    for part_size in parts:
        if part_size < 2:
            raise OriginalZipError("polyline part has fewer than two vertices")
        previous = struct.unpack_from("<dd", xy, offset * 16)
        for idx in range(offset + 1, offset + part_size):
            nxt = struct.unpack_from("<dd", xy, idx * 16)
            total += _haversine_metres(previous, nxt)
            previous = nxt
        offset += part_size
    answer = total / 1_000.0
    if not math.isfinite(answer):
        raise OriginalZipError("nonfinite approximate spherical length")
    return answer


def planar_original_wgs84_length_in_degrees(shape):
    """Simple 2-D Euclidean lon/lat length, direct source degrees, no dateline wrap.

    This control deliberately uses the original projected-on-a-plane coordinate
    representation. It is *not* a physical ground distance in kilometres.
    """
    parts, xy = shape
    if not parts:
        return 0.0
    if len(xy) != 16 * sum(parts):
        raise OriginalZipError("invalid original planar degree SHP structure")
    total, offset = 0.0, 0
    for n in parts:
        if n < 2:
            raise OriginalZipError("original planar degree polyline part too short")
        previous = struct.unpack_from("<dd", xy, offset * 16)
        for k in range(offset + 1, offset + n):
            current = struct.unpack_from("<dd", xy, k * 16)
            total += math.hypot(current[0] - previous[0],
                                current[1] - previous[1])
            previous = current
        offset += n
    if not math.isfinite(total):
        raise OriginalZipError("nonfinite original planar degree length")
    return total


def _pct(values, fraction):
    if not values:
        return None
    sorted_values = sorted(values)
    index = min(len(sorted_values) - 1, max(0, math.ceil(len(sorted_values) * fraction) - 1))
    return round(sorted_values[index], 10)


def _distribution(values):
    return {
        "count": len(values),
        "p05": _pct(values, .05),
        "p50": _pct(values, .50),
        "p95": _pct(values, .95),
        "p99": _pct(values, .99),
        "min": round(min(values), 10) if values else None,
        "max": round(max(values), 10) if values else None,
    }


def compare_length_releases(a, b):
    """Original export-OBJECTID candidate join; emit only bounded aggregates."""
    ids_a, reported_a, shapes_a = a
    ids_b, reported_b, shapes_b = b
    if (not len(ids_a) or len(ids_a) > MAX_FEATURES
            or len(ids_a) != len(reported_a) or len(ids_a) != len(shapes_a)
            or len(ids_b) != len(reported_b) or len(ids_b) != len(shapes_b)
            or len(set(ids_a)) != len(ids_a) or len(set(ids_b)) != len(ids_b)
            or set(ids_a) != set(ids_b)):
        raise OriginalZipError("original OBJECTID lengths/shapes are not uniquely joinable")
    index_b = {key: i for i, key in enumerate(ids_b)}
    report_ratio = []
    abs_relative = []
    delta_source = []
    geodesic_by_vintage = {"2018": [], "2026": []}
    original_degree_length_ratio = []
    original_degree_relative_error = []
    new_km_spherical_relative_error = []
    degree_error_thresholds = Counter()
    spherical_error_thresholds = Counter()
    diagnostic_tolerances = (1e-9, 1e-6, 1e-4, 0.01, 0.1)
    zero_denominator = 0
    same_xy_relative = []
    changed_xy_relative = []
    thresholds = Counter()
    changed_shape_leng = 0
    identical_xy_pairs = 0
    zero_geographic_lengths = Counter()
    for i, key in enumerate(ids_a):
        j = index_b[key]
        old, new = reported_a[i], reported_b[j]
        if not all(math.isfinite(x) and x >= 0 for x in (old, new)):
            raise OriginalZipError("unvalidated original source length")
        if old != new:
            changed_shape_leng += 1
        delta_source.append(new - old)
        if old > 0 and new > 0:
            ratio = new / old
            report_ratio.append(ratio)
            abs_relative.append(abs(ratio - 1.0))
            for limit in RELATIVE_DELTA_THRESHOLDS:
                if abs(ratio - 1) > limit:
                    thresholds[str(limit)] += 1
            if shapes_a[i] == shapes_b[j]:
                identical_xy_pairs += 1
                same_xy_relative.append(abs(ratio - 1))
            else:
                changed_xy_relative.append(abs(ratio - 1))
        else:
            zero_denominator += 1
            if shapes_a[i] == shapes_b[j]:
                identical_xy_pairs += 1
        for label, source_length, shape in (
                ("2018", old, shapes_a[i]), ("2026", new, shapes_b[j])):
            spherical = spherical_centerline_length_km(shape)
            angular = planar_original_wgs84_length_in_degrees(shape)
            if spherical > 0:
                ratio_km = source_length / spherical
                geodesic_by_vintage[label].append(ratio_km)
                if label == "2026":
                    err_km = abs(ratio_km - 1.0)
                    new_km_spherical_relative_error.append(err_km)
                    for t in diagnostic_tolerances:
                        if err_km > t:
                            spherical_error_thresholds[str(t)] += 1
            else:
                zero_geographic_lengths[label] += 1
            if angular > 0 and label == "2018":
                ratio_deg = source_length / angular
                original_degree_length_ratio.append(ratio_deg)
                err_deg = abs(ratio_deg - 1.0)
                original_degree_relative_error.append(err_deg)
                for t in diagnostic_tolerances:
                    if err_deg > t:
                        degree_error_thresholds[str(t)] += 1
    # Source product documentation reported Shape_Leng in kilometres; the
    # spherical comparison is only diagnostic and must not be used to
    # reinterpret the field units without upstream processing evidence.
    return {
        "schema": SCHEMA,
        "matched_unique_export_objectid_candidates": len(ids_a),
        "export_objectid_order_equal": ids_a == ids_b,
        "reported_shape_leng_value_changed": changed_shape_leng,
        "source_shape_leng_difference_new_minus_old": _distribution(delta_source),
        "ratio_2026_over_2018": _distribution(report_ratio),
        "abs_relative_change_fraction": _distribution(abs_relative),
        "features_with_absolute_relative_change_exceeding_fraction": {
            str(t): thresholds[str(t)] for t in RELATIVE_DELTA_THRESHOLDS
        },
        "same_xy_pair_count": identical_xy_pairs,
        "same_xy_pair_abs_relative_change": _distribution(same_xy_relative),
        "different_xy_pair_abs_relative_change": _distribution(changed_xy_relative),
        "zero_source_length_denominator_pairs": zero_denominator,
        "reported_shape_leng_over_spherical_centerline_km_by_release": {
            label: _distribution(values)
            for label, values in geodesic_by_vintage.items()
        },
        "nonpositive_spherical_centerline_length_count_by_release": dict(zero_geographic_lengths),
        "original_2018_shape_leng_over_wgs84_planar_degrees": _distribution(original_degree_length_ratio),
        "original_2018_abs_relative_error_vs_planar_degrees": _distribution(original_degree_relative_error),
        "original_2018_features_exceeding_planar_degree_rel_error": {
            str(t): degree_error_thresholds[str(t)] for t in diagnostic_tolerances
        },
        "original_2026_abs_relative_error_vs_spherical_km": _distribution(new_km_spherical_relative_error),
        "original_2026_features_exceeding_spherical_km_rel_error": {
            str(t): spherical_error_thresholds[str(t)] for t in diagnostic_tolerances
        },
        "planar_degree_control_is_not_ground_distance": True,
        "spherical_length_diagnostic_basis": EARTH_LENGTH_APPROXIMATION,
        "geodesic_distance_or_projection_method_of_source_verified": False,
        "source_shape_leng_units_independently_verified": False,
        "source_formula_change_explained": False,
        "export_objectid_verified_as_hydrologic_identity": False,
        "river_width_change_verified": False,
        "flood_hazard_or_insured_loss_calculated": False,
        "model_source_admitted": False,
        "raw_original_rows_or_coordinates_emitted": False,
        "production_database_modified": False,
    }


def original_length_audit():
    with tempfile.TemporaryDirectory(prefix="grwl-shape-length-source-") as scratch:
        versions = {}
        receipts = []
        for release in ("2018", "2026"):
            path = Path(scratch) / SOURCE_FILES[release][0]
            receipt = download_fixed(release, path)
            structure = inspect_original_zip(path, release)
            source_sha = PINNED_SOURCE_SHA256[release]
            if (receipt["independent_original_zip_sha256"] != source_sha
                    or structure["independently_computed_original_zip_sha256"] != source_sha):
                raise OriginalZipError("original source ZIP sha256 mismatch: fail closed")
            with zipfile.ZipFile(path) as archive:
                dbf_metadata = read_dbf_semantics(archive)
                ids, source_lengths = read_keyed_source_lengths(archive, dbf_metadata)
                shapes, _ = read_original_polylines(archive)
            versions[release] = (ids, source_lengths, shapes)
            receipts.append({"release": release, "verified_original_zip_sha256": source_sha})
        return {
            "source_identity": receipts,
            "comparison": compare_length_releases(versions["2018"], versions["2026"]),
            "source_bytes_published": False,
            "model_input_admitted": False,
        }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true",
                   help="explicit reviewed-main network-only original source audit")
    args = p.parse_args(argv)
    if not args.live:
        p.print_help()
        return 2
    try:
        result = original_length_audit()
    except OriginalZipError as exc:
        p.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
