#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline GFWED GEOS-5 v2.0 NetCDF identity / optional metadata preflight.

This tool has NO network code, cannot change the source access contract and
never opens scientific variable values. An operator-supplied SHA-256 is not a
publisher checksum and cannot alone prove source identity, legal rights, or
scientific admissibility. Only a separately acquired exact original may be used.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

SOURCE_ID = "nasa.giss.gfwed.geos5.daily-fwi.v2.0"
SOURCE_NAME = "FWI.GEOS-5.Daily.Default.20140501.nc"
SOURCE_URL = (
    "https://portal.nccs.nasa.gov/datashare/GlobalFWI/"
    "v2.0/fwiCalcs.GEOS-5/Default/GEOS-5/2014/" + SOURCE_NAME
)
ROOT = Path(__file__).resolve().parents[1]
MAX_ORIGINAL_BYTES = 128 * 1024 * 1024
MAX_DIMENSIONS = 24
MAX_VARIABLES = 160
MAX_DIMENSION_LENGTH = 100_000_000
MAX_ATTR_CHARS = 256
MAX_VARIABLE_RANK = 6
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SAFE_LABEL = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z")
CDF_SIGS = {b"CDF\x01": "netcdf_classic", b"CDF\x02": "netcdf_64bit_offset", b"CDF\x05": "netcdf_cdf5"}
HDF5_SIG = b"\x89HDF\r\n\x1a\n"


class GFWEDPreflightError(ValueError):
    """Source identity, bounded-byte, or metadata-only contract failed."""


def netcdf_container_type(data: bytes) -> str:
    if len(data) >= len(HDF5_SIG) and data.startswith(HDF5_SIG):
        return "netcdf4_candidate_hdf5"
    if len(data) >= 4 and data[:4] in CDF_SIGS:
        return CDF_SIGS[data[:4]]
    raise GFWEDPreflightError("original bytes lack recognized NetCDF CDF/HDF5 signature")


def _descriptor(path: Path, *, expected_sha256: str) -> tuple[dict[str, Any], bytes]:
    """Open one external regular file with no symlink follow and bounded read."""
    if path.name != SOURCE_NAME:
        raise GFWEDPreflightError("original filename differs from published NASA example")
    if not isinstance(expected_sha256, str) or not SHA256.fullmatch(expected_sha256):
        raise GFWEDPreflightError("expected SHA-256 must be a pre-recorded lowercase hex digest")
    if path.resolve().is_relative_to(ROOT):
        raise GFWEDPreflightError("provider bytes may not be read from the repository checkout")
    if not hasattr(os, "O_NOFOLLOW"):
        raise GFWEDPreflightError("this platform lacks safe O_NOFOLLOW source opening")
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise GFWEDPreflightError("original must be an ordinary non-symlink file")
        if not 8 <= before.st_size <= MAX_ORIGINAL_BYTES:
            raise GFWEDPreflightError("original bytes outside 8-byte to 128-MiB limit")
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        with os.fdopen(os.open(path, flags), "rb") as handle:
            opened = os.fstat(handle.fileno())
            identity = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns)
            if not stat.S_ISREG(opened.st_mode) or identity(opened) != identity(before):
                raise GFWEDPreflightError("source identity changed between stat and open")
            data = handle.read(MAX_ORIGINAL_BYTES + 1)
            after = os.fstat(handle.fileno())
            if len(data) != before.st_size or identity(after) != identity(before):
                raise GFWEDPreflightError("source identity or byte length changed during read")
        on_disk = path.lstat()
        if identity(on_disk) != identity(before):
            raise GFWEDPreflightError("source pathname identity changed during read")
    except GFWEDPreflightError:
        raise
    except OSError as exc:
        raise GFWEDPreflightError("unable to safely read original local file") from exc
    observed_sha = hashlib.sha256(data).hexdigest()
    if not hmac.compare_digest(observed_sha, expected_sha256):
        raise GFWEDPreflightError("original SHA-256 differs from external expected pin")
    kind = netcdf_container_type(data)
    descriptor = {
        "source_id": SOURCE_ID,
        "original_source_url_unfetched_by_tool": SOURCE_URL,
        "exact_filename": SOURCE_NAME,
        "original_byte_count": len(data),
        "verified_against_operator_supplied_sha256": True,
        "observed_sha256": observed_sha,
        "original_container_signature": kind,
        "publisher_checksum_independently_verified": False,
        "external_pin_proven_independent_of_file_by_tool": False,
    }
    return descriptor, data


def _text(value: Any, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str) or len(value) > MAX_ATTR_CHARS:
        raise GFWEDPreflightError(f"{field} has non-string or oversized NetCDF attribute")
    return value


def inventory_header(data: bytes) -> dict[str, Any]:
    """Only inspect NetCDF structure/attributes; never slice scientific arrays."""
    try:
        import netCDF4  # type: ignore[import-not-found]
    except ImportError as exc:
        raise GFWEDPreflightError("optional netCDF4 dependency needed for header inventory") from exc
    try:
        with netCDF4.Dataset("gfwed-pinned-in-memory.nc", mode="r", memory=data) as ds:
            if not 1 <= len(ds.dimensions) <= MAX_DIMENSIONS:
                raise GFWEDPreflightError("invalid NetCDF dimension inventory size")
            if not 1 <= len(ds.variables) <= MAX_VARIABLES:
                raise GFWEDPreflightError("invalid NetCDF variable inventory size")
            dims: dict[str, int] = {}
            for name, dim in ds.dimensions.items():
                if not isinstance(name, str) or not SAFE_LABEL.fullmatch(name):
                    raise GFWEDPreflightError("unsafe NetCDF dimension name")
                size = len(dim)
                if not 0 < size <= MAX_DIMENSION_LENGTH:
                    raise GFWEDPreflightError("unsafe NetCDF dimension length")
                dims[name] = size
            variables: list[dict[str, Any]] = []
            for name, variable in ds.variables.items():
                if not isinstance(name, str) or not SAFE_LABEL.fullmatch(name):
                    raise GFWEDPreflightError("unsafe NetCDF variable name")
                axes = list(variable.dimensions)
                if len(axes) > MAX_VARIABLE_RANK or any(a not in dims for a in axes):
                    raise GFWEDPreflightError("NetCDF variable has unsupported rank or unknown axis")
                shape = list(variable.shape)
                if shape != [dims[a] for a in axes]:
                    raise GFWEDPreflightError("NetCDF variable shape does not match axes")
                dtype = str(variable.dtype)
                if len(dtype) > 80:
                    raise GFWEDPreflightError("oversized NetCDF dtype label")
                ncattrs = set(variable.ncattrs())
                variables.append({
                    "name": name,
                    "dimensions": axes,
                    "shape": shape,
                    "dtype_label_unverified": dtype,
                    "units": _text(variable.getncattr("units") if "units" in ncattrs else "", name + ".units"),
                    "standard_name": _text(variable.getncattr("standard_name") if "standard_name" in ncattrs else "", name + ".standard_name"),
                    "long_name": _text(variable.getncattr("long_name") if "long_name" in ncattrs else "", name + ".long_name"),
                })
    except GFWEDPreflightError:
        raise
    except Exception as exc:
        raise GFWEDPreflightError("NetCDF header inventory blocked by unreadable format") from exc
    return {
        "dimensions": dims,
        "variables": sorted(variables, key=lambda x: x["name"]),
        "inventory_only": True,
        "netcdf_values_loaded": False,
        "grid_coordinates_validated": False,
        "fwi_indices_semantically_validated": False,
        "fire_events_or_footprints_observed": False,
    }


def inspect_local_original(path: Path, *, expected_sha256: str, include_header: bool = False) -> dict[str, Any]:
    descriptor, data = _descriptor(path, expected_sha256=expected_sha256)
    header = inventory_header(data) if include_header else None
    return {
        "schema_version": "gfwed-geos5-v2-original-receipt-v0",
        "inspected_at_utc": datetime.now(timezone.utc).isoformat(),
        "original_byte_evidence": descriptor,
        "netcdf_header_inventory": header,
        "header_inspection_performed": bool(include_header),
        "access_contract_id": "nasa.giss.gfwed.geos5-v2.http-file.documented",
        "access_contract_mode_changed": False,
        "source_downloaded_by_this_tool": False,
        "provider_bytes_persisted_by_this_tool": False,
        "provider_rights_cleared": False,
        "commercial_use_approved": False,
        "scientific_fitness_approved": False,
        "model_source_admitted": False,
        "data_synced_to_neon": False,
    }


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    if path.suffix != ".json" or path.resolve().is_relative_to(ROOT):
        raise GFWEDPreflightError("receipt must be a JSON path outside the repository checkout")
    if not hasattr(os, "O_NOFOLLOW"):
        raise GFWEDPreflightError("this platform lacks safe no-follow receipt creation")
    blob = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        with os.fdopen(os.open(path, flags, 0o600), "wb") as handle:
            handle.write(blob)
    except OSError as exc:
        raise GFWEDPreflightError("receipt exists or cannot be created safely") from exc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original", type=Path, required=True, help="Independently obtained NASA original on local disk")
    ap.add_argument("--expected-sha256", required=True, help="Pre-recorded operator-supplied digest, NOT NASA-published")
    ap.add_argument("--inspect-header", action="store_true", help="Metadata-only NetCDF header inventory if netCDF4 installed")
    ap.add_argument("--out", type=Path, required=True, help="New JSON receipt outside Git; must not already exist")
    args = ap.parse_args()
    if args.original.resolve() == args.out.resolve():
        raise GFWEDPreflightError("refusing to overwrite original bytes")
    receipt = inspect_local_original(args.original, expected_sha256=args.expected_sha256, include_header=args.inspect_header)
    write_receipt(args.out, receipt)
    print("PASS: local NASA GFWED container receipt (NO data-rights or CAT-source approval)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
