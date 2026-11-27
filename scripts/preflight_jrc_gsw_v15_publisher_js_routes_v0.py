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

from html.parser import HTMLParser
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
_FUNCTION = re.compile(r"\bfunction\s+set_paths\s*\(")
_BASE_ASSIGNMENT = re.compile(
    r"\bvar\s+BASE_URL\s*=\s*(['\"])(https://[^'\"\s<>]+)\1\s*;"
)
_ALL_BASE_WRITES = re.compile(r"\bBASE_URL\s*=")


class JSRouteBlocked(ValueError):
    """The JRC page's first-party original route selector has changed."""


class _ScriptCollector(HTMLParser):
    """Read inline script elements using HTML tokens, not a tag regexp.

    Noncanonical/ambiguous closing tags must not produce an accepted
    first-party script. No JavaScript is executed or source HTML echoed.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.blocks: list[tuple[str, bool]] = []
        self._parts: list[str] | None = None
        self._has_src = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            if self._parts is not None:
                raise JSRouteBlocked("ambiguous nested script element")
            self._parts = []
            self._has_src = any(name == "src" for name, _ in attrs)

    def handle_data(self, data: str) -> None:
        if self._parts is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            if self._parts is None:
                raise JSRouteBlocked("unmatched publisher script closing tag")
            self.blocks.append(("".join(self._parts), self._has_src))
            self._parts = None

    def extract(self, page: str) -> list[tuple[str, bool]]:
        self.feed(page)
        self.close()
        if self._parts is not None:
            raise JSRouteBlocked("unclosed publisher script element")
        return self.blocks


def _reject_noncanonical_script_end_tags(page: str) -> None:
    """Reject ambiguous HTML5 closing syntax before HTMLParser tokenization.

    Python's HTMLParser and browsers differ about '</script ...>' and
    '</script/foo>' handling, including across Python runtime versions.
    This is a conservative literal lexical guard, not a regex HTML parser:
    an accepted publisher script must use '</script>' with optional
    whitespace only before '>'. The original publisher uses canonical tags.
    """
    lower = page.lower()
    position = 0
    while True:
        start = lower.find("</script", position)
        if start < 0:
            return
        end = page.find(">", start)
        if end < 0 or page[start + len("</script"):end].strip():
            raise JSRouteBlocked("noncanonical publisher script closing tag")
        position = end + 1


def inspect_inline_tile_routes(raw: bytes) -> dict[str, object]:
    if type(raw) is not bytes or not (0 < len(raw) <= MAX_HTML_BYTES):
        raise JSRouteBlocked("source HTML is absent or exceeds documented cap")
    try:
        page = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise JSRouteBlocked("publisher HTML not strict UTF-8") from exc
    if "\x00" in page:
        raise JSRouteBlocked("binary content in publisher HTML")
    _reject_noncanonical_script_end_tags(page)
    blocks = []
    for code, has_external_src in _ScriptCollector().extract(page):
        if _FUNCTION.search(code):
            if has_external_src:
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
