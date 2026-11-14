# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Trusted-main GRWL WGS84 vertex correspondence proof, NOT a flood hazard model.

The exact 2018/2026 original ZIP SHA256 checks are compulsory. Compare matching
unique export OBJECTID candidate rows; never emit original geometry or keys.
Reverse polyline vertex orientation, and optionally reverse multipart order,
before measuring approximate great-circle *corresponding-vertex* separation.
This is not a Hausdorff distance, reprojection proof, or stable river-ID claim.
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

from research_runners.grwl_original_zip_structure_preflight_v0 import (
    OriginalZipError, SOURCE_FILES, inspect_original_zip,
)
from research_runners.grwl_original_aggregate_semantic_diff_v0 import (
    MAX_DBF_RECORDS, MAX_SHP_RECORD_BYTES, PINNED_SOURCE_SHA256,
    _member, _read_exact, read_dbf_semantics,
)
from research_runners.grwl_trusted_original_byte_proof_v0 import download_fixed

SCHEMA = "opencatastrophe-grwl-wgs84-oriented-vertex-proof-v0"
EARTH_MEAN_RADIUS_METRES = 6_371_008.8
THRESHOLDS_METRES = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)
MAX_TOTAL_POINTS = 5_000_000


def _vertices(raw):
    return struct.iter_unpack("<dd", raw)


def read_original_polylines(archive: zipfile.ZipFile):
    """Read only bounded original SHP records to ephemeral memory (no output)."""
    member = _member(archive, ".shp")
    output = []
    point_total = 0
    with archive.open(member, "r") as stream:
        header = _read_exact(stream, 100)
        if (struct.unpack_from(">I", header, 0)[0] != 9994
                or struct.unpack_from(">I", header, 24)[0] * 2 != member.file_size
                or struct.unpack_from("<I", header, 28)[0] != 1000):
            raise OriginalZipError("original SHP header mismatch")
        shape_type = struct.unpack_from("<I", header, 32)[0]
        if shape_type not in (3, 13, 23):
            raise OriginalZipError("only original GRWL polyline shapes supported")
        consumed = 100
        while consumed < member.file_size:
            record_header = _read_exact(stream, 8)
            ordinal, words = struct.unpack(">II", record_header)
            body_bytes = words * 2
            if (ordinal != len(output) + 1 or not 4 <= body_bytes <= MAX_SHP_RECORD_BYTES
                    or consumed + 8 + body_bytes > member.file_size):
                raise OriginalZipError("bad original SHP record index/byte extent")
            body = _read_exact(stream, body_bytes)
            consumed += 8 + body_bytes
            kind = struct.unpack_from("<I", body, 0)[0]
            if kind == 0:
                if body_bytes != 4:
                    raise OriginalZipError("invalid original NullShape payload")
                output.append(((), b""))
                continue
            if kind != shape_type or body_bytes < 44:
                raise OriginalZipError("unexpected GRWL record shape type")
            part_count, point_count = struct.unpack_from("<II", body, 36)
            if not 1 <= part_count <= 10000 or not 2 <= point_count <= 100000:
                raise OriginalZipError("unexpected original part or point count")
            xy_end = 44 + 4 * part_count + 16 * point_count
            if xy_end > body_bytes:
                raise OriginalZipError("truncated original coordinates")
            starts = struct.unpack_from("<" + "I" * part_count, body, 44)
            if (starts[0] != 0 or any(a >= b for a, b in zip(starts, starts[1:]))
                    or starts[-1] >= point_count):
                raise OriginalZipError("invalid original part breaks")
            parts = tuple(b - a for a, b in zip(starts, starts[1:] + (point_count,)))
            xy = body[44 + 4 * part_count:xy_end]
            for longitude, latitude in _vertices(xy):
                if (not math.isfinite(longitude) or not math.isfinite(latitude)
                        or abs(longitude) > 180.0001 or abs(latitude) > 90.0001):
                    raise OriginalZipError("bad original WGS84 vertex")
            point_total += point_count
            if point_total > MAX_TOTAL_POINTS:
                raise OriginalZipError("aggregate original XY vertex safety cap")
            output.append((parts, xy))
            if len(output) > MAX_DBF_RECORDS:
                raise OriginalZipError("original SHP feature count cap")
        if consumed != member.file_size or stream.read(1):
            raise OriginalZipError("original SHP bytes not fully exhausted")
    return output, point_total


def _haversine_metres(a, b):
    """Approximate spherical great-circle metres, NOT a project CRS distance."""
    lon1, lat1 = a
    lon2, lat2 = b
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    lam = math.radians(((lon2 - lon1 + 180.0) % 360.0) - 180.0)
    hav = (math.sin(dphi / 2) ** 2 +
           math.cos(phi1) * math.cos(phi2) * math.sin(lam / 2) ** 2)
    return 2.0 * EARTH_MEAN_RADIUS_METRES * math.asin(math.sqrt(min(1.0, max(0.0, hav))))


def _starts(parts):
    starts = []
    current = 0
    for length in parts:
        starts.append(current)
        current += length
    return starts


def _equal_oriented(a, b, reverse_parts=False):
    """Exact same vertex values with per-part direction and optional part-order reversal."""
    pa, xa = a
    pb, xb = b
    astarts, bstarts = _starts(pa), _starts(pb)
    other_parts = list(range(len(pb)))
    if reverse_parts:
        other_parts.reverse()
    if len(pa) != len(pb) or any(pa[k] != pb[other_parts[k]] for k in range(len(pa))):
        return False
    for k, j in enumerate(other_parts):
        n = pa[k]
        left = xa[astarts[k] * 16:(astarts[k] + n) * 16]
        right = xb[bstarts[j] * 16:(bstarts[j] + n) * 16]
        if left == right:
            continue
        if any(left[i * 16:i * 16 + 16] != right[(n - 1 - i) * 16:(n - i) * 16]
               for i in range(n)):
            return False
    return True


def _paired_score(a, b, reverse_parts=False):
    pa, xa = a
    pb, xb = b
    if len(pa) != len(pb):
        return None
    other_parts = list(range(len(pb)))
    if reverse_parts:
        other_parts.reverse()
    if any(pa[k] != pb[other_parts[k]] for k in range(len(pa))):
        return None
    astarts, bstarts = _starts(pa), _starts(pb)
    square_sum = 0.0
    max_metres = 0.0
    for k, j in enumerate(other_parts):
        n = pa[k]
        start_a, start_b = astarts[k], bstarts[j]
        # Choose orientation by minimum sum-of-squared spherical separation.
        choices = []
        for backwards in (False, True):
            subtotal = 0.0
            furthest = 0.0
            for i in range(n):
                idx_b = n - 1 - i if backwards else i
                left = struct.unpack_from("<dd", xa, (start_a + i) * 16)
                right = struct.unpack_from("<dd", xb, (start_b + idx_b) * 16)
                distance = _haversine_metres(left, right)
                subtotal += distance * distance
                furthest = max(furthest, distance)
            choices.append((subtotal, furthest))
        best = min(choices)
        square_sum += best[0]
        max_metres = max(max_metres, best[1])
    return square_sum, max_metres


def compare_geometry(a, b):
    """Exact, direction-equivalent, or bounded oriented vertex correspondence."""
    if a == b:
        return {"class": "byte_identical", "max_vertex_correspondence_metres": 0.0}
    if _equal_oriented(a, b) or _equal_oriented(a, b, reverse_parts=True):
        return {"class": "direction_or_part_order_only",
                "max_vertex_correspondence_metres": 0.0}
    scores = [candidate for reverse in (False, True)
              if (candidate := _paired_score(a, b, reverse_parts=reverse)) is not None]
    if not scores:
        return {"class": "vertex_topology_not_correspondable",
                "max_vertex_correspondence_metres": None}
    # Choose minimum per-vertex squared distance; ties prefer smaller maximum.
    best = min(scores)
    return {"class": "oriented_vertex_correspondence",
            "max_vertex_correspondence_metres": best[1]}


def compare_original_by_objectid(early_dbf, later_dbf, old_shapes, new_shapes):
    if (early_dbf["fields"] != later_dbf["fields"]
            or len(old_shapes) != early_dbf["record_count"]
            or len(new_shapes) != later_dbf["record_count"]):
        raise OriginalZipError("DBF/SHP schema or record count cannot align")
    kinds = {name: kind for name, kind, width in early_dbf["fields"]}
    if kinds.get("OBJECTID") != "N":
        raise OriginalZipError("numeric original OBJECTID required")
    ids_a = early_dbf["field_value_hashes_by_ordinal"]["OBJECTID"]
    ids_b = later_dbf["field_value_hashes_by_ordinal"]["OBJECTID"]
    if (len(set(ids_a)) != len(ids_a) or len(set(ids_b)) != len(ids_b)
            or set(ids_a) != set(ids_b)):
        raise OriginalZipError("original candidate OBJECTID lacks unique equal-key set")
    map_b = {key: i for i, key in enumerate(ids_b)}
    classes = Counter()
    max_m = []
    thresholds = Counter()
    for index, key in enumerate(ids_a):
        result = compare_geometry(old_shapes[index], new_shapes[map_b[key]])
        classes[result["class"]] += 1
        distance = result["max_vertex_correspondence_metres"]
        if distance is not None:
            max_m.append(distance)
            for threshold in THRESHOLDS_METRES:
                if distance > threshold:
                    thresholds[str(threshold)] += 1
    max_m.sort()
    def quantile(p):
        if not max_m:
            return None
        return round(max_m[max(0, math.ceil(p * len(max_m)) - 1)], 6)
    return {
        "schema": SCHEMA,
        "matched_unique_export_objectid_candidates": len(ids_a),
        "export_objectid_order_equal": ids_a == ids_b,
        "geometry_match_classes": dict(sorted(classes.items())),
        "quantiles_of_per_feature_max_vertex_correspondence_metres_approx": {
            "p50": quantile(0.50), "p95": quantile(0.95), "p99": quantile(0.99),
            "max": round(max_m[-1], 6) if max_m else None,
        },
        "features_with_max_correspondence_greater_than_metres": {
            str(t): thresholds[str(t)] for t in THRESHOLDS_METRES
        },
        "metric_basis": "spherical_haversine_best_direction_paired_vertices_not_Hausdorff",
        "unmatched_part_or_point_topologies_are_not_assigned_metric_distance": True,
        "export_objectid_verified_as_hydrologic_identity": False,
        "geometric_river_relocation_verified": False,
        "flood_loss_impact_calculated": False,
        "source_data_admitted": False,
        "production_database_modified": False,
        "any_original_keys_or_coordinates_published": False,
    }


def live_original_geometry_compare():
    with tempfile.TemporaryDirectory(prefix="grwl-original-metric-") as tmp:
        versions = {}
        identities = []
        for release in ("2018", "2026"):
            file = Path(tmp) / SOURCE_FILES[release][0]
            receipt = download_fixed(release, file)
            safety = inspect_original_zip(file, release)
            exact = PINNED_SOURCE_SHA256[release]
            if (receipt["independent_original_zip_sha256"] != exact or
                    safety["independently_computed_original_zip_sha256"] != exact):
                raise OriginalZipError("download did not match independently pinned original ZIP")
            with zipfile.ZipFile(file) as archive:
                dbf = read_dbf_semantics(archive)
                geometries, point_count = read_original_polylines(archive)
            versions[release] = (dbf, geometries, point_count)
            identities.append({"release": release, "verified_original_zip_sha256": exact})
        early, late = versions["2018"], versions["2026"]
        return {
            "source_identity": identities,
            "original_xy_point_counts": {"2018": early[2], "2026": late[2]},
            "comparison": compare_original_by_objectid(early[0], late[0], early[1], late[1]),
            "raw_source_data_in_receipt": False,
            "model_input_admitted": False,
        }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true")
    args = p.parse_args(argv)
    if not args.live:
        p.print_help()
        return 2
    try:
        out = live_original_geometry_compare()
    except OriginalZipError as exc:
        p.error(str(exc))
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
