#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed BKG original-pixel evidence -> insurance CAT data-readiness gate.

This module NEVER converts BKG raw integer raster codes into depths, losses,
insured exposure, claims, probabilities or per-building interpretations.
Consumes a single checked, metadata-only original-source research receipt.
No internet, model execution, provider data, arbitrary input file or DB writes.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (ROOT / "docs/research" /
           "berlin-bld4-bkg-original-exterior-ring-receipt-20261101.toml")
ORIGINAL_MAIN_SHA = "63a13bd477067527dc9e67e6e6d4ba817189178f"
BKG_TIFF_SHA = "7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f"
WFS_RESPONSE_SHA = "c4342109c0c13b31996d7cb9a5a16db56af3e536dc4910938a9fc72bab049bba"
BKG_URL = ("https://daten.gdz.bkg.bund.de/produkte/sonstige/starkregen/aktuell/"
           "be/maxdepth_kostra/s32790/starkregen_maxdepth_kostra_32790_5820_10_be.tif")
BANDS = ((0, 1), (1, 3), (3, 5))


class EvidenceBlocked(ValueError):
    """Missing, implausible or altered source evidence: no output is admitted."""


def _finite_number(value, *, positive=False) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise EvidenceBlocked("non-finite, Boolean, or nonnumeric original area")
    if value < 0 or (positive and value <= 0):
        raise EvidenceBlocked("negative or empty original area")
    return float(value)


def _source_provenance_gate(x: dict) -> None:
    if not isinstance(x, dict):
        raise EvidenceBlocked("receipt must be one TOML table")
    expected = {
        "receipt_schema": "berlin-bld4-bkg-verified-original-exterior-raw-support-v0",
        "original_github_actions_run_id": 41350285830,
        "original_main_commit": ORIGINAL_MAIN_SHA,
        "original_bkg_full_file_sha256_locally_verified": BKG_TIFF_SHA,
        "original_bkg_tiff_bytes": 47_280_200,
        "original_bkg_source_url": BKG_URL,
        "original_alkis_wfs_response_sha256": WFS_RESPONSE_SHA,
        "original_alkis_clipped_building_count": 5,
        "fixed_pilot_crs": "EPSG:25833",
        "raster_crs": "EPSG:25832",
        "original_raster_window_cells": 47_089,
        "original_raster_resolution_metres": 1,
        "research_only": True,
        "original_source_wfs_response_mutable": True,
        "all_exterior_bands_unique_and_disjoint": True,
    }
    for key, value in expected.items():
        if type(x.get(key)) is not type(value) or x[key] != value:
            raise EvidenceBlocked("original source provenance mismatch: " + key)
    # Every single scientifically required uncertainty must remain explicitly
    # *false*. Removing the key or making it true is a hard failure, never
    # a pathway for a caller to invent an unreviewed unit calibration.
    unknowns = (
        "original_numeric_raw_code_physical_depth_unit_verified",
        "original_raster_zero_indicates_observed_dryness",
        "original_raster_nodata_indicates_observed_dryness",
        "actual_building_entrance_and_basement_elevation_verified",
        "model_product_building_vintage_consistent",
        "annual_loss_probability_or_recurrence_estimated",
        "individual_building_ids_or_geometry_exported",
        "original_source_data_persisted",
        "insured_building_exposure_or_cat_loss_admitted",
    )
    for key in unknowns:
        if x.get(key) is not False:
            raise EvidenceBlocked("unauthorized promotion or incomplete gate: " + key)


def _checked_areas(x: dict) -> tuple[float, list[dict]]:
    total = _finite_number(x.get("original_building_area_total_m2"), positive=True)
    missing = _finite_number(x.get("original_building_nodata_area_m2"))
    zero = _finite_number(x.get("original_building_valid_zero_area_m2"))
    positive = _finite_number(x.get("original_building_positive_raw_area_m2"))
    outside = _finite_number(x.get("original_building_outside_window_area_m2"))
    if (not math.isclose(total, missing + zero + positive + outside, rel_tol=0, abs_tol=3e-6)
            or missing > total or x.get("original_buildings_all_area_valid") != 0
            or x.get("original_buildings_without_valid_codes") != 2
            or x.get("original_buildings_any_positive_code") != 3):
        raise EvidenceBlocked("building-polygon evidence does not conserve valid/NoData support")

    bands = x.get("exterior_bands")
    if not isinstance(bands, list) or len(bands) != len(BANDS):
        raise EvidenceBlocked("exterior band receipt is absent, missing or duplicated")
    output = []
    for band, (lo, hi) in zip(bands, BANDS):
        if (not isinstance(band, dict)
                or type(band.get("distance_min_m")) is not int
                or type(band.get("distance_max_m")) is not int
                or (band["distance_min_m"], band["distance_max_m"]) != (lo, hi)):
            raise EvidenceBlocked("unknown, reversed or overlapping exterior distance band")
        area = _finite_number(band.get("sample_area_m2"), positive=True)
        p = _finite_number(band.get("positive_raw_area_m2"))
        z = _finite_number(band.get("valid_zero_area_m2"))
        n = _finite_number(band.get("source_nodata_area_m2"))
        o = _finite_number(band.get("outside_window_area_m2"))
        valid_fraction = _finite_number(band.get("valid_numeric_support_fraction"))
        if (not math.isclose(area, p+z+n+o, rel_tol=0, abs_tol=3e-6)
                or valid_fraction > 1
                or not math.isclose(valid_fraction, (p+z)/area,
                                    rel_tol=0, abs_tol=1.1e-6)):
            raise EvidenceBlocked("original exterior area or coverage fraction inconsistent")
        output.append({
            "distance_band_m": [lo, hi],
            "original_exterior_area_m2": round(area, 6),
            "valid_numeric_support_fraction": round((p+z)/area, 6),
            "nodata_or_outside_fraction": round((n+o)/area, 6),
            "positive_raw_code_area_fraction_of_total": round(p/area, 6),
            "positive_raw_code_is_not_calibrated_depth": True,
        })
    return missing/total, output


def assess_receipt(receipt: dict) -> dict:
    """Return aggregated screening diagnostic, never a risk score.

    Strictly no numerical depth, loss, flood-status or risk-probability field
    exists in this return schema. Even full ring coverage would NOT authorize
    physically interpreting raw BKG TIFF Int16 data.
    """
    _source_provenance_gate(receipt)
    building_nodata_fraction, bands = _checked_areas(receipt)
    return {
        "profile": "bkg-berlin-hazard-quality-screening-only-v0",
        "source_evidence_run_id": 41350285830,
        "five_original_footprints_only": True,
        "original_source_metadata_verified": True,
        "raw_geometric_support_screening_available": True,
        "building_nodata_fraction": round(building_nodata_fraction, 6),
        "original_exterior_support": bands,
        "physical_depth_unit_or_scale_verified": False,
        "actual_entrance_elevation_or_basement_level_verified": False,
        "contemporaneous_alkis_building_vintage_verified": False,
        "calibrated_annual_cat_event_frequency_verified": False,
        "source_reuse_and_derivative_admission_complete": False,
        "building_depth_calculation_authorized": False,
        "insured_loss_or_tiv_calculation_authorized": False,
        "cat_model_input_admitted": False,
        "blockers": [
            "BKG_EXACT_INT16_TO_DEPTH_UNIT_SCALE_UNVERIFIED",
            "BUILDING_FOOTPRINT_MAJORITY_NODATA",
            "BUILDING_ENTRANCE_LEVELS_UNVERIFIED",
            "BLD4_2026_VS_BKG_BASELINE_VINTAGE_UNALIGNED",
            "KOSTRA_DESIGN_EVENT_NOT_AN_INSURED_ANNUAL_LOSS_DISTRIBUTION",
            "SOURCE_RIGHTS_AND_SCIENTIFIC_FITNESS_NOT_ADMITTED",
        ],
    }


def main():
    doc = tomllib.loads(RECEIPT.read_text(encoding="utf-8"))
    print(json.dumps(assess_receipt(doc), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
