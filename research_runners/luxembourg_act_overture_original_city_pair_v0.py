# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Transient ACT GeoBase2026 × Overture2026 Luxembourg-city original overlay.

Only public, pinned original sources. Checks full ACT ZIP/GPKG SHA-256 and
original Overture row-group metadata before a small city-area spatial overlap.
No original coordinates/IDs/WKB exported, no OSM/GERS proof, insurance TIV,
database writes or scientific model-data admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import struct
import sys
import tempfile
import zipfile

from pyproj import Transformer
from shapely import wkb
from shapely.geometry import box
from shapely.ops import transform
from shapely.errors import GEOSException

from research_runners.luxembourg_geobase_2026_id_quality_v0 import (
    EXPECTED_ZIP_SHA256, EXPECTED_GPKG_SHA256, EXPECTED_FEATURE_COUNT,
    EXPECTED_LAYER, MAX_GPKG_BYTES, audit as verify_act_zip,
)
from research_runners.luxembourg_geobase_buildings_20261001_v0 import (
    GeoBaseError, _safe,
)
from research_runners.overture_lu_rowgroup_metadata_v0 import (
    probe as overture_source_metadata_probe,
)
from research_runners.overture_lu_one_rowgroup_geometry_observation_v0 import (
    TARGET_ROW_GROUP, TARGET_ROW_COUNT, _coordinates_in_city_box,
    _expected_column_bytes, CITY_BOX, S3_PATH, BUCKET, REGION,
    EXPECTED_BYTES, EXPECTED_ROWS, EXPECTED_ROW_GROUPS_STAC,
)

SCHEMA = "opencatastrophe-luxembourg-act2026-overture2026-real-source-geometric-candidates-v0"
MAX_SOURCE_ROWS = 250000
MIN_IOU = 0.75
MIN_POSITIVE_OVERLAP_M2 = 0.01
TO_LU = Transformer.from_crs("EPSG:4326", "EPSG:2169", always_xy=True)


def _gpkg_polygon(blob):
    if not isinstance(blob, bytes) or not 13 <= len(blob) <= 2_000_000:
        raise GeoBaseError("original ACT geometry absent or exceeds bound")
    if blob[:2] != b"GP" or blob[2] != 0 or blob[3] & 0xE0:
        raise GeoBaseError("invalid original ACT GeoPackage geometry header")
    envelope = (blob[3] >> 1) & 7
    sizes = {0: 0, 1: 4, 2: 6, 3: 6, 4: 8}
    if envelope not in sizes:
        raise GeoBaseError("unsupported original GPKG envelope")
    prefix = "<" if blob[3] & 1 else ">"
    if struct.unpack_from(prefix + "i", blob, 4)[0] != 2169:
        raise GeoBaseError("original ACT geometry has unexpected declared CRS")
    offset = 8 + sizes[envelope] * 8
    if len(blob) < offset + 5:
        raise GeoBaseError("truncated original ACT geometry")
    try:
        geom = wkb.loads(blob[offset:])
    except (ValueError, GEOSException, TypeError) as exc:
        raise GeoBaseError("original ACT WKB not parseable") from exc
    if geom.geom_type not in ("Polygon", "MultiPolygon"):
        raise GeoBaseError("unexpected ACT nonpolygon geometry")
    return geom


def original_act_city(source_zip):
    """Verify complete original and yield city-screened geometries in memory only."""
    receipt = verify_act_zip(Path(source_zip))
    if receipt["original_zip_sha256"] != EXPECTED_ZIP_SHA256:
        raise GeoBaseError("original ACT archive is not the pinned source")
    window = transform(TO_LU.transform, box(*CITY_BOX))
    kept = []
    invalid_total = 0
    scanned = 0
    with tempfile.TemporaryDirectory(prefix="oc-act-city-private-") as tmp:
        target = Path(tmp) / "source.gpkg"
        with zipfile.ZipFile(source_zip) as archive:
            gpkg = [item for item in archive.infolist() if not item.is_dir()
                    and item.filename.lower().endswith(".gpkg")]
            if len(gpkg) != 1:
                raise GeoBaseError("unexpected ACT GeoPackage count")
            member = gpkg[0]
            _safe(member)
            if member.file_size > MAX_GPKG_BYTES:
                raise GeoBaseError("unbounded ACT original extraction")
            h = hashlib.sha256()
            total = 0
            with archive.open(member) as stream, target.open("xb") as output:
                while block := stream.read(1024 * 1024):
                    total += len(block)
                    if total > MAX_GPKG_BYTES or total > member.file_size:
                        raise GeoBaseError("original ACT extraction exceeded cap")
                    h.update(block)
                    output.write(block)
            if total != member.file_size or h.hexdigest() != EXPECTED_GPKG_SHA256:
                raise GeoBaseError("unverified original ACT GeoPackage bytes")
        db = sqlite3.connect(target.resolve().as_uri()+"?mode=ro&immutable=1", uri=True)
        try:
            db.execute("PRAGMA query_only=ON")
            n = db.execute('SELECT count(*) FROM "Buildings_BU_Building"').fetchone()[0]
            if n != EXPECTED_FEATURE_COUNT:
                raise GeoBaseError("ACT original feature count changed")
            for (raw,) in db.execute('SELECT geom FROM "Buildings_BU_Building" ORDER BY id'):
                scanned += 1
                try:
                    polygon = _gpkg_polygon(raw)
                except GeoBaseError:
                    invalid_total += 1
                    continue
                if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
                    invalid_total += 1
                    continue
                if polygon.intersects(window) and polygon.intersection(window).area > 0:
                    kept.append(polygon)
            if scanned != n:
                raise GeoBaseError("ACT original read did not conserve source rows")
        finally:
            db.close()
    return kept, scanned, invalid_total


def original_overture_city():
    """One S3 row group, bbox+geometry columns only, original bytes transient."""
    source = overture_source_metadata_probe()
    if source["original_zero_based_rowgroup_indices_for_followup"] != [TARGET_ROW_GROUP]:
        raise GeoBaseError("original provider city row-group selection changed")
    import pyarrow.fs as fs
    import pyarrow.parquet as pq

    client = fs.S3FileSystem(anonymous=True, region=REGION,
                             connect_timeout=15, request_timeout=15)
    if client.get_file_info(S3_PATH).size != EXPECTED_BYTES:
        raise GeoBaseError("original Overture file identity/size changed")
    reader = pq.ParquetFile(S3_PATH, filesystem=client, pre_buffer=False)
    if (reader.metadata.num_rows != EXPECTED_ROWS or
            reader.metadata.num_row_groups != EXPECTED_ROW_GROUPS_STAC or
            reader.metadata.row_group(TARGET_ROW_GROUP).num_rows != TARGET_ROW_COUNT):
        raise GeoBaseError("actual Overture original row-group metadata mismatch")
    _expected_column_bytes(reader.metadata.row_group(TARGET_ROW_GROUP))
    source_column_bytes = sum(
        reader.metadata.row_group(TARGET_ROW_GROUP).column(j).total_compressed_size
        for j in range(reader.metadata.row_group(TARGET_ROW_GROUP).num_columns)
        if reader.metadata.row_group(TARGET_ROW_GROUP).column(j).path_in_schema.startswith("sources.")
    )
    if source_column_bytes <= 0 or source_column_bytes > 8 * 1024 * 1024:
        raise GeoBaseError("upstream original sources column exceeds bounded research budget")
    table = reader.read_row_group(TARGET_ROW_GROUP,
                                  columns=["bbox", "geometry", "sources"],
                                  use_threads=False)
    if table.num_rows != TARGET_ROW_COUNT:
        raise GeoBaseError("selected Overture original population mismatch")
    outlines, invalid, original_source_families = [], 0, []
    city_window = transform(TO_LU.transform, box(*CITY_BOX))
    for bound, raw, lineage in zip(table["bbox"].to_pylist(),
                                   table["geometry"].to_pylist(),
                                   table["sources"].to_pylist()):
        if not _coordinates_in_city_box(bound):
            continue
        if not isinstance(raw, bytes) or not 0 < len(raw) <= 500000:
            invalid += 1
            continue
        try:
            original = wkb.loads(raw)
            if (original.geom_type not in ("Polygon", "MultiPolygon")
                    or original.is_empty or not original.is_valid):
                invalid += 1
                continue
            national = transform(TO_LU.transform, original)
            if not national.is_valid or national.area <= 0:
                invalid += 1
                continue
            if not national.intersects(city_window) or national.intersection(city_window).area <= 0:
                continue
            outlines.append(national)
            dataset_labels = set()
            if type(lineage) is list and len(lineage) <= 128:
                for item in lineage:
                    if type(item) is dict and type(item.get("dataset")) is str:
                        dataset_labels.add(item["dataset"])
            original_source_families.append(
                next(iter(dataset_labels)) if len(dataset_labels) == 1
                and next(iter(dataset_labels)) in ("OpenStreetMap", "Microsoft ML Buildings")
                else "unknown_or_multiple"
            )
        except (GEOSException, ValueError, TypeError):
            invalid += 1
    return outlines, TARGET_ROW_COUNT, invalid, original_source_families


def _require_valid_projected_footprints(footprints, *, label):
    """Refuse untrusted non-polygon, invalid or numerically unstable geometry.

    A best-IoU comparison is meaningful only on valid, finite-area planar
    geometries. Invalid input must be blocked, not silently omitted or repaired:
    omission can make an ambiguous many-to-one relationship appear reciprocal.
    """
    for geometry in footprints:
        try:
            if geometry.geom_type not in ("Polygon", "MultiPolygon"):
                raise GeoBaseError(f"{label} source has non-polygon geometry")
            if geometry.is_empty or not geometry.is_valid:
                raise GeoBaseError(f"{label} source has invalid geometry")
            if (not math.isfinite(geometry.area) or geometry.area <= 0
                    or len(geometry.bounds) != 4
                    or not all(math.isfinite(v) for v in geometry.bounds)):
                raise GeoBaseError(f"{label} source has non-finite projected geometry")
        except GeoBaseError:
            # Preserve the precise, safely redacted domain failure for tests
            # and diagnostics; never flatten it into an unrelated GEOS fault.
            raise
        except (GEOSException, ValueError, TypeError, AttributeError, OverflowError) as exc:
            raise GeoBaseError(f"{label} source geometry cannot be safely checked") from exc


def geometric_candidates(act, overture, *, overture_source_families=None):
    """Reciprocal geometric candidates with only aggregate upstream lineage."""
    if len(act) > 500 or len(overture) > 500:
        raise GeoBaseError("excessive local city-pilot source candidates")
    _require_valid_projected_footprints(act, label="ACT")
    _require_valid_projected_footprints(overture, label="Overture")
    if overture_source_families is not None and (
            type(overture_source_families) is not list
            or len(overture_source_families) != len(overture)
            or any(x not in ("OpenStreetMap", "Microsoft ML Buildings", "unknown_or_multiple")
                   for x in overture_source_families)):
        raise GeoBaseError("source-family association must preserve sampled geometry order")
    act_hits = [[] for _ in act]
    overture_hits = [[] for _ in overture]
    qualifying_pairs = 0
    positive_area_pairs = 0
    # Scores only; indices are ephemeral and never emitted or persisted.
    # Sensitivity helps expose matches caused solely by a chosen IoU cutoff.
    overlap_scores = []
    best_act = [0.0] * len(act)
    best_overture = [0.0] * len(overture)
    for ai, a in enumerate(act):
        for oi, b in enumerate(overture):
            try:
                if not a.intersects(b):
                    continue
                area = a.intersection(b).area
                if area < MIN_POSITIVE_OVERLAP_M2:
                    continue
                union = a.union(b).area
                if union <= 0 or not math.isfinite(union):
                    raise GeoBaseError("invalid geometry union")
                ratio = area/union
            except GEOSException as exc:
                raise GeoBaseError("source overlay topology failure") from exc
            positive_area_pairs += 1
            if not math.isfinite(ratio) or ratio <= 0 or ratio > 1:
                raise GeoBaseError("invalid projected IoU ratio")
            overlap_scores.append((ai, oi, ratio))
            best_act[ai] = max(best_act[ai], ratio)
            best_overture[oi] = max(best_overture[oi], ratio)
            if ratio < MIN_IOU:
                continue
            qualifying_pairs += 1
            act_hits[ai].append(oi)
            overture_hits[oi].append(ai)
    def histogram(values):
        bands = {"no_positive_area_overlap": 0, "iou_below_0_25": 0,
                 "iou_0_25_to_0_50": 0, "iou_0_50_to_0_75": 0,
                 "iou_at_least_0_75": 0}
        for value in values:
            if value <= 0:
                bands["no_positive_area_overlap"] += 1
            elif value < .25:
                bands["iou_below_0_25"] += 1
            elif value < .50:
                bands["iou_0_25_to_0_50"] += 1
            elif value < .75:
                bands["iou_0_50_to_0_75"] += 1
            else:
                bands["iou_at_least_0_75"] += 1
        return bands

    # Diagnostic only: never use relaxed cutoffs as an identity admission.
    # At each threshold, recompute reciprocal pairs and ambiguity from the
    # *whole* candidate graph; best-IoU alone cannot detect split/merge cases.
    sensitivity = {}
    for name, threshold in (("iou_0_50", 0.50), ("iou_0_75", MIN_IOU),
                            ("iou_0_90", 0.90)):
        threshold_act = [[] for _ in act]
        threshold_overture = [[] for _ in overture]
        for ai, oi, ratio in overlap_scores:
            if ratio >= threshold:
                threshold_act[ai].append(oi)
                threshold_overture[oi].append(ai)
        sensitivity[name] = {
            "overlap_pairs_at_or_above_threshold":
                sum(len(hits) for hits in threshold_act),
            "reciprocal_one_to_one_geometric_candidates":
                sum(len(hits) == 1 and len(threshold_overture[hits[0]]) == 1
                    for hits in threshold_act if hits),
            "act_features_with_ambiguous_geometric_candidates":
                sum(len(hits) > 1 or
                    (len(hits) == 1 and len(threshold_overture[hits[0]]) > 1)
                    for hits in threshold_act),
            "act_features_without_above_threshold_match":
                sum(not hits for hits in threshold_act),
        }
    matched = sum(len(xs) == 1 and len(overture_hits[xs[0]]) == 1
                  for xs in act_hits if xs)
    if (sensitivity["iou_0_75"]["reciprocal_one_to_one_geometric_candidates"]
            != matched or sensitivity["iou_0_75"]["overlap_pairs_at_or_above_threshold"]
            != qualifying_pairs):
        raise GeoBaseError("threshold sensitivity does not reconcile with frozen IoU gate")
    ambiguous_act = sum(len(xs) > 1 or
                        (len(xs) == 1 and len(overture_hits[xs[0]]) > 1)
                        for xs in act_hits)
    result = {
        "original_act_city_candidate_footprints": len(act),
        "original_overture_city_candidate_footprints": len(overture),
        "positive_area_original_source_overlap_pairs": positive_area_pairs,
        "ACT_best_geometric_iou_distribution": histogram(best_act),
        "Overture_best_geometric_iou_distribution": histogram(best_overture),
        "overlap_pairs_above_iou_0_75": qualifying_pairs,
        "reciprocal_one_to_one_geometric_candidates": matched,
        "geometric_threshold_sensitivity_research_only": sensitivity,
        "threshold_sensitivity_is_identity_confidence": False,
        "act_features_with_ambiguous_many_to_many_candidates": ambiguous_act,
        "act_features_without_above_threshold_match": sum(not x for x in act_hits),
        "overture_features_without_above_threshold_match": sum(not x for x in overture_hits),
    }
    if overture_source_families is not None:
        by_family = {"OpenStreetMap": 0, "Microsoft ML Buildings": 0,
                     "unknown_or_multiple": 0}
        for hits in act_hits:
            if len(hits) == 1 and len(overture_hits[hits[0]]) == 1:
                by_family[overture_source_families[hits[0]]] += 1
        if sum(by_family.values()) != matched:
            raise GeoBaseError("source provenance counts do not conserve strict candidates")
        result["reciprocal_candidate_overture_source_family_counts"] = by_family
    return result


def live(source_zip):
    act, act_total, invalid_act = original_act_city(source_zip)
    overture, overture_total, invalid_ov, families = original_overture_city()
    summary = geometric_candidates(act, overture, overture_source_families=families)
    return {
        "schema": SCHEMA,
        "ACT_original_release": "2026-10-01",
        "ACT_source_SHA256_verified": True,
        "ACT_source_feature_rows_scanned": act_total,
        "ACT_invalid_original_geometry_total_quarantined": invalid_act,
        "Overture_release": "2026-10-21.0",
        "Overture_source_rowgroup": TARGET_ROW_GROUP,
        "Overture_original_source_rows_examined": overture_total,
        "Overture_invalid_original_city_geometry_quarantined": invalid_ov,
        "area_overlap_method": "EPSG:2169_projected_planar_IoU",
        "source_crs_and_epoch_ground_control_certified": False,
        "GERS_registry_membership_verified": False,
        "same_source_lineage_independence_verified": False,
        "original_overture_full_file_SHA256_verified": False,
        "source_licenses_approved_for_insurer_models": False,
        "source_geometry_or_ids_persisted": False,
        "individual_insured_objects_identified": False,
        "insured_TIV_inferred": False,
        "CAT_model_inputs_approved": False,
        "Neon_modified": False,
        **summary,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--live", action="store_true",
                        help="Explicit opt-in to two exact public original providers")
    args = parser.parse_args(argv)
    if not args.live:
        print("BLOCKED: --live required for source geometry", file=sys.stderr)
        return 2
    try:
        outcome = live(args.source_zip)
    except (OSError, ValueError, TypeError, GeoBaseError) as exc:
        print("BLOCKED: source-original comparison did not pass", file=sys.stderr)
        return 2
    print(json.dumps(outcome, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
