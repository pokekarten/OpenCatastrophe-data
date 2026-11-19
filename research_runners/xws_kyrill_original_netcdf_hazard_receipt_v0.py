# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original XWS Kyrill NetCDF hazard source: bounded research-only byte receipts.

Four original gridded storm *views* are one 18 January 2007 storm, NOT four
independent annual events. Rotated-pole coordinates are NOT WGS84 points.
The download is ephemeral. No insured locations, vulnerability or losses.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import sys
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = "https://www.europeanwindstorms.org/repository/Kyrill/"
STORM = "Kyrill"
MAX_SOURCE_BYTES = 256_000
PRODUCTS = {
    "uncontaminated_raw": "Kyrill_rawFootUncon.nc",
    "recalibrated_lower_95": "Kyrill_biasL95.nc",
    "recalibrated_mean": "Kyrill_biasMean.nc",
    "recalibrated_upper_95": "Kyrill_biasU95.nc",
}
ORIGINAL_SHA256 = {
    "uncontaminated_raw": "bf18bd37b0fa441bd02a00860c0fa74474c77691efe316efd46bde0ca8b483f5",
    "recalibrated_lower_95": "5ac73f78239ef62bb177c210dbefaf7608e0dbac7cccc53cf10819bf3cbb64e0",
    "recalibrated_mean": "aef5c8cd7ed2cf475c190e08f5dc0148231fd91dd47bdb541a6360552ccd28bb",
    "recalibrated_upper_95": "ab4bc78cc1b330f5c3a4a5ab9e67422865a0fbd44c0c6585dd127a0e95826f82",
}
ORIGINAL_BYTES = 122304
ORIGINAL_RUN = "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/42106677697"
EXPECTED_LICENSE = "CC BY 4.0"
XWS_METHOD = "https://www.europeanwindstorms.org/method/footprint/"
EXPECTED_CDF_MAGIC = b"CDF\x01"
REQUIRED_RAW_HEADER = (b"wind_speed_of_gust", b"rotated_pole",
                       b"grid_north_pole_latitude",
                       b"grid_north_pole_longitude", b"CF-1.0")


class SourceBlocked(ValueError):
    pass


def download(url: str, *, opener=urlopen) -> bytes:
    if url not in {ROOT + name for name in PRODUCTS.values()}:
        raise SourceBlocked("nonallowlisted original XWS URL")
    req = Request(url, headers={"User-Agent": "OpenCatastrophe-research-XWS-original-source/1.0"})
    with opener(req, timeout=40) as r:
        effective = urlsplit(r.geturl())
        if effective.scheme != "https" or effective.hostname != "www.europeanwindstorms.org":
            raise SourceBlocked("nonissuer redirect not permitted")
        chunks = []
        total = 0
        while True:
            block = r.read(32768)
            if not block:
                break
            total += len(block)
            if total > MAX_SOURCE_BYTES:
                raise SourceBlocked("original NetCDF too large; no unbounded download")
            chunks.append(block)
    raw = b"".join(chunks)
    if len(raw) < 12000 or raw[:4] != EXPECTED_CDF_MAGIC:
        raise SourceBlocked("truncated, wrong NetCDF variant or unknown format")
    if any(x not in raw[:8192] for x in REQUIRED_RAW_HEADER):
        raise SourceBlocked("original source CF, rotated pole or gust header absent")
    return raw


def _text(x) -> str:
    if isinstance(x, bytes):
        return x.decode("ascii", "strict")
    if isinstance(x, str):
        return x
    raise SourceBlocked("NetCDF source attribute type unrecognized")


def inspect(name: str, data: bytes) -> dict:
    if name not in PRODUCTS:
        raise SourceBlocked("unrecognized storm product")
    if len(data) > MAX_SOURCE_BYTES or data[:4] != EXPECTED_CDF_MAGIC:
        raise SourceBlocked("original NetCDF bytes invalid")
    if len(data) != ORIGINAL_BYTES or hashlib.sha256(data).hexdigest() != ORIGINAL_SHA256[name]:
        raise SourceBlocked("original issuer Kyrill NetCDF size/SHA-256 changed")
    try:
        import numpy as np
        from scipy.io import netcdf_file
    except ImportError as exc:
        raise SourceBlocked("pinned scientific NetCDF reader not installed") from exc
    with netcdf_file(io.BytesIO(data), mode="r", mmap=False) as nc:
        if not {"lat", "lon", "time"}.issubset(nc.dimensions):
            raise SourceBlocked("original rotated source axes absent")
        for key in ("wind_speed_of_gust", "rotated_pole", "lat", "lon"):
            if key not in nc.variables:
                raise SourceBlocked("missing original source variable: " + key)
        pole = nc.variables["rotated_pole"]
        if _text(getattr(pole, "grid_mapping_name", "")) != "rotated_latitude_longitude":
            raise SourceBlocked("not the documented XWS rotated-pole projection")
        lat = np.asarray(nc.variables["lat"][:], dtype="float64").copy()
        lon = np.asarray(nc.variables["lon"][:], dtype="float64").copy()
        if (lat.ndim != 1 or lon.ndim != 1
                or not 20 <= len(lat) <= 600 or not 20 <= len(lon) <= 600
                or len(lat)*len(lon) > 160000
                or not np.all(np.isfinite(lat)) or not np.all(np.isfinite(lon))
                or not np.all(np.diff(lat) > 0) or not np.all(np.diff(lon) > 0)):
            raise SourceBlocked("rotated grid axes irregular, missing or oversized")
        var = nc.variables["wind_speed_of_gust"]
        if _text(getattr(var, "units", "")) not in ("metres per second", "m s-1", "m/s"):
            raise SourceBlocked("unsupported wind intensity units")
        if _text(getattr(var, "grid_mapping", "")) != "rotated_pole":
            raise SourceBlocked("gust field missing rotated-pole geometry link")
        field = np.asarray(var[:], dtype="float64")
        if field.size != len(lat)*len(lon):
            raise SourceBlocked("not a single original storm footprint")
        field = field.reshape(len(lat),len(lon))
        valid = np.isfinite(field) & (field >= 0) & (field <= 150)
        if int(valid.sum()) < 100:
            raise SourceBlocked("no usable physical wind intensities")
        vals = field[valid]
        return {
            "source_product": name,
            "source_original_url": ROOT + PRODUCTS[name],
            "original_sha256": hashlib.sha256(data).hexdigest(),
            "original_bytes": len(data),
            "original_NetCDF_classic_CDF1": True,
            "source_cf_version": _text(getattr(nc, "Conventions", "")),
            "gust_var": "wind_speed_of_gust",
            "source_gust_unit": _text(var.units),
            "source_rotated_grid_nlat": len(lat),
            "source_rotated_grid_nlon": len(lon),
            "source_rotated_grid_lat_first_last": [float(lat[0]),float(lat[-1])],
            "source_rotated_grid_lon_first_last": [float(lon[0]),float(lon[-1])],
            "original_valid_grid_cells": int(valid.sum()),
            "original_invalid_or_missing_grid_cells": int(valid.size-valid.sum()),
            "original_valid_gust_min_m_s": float(vals.min()),
            "original_valid_gust_max_m_s": float(vals.max()),
            "original_valid_gust_mean_m_s": float(vals.mean()),
            "rotated_north_pole_lat": float(pole.grid_north_pole_latitude),
            "rotated_north_pole_lon": float(pole.grid_north_pole_longitude),
            "source_coordinates_are_WGS84_lonlat": False,
            "physical_original_grid_reprojected_to_WGS84": False,
        }


def main() -> int:
    receipts = {}
    for name in PRODUCTS:
        receipts[name] = inspect(name, download(ROOT + PRODUCTS[name]))
        print("XWS_ORIGINAL_NETCDF_SOURCE_RECEIPT "
              + json.dumps(receipts[name], sort_keys=True), flush=True)
    dims = {(x["source_rotated_grid_nlat"],x["source_rotated_grid_nlon"])
            for x in receipts.values()}
    if len(dims) != 1:
        raise SourceBlocked("four products not on common original rotated grid")
    print(json.dumps({
        "schema": "XWS_KYRILL_2007_FOUR_ORIGINAL_NETCDF_RESEARCH_RECEIPTS_V0",
        "status": "FOUR_HISTORIC_STORM_VIEWS_SOURCE_READABLE_NOT_CAT_ADMITTED",
        "physical_historical_storm_count": 1,
        "distinct_annual_events_inferred": False,
        "historical_storm": "Kyrill 2007-01-18",
        "source_original_catalogue": "https://www.europeanwindstorms.org/",
        "publisher_dataset_license_observed": EXPECTED_LICENSE,
        "exact_publisher_rights_notice": XWS_METHOD,
        "publisher_attribution_required": "Met Office, University of Reading and University of Exeter",
        "source_raw_files_redistributed": False,
        "third_party_source_written_to_repository": False,
        "observed_carrier_insured_sites": False,
        "actual_storm_footprint_sampled_on_NRW_10k_sites": False,
        "source_rotated_grid_reprojected": False,
        "wind_vulnerability_curve_verified": False,
        "German_GUL_IL_RI_run": False,
        "Gross_Net_OEP_AEP_calibrated": False,
        "receipts": receipts,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SourceBlocked,OSError,UnicodeError,ValueError) as exc:
        print("XWS_KYRILL_ORIGINAL_SOURCE_BLOCKED: "+str(exc)[:200],file=sys.stderr)
        raise SystemExit(2)
