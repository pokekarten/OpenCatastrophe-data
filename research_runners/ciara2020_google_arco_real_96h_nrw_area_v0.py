# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-pinned 96-hour actual Google public ARCO ERA5 10fg NRW wind area.

Read one original 0.25-degree global field chunk at a time from the
public Google Research ARCO ERA5 distribution. Inspect ONLY bounded
10x16 NRW atmospheric grid values in memory (96 x 160 = 15,360 gusts).
Output source + decoded-value SHA and aggregate hazard statistics ONLY.
No original Google compressed chunk SHA, insurer damage or loss model.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import tomllib

from ciara2020_google_arco_public_10fg_metadata_v0 import (
    VAR, SOURCE_ERA5_DATA_URL, source_metadata_receipt, PublicARCOMetadataBlocked,
)
from ciara2020_google_arco_real_onehour_gust_v0 import (
    FROZEN, verify_original_zarr_metadata,
)

SCHEMA = "CIARA2020_GOOGLE_ARCO_ORIGINAL_96H_160NODE_NRW_10FG_HAZARD_V0"
START = datetime(2020, 2, 8, tzinfo=timezone.utc)
HOURS = 96
LATITUDE = tuple(52.5 - 0.25 * i for i in range(10))
LONGITUDE = tuple(5.75 + 0.25 * i for i in range(16))
THRESHOLDS = (25.0, 30.0, 35.0, 40.0)
EXPECTED_ONEHOUR_20200209_12_LAT51_LON7_GUST_SHA = (
    "12d34d73cece12a90220ddbbb5b092e388a6b1e0d9b0c9dcf5004a01a7c3119c"
)
ONEHOUR_INDEX = 36
ONEHOUR_GRID = (6, 5)


class RealGridBlocked(ValueError):
    """Inconsistent original source, time, grid support or finite wind value."""


class WindAreaAccumulator:
    """Independent pure-Python hourly envelope with fail-closed exact support."""

    def __init__(self, expected_hours: int = HOURS):
        if type(expected_hours) is not int or not 1 <= expected_hours <= HOURS:
            raise RealGridBlocked("bounded original 1..96 hourly steps required")
        self.expected_hours = expected_hours
        self.n_hours = 0
        self.values_sha = hashlib.sha256()
        self.peaks = [[-1.0 for _ in LONGITUDE] for _ in LATITUDE]
        self.peak_hours = [[-1 for _ in LONGITUDE] for _ in LATITUDE]
        self.one_hour_sha = None

    def ingest(self, *, timestamp: str, latitudes: list[float],
               longitudes: list[float], gust_grid: list[list[float]]) -> None:
        if self.n_hours >= self.expected_hours:
            raise RealGridBlocked("extra or repeated 2020 source hour")
        hour = START + timedelta(hours=self.n_hours)
        if timestamp != hour.strftime("%Y-%m-%dT%H:%M:%SZ"):
            raise RealGridBlocked("source hour not contiguous exact UTC 2020-02-08..11")
        if (len(latitudes) != len(LATITUDE)
            or len(longitudes) != len(LONGITUDE)
            or any(type(v) not in (int, float) or v != ref
                   for v, ref in zip(latitudes, LATITUDE))
            or any(type(v) not in (int, float) or v != ref
                   for v, ref in zip(longitudes, LONGITUDE))
            or len(gust_grid) != len(LATITUDE)
            or any(len(row) != len(LONGITUDE) for row in gust_grid)):
            raise RealGridBlocked("ERA5 0.25-degree NRW grid or variable shape drift")
        for lat_i, row in enumerate(gust_grid):
            for lon_i, v in enumerate(row):
                if (type(v) not in (int, float) or not math.isfinite(v)
                    or not 0 <= v <= 150):
                    raise RealGridBlocked("masked, nonfinite, negative or implausible gust")
                raw = struct.pack("<f", v)
                self.values_sha.update(raw)
                if v > self.peaks[lat_i][lon_i]:
                    self.peaks[lat_i][lon_i] = float(v)
                    self.peak_hours[lat_i][lon_i] = self.n_hours
                if (self.n_hours == ONEHOUR_INDEX
                    and (lat_i, lon_i) == ONEHOUR_GRID):
                    self.one_hour_sha = hashlib.sha256(raw).hexdigest()
        self.n_hours += 1

    def finish(self, *, require_first_original_point: bool = True) -> dict:
        if self.n_hours != self.expected_hours:
            raise RealGridBlocked("missing one or more original hourly fields")
        if require_first_original_point and (
            self.expected_hours != HOURS
            or self.one_hour_sha != EXPECTED_ONEHOUR_20200209_12_LAT51_LON7_GUST_SHA
        ):
            raise RealGridBlocked("2020-02-09 12Z 51N/7E live source parity drift")
        peaks = [v for row in self.peaks for v in row]
        if len(peaks) != 160 or any(v < 0 for v in peaks):
            raise RealGridBlocked("source grid peak support incomplete")
        return {
            "normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256": self.values_sha.hexdigest(),
            "actual_hourly_ERA5_original_grid_timestamps_verified": self.n_hours,
            "original_source_0p25_degree_nodes": len(peaks),
            "event_max_over_96h_gust_mps_at_160_nodes_min": min(peaks),
            "event_max_over_96h_gust_mps_at_160_nodes_max": max(peaks),
            "event_max_over_96h_gust_mps_at_160_nodes_mean": sum(peaks) / len(peaks),
            "node_count_event_peak_gust_above_threshold_mps": {
                str(int(t)): sum(v >= t for v in peaks) for t in THRESHOLDS
            },
            "single_2020_02_09_12_51N_7E_source_crosscheck_sha256": self.one_hour_sha,
            "original_compressed_GCS_chunk_SHAs_independently_verified": False,
        }


def original_96h_grid(*, include_public_grid_peaks: bool = False) -> dict:
    # No full original site/insurer records required for public hazard-only
    # grid; the separate source-pinned 10k insurance OED site join remains
    # NOT performed / NOT admitted by this single-event meteorology.
    with FROZEN.open("rb") as f:
        pinned = tomllib.load(f)
    metadata = source_metadata_receipt()
    verify_original_zarr_metadata(metadata, pinned)
    try:
        import numpy as np
        import xarray as xr
        ds = xr.open_zarr(
            SOURCE_ERA5_DATA_URL, chunks=None,
            storage_options={"token": "anon"}, consolidated=True,
        )
        field = ds[VAR]
        if (field.dims != ("time", "latitude", "longitude")
            or field.attrs.get("units") not in ("m/s", "m s-1", "m s**-1")):
            raise RealGridBlocked("real source is not unambiguous original hourly 10fg m/s")
        requested = field.sel(time=slice(
            "2020-02-08T00:00:00", "2020-02-11T23:00:00"
        ))
        time_coord = requested["time"].values
        if len(time_coord) != HOURS or any(
            np.datetime_as_string(t, unit="s")
            != (START + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%S")
            for i, t in enumerate(time_coord)
        ):
            raise RealGridBlocked("source 2020-02-08..11 UTC time axis is not 96 unique hours")
        # Public reanalysis latitude is descending and longitude ascending.
        cropped = requested.sel(
            latitude=slice(LATITUDE[0], LATITUDE[-1]),
            longitude=slice(LONGITUDE[0], LONGITUDE[-1]),
        )
        if (cropped.sizes.get("latitude") != 10
            or cropped.sizes.get("longitude") != 16
            or cropped.sizes.get("time") != HOURS):
            raise RealGridBlocked("source 0.25 degree NRW target grid not supported")
        lats = [float(v) for v in cropped.latitude.values]
        lons = [float(v) for v in cropped.longitude.values]
        acc = WindAreaAccumulator()
        for h in range(HOURS):
            # One time chunk at a time: no full 96xglobal array retained.
            block = cropped.isel(time=h).values
            if block.shape != (10, 16) or np.ma.is_masked(block):
                raise RealGridBlocked("missing one-hour original field")
            # Reading a whole global source chunk is a property of the
            # publisher's current (1 x 721 x 1440) chunking, not a 10k-site
            # physical-building download. Only 160 decoded node values/h.
            acc.ingest(
                timestamp=(START + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                latitudes=lats, longitudes=lons,
                gust_grid=[[float(v) for v in row] for row in block],
            )
        outcome = acc.finish()
    except RealGridBlocked:
        raise
    except (OSError, RuntimeError, ValueError, TypeError, ImportError, KeyError) as exc:
        raise RealGridBlocked("public original 96h Google ARCO bounded read failed") from None

    # The first actually successful original publisher replay on GitHub is
    # frozen independently as a factual source receipt. Reject source-data
    # drift without provenance review rather than silently republishing.
    accepted_path = (FROZEN.parent /
        "ciara2020_google_arco_real_96h_160node_nrw_gust_20261113.toml")
    with accepted_path.open("rb") as handle:
        accepted = tomllib.load(handle)
    if (accepted.get("schema") != SCHEMA
        or accepted.get("github_live_ci_run_id") != 43482459090
        or accepted.get("original_hourly_time_steps") != HOURS
        or accepted.get("verified_original_10fg_gust_scalar_count") != HOURS * 160
        or accepted.get("canonical_decoded_96h_10x16_float32_le_sha256_not_original_zarr_chunk_sha256")
        != outcome["normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256"]
        or accepted.get("earlier_source_2020_02_09_12_51N_7E_float32_sha256")
        != outcome["single_2020_02_09_12_51N_7E_source_crosscheck_sha256"]
        or accepted.get("event_gridpoint_peak_gust_mps_min")
        != outcome["event_max_over_96h_gust_mps_at_160_nodes_min"]
        or accepted.get("event_gridpoint_peak_gust_mps_mean")
        != outcome["event_max_over_96h_gust_mps_at_160_nodes_mean"]
        or accepted.get("event_gridpoint_peak_gust_mps_max")
        != outcome["event_max_over_96h_gust_mps_at_160_nodes_max"]
        or any(accepted.get(f"node_count_peak_gust_ge{t}mps")
               != outcome["node_count_event_peak_gust_above_threshold_mps"][str(t)]
               for t in (25, 30, 35, 40))
        or accepted.get("original_compressed_GCS_chunk_shas_verified") is not False
        or accepted.get("building_vulnerability_fit_and_native_GUL_IL_RI_OEP_AEP_admitted") is not False):
        raise RealGridBlocked("new original 96h publisher field differs from independently verified first live-source receipt")

    result = {
        "schema": SCHEMA,
        "status": "PUBLIC_ORIGINAL_GOOGLE_ARCO_REAL_96H_160NODE_GUST_HAZARD_NO_LOSS",
        "original_publisher": "Google Research ARCO ERA5; underlying C3S/ECMWF",
        "public_original_source": SOURCE_ERA5_DATA_URL,
        "source_variable": VAR,
        "source_units": "m/s",
        "event_utc_first": "2020-02-08T00:00:00Z",
        "event_utc_last_inclusive": "2020-02-11T23:00:00Z",
        "area_n_w_s_e": [52.5, 5.75, 50.25, 9.5],
        "underlying_source_0p25_degree_hourly_support": 96,
        "previous_original_metadata_SHA256s_match": True,
        "google_public_data_licence": "Copernicus Licence with C3S attribution",
        **outcome,
        "NRW_2022_public_building_candidate_geocodes_joined": False,
        "source_verified_10k_fictional_OED_sites_joined": False,
        "real_RV_insurer_claims_or_policy_terms_obtained": False,
        "German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted": False,
        "annual_event_catalogue_or_annual_EP_admitted": False,
    }
    if include_public_grid_peaks:
        # Explicit opt-in, in-memory-only interface for separate source-pinned
        # public HU22 fictitious OED aggregation. Do not print individual sites
        # or alter the default original-source-only CLI evidence contract.
        result["_internal_public_10x16_event_peak_gust_mps"] = [
            list(row) for row in acc.peaks
        ]
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    options = p.add_mutually_exclusive_group(required=True)
    options.add_argument("--dry-run", action="store_true")
    options.add_argument("--live-96h", action="store_true")
    args = p.parse_args()
    try:
        if args.dry_run:
            result = {
                "schema": SCHEMA,
                "status": "PUBLIC_GOOGLE_ORIGINAL_96H_160NODE_CIARA_SOURCE_NOT_YET_READ",
                "original_source": SOURCE_ERA5_DATA_URL,
                "source_variable": VAR,
                "hours_requested": HOURS,
                "grid_nodes_requested": 160,
                "original_Ciara_96h_values_retrieved": False,
                "German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted": False,
            }
        else:
            result = original_96h_grid()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (RealGridBlocked, PublicARCOMetadataBlocked, OSError) as exc:
        p.exit(2, "GOOGLE_ORIGINAL_CIARA2020_96H_160NODE_NO_GO: " + str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
