# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict *normalized* hourly Ciara2020 ERA5 10fg NetCDF grid source preflight.

DOES NOT download CDS, accept licenses, parse an uninspected original CDS
layout, or assert insurer loss / wind-vulnerability calibration.
Provider output naming/time-coordinate conventions are NOT attested yet.
The normalization step must be reviewed separately against ORIGINAL bytes.
No original weather bytes or public building coordinates are written to Git.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from ciara2020_nrw_10k_era5_area_request_v0 import (
    STEP, SOURCE_ARTIFACT_SHA256, SOURCE_CSV_SHA256,
    EXPECTED_SITES, EXPECTED_SOURCE_TIV_EUR,
    _coordinate, plan_from_archived_source,
)

SCHEMA = "CIARA2020_NRW10K_NORMALIZED_ERA5_10FG_NETCDF_HAZARD_AUDIT_V0"
GUST_NAME = "i10fg"
GUST_SOURCE_NAME = "10m_wind_gust_since_previous_post_processing"
LAT_NODES = tuple(Decimal("52.50") - STEP * i for i in range(10))
LON_NODES = tuple(Decimal("5.75") + STEP * i for i in range(16))
THRESHOLDS = (25, 30, 35, 40)
NETCDF_MAX_BYTES = 30_000_000
TIME_UNITS = "hours since 2020-02-08 00:00:00"
CALENDAR = "proleptic_gregorian"
DIMENSIONS = {"time": 96, "latitude": 10, "longitude": 16}


class CiaraNetCDFBlocked(ValueError):
    """An unreviewed source, malformed CF structure or unsafe model admission."""


def _load_netcdf4():
    try:
        import netCDF4
    except ImportError as exc:
        raise CiaraNetCDFBlocked(
            "pinned optional netCDF4 acquisition dependency required; no silent fallback"
        ) from exc
    return netCDF4


def _validate_regular_file(path: Path) -> None:
    if (path.is_symlink() or not path.is_file() or path.suffix.lower() != ".nc"
        or not 512 <= path.stat().st_size <= NETCDF_MAX_BYTES):
        raise CiaraNetCDFBlocked("regular bounded normalized NetCDF .nc file required")


def read_normalized_grid(path: Path) -> dict:
    """Inspect exact 96x10x16 normalized ERA5 shape and all finite source values.

    The returned cell peaks are temporary memory, never a native hazard or
    insured-damage product. A source-provenance attestation is intentionally
    NOT inferred from a self-described NetCDF file.
    """
    _validate_regular_file(path)
    netcdf4 = _load_netcdf4()
    try:
        with netcdf4.Dataset(str(path), "r") as ds:
            if ds.data_model != "NETCDF4":
                raise CiaraNetCDFBlocked("normalized NetCDF4/HDF5 format required")
            if (set(ds.dimensions) != set(DIMENSIONS)
                or any(len(ds.dimensions[k]) != count or ds.dimensions[k].isunlimited()
                       for k, count in DIMENSIONS.items())):
                raise CiaraNetCDFBlocked("required fixed 96 time x 10 lat x 16 lon grid")
            if set(ds.variables) != {"time", "latitude", "longitude", GUST_NAME}:
                raise CiaraNetCDFBlocked("unrecognized original/normalized ERA5 variables")
            t = ds.variables["time"]
            lat = ds.variables["latitude"]
            lon = ds.variables["longitude"]
            g = ds.variables[GUST_NAME]
            if (t.dimensions != ("time",)
                or lat.dimensions != ("latitude",)
                or lon.dimensions != ("longitude",)
                or g.dimensions != ("time", "latitude", "longitude")
                or getattr(t, "units", None) != TIME_UNITS
                or getattr(t, "calendar", None) != CALENDAR
                or getattr(lat, "units", None) != "degrees_north"
                or getattr(lon, "units", None) != "degrees_east"
                or getattr(g, "units", None) not in ("m/s", "m s-1")
                or getattr(g, "original_era5_variable", None) != GUST_SOURCE_NAME):
                raise CiaraNetCDFBlocked("CF coordinate/time/10fg gust metadata drift")
            # Inspect actual coordinate values; do not trust a source label.
            import numpy as np
            hours = np.ma.asarray(t[:])
            la = np.ma.asarray(lat[:])
            lo = np.ma.asarray(lon[:])
            if (np.ma.is_masked(hours) and np.ma.count_masked(hours)
                or np.ma.is_masked(la) and np.ma.count_masked(la)
                or np.ma.is_masked(lo) and np.ma.count_masked(lo)):
                raise CiaraNetCDFBlocked("masked original time or coordinate")
            if (not np.all(np.isfinite(hours)) or not np.all(np.isfinite(la))
                or not np.all(np.isfinite(lo))
                or list(hours.tolist()) != list(range(96))
                or [Decimal(str(v)) for v in la.tolist()] != list(LAT_NODES)
                or [Decimal(str(v)) for v in lo.tolist()] != list(LON_NODES)):
                raise CiaraNetCDFBlocked("ERA5 96h timing or quarter-degree grid coordinate drift")
            gust = np.ma.asarray(g[:])
            if (gust.shape != (96, 10, 16)
                or (np.ma.is_masked(gust) and np.ma.count_masked(gust))
                or not np.all(np.isfinite(gust))
                or np.any(gust < 0) or np.any(gust > 150)):
                raise CiaraNetCDFBlocked("masked, nonfinite or out-of-range hourly 10fg values")
            max_gust = np.asarray(gust.max(axis=0), dtype=float)
            peak_hour = np.asarray(gust.argmax(axis=0), dtype=int)
    except OSError as exc:
        raise CiaraNetCDFBlocked("invalid or unreadable normalized NetCDF4 bytes") from exc
    raw_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "sha256_of_local_normalized_netcdf": raw_sha,
        "size_bytes": path.stat().st_size,
        "temporal_records": 96,
        "grid_nodes": 160,
        "grid_peaks": {
            (int(la * 4), int(lo * 4)):
                (Decimal(str(max_gust[i, j])), int(peak_hour[i, j]))
            for i, la in enumerate(LAT_NODES)
            for j, lo in enumerate(LON_NODES)
        },
    }


def _occupied_nodes_from_source(zipped_path: Path) -> tuple[Counter, Counter]:
    # This is always called AFTER the exact archived HU2022 source ZIP and
    # full 10k source-identity checks in plan_from_archived_source().
    with zipfile.ZipFile(zipped_path) as z:
        records = list(csv.DictReader(
            io.StringIO(z.read("location.csv").decode("utf-8"), newline="")
        ))
    nodes, tivs = Counter(), Counter()
    for site in records:
        lat = int((_coordinate(site["Latitude"], "50", "52.8") / STEP)
                  .to_integral_value(rounding=ROUND_HALF_UP))
        lon = int((_coordinate(site["Longitude"], "5.5", "10") / STEP)
                  .to_integral_value(rounding=ROUND_HALF_UP))
        node = (lat, lon)
        nodes[node] += 1
        tivs[node] += int(site["BuildingTIV"])
    return nodes, tivs


def summarize_grid_exposure(
    plan: dict, gust: dict, nodes: Counter, tivs: Counter,
    *, expected_sites: int = EXPECTED_SITES,
    expected_tiv: int = EXPECTED_SOURCE_TIV_EUR
) -> dict:
    """Bounded synthetic/public-source hazard counts; NO loss calculation."""
    if (plan.get("schema") != "CIARA2020_NRW_HU22_10K_ERA5_10FG_AREA_REQUEST_PLAN_V0"
        or plan.get("request", {}).get("area") != [52.5, 5.75, 50.25, 9.5]
        or plan.get("event_hourly_timesteps") != 96
        or plan.get("original_CDS_source_data_acquired_or_attested") is not False
        or plan.get("German_wind_vulnerability_or_gross_net_EP_model_admitted") is not False):
        raise CiaraNetCDFBlocked("untrusted or unsafe ERA5 source request receipt")
    if (len(nodes) != plan.get("occupied_grid_nodes_by_public_building_candidates")
        or sum(nodes.values()) != expected_sites
        or sum(tivs.values()) != expected_tiv
        or set(nodes) != set(tivs)
        or any(n <= 0 or tiv <= 0 for n, tiv in zip(nodes.values(), tivs.values()))
        or len(gust.get("grid_peaks", {})) != 160):
        raise CiaraNetCDFBlocked("10k source-derived grid/tiv support changed")
    signature = "".join(
        f"{lat}:{lon}:{nodes[(lat,lon)]}\n" for lat, lon in sorted(nodes)
    ).encode("ascii")
    if hashlib.sha256(signature).hexdigest() != plan.get("occupied_nodes_count_sha256"):
        raise CiaraNetCDFBlocked("public source 93-occupied-grid count SHA changed")
    views = {}
    for threshold in THRESHOLDS:
        selected = [node for node in nodes
                    if node in gust["grid_peaks"]
                    and gust["grid_peaks"][node][0] >= threshold]
        views[str(threshold)] = {
            "public_building_candidate_count": sum(nodes[key] for key in selected),
            "fictional_original_TIV_eur": sum(tivs[key] for key in selected),
            "occupied_grid_nodes": len(selected),
        }
    if (len(views) != 4
        or any(node not in gust["grid_peaks"] for node in nodes)):
        raise CiaraNetCDFBlocked("ERA5 grid missing occupied public-site nodes")
    return {
        "schema": SCHEMA,
        "status": "LOCAL_NORMALIZED_NETCDF_HAZARD_ONLY_NOT_ORIGINAL_SOURCE_ATTESTED",
        "local_normalized_netcdf_sha256": gust["sha256_of_local_normalized_netcdf"],
        "local_normalized_netcdf_size_bytes": gust["size_bytes"],
        "original_2022_HU_archive_SHA256": plan.get("historical_original_NRW_HU2022_zip_sha256"),
        "source_derived_10k_fictional_OED_zip_sha256": SOURCE_ARTIFACT_SHA256,
        "request_area_n_w_s_e": plan["request"]["area"],
        "source_derived_occupied_grid_signature_SHA256": plan["occupied_nodes_count_sha256"],
        "normalized_time_steps": 96,
        "validated_grid_nodes": 160,
        "matched_public_building_candidates": sum(nodes.values()),
        "source_NRW_counties": plan.get("source_2022_NRW_counties"),
        "grid_points_with_public_candidate": len(nodes),
        "fictional_original_building_tiv_eur": sum(tivs.values()),
        "pointwise_max_2020_ciara_gust_mps_thresholds": views,
        "CDS_original_bytes_and_license_independently_verified": False,
        "NetCDF_original_CDS_provider_structure_directly_parsed": False,
        "dataset_CDS_license_explicitly_accepted_in_this_run": False,
        "actual_RV_insured_positions_or_claims": False,
        "original_ERA5_hazard_is_observed_insured_loss": False,
        "vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted": False,
    }


def run(original_derived_zip: Path, local_normalized_netcdf: Path) -> dict:
    plan = plan_from_archived_source(original_derived_zip)
    nodes, tivs = _occupied_nodes_from_source(original_derived_zip)
    gust = read_normalized_grid(local_normalized_netcdf)
    return summarize_grid_exposure(plan, gust, nodes, tivs)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("original_HU2022_derived_10k_OED_zip", type=Path)
    p.add_argument("locally_normalized_ERA5_10fg_NetCDF4", type=Path)
    p.add_argument("--receipt-json", type=Path)
    args = p.parse_args()
    try:
        receipt = run(
            args.original_HU2022_derived_10k_OED_zip,
            args.locally_normalized_ERA5_10fg_NetCDF4
        )
        result = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
        if args.receipt_json:
            dest = args.receipt_json
            if dest.exists() or dest.is_symlink() or not dest.parent.is_dir():
                raise CiaraNetCDFBlocked("receipt path must be fresh regular output")
            dest.write_text(result, encoding="utf-8")
        print(result)
        return 0
    except (OSError, KeyError, CiaraNetCDFBlocked, ValueError, zipfile.BadZipFile) as exc:
        p.exit(2, "CIARA_NORMALIZED_ERA5_NO_ORIGINAL_SOURCE_ADMISSION: " + str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
