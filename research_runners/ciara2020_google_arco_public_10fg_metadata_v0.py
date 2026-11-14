# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded anonymous Google ARCO-ERA5 10fg original Zarr metadata preflight.

Unlike the direct authenticated ECMWF/CDS ARCO service, Google Research
publishes an independently hosted anonymous GCS ERA5 mirror under the
Copernicus Licence (commercial/research reuse with attribution).
This tool fetches ONLY tiny public original Zarr metadata objects from
one allowlisted official Google public bucket. No site values, weather
array chunks, paid cloud credentials, insurer data or model input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib import error, request

BUCKET = "gcp-public-data-arco-era5"
SOURCE_REPO = "https://github.com/google-research/arco-era5"
SOURCE_ERA5_DATA_URL = "gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"
DATASET_DOI = "10.24381/cds.adbb2d47"
COPERNICUS_LICENSE = "https://cds.climate.copernicus.eu/api/v2/terms/static/licence-to-use-copernicus-products.pdf"
REQUIRED_ATTRIBUTION = "Copernicus Climate Change Service (C3S); Google Research ARCO-ERA5."
PREFIX = "https://storage.googleapis.com/" + BUCKET + "/ar/full_37-1h-0p25deg-chunk-1.zarr-v3/"
VAR = "10m_wind_gust_since_previous_post_processing"
SOURCE_VARIABLES = (VAR, "time", "latitude", "longitude")
MAX_METADATA_BYTES = 2_000_000
SCHEMA = "CIARA2020_GOOGLE_PUBLIC_ARCO_ERA5_10FG_ORIGINAL_ZARR_METADATA_V0"
AREA = (52.5, 5.75, 50.25, 9.5)
HOURS = 96
EXPECTED_CANDIDATES = 10_000
EXPECTED_NODES = 160


class PublicARCOMetadataBlocked(ValueError):
    """Publisher-original unsigned metadata not independently read/validated."""


class NoRedirects(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PublicARCOMetadataBlocked("redirect disallowed for pinned public original source")


def _get_metadata(url: str, opener=None) -> tuple[dict, str, int]:
    allowed = {PREFIX + v + "/.zarray" for v in SOURCE_VARIABLES}
    if url not in allowed:
        raise PublicARCOMetadataBlocked("URL must be a single pinned public GCS Zarr variable metadata")
    opener = opener if opener is not None else request.build_opener(NoRedirects())
    try:
        with opener.open(request.Request(
            url, headers={"Accept": "application/json", "User-Agent": "OpenCatastrophe-ARCO-metadata-v0"}
        ), timeout=16) as r:
            if r.status != 200:
                raise PublicARCOMetadataBlocked("public metadata response is not 200")
            blob = r.read(MAX_METADATA_BYTES + 1)
    except (error.URLError, TimeoutError, OSError) as exc:
        raise PublicARCOMetadataBlocked("anonymous public GCS metadata retrieval failed") from None
    if not 20 <= len(blob) <= MAX_METADATA_BYTES:
        raise PublicARCOMetadataBlocked("absent, truncated or oversized Zarr metadata")
    try:
        metadata = json.loads(blob)
    except (ValueError, UnicodeError) as exc:
        raise PublicARCOMetadataBlocked("public GCS returned non-JSON original metadata") from exc
    if not isinstance(metadata, dict):
        raise PublicARCOMetadataBlocked("Zarr original metadata must be one JSON mapping")
    return metadata, hashlib.sha256(blob).hexdigest(), len(blob)


def _validate_zarray(name: str, metadata: dict) -> dict:
    if (metadata.get("zarr_format") != 2
        or not isinstance(metadata.get("shape"), list)
        or not isinstance(metadata.get("chunks"), list)
        or not isinstance(metadata.get("dtype"), str)
        or not isinstance(metadata.get("order"), str)
        or len(metadata["shape"]) != len(metadata["chunks"])
        or not 1 <= len(metadata["shape"]) <= 6
        or any(type(n) is not int or n <= 0 for n in metadata["shape"])
        or any(type(n) is not int or n <= 0 for n in metadata["chunks"])):
        raise PublicARCOMetadataBlocked("unrecognized Zarr v2 variable coordinate/chunk shape")
    if name == VAR:
        if len(metadata["shape"]) != 3:
            raise PublicARCOMetadataBlocked("published 10fg is not a 3D hourly spatial field")
        if metadata["shape"][0] < 100_000:
            raise PublicARCOMetadataBlocked("ERA5 historical time coverage insufficient for 2020")
    elif len(metadata["shape"]) != 1:
        raise PublicARCOMetadataBlocked("published ERA5 original spatial/time coordinate is not 1D")
    return {"shape": metadata["shape"], "chunks": metadata["chunks"],
            "dtype": metadata["dtype"], "order": metadata["order"]}


def source_metadata_receipt(*, opener=None) -> dict:
    results = {}
    for name in SOURCE_VARIABLES:
        doc, sha, size = _get_metadata(PREFIX + name + "/.zarray", opener=opener)
        results[name] = {
            "original_metadata_sha256": sha,
            "original_metadata_bytes": size,
            **_validate_zarray(name, doc),
        }
    wind, time, lat, lon = (results[k] for k in SOURCE_VARIABLES)
    # This is a candidate 3D grid, not yet a proven individual 96h value set.
    if wind["shape"] != [time["shape"][0], lat["shape"][0], lon["shape"][0]]:
        raise PublicARCOMetadataBlocked("public Zarr axes and 10fg variable metadata disagree")
    return {
        "schema": SCHEMA,
        "status": "ANONYMOUS_PUBLIC_PUBLISHER_ZARR_METADATA_READ_ONLY_NOT_96H_DATA",
        "source_repo": SOURCE_REPO,
        "original_public_gcs_url": SOURCE_ERA5_DATA_URL,
        "provider": "Google Research ARCO-ERA5 / underlying ECMWF/C3S",
        "underlying_ERA5_doi": DATASET_DOI,
        "license": "Copernicus Licence – attribution required for commercial use",
        "copernicus_licence_url": COPERNICUS_LICENSE,
        "source_attribution": REQUIRED_ATTRIBUTION,
        "ciara2020_time_window_utc": ["2020-02-08T00:00:00Z", "2020-02-11T23:00:00Z"],
        "requested_site_support_area_nwse": list(AREA),
        "requested_hourly_steps": HOURS,
        "candidate_2022_public_buildings_not_real_insurer_sites": EXPECTED_CANDIDATES,
        "requested_0p25_degree_grid_nodes": EXPECTED_NODES,
        "source_variable": VAR,
        "public_original_zarr_v2_metadata": results,
        "public_original_cloud_metadata_fetched_without_cds_token": True,
        "source_original_2020_10fg_hourly_values_fetched": False,
        "no_CDS_operator_terms_accepted_or_cdsapi_used": True,
        "annual_event_rates_insured_claims_or_GUL_IL_RI_OEP_AEP_admitted": False,
    }


def preview() -> dict:
    return {
        "schema": SCHEMA,
        "status": "PUBLIC_GOOGLE_ARCO_METADATA_CANDIDATE_NOT_FETCHED",
        "public_source_root": SOURCE_ERA5_DATA_URL,
        "request_metadata_urls": [PREFIX + n + "/.zarray" for n in SOURCE_VARIABLES],
        "underlying_ERA5_doi": DATASET_DOI,
        "license": "Copernicus Licence with attribution",
        "expected_grid": list(AREA),
        "expected_hourly_time_steps": HOURS,
        "public_metadata_bytes_confirmed": False,
        "source_original_2020_10fg_hourly_values_fetched": False,
        "annual_event_rates_insured_claims_or_GUL_IL_RI_OEP_AEP_admitted": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    choice = p.add_mutually_exclusive_group(required=True)
    choice.add_argument("--dry-run", action="store_true")
    choice.add_argument("--live-metadata", action="store_true")
    p.add_argument("--out-json", type=Path)
    args = p.parse_args()
    try:
        receipt = source_metadata_receipt() if args.live_metadata else preview()
        contents = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        if args.out_json:
            if (args.out_json.exists() or args.out_json.is_symlink()
                or not args.out_json.parent.is_dir()):
                raise PublicARCOMetadataBlocked("receipt must have new regular output path")
            args.out_json.write_text(contents, encoding="utf-8")
        print(contents)
        return 0
    except (OSError, PublicARCOMetadataBlocked) as exc:
        p.exit(2, "GOOGLE_PUBLIC_ARCO_10FG_METADATA_NOT_ADMITTED: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
