#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original-byte, read-only Germany GADM-v4.1 vs BKG-2022 geometry challenge.

This analysis is non-commercial research only, subject to upstream GADM rights.
A successful geometry comparison DOES NOT authorize cross-source building GFA
allocation, insurer site identification, insured sums or CAT model admission.

Optional geometrical runtime dependencies: pyshp, shapely and pyproj.
They are imported only for the explicit original geometry replay; standard
repository unit tests remain dependency-free.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import io
import json
from math import isfinite
from pathlib import Path
from statistics import median
import zipfile

from research_runners.materialcities_bkg_gadm_2022_code_crosswalk_v0 import (
    BKG_SHA256, GADM_SHA256, MATERIALCITIES_SHA256,
    EXCEPTIONAL_OLD_TO_2022_AGS, inspect_exact_sources,
    CodeCrosswalkError,
)

SOURCE_CRS_EPSG = 31467  # Read from original BKG GK3 PRJ; never assume its coordinates are WGS84.
AREA_CRS_EPSG = 3035  # Equal-area European LAEA, square metres.
MANUAL_REVIEW_IOU_THRESHOLD = 0.95
ORIGINAL_BKG_SHAPES = 430
ORIGINAL_BKG_LAND_RECORDS = 400
ORIGINAL_BKG_MARINE_RECORDS = 30
ORIGINAL_TARGET_AGS = 400
ORIGINAL_GADM_FEATURES = 403
HIGHLIGHT_AGS = ("03159", "16063", "16054", "01001", "09162")


class GeometryOverlapError(ValueError):
    """Independent geometry evidence cannot be trusted or is incomplete."""


def validate_bkg_geofactors(geofactors: dict[str, list[int]], *,
                            exact_original: bool = True) -> dict:
    """BKG VG250 specification: exactly one GF=4 land polygon per Kreis.

    GF=2 is a separate coastal/Bodensee water polygon, never an extra Kreis
    or a stand-in for land. Do not silently ignore unknown GF values.
    """
    if not geofactors:
        raise GeometryOverlapError("BKG source land/water geofactors are absent")
    land = 0
    water = 0
    with_marine = 0
    for ags, flags in geofactors.items():
        if (not isinstance(ags, str) or len(ags) != 5 or not ags.isdigit()
                or not isinstance(flags, list) or
                any(type(gf) is not int or gf not in (2, 4) for gf in flags)):
            raise GeometryOverlapError("BKG source GF must be the documented 2/4 codes")
        if flags.count(4) != 1:
            raise GeometryOverlapError("each official AGS must have exactly one GF=4 land geometry")
        land += 1
        water += flags.count(2)
        with_marine += int(2 in flags)
    if exact_original and (land != ORIGINAL_BKG_LAND_RECORDS or
                           water != ORIGINAL_BKG_MARINE_RECORDS or
                           land + water != ORIGINAL_BKG_SHAPES):
        raise GeometryOverlapError("original BKG 2022 GF=4/2 land/marine profile changed")
    return {
        "source_GF4_land_shape_records": land,
        "source_GF2_coastal_or_lake_shape_records": water,
        "official_AGS_with_GF2_marine_parts": with_marine,
        "each_official_AGS_has_one_GF4_land_geometry": True,
        "GF2_marine_excluded_from_building_land_comparison": True,
    }


def compare_land_water_scores(land_scores: dict[str, dict],
                              all_scores: dict[str, dict]) -> dict:
    """Contrast land-only with earlier all-pieces scores without admitting a join."""
    if not land_scores or set(land_scores) != set(all_scores):
        raise GeometryOverlapError("land/all BKG geographic cohorts cannot differ")
    for scores in (land_scores, all_scores):
        for row in scores.values():
            if (not isinstance(row, dict) or type(row.get("iou")) is not float or
                    not isfinite(row["iou"]) or not 0 <= row["iou"] <= 1):
                raise GeometryOverlapError("invalid land/water original IoU score")
    changed_to_pass = sum(
        all_scores[key]["iou"] < MANUAL_REVIEW_IOU_THRESHOLD <= land_scores[key]["iou"]
        for key in land_scores
    )
    changed_to_fail = sum(
        land_scores[key]["iou"] < MANUAL_REVIEW_IOU_THRESHOLD <= all_scores[key]["iou"]
        for key in land_scores
    )
    return {
        "previous_all_BKG_pieces_to_GF4_land_only_passes": changed_to_pass,
        "previous_all_BKG_pieces_to_GF4_land_only_fails": changed_to_fail,
        "comparable_original_AGS": len(land_scores),
        "neither_mode_establishes_spatial_exposure_admission": True,
    }


def overlap_metrics(a_m2: float, b_m2: float, intersection_m2: float) -> dict:
    """Compute symmetric intersection-over-union and directional coverage."""
    values = (a_m2, b_m2, intersection_m2)
    if any(type(v) not in (int, float) or not isfinite(v) for v in values):
        raise GeometryOverlapError("geometry areas must be finite source-metric values")
    if a_m2 <= 0 or b_m2 <= 0 or intersection_m2 < 0:
        raise GeometryOverlapError("negative/empty source geometry area")
    if intersection_m2 > min(a_m2, b_m2) + 1e-8 * min(a_m2, b_m2):
        raise GeometryOverlapError("intersection larger than either source area")
    union_m2 = a_m2 + b_m2 - intersection_m2
    if union_m2 <= 0:
        raise GeometryOverlapError("invalid polygon union area")
    iou = intersection_m2 / union_m2
    if not 0 <= iou <= 1 + 1e-8:
        raise GeometryOverlapError("invalid polygon IoU")
    return {
        "iou": min(iou, 1.0),
        "official_bkg_covered_fraction": intersection_m2 / a_m2,
        "gadm_covered_fraction": intersection_m2 / b_m2,
        "bkg_area_km2": a_m2 / 1e6,
        "gadm_area_km2": b_m2 / 1e6,
        "area_difference_gadm_minus_bkg_km2": (b_m2 - a_m2) / 1e6,
    }


def summarize_scores(scores: dict[str, dict], *, exact_original: bool = True) -> dict:
    if not scores or any(not isinstance(k, str) or not isinstance(v, dict) or
                         "iou" not in v for k, v in scores.items()):
        raise GeometryOverlapError("complete AGS-keyed polygon scores are required")
    vals = sorted(v["iou"] for v in scores.values())
    if any(type(v) is not float or not isfinite(v) or not 0 <= v <= 1 for v in vals):
        raise GeometryOverlapError("invalid geometry IoU in score inventory")
    if exact_original and (len(scores) != ORIGINAL_TARGET_AGS or
                           any(code not in scores for code in HIGHLIGHT_AGS)):
        raise GeometryOverlapError("original 400-Kreis evidence scope incomplete")
    low = sorted((key for key in scores if scores[key]["iou"] < MANUAL_REVIEW_IOU_THRESHOLD))
    worst = min(scores, key=lambda k: (scores[k]["iou"], k))
    highlights = {
        k: {"iou": scores[k]["iou"],
            "bkg_area_km2": scores[k]["bkg_area_km2"],
            "gadm_area_km2": scores[k]["gadm_area_km2"],
            "gadm_coverage_fraction": scores[k]["gadm_covered_fraction"],
            "official_bkg_coverage_fraction": scores[k]["official_bkg_covered_fraction"]}
        for k in HIGHLIGHT_AGS if k in scores
    }
    return {
        "unique_2022_ags_with_geometry_compared": len(scores),
        "intersection_over_union_minimum": vals[0],
        "intersection_over_union_median": median(vals),
        "intersection_over_union_p05": vals[int((len(vals) - 1) * 0.05)],
        "intersection_over_union_maximum": vals[-1],
        "count_iou_at_least_0_95": sum(v >= MANUAL_REVIEW_IOU_THRESHOLD for v in vals),
        "count_manual_review_iou_below_0_95": len(low),
        "worst_ags": worst,
        "worst_iou": scores[worst]["iou"],
        "source_identity_exceptions_focus": highlights,
        # No complete per-Kreis table or polygons in Git/public receipts.
        "full_per_region_geometry_exported": False,
        "bkg_gadm_area_join_suitable_for_rva_exposure": False,
        "gadm_redistribution_or_commercial_rights_granted": False,
        "materialcities_gfa_reallocated": False,
        "zensus_2022_2025_insurer_vintage_equivalence_proven": False,
        "actual_insured_building_geocoding_proven": False,
        "cat_model_input_admitted": False,
        "research_only": True,
    }


def _required_geometry_imports():
    try:
        import shapefile
        from shapely.geometry import shape
        from shapely.ops import transform, unary_union
        from pyproj import CRS, Transformer
        import shapely
        import pyproj
    except ImportError as exc:
        raise GeometryOverlapError(
            "opt-in research requires pyshp, shapely and pyproj; no silent fallback"
        ) from exc
    return shapefile, shape, transform, unary_union, CRS, Transformer, shapely, pyproj


def inspect_original_geometry(
    bkg_zip_bytes: bytes, gadm_zip_bytes: bytes,
    materialcities_zip_bytes: bytes, zensus_toml_bytes: bytes,
) -> dict:
    # The existing four-source gate confirms SHA-256, exact 2022 AGS rosters,
    # the GADM 4.1 CC_2 and MaterialCities ID scopes, and legal exception IDs.
    code_receipt = inspect_exact_sources(
        bkg_zip_bytes, gadm_zip_bytes, materialcities_zip_bytes, zensus_toml_bytes,
        exact_pin=True, original_counts=True,
    )
    if code_receipt["historical_obsolete_ags_codes_needing_review"] != 3:
        raise GeometryOverlapError("original historical source identity changed")
    shapefile, shape, transform, unary_union, CRS, Transformer, shapely, pyproj = _required_geometry_imports()
    target = CRS.from_epsg(AREA_CRS_EPSG)
    with zipfile.ZipFile(io.BytesIO(bkg_zip_bytes)) as z:
        names = z.namelist()
        roots = [n[:-4] for n in names if n.endswith("/VG250_KRS.shp")]
        if len(roots) != 1 or any(root + x not in names for root in roots for x in (".shp", ".shx", ".dbf", ".prj")):
            raise GeometryOverlapError("BKG original KRS geometries incomplete")
        root = roots[0]
        try:
            original_prj_wkt = z.read(root + ".prj").decode("utf-8-sig")
            prj = CRS.from_wkt(original_prj_wkt)
        except (UnicodeError, ValueError) as exc:
            raise GeometryOverlapError("unreviewed BKG source projection WKT") from exc
        # The original ESRI WKT explicitly identifies EPSG:31467; PROJ 3.7
        # normalizes this easting/northing-axis variant to EPSG:5677.
        # Both represent the exact original, hash-pinned Gauss-Kruger zone 3.
        if ('AUTHORITY["EPSG",31467]' not in original_prj_wkt or
                prj.to_epsg() not in (SOURCE_CRS_EPSG, 5677)):
            raise GeometryOverlapError("BKG source GK3 CRS drift")
        source_projection = Transformer.from_crs(prj, target, always_xy=True).transform
        with shapefile.Reader(shp=io.BytesIO(z.read(root + ".shp")),
                              shx=io.BytesIO(z.read(root + ".shx")),
                              dbf=io.BytesIO(z.read(root + ".dbf")),
                              encoding="utf-8") as reader:
            bkg_groups: dict[str, list] = defaultdict(list)
            bkg_land_groups: dict[str, list] = defaultdict(list)
            bkg_marine_groups: dict[str, list] = defaultdict(list)
            bkg_gf: dict[str, list[int]] = defaultdict(list)
            bkg_rows = 0
            for entry in reader.iterShapeRecords():
                bkg_rows += 1
                properties = entry.record.as_dict()
                ags = properties.get("AGS")
                gf = properties.get("GF")
                if not isinstance(ags, str) or len(ags) != 5 or not ags.isdigit():
                    raise GeometryOverlapError("unrecognised official geometry AGS")
                if type(gf) is not int or gf not in (2, 4):
                    raise GeometryOverlapError("original BKG land/water GF source value invalid")
                geom = transform(source_projection, shape(entry.shape.__geo_interface__))
                if not geom.is_valid or geom.is_empty or geom.area <= 0:
                    raise GeometryOverlapError("invalid projected BKG original geometry")
                bkg_groups[ags].append(geom)
                bkg_gf[ags].append(gf)
                (bkg_land_groups if gf == 4 else bkg_marine_groups)[ags].append(geom)
    if bkg_rows != ORIGINAL_BKG_SHAPES or len(bkg_groups) != ORIGINAL_TARGET_AGS:
        raise GeometryOverlapError("BKG projected original geometry roster drift")
    gf_receipt = validate_bkg_geofactors(bkg_gf)
    if set(bkg_land_groups) != set(bkg_groups):
        raise GeometryOverlapError("BKG source GF4 land does not cover all 400 Kreise")

    with zipfile.ZipFile(io.BytesIO(gadm_zip_bytes)) as z:
        features = json.loads(z.read("gadm41_DEU_2.json"))["features"]
    if len(features) != ORIGINAL_GADM_FEATURES:
        raise GeometryOverlapError("GADM source geometry scope drift")
    gadm_projection = Transformer.from_crs("EPSG:4326", target, always_xy=True).transform
    gadm_groups: dict[str, list] = defaultdict(list)
    excluded_non_ags = 0
    for entry in features:
        p = entry.get("properties")
        if not isinstance(p, dict):
            raise GeometryOverlapError("GADM GeoJSON property schema changed")
        original_code = p.get("CC_2")
        if original_code == "NA":
            excluded_non_ags += 1
            continue
        target_ags = EXCEPTIONAL_OLD_TO_2022_AGS.get(original_code, original_code)
        if target_ags not in bkg_groups:
            raise GeometryOverlapError("GADM source geometry lacks a 2022 BKG AGS target")
        projected = transform(gadm_projection, shape(entry["geometry"]))
        if not projected.is_valid or projected.is_empty or projected.area <= 0:
            raise GeometryOverlapError("invalid projected original GADM geometry")
        gadm_groups[target_ags].append(projected)
    if excluded_non_ags != 1 or set(gadm_groups) != set(bkg_groups):
        raise GeometryOverlapError("incomplete countrywide original GADM geography")

    scores_land = {}
    scores_all_surfaces = {}
    for ags in sorted(bkg_groups):
        # The former study included BKG GF2 marine polygons and counted
        # spurious coastal mismatches. Preserve that view only for comparison.
        # Official GF4 means LAND; no GF2 sea/Bodensee surface is allocated
        # to buildings, irrespective of whether GADM includes similar water.
        bkg_all_geom = unary_union(bkg_groups[ags])
        bkg_land_geom = unary_union(bkg_land_groups[ags])
        gadm_geom = unary_union(gadm_groups[ags])
        if (not bkg_all_geom.is_valid or not bkg_land_geom.is_valid or
                not gadm_geom.is_valid or bkg_land_geom.is_empty or
                bkg_all_geom.is_empty or gadm_geom.is_empty):
            raise GeometryOverlapError("invalid projected original land/water region")
        land_intersection = bkg_land_geom.intersection(gadm_geom).area
        all_intersection = bkg_all_geom.intersection(gadm_geom).area
        scores_land[ags] = overlap_metrics(
            bkg_land_geom.area, gadm_geom.area, land_intersection)
        scores_all_surfaces[ags] = overlap_metrics(
            bkg_all_geom.area, gadm_geom.area, all_intersection)
    # Corrected primary metric is the 400 source GF4 LAND polygons.
    report = summarize_scores(scores_land)
    all_summary = summarize_scores(scores_all_surfaces)
    delta = compare_land_water_scores(scores_land, scores_all_surfaces)
    report.update({
        "source_original_sha256": {
            "BKG_VG250_2022_12_31": BKG_SHA256,
            "GADM_v4_1_DEU_ADM2": GADM_SHA256,
            "MaterialCities_2026_9": MATERIALCITIES_SHA256,
        },
        "source_original_bkg_shape_pieces": bkg_rows,
        "BKG_GF4_GF2_source_profile": gf_receipt,
        "original_GADM_BKG_GF4_land_only_primary_metric": True,
        "previous_all_surfaces_baseline": {
            "count_iou_at_least_0_95": all_summary["count_iou_at_least_0_95"],
            "count_manual_review_iou_below_0_95": all_summary["count_manual_review_iou_below_0_95"],
            "intersection_over_union_median": all_summary["intersection_over_union_median"],
            "intersection_over_union_minimum": all_summary["intersection_over_union_minimum"],
        },
        "land_only_vs_all_surfaces_95pct_comparison": delta,
        "source_original_gadm_level2_features": len(features),
        "source_original_non_AGS_gadm_excluded": excluded_non_ags,
        "source_original_historical_gadm_2022_ags_groups": {
            key: len(gadm_groups[key]) for key in ("03159", "16063")
        },
        "bkg_source_epsg": SOURCE_CRS_EPSG,
        "comparison_equal_area_epsg": AREA_CRS_EPSG,
        "reprojection_method": "pyproj WKT source -> ETRS89-LAEA, original GADM WGS84 -> ETRS89-LAEA",
        "geometry_engine": {
            "shapely": shapely.__version__,
            "pyproj": pyproj.__version__,
            "pyshp": shapefile.__version__,
        },
        "independent_source_vintage_equality_proven": False,
        "bkg_area_geographic_attribute_rights_reviewed": False,
    })
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bkg-zip", type=Path, required=True)
    parser.add_argument("--gadm-zip", type=Path, required=True)
    parser.add_argument("--materialcities-zip", type=Path, required=True)
    parser.add_argument("--zensus-toml", type=Path, default=Path(
        "research/observations/zensus2022_400_kreis_original_building_aggregates_v0.toml"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.out.exists():
            raise GeometryOverlapError("refuse to overwrite research receipt")
        result = inspect_original_geometry(
            args.bkg_zip.read_bytes(), args.gadm_zip.read_bytes(),
            args.materialcities_zip.read_bytes(), args.zensus_toml.read_bytes())
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, CodeCrosswalkError, GeometryOverlapError,
            ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"BLOCKED: {exc}\n")
    print("RESEARCH ONLY:", result["count_iou_at_least_0_95"], "of",
          result["unique_2022_ags_with_geometry_compared"],
          "source geography candidates >= 0.95 IoU; NO MODEL OR RIGHTS ADMISSION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
