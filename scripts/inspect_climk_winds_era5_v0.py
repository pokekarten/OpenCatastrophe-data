#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Scientific metadata-only NetCDF inspection of pinned CLIMK-WINDS ERA5 v2.

No losses, grids, insurer portfolios or provider file bytes are written out.
This is a first scientific *format* receipt, not a vendor/Oasis event producer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

SOURCE_URL = (
    "https://zenodo.org/api/records/15305753/files/"
    "ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc/content"
)
SOURCE_NAME = "ERA5_StormFootprint_Database_Europe_Winter_1995-2015.nc"
PUBLISHED_SIZE = 6_792_278
PUBLISHED_MD5 = "887ae3218793c599862f115876c145f9"
# This is set only after an independently reproduced exact-head live receipt.
PINNED_SHA256 = ""
MAX_SOURCE_SIZE = 7_500_000
MAX_DIMENSIONS = 30
MAX_VARIABLES = 80


class WindSourceError(ValueError):
    """Source identity, byte integrity or NetCDF format cannot be established."""


def fetch_provider_bytes() -> bytes:
    request = Request(SOURCE_URL, headers={"User-Agent": "OpenCatastrophe-Research-CLIMK/1.0"})
    with urlopen(request, timeout=90) as response:
        target = urlsplit(response.geturl())
        if target.scheme != "https" or target.hostname != "zenodo.org":
            raise WindSourceError("publisher-host URL redirection is disallowed")
        data = response.read(MAX_SOURCE_SIZE + 1)
    if len(data) > MAX_SOURCE_SIZE:
        raise WindSourceError("source exceeds fixed-size acquisition budget")
    return data


def verify_source_bytes(data: bytes, *, require_sha256: bool = False) -> dict:
    if type(data) is not bytes or len(data) != PUBLISHED_SIZE:
        raise WindSourceError("CLIMK v2 ERA5 byte length differs from published file")
    md5 = hashlib.md5(data, usedforsecurity=False).hexdigest()
    if md5 != PUBLISHED_MD5:
        raise WindSourceError("CLIMK v2 ERA5 MD5 differs from publisher receipt")
    sha256 = hashlib.sha256(data).hexdigest()
    if PINNED_SHA256:
        if sha256 != PINNED_SHA256:
            raise WindSourceError("CLIMK v2 ERA5 source changed from pinned SHA256")
    elif require_sha256:
        raise WindSourceError("SHA256 not yet independently pinned; blocked")
    return {
        "version": "CLIMK-WINDS v2 / ERA5",
        "publisher_record": "https://zenodo.org/records/15305753",
        "source_filename": SOURCE_NAME,
        "size_bytes": len(data),
        "md5_publisher": md5,
        "sha256_observed": sha256,
        "sha256_pinned": bool(PINNED_SHA256),
    }


def inspect_netcdf_header(data: bytes) -> dict:
    """Open provider bytes in memory and export only metadata, never raw grid cells."""
    try:
        from netCDF4 import Dataset
    except ImportError as exc:
        raise WindSourceError("netCDF4 required: install pinned acquisition dependency") from exc
    try:
        with Dataset("climk-winds-v2-ERA5", mode="r", memory=data) as ds:
            dims = {name: len(dim) for name, dim in ds.dimensions.items()}
            if not dims or len(dims) > MAX_DIMENSIONS:
                raise WindSourceError("invalid NetCDF dimension inventory")
            if 50 not in dims.values():
                raise WindSourceError("50-storm selection not evidenced by any dimension")
            if not ds.variables or len(ds.variables) > MAX_VARIABLES:
                raise WindSourceError("invalid NetCDF variable inventory")
            variables = []
            for name, var in ds.variables.items():
                if len(name) > 128 or len(var.dimensions) > MAX_DIMENSIONS:
                    raise WindSourceError("unexpected variable or dimension metadata")
                variables.append({
                    "name": name,
                    "dimensions": list(var.dimensions),
                    "shape": list(var.shape),
                    "dtype": str(var.dtype),
                    "units": str(getattr(var, "units", ""))[:160],
                    "long_name": str(getattr(var, "long_name", ""))[:160],
                    "standard_name": str(getattr(var, "standard_name", ""))[:160],
                })
    except WindSourceError:
        raise
    except Exception as exc:
        raise WindSourceError("NetCDF4 opening or metadata inspection failed") from exc
    labels = " ".join(
        f"{v['name']} {v['long_name']} {v['standard_name']}" for v in variables
    ).lower()
    if not any(term in labels for term in ("wind", "gust", "storm", "footprint")):
        raise WindSourceError("windstorm scientific variable identity not established")
    if not any(v["shape"] and 50 in v["shape"] for v in variables):
        raise WindSourceError("no variable is indexed over a 50-storm dimension")
    return {
        "dimensions": dims,
        "variables": variables,
        "metadata_only": True,
        "full_grid_values_inspected": False,
        "provider_grid_data_redistributed": False,
        "model_admission": False,
    }


def verify_and_profile(data: bytes, *, require_sha256: bool = False) -> dict:
    evidence = verify_source_bytes(data, require_sha256=require_sha256)
    return {
        "schema_version": "climk-winds-era5-scientific-header-v0",
        "status": "source_bytes_and_netcdf_header_checked",
        "evidence": evidence,
        "inventory": inspect_netcdf_header(data),
        "cross_model_event_matching_done": False,
        "insured_loss_generated": False,
        "model_admission": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fetch", action="store_true", help="fetch the exact Zenodo v2 ERA5 NetCDF")
    mode.add_argument("--file", type=Path, help="independently acquired local original NetCDF")
    parser.add_argument("--require-sha256", action="store_true", help="fail closed if not pinned")
    parser.add_argument("--output", type=Path, help="optional metadata-only JSON output")
    args = parser.parse_args(argv)
    raw = fetch_provider_bytes() if args.fetch else args.file.read_bytes()
    report = verify_and_profile(raw, require_sha256=args.require_sha256)
    result = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        if args.file and args.file.resolve() == args.output.resolve():
            raise WindSourceError("refusing to overwrite original NetCDF")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
