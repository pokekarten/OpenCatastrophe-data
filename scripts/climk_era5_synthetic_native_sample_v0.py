#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Point-sample one pinned CLIMK-WINDS ERA5 event for synthetic sites only.

Scientific raw gust observations (m/s), no annual event probability, no
insurer exposure or CAT losses. The source-specific 50 storm IDs cannot be
assumed to match storms identified by other reanalysis models.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.effis_synthetic_point_overlay_v0 import (  # noqa: E402
    load_synthetic_sites,
)
from scripts.inspect_climk_winds_era5_v0 import (  # noqa: E402
    EXPECTED_DIMENSIONS, WindSourceError, fetch_provider_bytes,
    inspect_netcdf_header, verify_source_bytes,
)


class WindPointError(ValueError):
    """Real provider grid point science or synthetic point location is uncertain."""


def nearest_native_cell(values: tuple, target: float) -> tuple[int, float]:
    """Nearest center on strict uniform monotonic 1D angular grid; no extrapolation."""
    if type(values) is not tuple or len(values) < 2:
        raise WindPointError("grid axis must have at least two centers")
    if type(target) not in (int, float) or not math.isfinite(target):
        raise WindPointError("finite angular site coordinate required")
    points = []
    for v in values:
        if type(v) not in (int, float) or not math.isfinite(v):
            raise WindPointError("grid axis has nonfinite or unsupported numeric coordinate")
        points.append(float(v))
    increasing = points[-1] > points[0]
    series = points if increasing else list(reversed(points))
    widths = [series[i+1]-series[i] for i in range(len(series)-1)]
    if min(widths) <= 0 or abs(max(widths)-min(widths)) > 1e-7:
        raise WindPointError("non-monotonic or irregular source grid axis")
    half = widths[0] / 2
    if target < series[0]-half-1e-10 or target > series[-1]+half+1e-10:
        raise WindPointError("site outside native source grid: no nearest extrapolation")
    ix = bisect_left(series, float(target))
    ix = max(0, min(len(series)-1, ix))
    if ix > 0 and abs(series[ix-1]-target) <= abs(series[ix]-target):
        ix -= 1
    if abs(series[ix]-target) > half+1e-10:
        raise WindPointError("point too distant from nearest native center")
    original = ix if increasing else len(series)-1-ix
    return original, series[ix]


def _safe_variable_value(raw, name: str, max_value: float) -> float:
    """Reject masked array scalar and out-of-range values instead of missing->zero."""
    if getattr(raw, "mask", False) is not False:
        # bool-mask can be np.bool_ or array; scalar expected
        try:
            if bool(raw.mask):
                raise WindPointError(name+" is masked")
        except (ValueError, TypeError) as exc:
            raise WindPointError(name+" has an ambiguous mask") from exc
    try:
        value = float(raw)
    except (ValueError, TypeError, OverflowError) as exc:
        raise WindPointError(name+" not numeric") from exc
    if not math.isfinite(value) or not 0 <= value <= max_value:
        raise WindPointError(name+" is nonfinite or not in supported physical bounds")
    return value


def sample_climk_era5(*, original: bytes, synthetic_sites_json: bytes,
                      storm_index: int) -> dict:
    if type(storm_index) is not int or not 0 <= storm_index < 50:
        raise WindPointError("storm selection must be zero-based index 0..49")
    evidence = verify_source_bytes(original, require_sha256=True)
    # Check all header dimensions and declared physical variable axes before reading.
    header = inspect_netcdf_header(original)
    if header["dimensions"] != EXPECTED_DIMENSIONS:
        raise WindPointError("source grid dimensions changed")
    sites = load_synthetic_sites(synthetic_sites_json)
    try:
        from netCDF4 import Dataset
    except ImportError as exc:
        raise WindPointError("netCDF4 required for selective research sampling") from exc
    try:
        with Dataset("climk-era5-source", mode="r", memory=original) as ds:
            longitude = tuple(float(x) for x in ds.variables["longitude"][:])
            latitude = tuple(float(x) for x in ds.variables["latitude"][:])
            if any(not math.isfinite(x) for x in longitude+latitude):
                raise WindPointError("nonfinite native grid coordinates")
            gust = ds.variables["absolute_maxwindgusts"]
            ratio = ds.variables["relative_maxwindgusts"]
            hits = []
            for ident, lon, lat in sites:
                ix, cx = nearest_native_cell(longitude, lon)
                iy, cy = nearest_native_cell(latitude, lat)
                absolute = _safe_variable_value(gust[storm_index, iy, ix],
                                               "absolute maximum gust", 200.0)
                relative = _safe_variable_value(ratio[storm_index, iy, ix],
                                               "relative climatological gust", 100.0)
                hits.append({
                    "site_id": ident,
                    "native_cell_x": ix,
                    "native_cell_y": iy,
                    "selected_cell_center_lon": cx,
                    "selected_cell_center_lat": cy,
                    "absolute_max_gust_m_s": absolute,
                    "relative_max_gust_dimensionless": relative,
                })
    except WindPointError:
        raise
    except Exception as exc:
        raise WindPointError("cannot read source-specific native ERA5 NetCDF point") from exc
    return {
        "schema_version": "oc-climk-era5-synthetic-native-point-sample-v0",
        "status": "SOURCE_VERIFIED_SYNTHETIC_HAZARD_SAMPLE_NOT_LOSS",
        "peril": "WINDSTORM",
        "source_dataset": "CLIMK-WINDS v2 / ERA5",
        "source_sha256": evidence["sha256_observed"],
        "source_sha_pinned": evidence["sha256_pinned"],
        "event_key": f"climk-winds:v2:ERA5:storm-index:{storm_index}",
        "storm_index_zero_based": storm_index,
        "event_identity_cross_model_matched": False,
        "grid_coordinate_system": "source_native_lat_lon_degrees",
        "spatial_sampling": "nearest_native_grid_center_no_extrapolation",
        "physical_intensity_measure": "MAX_WIND_GUST_ASSOCIATED_WITH_STORM_FOOTPRINT",
        "physical_intensity_unit": "m s**-1",
        "relative_intensity_measure": "MAX_GUST_DIVIDED_BY_98TH_PERCENTILE_CLIMATOLOGY",
        "relative_intensity_unit": "dimensionless",
        "site_count": len(hits),
        "site_samples": hits,
        "site_asset_ownership_admitted": False,
        "source_event_frequency_inferred": False,
        "full_grid_republished": False,
        "damage_or_insured_loss_computed": False,
        "scientifically_admitted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true")
    mode.add_argument("--file", type=Path)
    parser.add_argument("--sites", type=Path, required=True)
    parser.add_argument("--storm-index", type=int, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    original = fetch_provider_bytes() if args.fetch else args.file.read_bytes()
    result = sample_climk_era5(
        original=original, synthetic_sites_json=args.sites.read_bytes(),
        storm_index=args.storm_index,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n"
    if args.out:
        if args.file and args.out.resolve() == args.file.resolve():
            raise WindPointError("refusing to overwrite raw source")
        if args.out.resolve() == args.sites.resolve():
            raise WindPointError("refusing to overwrite synthetic sites")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
