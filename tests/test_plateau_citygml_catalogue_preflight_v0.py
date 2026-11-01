# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only adversarial tests; never download or commit PLATEAU provider bytes."""

from __future__ import annotations

import copy
import json
import unittest

from research_runners.plateau_citygml_catalogue_preflight_v0 import (
    CataloguePreflightError,
    MAX_INPUT_BYTES,
    preflight_bytes,
)


def valid_payload() -> dict:
    return {
        "datasets": [],
        "citygml": [
            {
                "id": "13104", "city": "Shinjuku", "city_code": "13104",
                "pref": "Tokyo", "pref_code": "13",
                "year": 2024, "registration_year": 2025, "spec": "4.1",
                "feature_types": ["bldg", "tran", "dem"],
                "url": "https://example.org/synthetic-source.zip",
                "composite_url": "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-2024/citygml.zip",
                "file_size": None, "gspatialjp_dataset_url": None,
                "gspatialjp_files": [],
            },
        ],
        "latest_citygml": [
            {"city_code": "13104", "year": "latest", "url": "https://example.org/synthetic-latest"}
        ],
    }


def check(payload: dict) -> dict:
    return preflight_bytes(json.dumps(payload).encode("utf-8"))


class PlateauCataloguePreflightTests(unittest.TestCase):
    def test_synthetic_fixed_release_passes_without_network_or_admission(self):
        result = check(valid_payload())
        self.assertEqual(result["target_city_code"], "13104")
        self.assertEqual(result["target_fiscal_year"], 2024)
        self.assertTrue(result["bldg_advertised"])
        self.assertTrue(result["mutable_latest_alias_present_but_not_selected"])
        self.assertFalse(result["provider_network_access"])
        self.assertFalse(result["provider_original_bytes_verified"])
        self.assertFalse(result["model_input_approved"])
        self.assertNotIn("url", result)

    def test_no_latest_alias_is_allowed(self):
        data = valid_payload()
        data["latest_citygml"] = []
        self.assertFalse(check(data)["mutable_latest_alias_present_but_not_selected"])

    def test_duplicate_target_city_year_rejected(self):
        data = valid_payload()
        data["citygml"].append(copy.deepcopy(data["citygml"][0]))
        with self.assertRaisesRegex(CataloguePreflightError, "exactly one"):
            check(data)

    def test_other_year_cannot_substitute_for_frozen_year(self):
        data = valid_payload()
        data["citygml"][0]["year"] = 2025
        with self.assertRaisesRegex(CataloguePreflightError, "exactly one"):
            check(data)

    def test_latest_cannot_substitute_concrete_year(self):
        data = valid_payload()
        data["citygml"][0]["year"] = "latest"
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_boolean_year_is_not_an_integer(self):
        data = valid_payload()
        data["citygml"][0]["year"] = True
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_duplicate_feature_type_rejected(self):
        data = valid_payload()
        data["citygml"][0]["feature_types"] = ["bldg", "bldg"]
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_missing_bldg_rejected(self):
        data = valid_payload()
        data["citygml"][0]["feature_types"] = ["tran"]
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(CataloguePreflightError, "duplicate JSON key"):
            preflight_bytes(b'{"citygml":[],"citygml":[],"latest_citygml":[]}')

    def test_nonfinite_json_rejected(self):
        with self.assertRaisesRegex(CataloguePreflightError, "non-finite"):
            preflight_bytes(b'{"citygml":NaN,"latest_citygml":[]}')

    def test_gigantic_input_rejected_before_json_parse(self):
        with self.assertRaisesRegex(CataloguePreflightError, "bounded metadata size"):
            preflight_bytes(b"x" * (MAX_INPUT_BYTES + 1))

    def test_wrong_prefecture_rejected(self):
        data = valid_payload()
        data["citygml"][0]["pref_code"] = "01"
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_negative_zip_size_rejected(self):
        data = valid_payload()
        data["citygml"][0]["file_size"] = -1
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_required_source_url_rejected_when_null(self):
        data = valid_payload()
        data["citygml"][0]["url"] = None
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_frozen_composite_url_is_verified_as_year_specific(self):
        self.assertTrue(check(valid_payload())["fixed_year_composite_url_present"])

    def test_null_composite_is_explicitly_reported_as_unavailable(self):
        data = valid_payload()
        data["citygml"][0]["composite_url"] = None
        self.assertFalse(check(data)["fixed_year_composite_url_present"])

    def test_latest_composite_url_rejected_even_with_fixed_row_year(self):
        data = valid_payload()
        data["citygml"][0]["composite_url"] = (
            "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-latest/citygml.zip"
        )
        with self.assertRaisesRegex(CataloguePreflightError, "must pin"):
            check(data)

    def test_wrong_municipality_in_composite_url_rejected(self):
        data = valid_payload()
        data["citygml"][0]["composite_url"] = (
            "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13105-2024/citygml.zip"
        )
        with self.assertRaisesRegex(CataloguePreflightError, "must pin"):
            check(data)

    def test_wrong_year_in_composite_url_rejected(self):
        data = valid_payload()
        data["citygml"][0]["composite_url"] = (
            "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-2025/citygml.zip"
        )
        with self.assertRaisesRegex(CataloguePreflightError, "must pin"):
            check(data)

    def test_mutable_latest_original_url_rejected(self):
        data = valid_payload()
        data["citygml"][0]["url"] = (
            "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-latest/citygml.zip"
        )
        with self.assertRaisesRegex(CataloguePreflightError, "mutable latest"):
            check(data)

    def test_private_or_loopback_source_url_rejected(self):
        for url in ("https://localhost/file.zip", "https://127.0.0.1/file.zip", "https://192.168.0.1/file.zip"):
            with self.subTest(url=url):
                data = valid_payload()
                data["citygml"][0]["url"] = url
                with self.assertRaises(CataloguePreflightError):
                    check(data)

    def test_signed_query_and_fragment_rejected(self):
        for url in ("https://example.org/file.zip?token=secret", "https://example.org/file.zip#fragment"):
            with self.subTest(url=url):
                data = valid_payload()
                data["citygml"][0]["url"] = url
                with self.assertRaises(CataloguePreflightError):
                    check(data)

    def test_invalid_port_rejected(self):
        data = valid_payload()
        data["citygml"][0]["url"] = "https://example.org:65536/file.zip"
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_credentialed_catalogue_url_rejected(self):
        data = valid_payload()
        data["citygml"][0]["url"] = "https://user:secret@example.org/file.zip"
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_bad_latest_year_rejected(self):
        data = valid_payload()
        data["latest_citygml"][0]["year"] = 2024
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_no_raw_provider_urls_emitted(self):
        data = valid_payload()
        data["citygml"][0]["gspatialjp_dataset_url"] = "https://example.org/rights-page"
        result = check(data)
        self.assertTrue(result["gspatial_catalogue_page_known"])
        self.assertNotIn("example.org", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
