# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed local original-byte receipt for one Zenodo GTSM NetCDF asset.

Read only: never fetches, persists or publishes provider data or model inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

RECORD_URL = "https://zenodo.org/records/14671593"
SOURCE_DOWNLOAD_URL = (
    "https://zenodo.org/records/14671593/files/"
    "ds_GTSM-ERA5-E_1950-2024_stats.nc?download=1"
)
SOURCE_NAME = "ds_GTSM-ERA5-E_1950-2024_stats.nc"
SOURCE_BYTES = 9_652_424
SOURCE_MD5 = "0f2b7071c6ec3585768be6cf427e6eab"
PINNED_SHA256 = "e366c79683438d03a48b23764f1159d5ed88845a459f625eeb787dff78cbd767"
CHUNK = 65536
HDF5_MAGIC = b"\x89HDF\r\n\x1a\n"
CDF_MAGIC = (b"CDF\x01", b"CDF\x02", b"CDF\x05")
EXPECTED_NATIVE_DIMS = {"quantile": 7, "return_period": 8, "stations": 38_957}
EXPECTED_COORD_PACKING = {
    "lon": {"scale_factor": "0.001", "add_offset": None, "_FillValue": "-999"},
    "lat": {"scale_factor": "0.001", "add_offset": None, "_FillValue": "-999"},
}
EXPECTED_NATIVE_FIELDS = {
    "lon": (("stations",), "degrees_east", "int32"),
    "lat": (("stations",), "degrees_north", "int32"),
    "stations": (("stations",), "", "uint16"),
    "quantile": (("quantile",), "", "float64"),
    "wl_quantiles": (("quantile", "stations"), "m", "float32"),
    "return_period": (("return_period",), "years", "int64"),
    "eva_param_scale": (("stations",), "", "float64"),
    "eva_param_shape": (("stations",), "", "float64"),
    "eva_param_loc": (("stations",), "", "float64"),
    "wl_extreme_bestfit": (("stations", "return_period"), "m", "float64"),
    "wl_extreme_5perc": (("stations", "return_period"), "m", "float64"),
    "wl_extreme_95perc": (("stations", "return_period"), "m", "float64"),
}


class GtsmReceiptError(ValueError):
    """Original bytes cannot be matched with the published source identity."""


def _file_receipt(path: Path, *, expected_size: int, expected_md5: str) -> dict[str, object]:
    """Testable pure local verifier; public CLI never accepts overridden pins."""
    if not path.is_file() or path.is_symlink():
        raise GtsmReceiptError("original path is not an ordinary non-symlink file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise GtsmReceiptError("unable to open original file safely") from exc
    with os.fdopen(fd, "rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size != expected_size:
            raise GtsmReceiptError("original file size differs from pinned publisher asset")
        md5 = hashlib.md5(usedforsecurity=False)
        sha256 = hashlib.sha256()
        prefix = b""
        seen = 0
        while True:
            block = source.read(CHUNK)
            if not block:
                break
            seen += len(block)
            if seen > expected_size:
                raise GtsmReceiptError("original file grew beyond pinned source size")
            if len(prefix) < 8:
                prefix += block[:8 - len(prefix)]
            md5.update(block)
            sha256.update(block)
        after = os.fstat(source.fileno())
        if seen != expected_size or after.st_size != expected_size or before.st_ino != after.st_ino:
            raise GtsmReceiptError("original size/identity changed during read")
    actual_md5 = md5.hexdigest()
    if not hmac.compare_digest(actual_md5, expected_md5):
        raise GtsmReceiptError("original MD5 does not match the publisher's fixed asset")
    if prefix != HDF5_MAGIC and not prefix.startswith(CDF_MAGIC):
        raise GtsmReceiptError("pinned asset lacks a recognized NetCDF/HDF5 file signature")
    return {"byte_length": seen, "publisher_md5_verified": actual_md5,
            "sha256_observed_not_publisher_pinned": sha256.hexdigest(),
            "container_signature": "netcdf4_hdf5" if prefix == HDF5_MAGIC else "netcdf_classic"}


def verify_original(path: Path, *, inspect_header: bool = False) -> dict[str, object]:
    receipt = _file_receipt(path, expected_size=SOURCE_BYTES, expected_md5=SOURCE_MD5)
    if not hmac.compare_digest(str(receipt["sha256_observed_not_publisher_pinned"]), PINNED_SHA256):
        raise GtsmReceiptError("original SHA-256 differs from independently observed pinned original")
    header = inspect_scientific_header(path) if inspect_header else None
    return {"schema_version": "gtsm-era5-e-original-byte-receipt-v0",
            "source_record": RECORD_URL, "source_filename": SOURCE_NAME,
            "source_version": "Zenodo 14671593 v2 / 1950-2024 statistics",
            "original_byte_evidence": receipt,
            "independent_sha256_pinned": True,
            "scientific_header_inventory": header,
            "publisher_sha256_available": False, "netcdf_variables_inspected": bool(inspect_header),
            "scientific_fitness_approved": False, "data_rights_approved": False,
            "model_admitted": False, "insurer_exposure_inferred": False,
            "provider_bytes_persisted_by_this_tool": False}


def validate_native_header(dims: dict[str, int], fields: list[dict[str, object]]) -> None:
    """Observed release-specific axes/type/unit invariant, no numeric data reads."""
    if dims != EXPECTED_NATIVE_DIMS:
        raise GtsmReceiptError("native GTSM axis identity or lengths changed")
    by_name = {str(x["name"]): x for x in fields}
    for name, (axes, unit, dtype) in EXPECTED_NATIVE_FIELDS.items():
        value = by_name.get(name)
        if value is None:
            raise GtsmReceiptError(f"native GTSM source variable missing: {name}")
        if (tuple(value["dimensions"]) != axes
                or value["units"] != unit or value["dtype"] != dtype
                or list(value["shape"]) != [dims[axis] for axis in axes]):
            raise GtsmReceiptError(f"native GTSM axes, units or numeric storage drift: {name}")


def validate_coordinate_packing(packing: dict[str, dict[str, str | None]]) -> None:
    """Reject silent 1000x geolocation scale drift from the pinned original."""
    if packing != EXPECTED_COORD_PACKING:
        raise GtsmReceiptError("native GTSM longitude/latitude scale, offset or fill value drift")


def inspect_scientific_header(path: Path) -> dict[str, object]:
    """Read only structural NetCDF metadata after full pinned-byte verification.

    No variable data slices, numeric arrays, model results or insured values.
    Header labels can guide a future science review; this is not that review.
    """
    try:
        from netCDF4 import Dataset
    except ImportError as exc:
        raise GtsmReceiptError("pinned netCDF4 acquisition dependency is required for header inspection") from exc
    try:
        with Dataset(path.as_posix(), "r") as ds:
            if not ds.dimensions or len(ds.dimensions) > 48:
                raise GtsmReceiptError("unexpected NetCDF dimension inventory size")
            if not ds.variables or len(ds.variables) > 200:
                raise GtsmReceiptError("unexpected NetCDF variable inventory size")
            dims = {}
            for name, dim in ds.dimensions.items():
                if not isinstance(name, str) or len(name) > 128:
                    raise GtsmReceiptError("unsafe NetCDF dimension label")
                dims[name] = len(dim)
            fields = []
            packing = {}
            for name, var in ds.variables.items():
                if not isinstance(name, str) or len(name) > 128 or len(var.dimensions) > 8:
                    raise GtsmReceiptError("unsafe NetCDF variable label or rank")
                def safe_attr(key: str) -> str:
                    value = getattr(var, key, "")
                    if not isinstance(value, str) or len(value) > 256:
                        return ""
                    return value
                if name in ("lon", "lat"):
                    attributes = set(var.ncattrs())
                    packing[name] = {
                        key: (str(getattr(var, key))[:80] if key in attributes else None)
                        for key in ("scale_factor", "add_offset", "_FillValue")
                    }
                fields.append({
                    "name": name,
                    "dimensions": list(var.dimensions),
                    "shape": list(var.shape),
                    "dtype": str(var.dtype)[:80],
                    "units": safe_attr("units"),
                    "standard_name": safe_attr("standard_name"),
                    "long_name": safe_attr("long_name"),
                })
    except GtsmReceiptError:
        raise
    except Exception as exc:
        raise GtsmReceiptError("unable to inspect pinned NetCDF scientific header") from exc
    validate_native_header(dims, fields)
    validate_coordinate_packing(packing)
    return {
        "dimensions": dims, "variables": fields,
        "coordinate_packing_attributes": packing,
        "coordinate_packing_schema_checked": True,
        "native_axes_units_and_dtypes_checked": True,
        "coordinate_unpacking_verified": False,
        "metadata_only": True, "variable_values_read": False,
        "vertical_datum_verified": False,
        "return_period_method_verified": False,
        "science_review_approved": False,
    }


class _ZenodoOnlyRedirect(HTTPRedirectHandler):
    """Refuse redirects away from the exact public publisher's HTTPS host."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        destination = urlsplit(newurl)
        if (destination.scheme != "https" or destination.hostname != "zenodo.org"
                or destination.port not in (None, 443)):
            raise GtsmReceiptError("disallowed non-Zenodo publisher redirect")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def fetch_verified_original(*, inspect_header: bool = False) -> dict[str, object]:
    """One fixed HTTPS original read, ephemeral file, only metadata receipt returned."""
    request = Request(SOURCE_DOWNLOAD_URL, headers={"User-Agent": "OpenCatastrophe-GTSM-Research/1.0"})
    try:
        with build_opener(_ZenodoOnlyRedirect()).open(request, timeout=60) as response:
            final = urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname != "zenodo.org" or final.port not in (None, 443):
                raise GtsmReceiptError("unexpected publisher response host")
            if response.status != 200:
                raise GtsmReceiptError("unexpected original publisher HTTP status")
            raw_length = response.headers.get("Content-Length")
            if raw_length is not None and (
                not raw_length.isdecimal() or int(raw_length) != SOURCE_BYTES
            ):
                raise GtsmReceiptError("provider Content-Length differs from pinned original size")
            with tempfile.TemporaryDirectory(prefix="gtsm-original-") as directory:
                path = Path(directory) / SOURCE_NAME
                received = 0
                with path.open("xb") as target:
                    while True:
                        block = response.read(min(CHUNK, SOURCE_BYTES - received + 1))
                        if not block:
                            break
                        received += len(block)
                        if received > SOURCE_BYTES:
                            raise GtsmReceiptError("source exceeds exact original-byte acquisition cap")
                        target.write(block)
                return verify_original(path, inspect_header=inspect_header)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise GtsmReceiptError("fixed Zenodo original acquisition unavailable") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--original", type=Path, help="existing original NetCDF, offline read-only")
    choice.add_argument("--fetch", action="store_true", help="one fixed HTTPS Zenodo original only")
    parser.add_argument("--inspect-header", action="store_true",
                        help="after SHA-256 validation, inspect only NetCDF dimension and variable metadata")
    args = parser.parse_args(argv)
    try:
        receipt = (fetch_verified_original(inspect_header=args.inspect_header) if args.fetch
                   else verify_original(args.original, inspect_header=args.inspect_header))
    except (GtsmReceiptError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
