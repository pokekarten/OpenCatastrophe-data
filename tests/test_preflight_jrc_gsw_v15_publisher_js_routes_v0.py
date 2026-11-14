# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only, no network: source-native JRC 2026 JavaScript route selection."""
from __future__ import annotations

import unittest

from scripts import preflight_jrc_gsw_v15_publisher_js_routes_v0 as jrc


def page(bases=jrc.PUBLISHED_ORDER, *, extra="", file_selector=None, use_base=True):
    assignments = "\n".join(f"var BASE_URL = '{url}';" for url in bases)
    selector = file_selector or (
        "var FILES = ['occurrence/occurrence', 'change/change',"
        " 'seasonality/seasonality', 'recurrence/recurrence'];"
    )
    constructed = (
        "var url = [BASE_URL, FILES[i], '_', lon, '_', lat,"
        " '_v1_5_2024.tif'].join('');"
        if use_base else
        "var url = ['https://unknown.example/', FILES[i]].join('');"
    )
    html = (
        "<!DOCTYPE html><html><body><script>\n"
        + assignments + "\n" + selector + "\n" + extra +
        "\nfunction set_paths(x, y) {\n" + constructed +
        "\n}\n</script></body></html>"
    )
    return html.encode("utf-8")


class OfficialJRCJavascriptRouteTests(unittest.TestCase):
    def test_firstparty_three_assignments_last_cloudferro_wins(self):
        r = jrc.inspect_inline_tile_routes(page())
        self.assertEqual(
            r["publisher_original_three_base_url_assignments"],
            list(jrc.PUBLISHED_ORDER),
        )
        self.assertEqual(r["effective_click_generated_tile_base_url"], jrc.CLOUDFERRO_ACTIVE)
        self.assertEqual(
            r["exact_current_click_tile_url_if_generator_invoked"],
            jrc.CLOUDFERRO_ACTIVE + jrc.ONE_TILE_SUFFIX,
        )
        self.assertEqual(
            r["candidate_google_v15_tile_url_from_overwritten_JS_only"],
            jrc.GCS_2024_OVERWRITTEN + jrc.ONE_TILE_SUFFIX,
        )
        self.assertNotEqual(
            r["effective_click_generated_tile_base_url"],
            r["overwritten_google_v15_candidate_base_url"],
        )
        self.assertTrue(r["google_v15_candidate_overwritten_before_tile_links"])
        self.assertTrue(r["legacy_v14_google_url_also_overwritten"])
        self.assertEqual(r["effective_download_host"], "s3.waw4-1.cloudferro.com")

    def test_offline_source_inspection_cannot_assert_asset_or_commercial_licence(self):
        r = jrc.inspect_inline_tile_routes(page())
        for k in (
            "publisher_javascript_executed",
            "original_cloudferro_tiff_fetched",
            "original_google_v15_tiff_fetched",
            "cloudferro_anonymous_bulk_or_range_terms_approved",
            "google_v15_object_current_access_verified",
            "google_v15_post_2026_11_10_correction_verified",
            "tiff_original_complete_sha256_verified",
            "raster_header_and_numeric_pixels_verified",
            "original_provider_bytes_persisted",
            "scientific_cat_model_input_approved",
        ):
            with self.subTest(k=k):
                self.assertFalse(r[k])
        self.assertEqual(r["automated_source_asset_requests_approved"], 0)
        self.assertEqual(
            r["profile"], "jrc_gsw_v15_publisher_inline_js_route_order_v0",
        )

    def test_missing_or_new_fourth_assignment_fails_closed(self):
        for bases in (
            jrc.PUBLISHED_ORDER[:1],
            jrc.PUBLISHED_ORDER[:2],
            jrc.PUBLISHED_ORDER + (jrc.CLOUDFERRO_ACTIVE,),
            (),
        ):
            with self.subTest(bases=bases), self.assertRaises(jrc.JSRouteBlocked):
                jrc.inspect_inline_tile_routes(page(bases=bases))

    def test_order_change_disallows_wrong_google_current_claim(self):
        for bases in (
            (jrc.GCS_2021_OLD, jrc.CLOUDFERRO_ACTIVE, jrc.GCS_2024_OVERWRITTEN),
            (jrc.CLOUDFERRO_ACTIVE, jrc.GCS_2024_OVERWRITTEN, jrc.GCS_2021_OLD),
            (jrc.GCS_2024_OVERWRITTEN, jrc.GCS_2021_OLD, jrc.CLOUDFERRO_ACTIVE),
        ):
            with self.subTest(bases=bases), self.assertRaises(jrc.JSRouteBlocked):
                jrc.inspect_inline_tile_routes(page(bases=bases))

    def test_unpublished_google_or_swift_host_changes_block(self):
        cases = (
            (jrc.GCS_2021_OLD, "https://evil.example/"),
            (jrc.GCS_2024_OVERWRITTEN, "https://storage.googleapis.com/other-bucket/"),
            (jrc.CLOUDFERRO_ACTIVE, "https://s3.other-cloudferro.example/"),
            ("VER1-5", "VER1-4"),
        )
        for before, after in cases:
            raw = page().replace(before.encode(), after.encode())
            with self.subTest(change=(before, after)), self.assertRaises(jrc.JSRouteBlocked):
                jrc.inspect_inline_tile_routes(raw)

    def test_unexpected_late_dynamic_assignment_blocks_trust(self):
        for extra in (
            "BASE_URL = 'https://evil.example/a/';",
            "var BASE_URL = 'https://evil.example/a/';",
            "if (true) { BASE_URL = 'https://evil.example/b/'; }",
        ):
            with self.subTest(extra=extra), self.assertRaises(jrc.JSRouteBlocked):
                jrc.inspect_inline_tile_routes(page(extra=extra))

    def test_no_script_or_duplicate_set_paths_code(self):
        raw = page()
        for changed in (
            b"<html><body>No script</body></html>",
            raw.replace(b"<script>", b"<script src='https://else.example/'>"),
            raw + raw,
        ):
            with self.subTest(raw=changed[:50]), self.assertRaises(jrc.JSRouteBlocked):
                jrc.inspect_inline_tile_routes(changed)

    def test_native_occurrence_product_and_LINK_builder_required(self):
        for raw in (
            page(file_selector="var FILES=['recurrence/recurrence'];"),
            page(use_base=False),
            page().replace(b"function set_paths", b"function set_other_paths"),
        ):
            with self.subTest(raw=raw[-120:]), self.assertRaises(jrc.JSRouteBlocked):
                jrc.inspect_inline_tile_routes(raw)

    def test_source_html_bytes_not_allowed_to_exceed_one_page(self):
        for raw in (
            b"", b"\xff", b"\x00" + page(),
            page() + b"a" * jrc.MAX_HTML_BYTES,
        ):
            with self.subTest(n=len(raw)), self.assertRaises(jrc.JSRouteBlocked):
                jrc.inspect_inline_tile_routes(raw)
        with self.assertRaises(jrc.JSRouteBlocked):
            jrc.inspect_inline_tile_routes("<html>some human-readable text</html>")

    def test_assignment_after_route_generator_is_not_accepted(self):
        raw=page()
        to_move = ("var BASE_URL = '" + jrc.CLOUDFERRO_ACTIVE + "';").encode("utf-8")
        move_to = b"}\n" + to_move
        changed=raw.replace(to_move, b"").replace(b"}\n</script>",move_to+b"\n</script>")
        with self.assertRaises(jrc.JSRouteBlocked):
            jrc.inspect_inline_tile_routes(changed)


if __name__ == "__main__":
    unittest.main()
