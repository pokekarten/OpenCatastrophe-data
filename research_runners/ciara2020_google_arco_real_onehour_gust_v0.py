# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Read one actual 2020 Ciara hourly 10fg gust from PUBLIC Google ARCO ERA5.

One fixed original 2020 UTC hour and one public 0.25-degree GRID CELL only.
This is not 96h, not 10k insured buildings, not event-max gust or GUL.
Google Research public distribution has Copernicus Licence attribution and
does not require authenticating to the distinct CDS account portal.
Never falls back to synthetic values or 10m mean U/V wind.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import struct
import tomllib

from ciara2020_google_arco_public_10fg_metadata_v0 import (
    SOURCE_ERA5_DATA_URL, VAR, SCHEMA as SOURCE_SCHEMA,
    source_metadata_receipt, PublicARCOMetadataBlocked,
)

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "research/observations/ciara2020_google_arco_10fg_public_original_metadata_receipt_20261112.toml"
SCHEMA = "CIARA2020_GOOGLE_ARCO_ONE_REAL_HOUR_ONE_GRIDPOINT_GUST_V0"
REQUESTED_HOUR = "2020-02-09T12:00:00"
REQUESTED_LATITUDE = Decimal("51.0")
REQUESTED_LONGITUDE = Decimal("7.0")
MAX_GUST_MPS = Decimal("150")


class OriginalWindBlocked(ValueError):
    """Original source/coordinate/time/magnitude not independent and safe."""


def verify_original_zarr_metadata(original: dict, pinned: dict) -> None:
    if (original.get("schema") != SOURCE_SCHEMA
        or original.get("public_original_cloud_metadata_fetched_without_cds_token") is not True
        or original.get("source_original_2020_10fg_hourly_values_fetched") is not False
        or original.get("original_public_gcs_url") != SOURCE_ERA5_DATA_URL
        or pinned.get("github_workflow_run_id") != 43306507106
        or pinned.get("origin") != SOURCE_ERA5_DATA_URL
        or pinned.get("original_wind_data_values_read") is not False):
        raise OriginalWindBlocked("unpinned or not-source-observed public Google Zarr")
    a = original.get("public_original_zarr_v2_metadata", {})
    b = pinned.get("original_variables", {})
    if set(a) != set(b) or set(b) != {VAR, "time", "latitude", "longitude"}:
        raise OriginalWindBlocked("original source variable population changed")
    for name in b:
        for theirs, ours in (
            ("original_metadata_sha256", "sha256"),
            ("original_metadata_bytes", "metadata_bytes"),
            ("shape", "shape"),
            ("chunks", "chunks"),
            ("dtype", "dtype")
        ):
            if a[name].get(theirs) != b[name].get(ours):
                raise OriginalWindBlocked("previously verified original public Zarr metadata SHA changed")


def validate_hour_sample(
    *, variable: str, time_iso: str, latitude: str, longitude: str,
    source_units: str, value: str
) -> dict:
    if variable != VAR or source_units not in ("m/s", "m s**-1", "m s-1"):
        raise OriginalWindBlocked("wrong meteorological 10fg field or units")
    try:
        timestamp = datetime.fromisoformat(time_iso.replace("Z", "+00:00"))
        lat, lon, gust = Decimal(latitude), Decimal(longitude), Decimal(value)
    except (ValueError, InvalidOperation, TypeError) as exc:
        raise OriginalWindBlocked("time, coordinate or wind is not finite decimal") from exc
    if (timestamp.tzinfo is None
        or timestamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") != REQUESTED_HOUR
        or not lat.is_finite() or not lon.is_finite() or not gust.is_finite()
        or lat != REQUESTED_LATITUDE or lon != REQUESTED_LONGITUDE
        or not Decimal(0) <= gust <= MAX_GUST_MPS):
        raise OriginalWindBlocked("wrong historical hour/gridpoint or non-finite gust")
    binary_value = struct.pack("<f", float(gust))
    return {
        "schema": SCHEMA,
        "status": "PUBLIC_ORIGINAL_GOOGLE_ARCO_HOURLY_GUST_ONE_CELL_NO_LOSS",
        "time_utc": REQUESTED_HOUR + "Z",
        "original_wind_variable": VAR,
        "grid_lat": float(lat),
        "grid_lon": float(lon),
        "gust_mps": str(gust),
        "gridpoint_value_float32_le_sha256_not_source_chunk_sha": hashlib.sha256(binary_value).hexdigest(),
        "source_ERA5_reanalysis_not_station_or_insured_claim": True,
        "original_2020_Ciara_event_window_one_hour_not_full_96h": True,
        "matched_NRW_public_buildings_or_real_insured_contracts": False,
        "source_original_GCS_full_chunk_sha256_verified": False,
        "German_wind_damage_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted": False,
    }


def actual_original_onehour() -> dict:
    with FROZEN.open("rb") as f:
        pinned = tomllib.load(f)
    # Four publisher-original metadata SHA values must match the accepted,
    # previously independently verified 2026-11-12 source receipt.
    proof = source_metadata_receipt()
    verify_original_zarr_metadata(proof, pinned)
    try:
        import numpy as np
        import xarray as xr
        ds = xr.open_zarr(
            SOURCE_ERA5_DATA_URL, chunks=None,
            storage_options={"token": "anon"}, consolidated=True,
        )
        if VAR not in ds or set(ds[VAR].dims) != {"time", "latitude", "longitude"}:
            raise OriginalWindBlocked("original Google Zarr 10fg dimension names unexpected")
        da = ds[VAR]
        selected = da.sel(time=REQUESTED_HOUR).sel(
            latitude=float(REQUESTED_LATITUDE), longitude=float(REQUESTED_LONGITUDE),
            method="nearest",
        )
        if selected.ndim != 0 or np.ma.is_masked(selected.values):
            raise OriginalWindBlocked("original hourly requested scalar gust is missing")
        original = validate_hour_sample(
            variable=VAR,
            time_iso=str(np.datetime_as_string(selected.time.values, unit="s")) + "Z",
            latitude=str(float(selected.latitude.values)),
            longitude=str(float(selected.longitude.values)),
            source_units=str(da.attrs.get("units", "")),
            value=str(float(selected.values)),
        )
    except (ImportError, KeyError, OSError, RuntimeError, ValueError) as exc:
        if isinstance(exc, OriginalWindBlocked):
            raise
        raise OriginalWindBlocked("real anonymous original Google Zarr hourly read failed") from None
    return {
        **original,
        "original_public_source_url": SOURCE_ERA5_DATA_URL,
        "original_metadata_sha256s_verified_against_GitHub_live_source": True,
        "attribution": "Copernicus Climate Change Service (C3S), Google Research ARCO-ERA5",
        "source_data_licence": "Copernicus Licence with C3S attribution",
        "2020_single_hour_reanalysis_value_obtained": True,
        "source_10fg_underlying_ERA5_modelled_wind_not_real_loss": True,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--live-one-hour", action="store_true")
    args = p.parse_args()
    try:
        if args.dry_run:
            receipt = {
                "schema": SCHEMA,
                "status": "GOOGLE_ARCO_ONE_REAL_HOUR_PUBLIC_SOURCE_CANDIDATE_NOT_FETCHED",
                "time_utc": REQUESTED_HOUR + "Z",
                "grid_lat": float(REQUESTED_LATITUDE),
                "grid_lon": float(REQUESTED_LONGITUDE),
                "original_2020_10fg_values_fetched": False,
                "insured_loss_calibrated": False,
            }
        else:
            receipt = actual_original_onehour()
        print(json.dumps(receipt, sort_keys=True, indent=2))
        return 0
    except (OriginalWindBlocked, OSError, PublicARCOMetadataBlocked) as exc:
        p.exit(2, "GOOGLE_ORIGINAL_ERA5_10FG_REAL_HOUR_NOT_ADMITTED: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
