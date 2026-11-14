# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict OFFLINE parser of JRC GSW v1.5 HTML inline tile-link JavaScript.

The first-party JRC publisher page sets JavaScript BASE_URL THREE times, in
sequence. The last one before set_paths() is the effective path for clicks.
The earlier water-world GCS v1.5 URL is an overwritten candidate, not a
verified post-2026-11-10 original GSW TIFF or authorized network route.

Never execute JavaScript, visit URLs, read provider TIFF bytes, or infer
download rights or scientific hazard-model admission from source-code text.
"""
from __future__ import annotations

import re

SOURCE = "ec-jrc.global-surface-water.1984-2024"
PUBLISHER_URL = "https://global-surface-water.appspot.com/download"
GCS_2021_OLD = "https://storage.googleapis.com/global-surface-water/downloads2021/"
GCS_2024_OVERWRITTEN = "https://storage.googleapis.com/water-world/download2024/VER1-5/"
CLOUDFERRO_ACTIVE = (
    "https://s3.waw4-1.cloudferro.com/swift/v1/"
    "global-surface-water/download2024/Aggregated/VER1-5/"
)
PUBLISHED_ORDER = (GCS_2021_OLD, GCS_2024_OVERWRITTEN, CLOUDFERRO_ACTIVE)
ONE_TILE_SUFFIX = "occurrence/occurrence_10E_50N_v1_5_2024.tif"
MAX_HTML_BYTES = 262144
_SCRIPT_BLOCK = re.compile(
    r"<script\b[^>]*>(.*?)</script\s*>", flags=re.IGNORECASE | re.DOTALL
)
_FUNCTION = re.compile(r"\bfunction\s+set_paths\s*\(")
_BASE_ASSIGNMENT = re.compile(
    r"\bvar\s+BASE_URL\s*=\s*(['\"])(https://[^'\"\s<>]+)\1\s*;"
)
_ALL_BASE_WRITES = re.compile(r"\bBASE_URL\s*=")


class JSRouteBlocked(ValueError):
    """The JRC page's first-party original route selector has changed."""


def inspect_inline_tile_routes(raw: bytes) -> dict[str, object]:
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_HTML_BYTES):
        raise JSRouteBlocked("source HTML is absent or exceeds documented cap")
    try:
        page = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise JSRouteBlocked("publisher HTML not strict UTF-8") from exc
    if "\x00" in page:
        raise JSRouteBlocked("binary content in publisher HTML")
    blocks = []
    for item in _SCRIPT_BLOCK.finditer(page):
        code = item.group(1)
        if _FUNCTION.search(code):
            opening_tag = item.group(0).split(">", 1)[0]
            if re.search(r"\bsrc\s*=", opening_tag, flags=re.IGNORECASE):
                raise JSRouteBlocked("external script src cannot prove inline publisher routing")
            blocks.append(code)
    if len(blocks) != 1:
        raise JSRouteBlocked("exactly one publisher set_paths inline script required")
    code = blocks[0]
    assignments = list(_BASE_ASSIGNMENT.finditer(code))
    if len(assignments) != 3 or len(_ALL_BASE_WRITES.findall(code)) != 3:
        raise JSRouteBlocked("unexpected extra or missing dynamic tile base assignments")
    values = tuple(m.group(2) for m in assignments)
    if values != PUBLISHED_ORDER:
        raise JSRouteBlocked("publisher original source tile-host order drift")
    match_func = _FUNCTION.search(code)
    if match_func is None or assignments[-1].end() >= match_func.start():
        raise JSRouteBlocked("tile base selected after or within link constructor")
    if not re.search(
        r"\bvar\s+FILES\s*=\s*\[\s*['\"]occurrence/occurrence['\"]",
        code,
    ):
        raise JSRouteBlocked("official occurrence TIFF source product selector changed")
    if not re.search(
        r"\[\s*BASE_URL\s*,\s*FILES\s*\[\s*i\s*\]", code
    ):
        raise JSRouteBlocked("tile link constructor no longer uses source BASE_URL")
    # Do not execute the JS, construct caller-controlled URLs, or inspect any
    # network endpoint. These are literal source routes only.
    return {
        "profile": "jrc_gsw_v15_publisher_inline_js_route_order_v0",
        "source_id": SOURCE,
        "original_official_publisher_page": PUBLISHER_URL,
        "publisher_original_three_base_url_assignments": list(values),
        "effective_click_generated_tile_base_url": CLOUDFERRO_ACTIVE,
        "effective_download_host": "s3.waw4-1.cloudferro.com",
        "overwritten_google_v15_candidate_base_url": GCS_2024_OVERWRITTEN,
        "google_v15_candidate_overwritten_before_tile_links": True,
        "legacy_v14_google_url_also_overwritten": True,
        "exact_current_click_tile_url_if_generator_invoked":
            CLOUDFERRO_ACTIVE + ONE_TILE_SUFFIX,
        "candidate_google_v15_tile_url_from_overwritten_JS_only":
            GCS_2024_OVERWRITTEN + ONE_TILE_SUFFIX,
        "publisher_javascript_executed": False,
        "original_cloudferro_tiff_fetched": False,
        "original_google_v15_tiff_fetched": False,
        "cloudferro_anonymous_bulk_or_range_terms_approved": False,
        "google_v15_object_current_access_verified": False,
        "google_v15_post_2026_11_10_correction_verified": False,
        "tiff_original_complete_sha256_verified": False,
        "raster_header_and_numeric_pixels_verified": False,
        "automated_source_asset_requests_approved": 0,
        "original_provider_bytes_persisted": False,
        "scientific_cat_model_input_approved": False,
    }
