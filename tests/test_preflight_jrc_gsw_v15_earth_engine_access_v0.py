# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: GSW 1.5 GEE commercial transport is never an auto-pass."""
from __future__ import annotations

from copy import deepcopy
import tomllib
import unittest

from scripts import preflight_jrc_gsw_v15_earth_engine_access_v0 as jrc


class JRCEarthEngineAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = tomllib.loads(jrc.POLICY_FILE.read_text(encoding="utf-8"))

    def test_exact_official_asset_and_commercial_transport_separation(self):
        result = jrc.inspect_policy(self.policy)
        self.assertEqual(result["original_publisher_earth_engine_asset_id"], jrc.ASSET_ID)
        self.assertEqual(self.policy["source_period"], "1984-2024")
        self.assertEqual(self.policy["publisher_correction_announcement_date"], "2026-11-10")
        self.assertTrue(result["publisher_data_commercial_reuse_allowed_with_attribution"])
        self.assertFalse(result["commercial_cloud_service_prerequisites_met_on_paper"])
        self.assertGreaterEqual(len(result["missing_commercial_service_prerequisites"]), 4)
        self.assertFalse(result["google_earth_engine_api_request_executed"])
        self.assertFalse(result["google_earth_engine_request_authorized_by_this_policy"])
        self.assertFalse(result["model_input_approved"])

    def test_unreviewed_noncommercial_and_wrong_version_are_blocked(self):
        for replacement in (
            "JRC/GSW1_4/GlobalSurfaceWater",
            "projects/global-surface-water/assets/GSW1_5/Recurrence",
            "https://storage.googleapis.com/water-world/tiles2024/occurrence/0/0/0.png",
        ):
            p = deepcopy(self.policy)
            p["publisher_asset_id"] = replacement
            with self.subTest(value=replacement), self.assertRaises(
                jrc.EarthEngineRouteBlocked
            ):
                jrc.inspect_policy(p)

    def test_billing_not_inferred_from_noncommercial_google_project(self):
        p = deepcopy(self.policy)
        p["reviewed_registered_commercial_cloud_project"] = True
        p["service_registration_state"] = "reviewed_commercial"
        result = jrc.inspect_policy(p)
        self.assertIn(
            "reviewed_paid_earth_engine_subscription",
            result["missing_commercial_service_prerequisites"],
        )
        self.assertFalse(result["google_earth_engine_request_authorized_by_this_policy"])

    def test_even_all_commercial_prerequisites_do_not_authorize_network_or_pixels(self):
        p = deepcopy(self.policy)
        p["service_registration_state"] = "reviewed_commercial"
        for key in jrc.REVIEW_FLAGS:
            p[key] = True
        result = jrc.inspect_policy(p)
        self.assertTrue(result["commercial_cloud_service_prerequisites_met_on_paper"])
        self.assertEqual(result["missing_commercial_service_prerequisites"], [])
        for key in (
            "google_earth_engine_api_request_executed",
            "google_earth_engine_request_authorized_by_this_policy",
            "post_2026_11_10_corrected_original_values_verified",
            "raw_source_bytes_persisted",
            "rgb_wmts_accepted_as_numeric_source",
            "model_input_approved",
        ):
            self.assertFalse(result[key])

    def test_reject_any_single_flag_network_or_source_admission_promotion(self):
        for key in jrc.NEVER_AUTOMATIC_FLAGS:
            p = deepcopy(self.policy)
            p[key] = True
            with self.subTest(key=key), self.assertRaises(
                jrc.EarthEngineRouteBlocked
            ):
                jrc.inspect_policy(p)
        p = deepcopy(self.policy)
        p["approved_network_requests"] = 1
        with self.assertRaises(jrc.EarthEngineRouteBlocked):
            jrc.inspect_policy(p)

    def test_reject_wrong_types_missing_policy_and_untrusted_query_inputs(self):
        for key, invalid in (
            ("approved_network_requests", True),
            ("reviewed_paid_earth_engine_subscription", 1),
            ("service_registration_state", "noncommercial"),
            ("source_period", "1984-2021"),
            ("required_attribution", ""),
        ):
            p = deepcopy(self.policy)
            p[key] = invalid
            with self.subTest(key=key), self.assertRaises(
                jrc.EarthEngineRouteBlocked
            ):
                jrc.inspect_policy(p)
        p = deepcopy(self.policy)
        p["google_cloud_project_id"] = "untrusted-project"
        with self.assertRaises(jrc.EarthEngineRouteBlocked):
            jrc.inspect_policy(p)

    def test_no_network_provider_clients_or_credentials(self):
        source = jrc.POLICY_FILE.read_text(encoding="utf-8") + (
            jrc.Path(jrc.__file__).read_text(encoding="utf-8")
        )
        for needle in (
            "google.auth", "ee.Initialize(", "requests.get(", "urlopen(",
            "urllib.request", "service_account_email", "service_account_key",
            "billing_account_id",
        ):
            self.assertNotIn(needle, source)
        with self.assertRaises(SystemExit):
            jrc.main(["--policy-file", "/nonexistent/gsw.toml"])


if __name__ == "__main__":
    unittest.main()
