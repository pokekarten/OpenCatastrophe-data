#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, fail-closed GHSL E2020 vs recent BVV HU-BY area comparability.

Consumes read-only, independently retrieved Neon aggregate rows 49/50 and
a successful trusted-main COMPLETE original BVV SHP source-run JSON receipt.
Produces only descriptive same-ROI area ratios with a mandatory temporal
mismatch warning. It does NOT download source pixels or SHP, admit model
inputs, infer unique buildings, insurer TIV, losses or historical accuracy.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re
import sys
from research_runners.bvv_oberbayern_full_shp_roi_stream_v0 import (
    URL as BVV_SOURCE, SOURCE_PREFIX_SHA256, UNCOMPRESSED_SHP_BYTES,
    ORIGINAL_DIRECTORY_CRC32_CLAIM, EXPECTED_SHX_ENTRIES,
    READ_BYTES, RANGE, MAX_ORIGINAL_SEGMENT_BYTES, frozen_roi_geometries,
)

SAMPLES={
    49: {
        "id":"ec-jrc.ghsl.ghs-built-s.r2023a",
        "sha":"9b3e183d113c10f0fa1a1142ce9041813043874980eac67f038ef39802fd0ed5",
        "block":"eae39538ec234c80d43f135e7022e1c2ad4be3e10d72dcdc2e82534431a276d9",
        "window":"2f1a3322b2081e70e8e7b08339dc14b61d5286605208f063fd57539e80121106",
        "raw_sum":74802406,"units":"square_metres_built_surface_per_cell",
    },
    50: {
        "id":"ec-jrc.ghsl.ghs-built-v.r2023a",
        "sha":"a9bf86d9fbbe6c84fbd81ad6050a2d8774171af38953b7976e6dd48eabc01876",
        "block":"578a62b6164f30ab82479e37cbfbf4353af2db18ff2eef65552aff5dce12e53c",
        "window":"2929b3c7e33e00948ca6589bec268eb80ff59bafe13d9463e8440ee7bf298ec9",
        "raw_sum":520775503,"units":"cubic_metres_built_volume_per_cell",
    },
}
SHA=re.compile(r"^[a-f0-9]{64}$")
EXPECTED_SEGMENTS=(READ_BYTES + MAX_ORIGINAL_SEGMENT_BYTES-1)//MAX_ORIGINAL_SEGMENT_BYTES
MAX_JSON_BYTES=150_000


class ComparisonBlocked(ValueError):
    """Unreviewed original source, area, CRS, epoch or science admission."""


def _sha(value):
    if not isinstance(value,str) or not SHA.fullmatch(value):
        raise ComparisonBlocked("original source SHA-256 is missing or malformed")
    return value


def _integer(value):
    return type(value) is int and not isinstance(value,bool)


def verify_ghsl_neon_row(row, ident):
    rule=SAMPLES[ident]
    if (type(row) is not dict
        or row.get("sample_id")!=ident
        or row.get("source_id")!=rule["id"]
        or row.get("sample_kind")!="observed_values"
        or row.get("sample_sha256")!=rule["sha"]
        or row.get("provider_response_sha256")!=rule["block"]
        or row.get("research_only") is not True
        or row.get("model_input_approved") is not False):
        raise ComparisonBlocked("not the original pinned research-only Neon GHSL sample")
    j=row.get("sample_json")
    if (type(j) is not dict
        or j.get("source_id")!=rule["id"]
        or j.get("profile")!="oc-ghsl-e2020-original-native-32x32-values-aggregate-research-v0"
        or j.get("product_epoch")!=2020
        or j.get("source_license")!="CC BY 4.0"
        or j.get("model_input_approved") is not False
        or j.get("fixed_original_window_shape")!=[32,32]
        or j.get("fixed_original_window_global_col_row")!=[22973,4899]
        or j.get("original_source_compressed_block_sha256")!=rule["block"]
        or j.get("fixed_window_uint32_le_sha256")!=rule["window"]
        or j.get("original_data_unit_from_publisher")!=rule["units"]
        or j.get("fixed_window_positive_sum_raw_source_units")!=rule["raw_sum"]
        or j.get("fixed_window_positive_non_sentinel_cells")!=937
        or j.get("fixed_window_zero_cells")!=87
        or j.get("fixed_window_potential_uint32_max_sentinel_cells")!=0
        or j.get("source_pixel_window_values_observed_for_research_only") is not True
        or j.get("individual_source_raster_pixels_persisted") is not False
        or j.get("insurer_exposure_or_tiv_inferred") is not False
        or j.get("native_window_scientifically_calibrated") is not False):
        raise ComparisonBlocked("native GHSL original window source evidence drift")
    return rule["raw_sum"]


def verify_full_bvv_receipt(row):
    if type(row) is not dict or row.get("source_id")!="de.bayern.hausumringe":
        raise ComparisonBlocked("missing original official Bavarian SHP source")
    exact={
        "profile":"oc-bvv-original-oberbayern-complete-shp-ghsl-roi-v0",
        "official_source_url":BVV_SOURCE,
        "original_member":"hausumringe.shp",
        "exact_source_range":RANGE,
        "original_partial_first_49197_sha256":SOURCE_PREFIX_SHA256,
        "original_full_decoded_shape_bytes":UNCOMPRESSED_SHP_BYTES,
        "original_full_decoded_shape_crc32":f"{ORIGINAL_DIRECTORY_CRC32_CLAIM:08x}",
        "original_full_native_records_checked":EXPECTED_SHX_ENTRIES,
        "original_shape_polygons_checked":EXPECTED_SHX_ENTRIES,
        "full_original_member_compressed_bytes":READ_BYTES-45,
        "provider_original_206_segments_verified":EXPECTED_SEGMENTS,
        "provider_source_range_mode":"contiguous_exact_206_bounded_segments",
        "original_source_epoch_is_2020":False,
        "ghsl_source_epoch":2020,
        "roi_complete_for_this_verified_SHAPE_archive_only":True,
        "original_cadastre_survey_vintage_verified":False,
        "historical_2020_ground_truth_verified":False,
        "ghsl_actual_accuracy_or_tiv_validated":False,
        "source_coordinates_geometries_or_bytes_persisted":False,
        "source_bytes_committed_or_persisted":False,
        "model_input_approved":False,
        "complete_original_zip_hash_verified":False,
        "official_BVV_HU_BY_CC_BY_4_license_only":True,
    }
    for k,v in exact.items():
        if row.get(k)!=v:
            raise ComparisonBlocked("original BVV complete source gate failed: "+k)
    _sha(row.get("original_full_decoded_shape_sha256"))
    _sha(row.get("full_original_compressed_member_sha256"))
    if (not _integer(row.get("roi_original_polygon_records_intersecting"))
        or not _integer(row.get("roi_bbox_candidates"))
        or not 0<row["roi_original_polygon_records_intersecting"]<=row["roi_bbox_candidates"]<=EXPECTED_SHX_ENTRIES
        or row.get("roi_invalid_geos_rings")!=0
        or row.get("roi_invalid_geos_polygons")!=0):
        raise ComparisonBlocked("incomplete or invalid original cadastral ROI geometry")
    roi, _=frozen_roi_geometries()
    expected_area=roi.area
    measured_area=row.get("projected_utm32_study_roi_area_m2")
    area=row.get("roi_original_polygon_areas_union_m2")
    total=row.get("roi_original_polygon_areas_sum_pre_union_m2")
    overlap=row.get("roi_original_polygon_overlap_area_m2")
    if any(type(v) not in (int,float) or not math.isfinite(v)
           for v in (measured_area,area,total,overlap)):
        raise ComparisonBlocked("missing numeric official ROI area aggregates")
    if abs(measured_area-expected_area)>0.01:
        raise ComparisonBlocked("original BVV ROI support not identical to pinned GHSL grid")
    if (not 0 < area <= measured_area+0.01
        or not area-0.01<=total
        or not 0<=overlap+0.01
        or abs((total-area)-overlap)>0.02):
        raise ComparisonBlocked("original BVV union/overlap area conservation failed")
    if not _integer(row.get("roi_geos_union_batches_completed")) or row["roi_geos_union_batches_completed"]<1:
        raise ComparisonBlocked("original ROI union never completed")
    return area, measured_area


def compare(surface,volume,bvv):
    s=verify_ghsl_neon_row(surface,49)
    v=verify_ghsl_neon_row(volume,50)
    footprint_area,roi_area=verify_full_bvv_receipt(bvv)
    ratio=footprint_area/s
    return {
        "profile":"oc-ghsl-e2020-vs-hu-by-recent-cross-epoch-area-descriptive-gate-v0",
        "ghsl_surface_neon_sample":49,
        "ghsl_volume_neon_sample":50,
        "bvv_original_receipt_is_full_2_703_736_frame_shp":True,
        "original_bvv_complete_shp_sha256":bvv["original_full_decoded_shape_sha256"],
        "original_ghsl_built_surface_e2020_sum_m2":s,
        "original_ghsl_built_volume_e2020_sum_m3_context_only":v,
        "original_bvv_current_cadastre_roi_polygon_union_m2":round(footprint_area,3),
        "same_roi_projected_area_m2":round(roi_area,3),
        "current_bvv_union_over_ghsl_e2020_modelled_surface_ratio":round(ratio,6),
        "difference_current_bvv_union_minus_ghsl_2020_surface_m2":round(footprint_area-s,3),
        "bvv_nonrandom_2026_source_not_historical_2020_ground_truth":True,
        "ratio_is_accuracy_or_model_calibration_metric":False,
        "ghsl_built_volume_not_comparable_to_bvv_2d_footprint_directly":True,
        "individual_original_data_coordinates_or_pixels_emitted":False,
        "insurer_tiv_or_losses_validated":False,
        "research_only":True,
        "model_input_approved":False,
    }


def _read(p):
    f=Path(p)
    if not f.is_file() or f.stat().st_size>MAX_JSON_BYTES:
        raise ComparisonBlocked("exact local research receipt missing or oversized")
    with f.open("r",encoding="utf8") as handle:
        v=json.load(handle)
    if type(v) is not dict:
        raise ComparisonBlocked("local research input not object")
    return v


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ghsl-s-neon",required=True)
    p.add_argument("--ghsl-v-neon",required=True)
    p.add_argument("--bvv-full-source-receipt",required=True)
    args=p.parse_args(argv)
    try:
        print(json.dumps(compare(_read(args.ghsl_s_neon),_read(args.ghsl_v_neon),
                                 _read(args.bvv_full_source_receipt)),
                         sort_keys=True,allow_nan=False))
        return 0
    except (ComparisonBlocked,OverflowError,ValueError,OSError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
