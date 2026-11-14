# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""MANUAL-only original Copernicus CDS 2020 Ciara 10fg 96h source acquisition.

Dry-run prints a strictly pinned candidate request and requires NO secrets.
Live mode MUST be explicitly selected after an operator has personally
accepted this dataset's terms on the CDS website and verified the actual
dataset API form. The request syntax is still a CANDIDATE until live proof.
No original CDS data, credentials or individual sites are uploaded to Git.
The resulting SHA/NetCDF structure receipt does NOT itself prove published
dataset byte identity, German storm loss calibration or EIOPA insurer claims.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import zipfile

from ciara2020_nrw_10k_era5_area_request_v0 import SOURCE_ARTIFACT_SHA256
from eiopa_ciara2020_era5_10fg_hourly_point_preflight_v0 import DS, VAR, HOURS

SCHEMA = "CIARA2020_CDS_ERA5_10FG_ORIGINAL_SOURCE_MANUAL_ONE_SHOT_V0"
API_BASE = "https://cds.climate.copernicus.eu/api"
TERMS_SENTINEL = "I_ACCEPTED_DATASET_TERMS_ON_CDS_WEBSITE"
FORM_SENTINEL = "I_VERIFIED_THIS_DATASET_API_FORM"
MAX_ORIGINAL_RESPONSE_BYTES = 100_000_000
MAX_NETCDF_BYTES = 95_000_000
EXPECTED_SOURCE_GEO = [52.5, 5.75, 50.25, 9.5]
EXPECTED_OCCUPIED_GRID_SHA = "de10099a9b79febb1a254bc765dc477a47589cb1f49ba75415bfe6b9723c2ebd"
EXPECTED_PUBLISHER_NOTE = "Copernicus Climate Change Service (C3S) ERA5"
EXPECTED_USER_REQUEST = {
    "variable": [VAR],
    "date": ["2020-02-08", "2020-02-11"],
    "area": EXPECTED_SOURCE_GEO,
    "data_format": "netcdf",
}


class CDSOriginalBlocked(ValueError):
    """No consent, no credential, unexpected provider payload or stale request."""


def canonical_request() -> dict:
    if HOURS != 96 or DS != "reanalysis-era5-single-levels-timeseries":
        raise CDSOriginalBlocked("unexpected original dataset or event-window drift")
    return {"dataset": DS, "request": EXPECTED_USER_REQUEST.copy()}


def request_fingerprint() -> str:
    payload = json.dumps(canonical_request(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_only_preview() -> dict:
    return {
        "schema": SCHEMA,
        "status": "MANUAL_CDS_DATASET_TERMS_AND_API_REQUEST_FORM_REQUIRED",
        **canonical_request(),
        "canonical_request_sha256": request_fingerprint(),
        "project_2022_original_HU_derived_10k_sha256": SOURCE_ARTIFACT_SHA256,
        "original_2022_public_NRW_building_candidates_not_RV_sites": 10_000,
        "occupied_2020_ERA5_grid_nodes_expected": 93,
        "occupied_grid_node_count_sha256": EXPECTED_OCCUPIED_GRID_SHA,
        "max_rectangle_nodes": 160,
        "expected_hourly_time_steps": 96,
        "source_publisher": EXPECTED_PUBLISHER_NOTE,
        "terms_accepted_on_CDS_website_independently_verified": False,
        "API_request_mirrors_actual_dataset_form_independently_verified": False,
        "CDS_request_executed": False,
        "original_CDS_downloaded_or_retained": False,
        "original_CDS_NetCDF_metadata_parsed": False,
        "observed_insured_2020_Ciara_losses_loaded": False,
        "German_wind_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted": False,
    }


def _require_user_consent(*, terms: str, api_form: str, api_key: str) -> None:
    if terms != TERMS_SENTINEL or api_form != FORM_SENTINEL:
        raise CDSOriginalBlocked("operator must manually accept dataset terms and verify API form")
    if (not isinstance(api_key, str) or not 12 <= len(api_key) <= 4096
        or any(ch in api_key for ch in "\r\n\0 ")):
        raise CDSOriginalBlocked("CDSAPI_KEY secret missing or invalid; no network request")


def _file_sha256(file: Path) -> str:
    with file.open("rb") as fd:
        return hashlib.file_digest(fd, "sha256").hexdigest()


def _inspect_netcdf(path: Path) -> dict:
    try:
        from netCDF4 import Dataset
    except ImportError as exc:
        raise CDSOriginalBlocked("netCDF4 acquisition dependency missing") from exc
    try:
        with Dataset(str(path), "r") as dataset:
            if (len(dataset.dimensions) > 16 or len(dataset.variables) > 64
                or len(dataset.dimensions) < 1 or len(dataset.variables) < 1):
                raise CDSOriginalBlocked("provider NetCDF has abnormal dimension/variable population")
            dims = {name: len(value) for name, value in dataset.dimensions.items()}
            variables = {
                name: {
                    "dimensions": list(value.dimensions),
                    "units": (
                        str(getattr(value, "units", ""))[:100]
                        if isinstance(getattr(value, "units", ""), (str, bytes)) else ""
                    ),
                }
                for name, value in dataset.variables.items()
            }
            model = dataset.data_model
    except (OSError, RuntimeError) as exc:
        raise CDSOriginalBlocked("source response NetCDF cannot be opened") from None
    if not (isinstance(model, str) and model.startswith("NETCDF")):
        raise CDSOriginalBlocked("source file is not a recognized NetCDF")
    return {"netcdf_data_model": model, "dimension_lengths": dims, "variables": variables,
            "actual_CDS_time_grid_and_gust_not_yet_normalized_or_admitted": True}


def inspect_original_response(path: Path) -> dict:
    """Hash original response bytes; inspect NetCDF axes, NOT data or insurer losses."""
    if (path.is_symlink() or not path.is_file()
        or not 512 <= path.stat().st_size <= MAX_ORIGINAL_RESPONSE_BYTES):
        raise CDSOriginalBlocked("unexpected original CDS response size or non-regular file")
    original_sha = _file_sha256(path)
    with path.open("rb") as fd:
        prefix = fd.read(8)
    if prefix.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(path, "r") as archive:
            entries = archive.infolist()
            if (len(entries) != 1 or entries[0].is_dir() or entries[0].flag_bits & 1
                or not entries[0].filename.lower().endswith(".nc")
                or entries[0].file_size < 512 or entries[0].file_size > MAX_NETCDF_BYTES
                or entries[0].filename != PurePosixPath(entries[0].filename).name
                or archive.testzip() is not None):
                raise CDSOriginalBlocked("source ZIP must contain one bounded, CRC-valid NetCDF")
            entry = entries[0]
            with tempfile.TemporaryDirectory(prefix="ciara-source-metadata-") as tempdir:
                member = Path(tempdir) / "member.nc"
                with archive.open(entry, "r") as inp, member.open("xb") as out:
                    while True:
                        block = inp.read(1024 * 1024)
                        if not block:
                            break
                        out.write(block)
                netcdf = _inspect_netcdf(member)
            return {
                "original_response_format": "ZIP_WITH_ONE_NC",
                "original_netcdf_member_basename": entry.filename,
                "original_netcdf_member_sha256": _file_sha256_of_member(path, entry.filename),
                "original_netcdf_member_size_bytes": entry.file_size,
                "original_response_sha256": original_sha,
                "original_response_size_bytes": path.stat().st_size,
                **netcdf,
            }
    if prefix == b"\x89HDF\r\n\x1a\n" or prefix[:3] in (b"CDF",):
        netcdf = _inspect_netcdf(path)
        return {
            "original_response_format": "NETCDF",
            "original_response_sha256": original_sha,
            "original_response_size_bytes": path.stat().st_size,
            **netcdf,
        }
    raise CDSOriginalBlocked("unrecognized source response signature (neither NetCDF nor one-NC ZIP)")


def _file_sha256_of_member(path: Path, name: str) -> str:
    digest = hashlib.sha256()
    with zipfile.ZipFile(path) as archive, archive.open(name) as src:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def acquire(*, destination: Path, terms: str, api_form: str, api_key: str,
            client_factory=None) -> dict:
    """Real retrieval allowed only in manual opt-in mode; never prints auth."""
    _require_user_consent(terms=terms, api_form=api_form, api_key=api_key)
    if (destination.is_symlink() or destination.exists()
        or not destination.parent.is_dir()):
        raise CDSOriginalBlocked("original response must be a fresh regular output path")
    if client_factory is None:
        try:
            import cdsapi
        except ImportError as exc:
            raise CDSOriginalBlocked("cdsapi acquisition dependency missing") from exc
        client_factory = cdsapi.Client
    try:
        client = client_factory(url=API_BASE, key=api_key,
                                quiet=True, progress=False, debug=False,
                                timeout=60, retry_max=2)
        client.retrieve(DS, dict(EXPECTED_USER_REQUEST), str(destination))
    except Exception:
        destination.unlink(missing_ok=True)
        raise CDSOriginalBlocked(
            "authenticated CDS download failed; check operator acceptance and official API form"
        ) from None
    try:
        scan = inspect_original_response(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return {
        **source_only_preview(),
        "status": "CDS_MANUAL_OPERATOR_AUTHENTICATED_SOURCE_RESPONSE_RECEIPT_ONLY",
        "operator_attested_CDS_dataset_terms_manually_accepted": True,
        "operator_attested_actual_CDS_dataset_API_form_checked": True,
        "CDS_request_executed": True,
        "original_CDS_downloaded_or_retained": True,
        "original_CDS_NetCDF_metadata_parsed": True,
        "original_bytes_stored_in_Git_or_uploaded_as_GitHub_artifact": False,
        "original_provider_published_independent_sha256_matched": False,
        "source_file_requires_independent_archive_or_private_storage_before_replay": True,
        **scan,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--live", action="store_true")
    parser.add_argument("--terms-confirmed", default="")
    parser.add_argument("--api-form-confirmed", default="")
    parser.add_argument("--original-response", type=Path)
    parser.add_argument("--receipt-json", type=Path)
    args = parser.parse_args()
    try:
        if args.live:
            if args.original_response is None:
                raise CDSOriginalBlocked("live retrieval needs original response path")
            receipt = acquire(
                destination=args.original_response,
                terms=args.terms_confirmed,
                api_form=args.api_form_confirmed,
                api_key=os.environ.get("CDSAPI_KEY", ""),
            )
        else:
            if args.original_response or args.terms_confirmed or args.api_form_confirmed:
                raise CDSOriginalBlocked("dry-run cannot simulate consent or source response")
            receipt = source_only_preview()
        output = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
        if args.receipt_json:
            dest = args.receipt_json
            if dest.is_symlink() or dest.exists() or not dest.parent.is_dir():
                raise CDSOriginalBlocked("new receipt path required")
            dest.write_text(output, encoding="utf-8")
        print(output)
        return 0
    except (CDSOriginalBlocked, OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(2, "CDS_CIARA_SOURCE_MANUAL_GATE_BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
