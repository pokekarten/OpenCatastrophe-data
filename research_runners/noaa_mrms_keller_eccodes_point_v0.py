#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Decode four physical MESH source cells near one NOAA historical hail report.

Fixed source object only; TLS/source SHA256/CRC and GRIB section integrity are
checked before ecCodes is called. No source bytes, full field, raster output,
or model/insured-loss data are written. This is a research *point comparison*,
not a CAT frequency, vulnerability or claim/loss calibration.
Run only in the opt-in, path-scoped research workflow.
"""
from __future__ import annotations

import importlib
import json
import math
import sys
from typing import Any

from research_runners.noaa_mrms_mesh_direct_https_proof_v0 import (
    DirectSourceProofError,
    fetch_pinned_original_object,
)
from research_runners.noaa_mrms_mesh_original_preflight_v0 import (
    MRMSPreflightError,
    SOURCE_OBJECTS,
    audit_original,
    inflate_gzip_capped,
)

PRODUCT = "mesh_keller_2021"
REPORT_LAT = 32.92
REPORT_LON = -97.29
REPORTED_HAIL_MM = 63.5
REPORT_NCEI_ID = 956694
MAX_RADIUS_KM = 2.0


class PointDecodeError(ValueError):
    """The point comparison is not scientifically or technically grounded."""


def _expected_four_indices(geography: dict) -> set[int]:
    """The rounded report point is close to a *four-cell corner*, not unique."""
    if geography.get("geometry_checked") is not True:
        raise PointDecodeError("original GRIB geographic grid not checked")
    grid_nx, grid_ny = geography["nx"], geography["ny"]
    longitude = REPORT_LON % 360
    step_i = geography["longitude_increment_deg"]
    step_j = geography["latitude_increment_deg"]
    fi = ((longitude - geography["longitude_first_east_0_360_deg"]) /
          (step_i * (1 if geography["i_eastward"] else -1)))
    fj = ((REPORT_LAT - geography["latitude_first_deg"]) /
          (step_j * (1 if geography["j_northward"] else -1)))
    ii = math.floor(fi)
    jj = math.floor(fj)
    if not (0 <= ii < grid_nx - 1 and 0 <= jj < grid_ny - 1):
        raise PointDecodeError("rounded report not surrounded by four grid cells")
    if not (0.40 <= fi - ii <= 0.60 and 0.40 <= fj - jj <= 0.60):
        raise PointDecodeError("source report point is not near four-cell corner")
    return {row * grid_nx + col for row in (jj, jj + 1) for col in (ii, ii + 1)}


def decode_original_keller(blob: bytes, decoder: Any = None) -> dict:
    """Validate original provider object then read four ecCodes nearest cells."""
    pinned = SOURCE_OBJECTS[PRODUCT]
    try:
        receipt = audit_original(blob, PRODUCT, pinned["basename"])
        if receipt["reference_utc"] != "2021-04-29T01:36:39+00:00":
            raise PointDecodeError("source UTC is not fixed report-window snapshot")
        geography = receipt["grid_geography"]
        expected = _expected_four_indices(geography)
        message = inflate_gzip_capped(blob)
    except MRMSPreflightError as exc:
        raise PointDecodeError("original SHA/gzip/GRIB verification failed") from exc
    if decoder is None:
        try:
            decoder = importlib.import_module("eccodes")
        except ImportError as exc:
            raise PointDecodeError("reviewed ecCodes dependency unavailable") from exc
    handle = None
    try:
        handle = decoder.codes_new_from_message(message)
        if handle is None:
            raise PointDecodeError("ecCodes did not open the verified GRIB2 message")
        exact = {
            "discipline": 209,
            "parameterCategory": 3,
            "parameterNumber": 28,
            "numberOfPoints": 24_500_000,
            "Ni": 7000,
            "Nj": 3500,
            "scanningMode": 0,
            "gridType": "regular_ll",
        }
        for key, expected_value in exact.items():
            if decoder.codes_get(handle, key) != expected_value:
                raise PointDecodeError("ecCodes original grid/product definition drift: " + key)
        # ecCodes uses great-circle nearest-point logic instead of the
        # nominal row/column-only rounding of our independent GRIB parser.
        nearest = decoder.codes_grib_find_nearest(
            handle, REPORT_LAT, REPORT_LON, is_lsm=False, npoints=4
        )
        if len(nearest) != 4:
            raise PointDecodeError("ecCodes failed to return exactly four nearest points")
        received_indices: set[int] = set()
        observations = []
        missing_sentinel = float(decoder.codes_get(handle, "missingValue"))
        for cell in nearest:
            idx = int(cell.index)
            lat = float(cell.lat)
            lon = float(cell.lon)
            dist = float(cell.distance)
            val = float(cell.value)
            if (idx not in expected or idx in received_indices
                    or not math.isfinite(lat) or not math.isfinite(lon)
                    or not math.isfinite(dist) or dist > MAX_RADIUS_KM
                    or abs(lat - REPORT_LAT) > 0.02
                    or abs(((lon - REPORT_LON + 180) % 360) - 180) > 0.02):
                raise PointDecodeError("ecCodes nearest four disagree with verified GRIB geography")
            received_indices.add(idx)
            is_missing = not math.isfinite(val) or val == missing_sentinel or val > 1e10
            if not is_missing and (val < 0 or val > 1000):
                raise PointDecodeError("unphysical or wrongly scaled decoded MESH")
            observations.append({
                "grib_flat_index_zero_based": idx,
                "grid_row_zero_based": idx // geography["nx"],
                "grid_column_zero_based": idx % geography["nx"],
                "latitude_deg": round(lat, 6),
                "longitude_deg_east_0_360": round(lon % 360, 6),
                "distance_to_report_km": round(dist, 4),
                "value_status": "missing" if is_missing else "decoded_radar_mesh_mm",
                "decoded_radar_mesh_mm": None if is_missing else round(val, 3),
            })
        if received_indices != expected:
            raise PointDecodeError("ecCodes nearest four omit adjacent report cells")
        observations.sort(key=lambda item: item["grib_flat_index_zero_based"])
        valid = [row["decoded_radar_mesh_mm"] for row in observations
                 if row["value_status"] == "decoded_radar_mesh_mm"]
        return {
            "schema_version": "noaa-mrms-keller-eccodes-four-cell-v0",
            "original_object_key": pinned["key"],
            "original_compressed_sha256": receipt["compressed_sha256"],
            "original_verified_gzip_crc32": receipt["gzip_crc32_checked"],
            "grib2_decoded_message_size": receipt["decoded_grib_bytes"],
            "ecCodes_python_version": str(getattr(decoder, "__version__", "unreported")),
            "grib2_origin_utc": receipt["reference_utc"],
            "independent_ground_report_ncei_id": REPORT_NCEI_ID,
            "independent_report_utc": "2021-04-29T01:37:00Z",
            "independent_report_latitude_deg": REPORT_LAT,
            "independent_report_longitude_deg": REPORT_LON,
            "independent_reported_hail_diameter_mm": REPORTED_HAIL_MM,
            "report_point_has_four_near_equal_neighbours": True,
            "source_grid_nx": geography["nx"],
            "source_grid_ny": geography["ny"],
            "source_grid_increments_deg": [geography["latitude_increment_deg"],
                                           geography["longitude_increment_deg"]],
            "four_nearest_radar_cells": observations,
            "valid_neighbour_count": len(valid),
            "missing_neighbour_count": 4 - len(valid),
            "decoded_local_min_radar_mesh_mm": min(valid) if valid else None,
            "decoded_local_max_radar_mesh_mm": max(valid) if valid else None,
            "physical_model_skill_established": False,
            "source_or_model_admitted": False,
            "annual_hail_frequency_estimated": False,
            "insured_losses_or_tiv_inferred": False,
            "original_source_bytes_committed_or_uploaded": False,
        }
    except PointDecodeError:
        raise
    except (ValueError, TypeError, RuntimeError, AttributeError, KeyError) as exc:
        raise PointDecodeError("independent ecCodes decoding/metadata check failed") from exc
    finally:
        if handle is not None:
            decoder.codes_release(handle)


def main() -> int:
    try:
        original = fetch_pinned_original_object(PRODUCT)
        receipt = decode_original_keller(original)
    except (DirectSourceProofError, PointDecodeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
