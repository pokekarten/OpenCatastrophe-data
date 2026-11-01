#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, aggregate-only QA of one original Berlin BLD4 x BKG ring receipt.

No provider requests, external geometry or pixel arrays; never turns raw code
support into depth, hazard probability, building exposure, or insured loss.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

SOURCE_SHA = "7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f"
SOURCE_BYTES = 47_280_200
EXPECTED_BANDS = [[0, 1], [1, 3], [3, 5]]
MAX_REPORT_BYTES = 40_000
HEX_SHA256 = re.compile(r"[a-f0-9]{64}\Z")
AREA_KEYS = (
    "unique_exterior_ring_area_m2",
    "positive_raw_integer_supported_area_m2",
    "valid_numeric_zero_supported_area_m2",
    "original_masked_nodata_area_m2",
    "outside_sample_window_area_m2",
)


class ExteriorReceiptBlocked(ValueError):
    """Identity, scientific or area-conservation proof was not satisfied."""


def _nonnegative(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExteriorReceiptBlocked(f"{name}: expected a numeric area")
    if not math.isfinite(value) or value < 0:
        raise ExteriorReceiptBlocked(f"{name}: negative or nonfinite area")
    return float(value)


def _required_flag(value: dict, key: str, expected: bool) -> None:
    if not isinstance(value, dict) or value.get(key) is not expected:
        raise ExteriorReceiptBlocked(f"required scientific provenance flag: {key}")


def validate(report: object) -> dict:
    if not isinstance(report, dict):
        raise ExteriorReceiptBlocked("original report is not a JSON object")
    if report.get("profile") != "berlin-bld4-bkg-real-kostra-raw-cell-support-v0":
        raise ExteriorReceiptBlocked("wrong original two-source QA profile")
    if (report.get("source_bkg_original_tiff_sha256") != SOURCE_SHA
            or report.get("source_bkg_original_size_bytes") != SOURCE_BYTES):
        raise ExteriorReceiptBlocked("full original BKG source identity mismatch")
    wfs_sha = report.get("source_bld4_wfs_response_sha256")
    if not isinstance(wfs_sha, str) or not HEX_SHA256.fullmatch(wfs_sha):
        raise ExteriorReceiptBlocked("missing mutable ALKIS WFS response SHA256")
    if report.get("pilot_window_cells_examined") != 47089:
        raise ExteriorReceiptBlocked("unexpected original raster pilot window")
    if report.get("pilot_clipped_buildings_checked") != 5:
        raise ExteriorReceiptBlocked("not the five reviewed original-derived footprints")

    for key in (
        "source_bld4_buildings_mutable_date_not_historic",
        "source_hazard_bkg_kostra_design_scenario",
        "original_bkg_bounded_real_pixel_window_used",
        "building_coverage_from_real_bkg_raw_codes_not_depth",
        "exact_polygon_cell_area_conservation_verified",
    ):
        _required_flag(report, key, True)
    for key in (
        "source_products_temporal_alignment_proven",
        "real_water_depth_units_verified",
        "cat_model_admitted",
        "any_property_ids_or_coordinates_written",
        "actual_insurance_exposure_or_loss_estimated",
        "individual_building_or_cell_values_exported",
    ):
        _required_flag(report, key, False)

    footprint = _nonnegative(report.get("clipped_building_area_in_raster_crs_m2"), "footprint total")
    components = [
        _nonnegative(report.get(k), k)
        for k in (
            "positive_raw_code_supported_area_m2",
            "valid_zero_raw_code_supported_area_m2",
            "original_nodata_supported_area_m2",
            "outside_sample_window_area_m2",
        )
    ]
    if not 0 < footprint <= 40000 or not math.isclose(
        footprint, sum(components), rel_tol=1e-8, abs_tol=1e-5
    ):
        raise ExteriorReceiptBlocked("footprint raw-code/mask area conservation failed")

    exterior = report.get("exterior_raw_code_support_research")
    if not isinstance(exterior, dict):
        raise ExteriorReceiptBlocked("no separate exterior raw support evidence")
    if (exterior.get("original_buildings_count") != 5
            or exterior.get("exterior_rings_m") != EXPECTED_BANDS):
        raise ExteriorReceiptBlocked("wrong original buildings or ring-band intervals")
    for key in (
        "raw_int16_values_not_physical_water_depths",
        "positive_raw_code_not_confirmed_as_centimetres_or_metres",
        "building_raster_nodata_never_interpreted_as_dry",
        "building_access_or_entrance_levels_not_verified",
        "exterior_rings_not_building_loss_depth",
    ):
        _required_flag(exterior, key, True)
    for key in (
        "original_per_building_ids_coords_or_pixel_values_exported",
        "cat_model_or_insurer_exposure_admitted",
    ):
        _required_flag(exterior, key, False)

    bands = exterior.get("bands")
    if not isinstance(bands, list) or len(bands) != 3:
        raise ExteriorReceiptBlocked("exactly three exterior bands required")
    out = []
    for expected, band in zip(EXPECTED_BANDS, bands):
        if not isinstance(band, dict) or band.get("distance_from_source_building_union_m") != expected:
            raise ExteriorReceiptBlocked("out-of-order or wrong exterior ring")
        vals = {key: _nonnegative(band.get(key), key) for key in AREA_KEYS}
        area = vals["unique_exterior_ring_area_m2"]
        pieces = sum(vals[key] for key in AREA_KEYS[1:])
        if not 0 < area < 20_000 or not math.isclose(
            area, pieces, rel_tol=1e-8, abs_tol=1e-5
        ):
            raise ExteriorReceiptBlocked("exterior support areas do not conserve")
        valid_fraction = _nonnegative(band.get("valid_numeric_support_fraction"), "support fraction")
        expected_fraction = (
            vals["positive_raw_integer_supported_area_m2"] +
            vals["valid_numeric_zero_supported_area_m2"]
        ) / area
        if valid_fraction > 1 or not math.isclose(
            valid_fraction, expected_fraction, rel_tol=0, abs_tol=1.5e-6
        ):
            raise ExteriorReceiptBlocked("exterior valid-numeric fraction inconsistent")
        out.append({
            "band_m": expected,
            "ring_m2": round(area, 6),
            "positive_raw_m2": round(vals["positive_raw_integer_supported_area_m2"], 6),
            "valid_zero_raw_m2": round(vals["valid_numeric_zero_supported_area_m2"], 6),
            "nodata_m2": round(vals["original_masked_nodata_area_m2"], 6),
            "outside_window_m2": round(vals["outside_sample_window_area_m2"], 6),
            "valid_numeric_fraction": round(valid_fraction, 6),
        })

    return {
        "profile": "berlin-bld4-bkg-exterior-original-receipt-qc-v0",
        "original_bkg_full_tiff_sha256": SOURCE_SHA,
        "original_mutable_alkis_wfs_response_sha256": wfs_sha,
        "building_count_research_sample": 5,
        "footprint_area_m2": round(footprint, 6),
        "footprint_original_nodata_area_m2": round(components[2], 6),
        "exterior_bands": out,
        "independently_validated_physical_depth_units": False,
        "building_level_flood_depth_or_insured_loss_inferred": False,
        "cat_model_input_approved": False,
    }


def _no_duplicate_object_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ExteriorReceiptBlocked(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.receipt.stat().st_size > MAX_REPORT_BYTES:
            raise ExteriorReceiptBlocked("source aggregate report too large")
        report = json.loads(args.receipt.read_text(encoding="utf-8"),
                            object_pairs_hook=_no_duplicate_object_keys)
        result = validate(report)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
