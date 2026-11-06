# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline ACT GeoBase 2026 vs Overture Luxembourg building candidate screen.

Requires independently prepared local polygon projections. Never fetches data,
publishes source geometries/IDs, writes to Neon, infers insured TIV or approves
model input. Provenance fields are user-supplied claims, not source proofs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from uuid import UUID

from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
from shapely.errors import GEOSException

SCHEMA = "opencatastrophe-lu-act-overture-building-identity-candidates-v0"
ACT_RELEASE = "2026-10-01"
ACT_ZIP_SHA256 = "6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3"
ACT_GPKG_SHA256 = "ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676"
OVERTURE_RELEASE = "2026-10-21.0"
# This exact part was independently identified through Overture's STAC item
# 00226: geographic bbox includes the Luxembourg-city research window.
LU_CITY_STAC_ITEM = "https://stac.overturemaps.org/2026-10-21.0/buildings/building/00226/00226.json"
LU_CITY_OVERTURE_ORIGINAL_KEY = (
    "release/2026-10-21.0/theme=buildings/type=building/"
    "part-00226-f2e989f6-97e6-5afe-b3d2-cfd2e6228d37-c000.zstd.parquet"
)
SOURCE_KEY = re.compile(
    r"release/2026-10-21\.0/theme=buildings/type=building/part-\d{5}-"
    r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}-c\d{3}\.zstd\.parquet\Z"
)
MAX_FILE_BYTES = 262_144
MAX_FEATURES_PER_SIDE = 64
MAX_COORDS_PER_FEATURE = 4096
MIN_IOU = .75
# Prevent numerical artefacts in inverse WGS84<->LUREF coordinates creating
# bogus positive intersections for exact boundary-touching synthetic features.
MIN_OVERLAP_M2 = .01
# Broad country envelope: screening only; not a sovereign/national boundary.
LU_SCREEN = (5.7, 49.4, 6.6, 50.2)
TO_WGS84 = Transformer.from_crs("EPSG:2169", "EPSG:4326", always_xy=True)
TO_LU = Transformer.from_crs("EPSG:4326", "EPSG:2169", always_xy=True)


class CandidateError(ValueError):
    """Unsafe or ungrounded research comparison."""


def _unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise CandidateError("duplicate JSON key")
        obj[key] = value
    return obj


def _nonfinite(value):
    raise CandidateError("nonfinite JSON number")


def _fields(obj, expected):
    if type(obj) is not dict or set(obj) != set(expected):
        raise CandidateError("wrong or unapproved record fields")


def _identifier(value, *, overture=False):
    if type(value) is not str or not value or len(value) > 128:
        raise CandidateError("invalid source identifier")
    if overture:
        try:
            if str(UUID(value)) != value:
                raise ValueError("noncanonical UUID")
        except ValueError as exc:
            raise CandidateError("invalid Overture UUID syntax") from exc
    return value


def _geometry(raw, *, local):
    _fields(raw, {"type", "coordinates"})
    if raw["type"] not in ("Polygon", "MultiPolygon"):
        raise CandidateError("only polygon footprints are screenable")
    polygons = [raw["coordinates"]] if raw["type"] == "Polygon" else raw["coordinates"]
    if type(polygons) is not list or not polygons:
        raise CandidateError("missing polygon components")
    count = 0
    for rings in polygons:
        if type(rings) is not list or not rings:
            raise CandidateError("missing polygon rings")
        for ring in rings:
            if type(ring) is not list or len(ring) < 4 or ring[0] != ring[-1]:
                raise CandidateError("invalid polygon ring")
            for coord in ring:
                if type(coord) is not list or len(coord) != 2:
                    raise CandidateError("bad polygon vertex")
                if any(type(x) not in (float, int) or not math.isfinite(x) for x in coord):
                    raise CandidateError("nonfinite/nonnumeric geometry")
                x, y = coord
                if local:
                    if not (0 < x < 200_000 and 0 < y < 200_000):
                        raise CandidateError("ACT coordinate outside source screen")
                elif not (-180 <= x <= 180 and -90 <= y <= 90):
                    raise CandidateError("Overture coordinate outside WGS84")
                count += 1
                if count > MAX_COORDS_PER_FEATURE:
                    raise CandidateError("oversized polygon vertex count")
    try:
        geom = shape(raw)
        if geom.is_empty or not geom.is_valid or geom.area <= 0:
            raise CandidateError("invalid source topology")
        wgs = transform(TO_WGS84.transform, geom) if local else geom
        if not wgs.is_valid:
            raise CandidateError("invalid transformed geometry")
        xmin, ymin, xmax, ymax = wgs.bounds
        left, bottom, right, top = LU_SCREEN
        if xmin < left or ymin < bottom or xmax > right or ymax > top:
            raise CandidateError("building outside Luxembourg screening envelope")
        if xmax - xmin > .02 or ymax - ymin > .02:
            raise CandidateError("oversized building footprint")
        projected = geom if local else transform(TO_LU.transform, geom)
        if not projected.is_valid or not .01 < projected.area <= 1_000_000:
            raise CandidateError("implausible physical footprint area")
        return projected
    except (GEOSException, OverflowError) as exc:
        raise CandidateError("geometry projection or clipping failure") from exc


def _source_rows(rows, *, local):
    if type(rows) is not list or not 1 <= len(rows) <= MAX_FEATURES_PER_SIDE:
        raise CandidateError("invalid bounded sample population")
    geometries, seen = [], set()
    for item in rows:
        _fields(item, {"source_id", "geometry"} if local
                else {"gers_id", "source_families", "geometry"})
        identity = _identifier(item["source_id" if local else "gers_id"],
                               overture=not local)
        if identity in seen:
            raise CandidateError("duplicate candidate source identity")
        seen.add(identity)
        if not local:
            families = item["source_families"]
            if (type(families) is not list or not 1 <= len(families) <= 16
                    or any(type(v) is not str or not v or len(v) > 96
                           for v in families)):
                raise CandidateError("invalid upstream source family")
            if len(families) != len(set(families)):
                raise CandidateError("duplicate upstream source family")
        geometries.append(_geometry(item["geometry"], local=local))
    return geometries


def compare(data, *, local_sample_sha256):
    _fields(data, {"schema", "act_release", "act_zip_sha256", "act_gpkg_sha256",
                   "act_crs", "overture_release", "overture_source_key",
                   "overture_crs", "act_buildings", "overture_buildings"})
    if data["schema"] != SCHEMA or data["act_release"] != ACT_RELEASE:
        raise CandidateError("wrong schema or ACT release")
    if (data["act_zip_sha256"] != ACT_ZIP_SHA256
            or data["act_gpkg_sha256"] != ACT_GPKG_SHA256):
        raise CandidateError("ACT original file hash claims do not match receipts")
    if (data["act_crs"] != "EPSG:2169" or data["overture_crs"] != "EPSG:4326"
            or data["overture_release"] != OVERTURE_RELEASE
            or type(data["overture_source_key"]) is not str
            or not SOURCE_KEY.fullmatch(data["overture_source_key"])
            or data["overture_source_key"] != LU_CITY_OVERTURE_ORIGINAL_KEY):
        raise CandidateError("wrong CRS or original Overture object reference")
    left = _source_rows(data["act_buildings"], local=True)
    right = _source_rows(data["overture_buildings"], local=False)
    act_hits = [[] for _ in left]
    overture_hits = [[] for _ in right]
    positive_overlaps = 0
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            if not a.intersects(b):
                continue
            try:
                intersection = a.intersection(b).area
                if intersection < MIN_OVERLAP_M2:
                    continue
                union = a.union(b).area
                if not math.isfinite(union) or union <= 0:
                    raise CandidateError("invalid candidate geometry union")
                score = intersection / union
                if not math.isfinite(score) or score > 1.000001:
                    raise CandidateError("invalid candidate IoU")
            except GEOSException as exc:
                raise CandidateError("projected overlay failure") from exc
            positive_overlaps += 1
            if score >= MIN_IOU:
                act_hits[i].append(j)
                overture_hits[j].append(i)
    matches = sum(1 for edges in act_hits
                  if len(edges) == 1 and len(overture_hits[edges[0]]) == 1)
    ambiguous = sum(1 for edges in act_hits
                    if len(edges) > 1 or
                    (len(edges) == 1 and len(overture_hits[edges[0]]) > 1))
    return {
        "schema": SCHEMA,
        "geography": "Luxembourg broad research envelope",
        "act_source_features_in_local_sample": len(left),
        "overture_features_in_local_sample": len(right),
        "positive_area_overlap_pairs": positive_overlaps,
        "reciprocal_one_to_one_geometric_candidates": matches,
        "ambiguous_act_features_quarantined": ambiguous,
        "act_features_without_above_threshold_match_in_slice":
            sum(not edges for edges in act_hits),
        "overture_features_without_above_threshold_match_in_slice":
            sum(not edges for edges in overture_hits),
        "area_overlap_method": "EPSG:2169_projected_planar_IoU",
        "stac_candidate_original_key": LU_CITY_OVERTURE_ORIGINAL_KEY,
        "minimum_candidate_iou": MIN_IOU,
        "minimum_physical_positive_overlap_m2": MIN_OVERLAP_M2,
        "local_pair_sample_sha256": local_sample_sha256,
        "act_zip_receipt_sha256_pinned_not_reverified_here": ACT_ZIP_SHA256,
        "act_gpkg_receipt_sha256_pinned_not_reverified_here": ACT_GPKG_SHA256,
        "act_geobase_and_overture_independent_observation_proven": False,
        "source_coordinate_epoch_accuracy_verified": False,
        "overture_original_file_sha256_verified": False,
        "overture_gers_registry_membership_verified": False,
        "real_original_rows_verified_in_this_run": False,
        "source_license_and_derivative_use_approved": False,
        "geometries_admitted_to_insurance_db": False,
        "insured_value_inferred": False,
        "cat_model_input_approved": False,
        "note": "Aggregate results from the supplied slice only. No source IDs or coordinates emitted; absence in slice is not absence in either original provider dataset."
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        path = args.input
        if (path.is_symlink() or not path.is_file()
                or not 0 < path.stat().st_size <= MAX_FILE_BYTES):
            raise CandidateError("input must be a bounded local regular file")
        payload = path.read_bytes()
        data = json.loads(payload.decode("utf-8", errors="strict"),
                          object_pairs_hook=_unique, parse_constant=_nonfinite)
        result = compare(data, local_sample_sha256=hashlib.sha256(payload).hexdigest())
    except (CandidateError, OSError, UnicodeError, ValueError, TypeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
