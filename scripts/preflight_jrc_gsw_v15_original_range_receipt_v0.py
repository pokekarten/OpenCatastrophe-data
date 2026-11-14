# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""OFFLINE-only expected JRC v1.5 TIFF prefix HTTP Range response gate.

Parses supplied header/bytes from a *separately reviewed and authorized*
original single-tile request. It DOES NOT initiate an HTTP request; current
JRC CloudFerro access contract authorizes ZERO original TIFF network reads.

A 4096-byte Range SHA is NOT the entire TIFF SHA, original post-correction
release or a validated CAT flood-risk model; never approve on this basis.
"""
from __future__ import annotations

import re
from typing import Mapping, Any
from scripts.preflight_jrc_gsw_v15_occurrence_header_v0 import (
    SOURCE_URL, PREFIX_BYTES, JRCHeaderBlocked, inspect_tiff_prefix,
)

MAX_WHOLE_ORIGINAL_TIFF_BYTES_DECLARATION = 20_000_000_000
SUPPORTED_MEDIA = frozenset({"image/tiff", "application/octet-stream"})

class JRCOriginalRangeBlocked(ValueError):
    """Range identity, size or native original TIFF prefix is not verified."""


def inspect_external_original_range(
    *, source_url: str, http_status: int,
    response_headers: Mapping[str, str], original_range_bytes: bytes,
) -> dict[str, Any]:
    """Only supplied exact 0-4095/total original HTTP206 receipt; no network."""
    if source_url != SOURCE_URL:
        raise JRCOriginalRangeBlocked("source URL is not the fixed JRC Occurrence original")
    if type(http_status) is not int or http_status != 206:
        raise JRCOriginalRangeBlocked("server ignored Range or response was not HTTP 206")
    if type(original_range_bytes) is not bytes or len(original_range_bytes) != PREFIX_BYTES:
        raise JRCOriginalRangeBlocked("exactly 4096 original prefix bytes required")
    headers: dict[str, str] = {}
    if not isinstance(response_headers, Mapping):
        raise JRCOriginalRangeBlocked("original HTTP header mapping required")
    for key, value in response_headers.items():
        if type(key) is not str or type(value) is not str:
            raise JRCOriginalRangeBlocked("non-string source HTTP headers")
        lower = key.strip().lower()
        if lower in headers:
            raise JRCOriginalRangeBlocked("duplicate original source HTTP header")
        headers[lower] = value.strip()
    content_range = headers.get("content-range", "")
    m = re.fullmatch(r"bytes 0-4095/([1-9][0-9]*)", content_range)
    if not m:
        raise JRCOriginalRangeBlocked("original Content-Range not precisely bytes 0-4095/TOTAL")
    total = int(m.group(1))
    if m.group(1) != str(total):
        raise JRCOriginalRangeBlocked("noncanonical original total size in Content-Range")
    if not PREFIX_BYTES < total <= MAX_WHOLE_ORIGINAL_TIFF_BYTES_DECLARATION:
        raise JRCOriginalRangeBlocked("unbounded or invalid declared total TIFF size")
    if headers.get("content-length") != str(PREFIX_BYTES):
        raise JRCOriginalRangeBlocked("original partial Content-Length not exactly 4096")
    if headers.get("content-encoding", "identity").lower() != "identity":
        raise JRCOriginalRangeBlocked("compressed or transcoded source bytes not accepted")
    media = headers.get("content-type", "").split(";", 1)[0].lower().strip()
    if media not in SUPPORTED_MEDIA:
        raise JRCOriginalRangeBlocked("original response is not TIFF/octet-stream")
    try:
        native = inspect_tiff_prefix(original_range_bytes)
    except JRCHeaderBlocked as ex:
        raise JRCOriginalRangeBlocked("received original range is not strict TIFF prefix") from ex
    # A Content-Range value supplies only DECLARED whole-file size, not whole-
    # body SHA or verified current JRC release vintage; it may be stale cache.
    return {
        "profile": "jrc_gsw_v15_original_4096_range_offline_transport_gate_v0",
        "source_id": native["source_id"],
        "exact_candidate_original_tiff_url": SOURCE_URL,
        "supplied_response_http_status": 206,
        "supplied_original_response_content_range": content_range,
        "original_prefix_bytes": PREFIX_BYTES,
        "claimed_whole_original_tiff_bytes_from_http_header_only": total,
        "original_prefix_sha256": native["external_prefix_sha256"],
        "tiff_flavour": native["tiff_flavour"],
        "tiff_byte_order": native["byte_order"],
        "first_ifd_fully_within_prefix": native["first_ifd_fully_within_prefix"],
        "expected_10_degree_tile_shape_if_inline": native["expected_10_degree_tile_40000x40000_if_inline"],
        "one_byte_single_band_if_inline": native["single_8bit_band_if_inline"],
        "original_tiff_whole_body_sha256_verified": False,
        "original_post_2026_11_10_corrected_asset_verified": False,
        "source_anonymous_host_service_permission_reviewed": False,
        "current_research_source_access_contract_authorizes_range_request": False,
        "original_provider_request_executed_by_this_validator": False,
        "source_original_prefix_bytes_saved_by_this_validator": False,
        "native_geoaffine_crs_and_pixel_values_verified": False,
        "scientific_cat_model_input_approved": False,
    }
