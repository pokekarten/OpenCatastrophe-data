# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed, one-event WISC NetCDF-4 tile to Oasis hazard CSV research adapter.

Only a pinned original *local* provider file and an explicitly selected small
tile are accepted. No downloads, occurrence.csv, vulnerability, insurer loss,
annualization, source approval or model-run claim.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys

DATASET_ID = "copernicus.c3s.wisc.synthetic-windstorms.22980"
HDF5_MAGIC = b"\x89HDF\r\n\x1a\n"
SOURCE_NAME = re.compile(
    r"(?:C3S_EvenSet_)?fp_ga3ups_(?P<time>\d{12})_(?P<track>\d{4})_(?P<code>\d{3})_v1\.nc\Z"
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
MAX_SOURCE_BYTES = 500_000_000
MAX_TILE_CELLS = 10_000
MAX_GRID_CELLS = 2_147_483_647
DEFAULT_BINS = "0,10,20,30,40,50,60,80,120,200"
CSV_HEADERS = {
    "events.csv": ["event_id"],
    "footprint.csv": ["event_id", "areaperil_id", "intensity_bin_id", "probability"],
    "intensity_bin_dict.csv": ["bin_index", "bin_from", "bin_to", "interpolation", "interval_type"],
    "areaperil_dict.csv": ["areaperil_id", "latitude", "longitude", "source_row", "source_col"],
}


class WiscTileError(ValueError):
    """Source identity, spatial support or bin mapping is not trustworthy."""


def parse_source_name(filename: str) -> dict[str, str]:
    match = SOURCE_NAME.fullmatch(filename)
    if not match:
        raise WiscTileError("unexpected WISC original filename; no guessed event identity")
    parts = match.groupdict()
    try:
        moment = datetime.strptime(parts["time"], "%Y%m%d%H%M")
    except ValueError as exc:
        raise WiscTileError("invalid simulated storm median timestamp") from exc
    if not 1985 <= moment.year <= 2011:
        raise WiscTileError("median timestamp outside modelled historical-forcing period")
    return parts


def number(value: object, label: str, *, minimum: float, maximum: float) -> float:
    if type(value) not in (int, float):
        raise WiscTileError(f"{label} must be numeric")
    try:
        parsed = float(value)
    except (ValueError, OverflowError) as exc:
        raise WiscTileError(f"{label} not finite") from exc
    if not math.isfinite(parsed) or not minimum <= parsed <= maximum:
        raise WiscTileError(f"{label} out of supported finite bounds")
    return parsed


def strict_vector(values: list[object], label: str, lo: float, hi: float) -> list[float]:
    if type(values) is not list or not values:
        raise WiscTileError(f"{label} coordinate vector missing")
    coordinates = [number(v, label, minimum=lo, maximum=hi) for v in values]
    if len(coordinates) > 1:
        ascending = all(b > a for a, b in zip(coordinates, coordinates[1:]))
        descending = all(b < a for a, b in zip(coordinates, coordinates[1:]))
        if not (ascending or descending):
            raise WiscTileError(f"{label} coordinates must be strictly monotone")
    return coordinates


def bins_from_text(source: str) -> list[Decimal]:
    if type(source) is not str:
        raise WiscTileError("intensity bins must be a comma-delimited string")
    parts = source.split(",")
    if not 2 <= len(parts) <= 50:
        raise WiscTileError("intensity bins must declare 2..50 consecutive endpoints")
    try:
        bins = [Decimal(p) for p in parts]
    except InvalidOperation as exc:
        raise WiscTileError("intensity bins must be decimal numbers") from exc
    if any(not x.is_finite() or x < 0 or x > 200 for x in bins):
        raise WiscTileError("intensity bins must be finite 0..200 m/s")
    if bins[0] != 0 or any(b <= a for a, b in zip(bins, bins[1:])):
        raise WiscTileError("intensity bins must start at zero and increase strictly")
    return bins


def csv_content(filename: str, rows: list[list[object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(CSV_HEADERS[filename])
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def render_tile(
    *,
    original_filename: str,
    original_sha256: str,
    event_id: int,
    synthetic_set: str,
    ensemble_member: int,
    grid_row_start: int,
    grid_col_start: int,
    full_latitudes: list[object],
    full_longitudes: list[object],
    gust_tile: list[list[object]],
    intensity_edges: list[Decimal],
) -> tuple[dict[str, bytes], dict[str, object]]:
    """Pure bounded conversion; accepts only explicit 2-D gust grids in m/s.

    A grid-cell centroid is NOT a footprint polygon, site geocoder, or
    proof of the original source variable's geographic/physical meaning.
    """
    source = parse_source_name(original_filename)
    if type(original_sha256) is not str or not SHA256.fullmatch(original_sha256):
        raise WiscTileError("expected exact original SHA-256")
    if type(event_id) is not int or not 1 <= event_id <= MAX_GRID_CELLS:
        raise WiscTileError("event_id must be a positive 32-bit signed integer")
    if synthetic_set not in ("1.2", "2.0", "3.0"):
        raise WiscTileError("select exactly one recognised synthetic set")
    if type(ensemble_member) is not int or not 1 <= ensemble_member <= 5:
        raise WiscTileError("ensemble member must be an integer 1..5")
    if type(grid_row_start) is not int or type(grid_col_start) is not int or min(grid_row_start, grid_col_start) < 0:
        raise WiscTileError("invalid tile grid start")
    if type(intensity_edges) is not list or len(intensity_edges) < 2 or not all(type(v) is Decimal for v in intensity_edges):
        raise WiscTileError("explicit ordered decimal intensity bin endpoints required")
    if intensity_edges[0] != 0 or any(not x.is_finite() or x < 0 or x > 200 for x in intensity_edges) or any(b <= a for a, b in zip(intensity_edges, intensity_edges[1:])):
        raise WiscTileError("intensity bin endpoints invalid")

    latitudes = strict_vector(full_latitudes, "latitude", -90, 90)
    longitudes = strict_vector(full_longitudes, "longitude", -180, 180)
    ny, nx = len(latitudes), len(longitudes)
    if ny * nx > MAX_GRID_CELLS:
        raise WiscTileError("full area-peril ID exceeds signed 32-bit support")
    if type(gust_tile) is not list or not gust_tile or any(type(row) is not list for row in gust_tile):
        raise WiscTileError("tile is empty or not an explicit 2D array")
    height, width = len(gust_tile), len(gust_tile[0])
    if width < 1 or height * width > MAX_TILE_CELLS or any(len(row) != width for row in gust_tile):
        raise WiscTileError("tile cells are unbounded or nonrectangular")
    if grid_row_start + height > ny or grid_col_start + width > nx:
        raise WiscTileError("tile extends beyond declared source grid")

    events = [[event_id]]
    footprint: list[list[object]] = []
    cell_map: list[list[object]] = []
    missing = 0
    for dy, row in enumerate(gust_tile):
        grid_row = grid_row_start + dy
        for dx, value in enumerate(row):
            grid_col = grid_col_start + dx
            if value is None or (type(value) is float and math.isnan(value)):
                missing += 1
                continue
            gust = number(value, "max_3s_gust_mps", minimum=0, maximum=200)
            intensity = Decimal(str(gust))
            if intensity > intensity_edges[-1]:
                raise WiscTileError("gust exceeds last declared intensity bin; refuse clipping")
            rank = bisect_right(intensity_edges, intensity)
            bin_id = min(rank, len(intensity_edges) - 1)
            if bin_id == 0:
                raise WiscTileError("gust is outside all bins")
            peril_id = grid_row * nx + grid_col + 1
            footprint.append([event_id, peril_id, bin_id, "1.0"])
            cell_map.append([peril_id, repr(latitudes[grid_row]), repr(longitudes[grid_col]), grid_row, grid_col])

    if not footprint:
        raise WiscTileError("tile contains no valid observed gust cells")
    db = []
    for k, (left, right) in enumerate(zip(intensity_edges, intensity_edges[1:]), 1):
        db.append([k, str(left), str(right), str((left + right) / 2), 1])

    files = {
        "events.csv": csv_content("events.csv", events),
        "footprint.csv": csv_content("footprint.csv", footprint),
        "intensity_bin_dict.csv": csv_content("intensity_bin_dict.csv", db),
        "areaperil_dict.csv": csv_content("areaperil_dict.csv", cell_map),
    }
    receipt = {
        "profile": "wisc_single_synthetic_event_hazard_tile_v0",
        "source_dataset_id": DATASET_ID,
        "original_filename": original_filename,
        "original_sha256_verified": original_sha256,
        "source_filename_parts": source,
        "source_time_is_simulated_not_actual_event_date": True,
        "source_calibration_set_claim": synthetic_set,
        "source_ensemble_member_claim": ensemble_member,
        "filename_set_ensemble_crosswalk_independently_verified": False,
        "event_id_local_experiment_only": event_id,
        "full_grid_shape": [ny, nx],
        "tile": {"row_start": grid_row_start, "col_start": grid_col_start, "height": height, "width": width},
        "gust_unit": "m/s; max 3-second 10-m gust over 72h",
        "valid_cells": len(footprint),
        "missing_gust_cells_weather_unknown": missing,
        "area_peril_centroids_only_not_geocoded_exposures": True,
        "oasis_footprint_probabilities_deterministic_one_per_cell": True,
        "source_rights_and_asset_admission_approved": False,
        "vulnerability_validated": False,
        "occurrence_file_created": False,
        "source_year_universe_complete": False,
        "period_weights_verified": False,
        "annual_oep_aep_authorized": False,
        "insured_or_reinsured_loss_validated": False,
        "native_oasis_run_verified": False,
        "output_files": {
            key: {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            for key, payload in sorted(files.items())
        },
    }
    return files, receipt


def hash_original(path: Path, expected_sha256: str) -> str:
    if not path.is_file() or path.is_symlink():
        raise WiscTileError("source must be a local regular NetCDF-4 file, not a symlink")
    if type(expected_sha256) is not str or not SHA256.fullmatch(expected_sha256):
        raise WiscTileError("source SHA-256 must be a lower-case 64-hex digest")
    if not 8 <= path.stat().st_size <= MAX_SOURCE_BYTES:
        raise WiscTileError("original NetCDF-4 source outside bounded size limits")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        if stream.read(8) != HDF5_MAGIC:
            raise WiscTileError("expected NetCDF-4 HDF5 signature, not a synthetic flat file")
        stream.seek(0)
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != expected_sha256:
        raise WiscTileError("original NetCDF-4 SHA-256 mismatch")
    return digest.hexdigest()


def convert_netcdf(
    source: Path,
    *,
    expected_sha256: str,
    variable: str,
    latitude_name: str,
    longitude_name: str,
    event_id: int,
    synthetic_set: str,
    ensemble_member: int,
    row_start: int,
    col_start: int,
    height: int,
    width: int,
    bin_edges: list[Decimal],
) -> tuple[dict[str, bytes], dict[str, object]]:
    """No grid variable guessed: explicit source dimensions and units required."""
    source_hash = hash_original(source, expected_sha256)
    if any(type(s) is not str or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,80}", s)
           for s in (variable, latitude_name, longitude_name)):
        raise WiscTileError("all source variables must be explicitly named")
    if type(row_start) is not int or type(col_start) is not int or min(row_start, col_start) < 0:
        raise WiscTileError("negative tile offset")
    if type(height) is not int or type(width) is not int or height <= 0 or width <= 0 or height * width > MAX_TILE_CELLS:
        raise WiscTileError("unsupported tile size")
    try:
        import xarray as xr
    except ImportError as exc:
        raise WiscTileError("native NetCDF reader unavailable: install xarray and netCDF4") from exc
    try:
        with xr.open_dataset(source, engine="netcdf4", decode_cf=True, mask_and_scale=True) as ds:
            if variable not in ds.data_vars or latitude_name not in ds.variables or longitude_name not in ds.variables:
                raise WiscTileError("named original NetCDF-4 source variables missing")
            field = ds[variable]
            if tuple(field.dims) != (latitude_name, longitude_name):
                raise WiscTileError("only 2-D latitude x longitude gust fields supported; no dimension guessing")
            if tuple(ds[latitude_name].dims) != (latitude_name,) or tuple(ds[longitude_name].dims) != (longitude_name,):
                raise WiscTileError("only explicit 1-D geographic coordinates supported")
            if field.attrs.get("units") not in ("m s-1", "m s^-1", "m s**-1", "m/s", "m s^{-1}"):
                raise WiscTileError("source gust units not verified as metres per second")
            lat = ds[latitude_name].values.tolist()
            lon = ds[longitude_name].values.tolist()
            sliced = field.isel({
                latitude_name: slice(row_start, row_start + height),
                longitude_name: slice(col_start, col_start + width),
            }).values.tolist()
    except (OSError, KeyError, IndexError, TypeError, ValueError, AttributeError) as exc:
        if isinstance(exc, WiscTileError):
            raise
        raise WiscTileError("failed to read explicit native NetCDF-4 tile") from exc
    return render_tile(
        original_filename=source.name, original_sha256=source_hash,
        event_id=event_id, synthetic_set=synthetic_set, ensemble_member=ensemble_member,
        grid_row_start=row_start, grid_col_start=col_start,
        full_latitudes=lat, full_longitudes=lon, gust_tile=sliced, intensity_edges=bin_edges,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--netcdf", type=Path, required=True)
    parser.add_argument("--original-sha256", required=True)
    parser.add_argument("--variable", required=True)
    parser.add_argument("--latitude-variable", required=True)
    parser.add_argument("--longitude-variable", required=True)
    parser.add_argument("--event-id", type=int, required=True)
    parser.add_argument("--synthetic-set", choices=("1.2", "2.0", "3.0"), required=True)
    parser.add_argument("--ensemble-member", type=int, required=True)
    parser.add_argument("--row-start", type=int, required=True)
    parser.add_argument("--col-start", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--bin-edges", default=DEFAULT_BINS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        bins = bins_from_text(args.bin_edges)
        files, receipt = convert_netcdf(
            args.netcdf, expected_sha256=args.original_sha256,
            variable=args.variable, latitude_name=args.latitude_variable,
            longitude_name=args.longitude_variable, event_id=args.event_id,
            synthetic_set=args.synthetic_set, ensemble_member=args.ensemble_member,
            row_start=args.row_start, col_start=args.col_start,
            height=args.height, width=args.width, bin_edges=bins,
        )
        if args.out.exists() or args.out.is_symlink():
            raise WiscTileError("output path already exists; refuse overwrite")
        if not args.out.parent.is_dir():
            raise WiscTileError("output parent directory missing")
        args.out.mkdir()
        for filename, data in sorted(files.items()):
            (args.out / filename).write_bytes(data)
        (args.out / "research_receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except (WiscTileError, OSError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
