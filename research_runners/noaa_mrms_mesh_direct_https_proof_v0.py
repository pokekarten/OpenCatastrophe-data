#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Opt-in, bounded direct HTTPS provenance check for pinned exact NOAA MRMS files.

This is NOT a general-purpose scraper. It is intentionally excluded from
unconditional check_all/CI to avoid network or NOAA outages failing the repo.
Run only on an unprivileged trusted runner, e.g. the separate path-scoped
GitHub Actions workflow. No source file bytes are written or uploaded.
A successful result proves a direct TLS-backed download of *these* object
bytes with a SHA-256 equal to the previously observed intermediary digest
and the limited GRIB2 metadata structure; NOT risk-model suitability.
"""

from __future__ import annotations

import json
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any

from research_runners.noaa_mrms_mesh_original_preflight_v0 import (
    MAX_COMPRESSED_BYTES,
    MRMSPreflightError,
    SOURCE_OBJECTS,
    audit_original,
    nominal_grid_cell,
)

ORIGIN = "https://noaa-mrms-pds.s3.amazonaws.com/"
NETWORK_TIMEOUT_S = 15


class DirectSourceProofError(ValueError):
    """The fixed first-party GET did not produce a trusted byte receipt."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Do not silently follow redirects to other hosts/objects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def make_origin_opener() -> urllib.request.OpenerDirector:
    # Explicitly do not honor ambient HTTP proxy configuration; verify host
    # certificate using the system trust store, and do not follow redirects.
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirect(),
    )


def fetch_pinned_original_object(product: str, opener: Any = None) -> bytes:
    """Receive only fixed original NOAA source bytes in memory; never persist."""
    if product not in SOURCE_OBJECTS:
        raise DirectSourceProofError("unknown fixed NOAA product")
    selected = SOURCE_OBJECTS[product]
    url = ORIGIN + selected["key"]
    opener = opener if opener is not None else make_origin_opener()
    request = urllib.request.Request(
        url, method="GET",
        headers={"Accept": "application/octet-stream",
                 "Accept-Encoding": "identity",
                 "User-Agent": "OpenCatastrophe-data-MRMS-research-probe/0.1"},
    )
    try:
        with opener.open(request, timeout=NETWORK_TIMEOUT_S) as response:
            if response.geturl() != url or response.status != 200:
                raise DirectSourceProofError("redirected or non-200 provider URL")
            declared_type = response.headers.get("Content-Encoding", "identity")
            if declared_type not in ("", "identity"):
                raise DirectSourceProofError("unexpected HTTP content encoding")
            declared_length = response.headers.get("Content-Length")
            if declared_length is not None:
                if (not declared_length.isdecimal()
                        or int(declared_length) != selected["compressed_size"]):
                    raise DirectSourceProofError("original HTTP Content-Length mismatch")
            source_bytes = response.read(MAX_COMPRESSED_BYTES + 1)
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        raise DirectSourceProofError("fixed NOAA HTTPS request failed") from exc
    if len(source_bytes) > MAX_COMPRESSED_BYTES:
        raise DirectSourceProofError("original provider response exceeded byte cap")
    return source_bytes


def fetch_and_audit(product: str, opener: Any = None) -> dict:
    source_bytes = fetch_pinned_original_object(product, opener)
    selected = SOURCE_OBJECTS[product]
    url = ORIGIN + selected["key"]
    try:
        receipt = audit_original(source_bytes, product, selected["basename"])
    except MRMSPreflightError as exc:
        raise DirectSourceProofError("original byte/GRIB2 integrity gate failed: " + str(exc)) from exc
    if receipt["decoded_grib_bytes"] <= 0:
        raise DirectSourceProofError("empty original GRIB2 payload")
    site_cell = None
    if product == "mesh_keller_2021":
        # Ground observation: NCEI Storm Events #956694, Keller Alta Vista.
        # The source's UTC reference time is 21 seconds before the report.
        if receipt["reference_utc"] != "2021-04-29T01:36:39+00:00":
            raise DirectSourceProofError("Keller radar reference timestamp drift")
        grid = receipt["grid_geography"]
        if grid.get("geometry_checked") is not True:
            raise DirectSourceProofError("Keller grid origin/increments not verified")
        site_cell = nominal_grid_cell(grid, 32.92, -97.29)
        if not site_cell["within_source_grid_bounds"]:
            raise DirectSourceProofError("Keller observed report outside MESH grid")
        site_cell["ncei_storm_events_report_id"] = 956694
        site_cell["separately_reported_hail_diameter_mm"] = 63.5
        site_cell["radar_source_utc_vs_report_seconds"] = -21
    return {
        "schema_version": "noaa-mrms-direct-https-source-proof-v0",
        "provider_https_host": "noaa-mrms-pds.s3.amazonaws.com",
        "transport": "HTTPS GET, verified default system CA, redirects and ambient proxies disabled",
        "source_url": url,
        "direct_http_status": 200,
        "fixed_object_identity_verified": True,
        "compressed_sha256_verified": receipt["compressed_sha256"],
        "compressed_byte_count": receipt["compressed_bytes"],
        "decoded_grib_byte_count": receipt["decoded_grib_bytes"],
        "gzip_crc32_verified": receipt["gzip_crc32_checked"],
        "product_definition": {
            "grib_discipline": receipt["grib_discipline"],
            "parameter_category": receipt["parameter_category"],
            "parameter_number": receipt["parameter_number"],
            "grid_template_number": receipt["grid_template_number"],
            "grid_points_declared": receipt["grid_points_declared"],
            "grid_geography": receipt["grid_geography"],
            "reference_utc": receipt["reference_utc"],
            "originating_center": receipt["originating_center"],
            "originating_subcenter": receipt["originating_subcenter"],
            "product_template_number": receipt["product_template_number"],
            "unit_per_published_noaa_table": receipt["source_parameter_unit_from_noaa_table"],
        },
        "independent_ground_report_grid_location": site_cell,
        "source_bytes_written_to_disk": False,
        "source_bytes_uploaded_to_github": False,
        "scientific_model_admission": False,
        "raw_grid_pixels_decoded": False,
        "physical_hail_intensity_validated": False,
        "insured_losses_or_tiv_inferred": False,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--product", required=True, choices=sorted(SOURCE_OBJECTS),
        help="Exact fixed historical object to retrieve directly (not URL input)",
    )
    args = parser.parse_args()
    try:
        result = fetch_and_audit(args.product)
    except DirectSourceProofError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
