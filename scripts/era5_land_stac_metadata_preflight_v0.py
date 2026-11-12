# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed offline QA for one original public ERA5-Land STAC collection.

Reads only caller-supplied, bounded public catalogue JSON bytes. It never
contacts CDS, accepts provider download URLs, acquires ERA5 GRIB/NetCDF, or
infers observed catastrophe events, insured loss or model-source admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SOURCE_ID = "copernicus.c3s.era5-land"
COLLECTION = "reanalysis-era5-land"
ORIGINAL_URL = "https://cds.climate.copernicus.eu/api/catalogue/v1/collections/reanalysis-era5-land"
LICENSE_LINK = "https://spdx.org/licenses/CC-BY-4.0"
DOI = "10.24381/cds.e2161bac"
PROFILE = "oc-era5-land-original-stac-metadata-preflight-v0"
MAX_BYTES = 16_384
# The exact 5537-byte provider JSON was captured on 2026-11-12 by read-only
# external transport. Pinning matches this observation, not cryptographic
# origin authentication or an approval for access to underlying data.
PINNED_BYTES = 5537
PINNED_SHA256 = "9cb5b77cfed967401d374eafcb4f9799f771cf53e1350aa18e20ffca8c0e2016"


class ERA5MetadataBlocked(ValueError):
    """An unsafe, ambiguous or non-matching ERA5-Land catalogue response."""


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key, value in pairs:
        if key in data:
            raise ERA5MetadataBlocked("duplicate STAC JSON key")
        data[key] = value
    return data


def _bad_constant(value: str) -> None:
    raise ERA5MetadataBlocked("nonfinite JSON constant")


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ERA5MetadataBlocked("nonfinite STAC JSON float")
    return result


def inspect_metadata(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ERA5MetadataBlocked("empty or unbounded provider metadata")
    try:
        obj = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_bad_constant,
            parse_float=_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ERA5MetadataBlocked("invalid original STAC JSON") from exc
    if type(obj) is not dict or (
        obj.get("type") != "Collection"
        or obj.get("id") != COLLECTION
        or obj.get("stac_version") != "1.1.0"
        or obj.get("license") != "CC-BY-4.0"
        or obj.get("sci:doi") != DOI
    ):
        raise ERA5MetadataBlocked("wrong source identity, release, DOI or licence")

    providers = obj.get("providers")
    if (type(providers) is not list or not providers
            or not any(type(p) is dict and p.get("name") == "ECMWF"
                       for p in providers)):
        raise ERA5MetadataBlocked("ECMWF original provider not identified")
    links = obj.get("links")
    if type(links) is not list or not all(type(x) is dict for x in links):
        raise ERA5MetadataBlocked("malformed STAC link inventory")
    if not any(x.get("rel") == "self" and x.get("href") == ORIGINAL_URL
               and x.get("type") == "application/json" for x in links):
        raise ERA5MetadataBlocked("missing exact original STAC self link")
    if not any(x.get("rel") == "license" and x.get("href") == LICENSE_LINK
               for x in links):
        raise ERA5MetadataBlocked("CC BY licence link missing or changed")

    extent = obj.get("extent")
    spatial = extent.get("spatial") if type(extent) is dict else None
    temporal = extent.get("temporal") if type(extent) is dict else None
    if type(spatial) is not dict or spatial.get("bbox") != [[0.0, -89.0, 360.0, 89.0]]:
        raise ERA5MetadataBlocked("original global spatial envelope changed")
    periods = temporal.get("interval") if type(temporal) is dict else None
    if (type(periods) is not list or len(periods) != 1
            or type(periods[0]) is not list or len(periods[0]) != 2
            or periods[0][0] != "1950-01-01T00:00:00+00:00"
            or type(periods[0][1]) is not str
            or not periods[0][1].endswith("+00:00")):
        raise ERA5MetadataBlocked("hourly ERA5-Land temporal coverage drift")
    sanity = obj.get("cads:sanity_check")
    if type(sanity) is not dict or sanity.get("status") not in ("available", "unavailable"):
        raise ERA5MetadataBlocked("missing original catalogue availability signal")

    digest = hashlib.sha256(raw).hexdigest()
    return {
        "profile": PROFILE,
        "source_id": SOURCE_ID,
        "collection_id": COLLECTION,
        "original_catalogue_url": ORIGINAL_URL,
        "original_response_bytes": len(raw),
        "original_response_sha256": digest,
        "matches_original_2026_11_12_stac_receipt": (
            len(raw) == PINNED_BYTES and digest == PINNED_SHA256
        ),
        "provider_authenticity_independently_proven": False,
        "catalogue_license_declared": "CC-BY-4.0",
        "catalogue_doi": DOI,
        "catalogue_updated": obj.get("updated"),
        "catalogue_temporal_start": periods[0][0],
        "catalogue_temporal_end_advertised": periods[0][1],
        "catalogue_availability_signal": sanity["status"],
        "catalogue_spatial_extent_is_not_grid_resolution": True,
        "represents_modelled_reanalysis_not_independent_event_observations": True,
        "underlying_cds_retrieval_requires_account_and_terms_acceptance": True,
        "original_grib_netcdf_values_read": 0,
        "external_links_followed": 0,
        "network_requests_performed_by_validator": 0,
        "raw_provider_data_persisted": False,
        "scientific_model_input_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.input.open("rb") as stream:
            result = inspect_metadata(stream.read(MAX_BYTES + 1))
    except (OSError, ERA5MetadataBlocked) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
