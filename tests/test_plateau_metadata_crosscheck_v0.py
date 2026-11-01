# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strictly synthetic PLATEAU REST/GraphQL metadata consistency tests."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from research_runners.plateau_citygml_catalogue_preflight_v0 import CataloguePreflightError
from research_runners.plateau_metadata_crosscheck_v0 import crosscheck_bytes, main

FIXED_COMPOSITE = (
    "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-2024/citygml.zip"
)


def rest_fixture() -> dict:
    return {
        "citygml": [{
            "id": "13104",
            "city": "Shinjuku",
            "city_code": "13104",
            "pref_code": "13",
            "year": 2024,
            "registration_year": 2025,
            "spec": "4.1",
            "feature_types": ["bldg", "tran"],
            "file_size": 12345,
            "url": "https://example.org/synthetic-cms.zip",
            "composite_url": FIXED_COMPOSITE,
            "gspatialjp_dataset_url": None,
            "gspatialjp_files": [{
                "kind": "citygml",
                "name": "Synthetic independent archive",
                "url": "https://example.org/synthetic-gspatial.zip",
                "file_size": 98765,
            }],
        }],
        "latest_citygml": [],
    }


def graphql_fixture() -> dict:
    return {
        "data": {"citygmlDatasets": [{
            "id": "synthetic-different-native-id",
            "cityCode": "13104",
            "prefectureCode": "13",
            "year": 2024,
            "registrationYear": 2025,
            "featureTypes": ["bldg", "tran"],
            "url": "https://example.org/synthetic-cms.zip",
            "compositeUrl": FIXED_COMPOSITE,
            "metadataZipUrls": [],
        }]},
    }


def compare(rest: dict, graphql: dict) -> dict:
    return crosscheck_bytes(
        json.dumps(rest).encode("utf-8"),
        json.dumps(graphql).encode("utf-8"),
    )


class PlateauMetadataCrosscheckTests(unittest.TestCase):
    def test_common_fields_agree_but_no_independent_or_legal_admission(self):
        rest, graphql = rest_fixture(), graphql_fixture()
        result = compare(rest, graphql)
        self.assertEqual(result["metadata_crosscheck"], "common_fields_structurally_consistent")
        self.assertEqual(result["target_city_code"], "13104")
        self.assertTrue(result["same_upstream_possible"])
        self.assertTrue(result["rest_cms_size_metadata_known"])
        for key in ("provider_original_bytes_verified", "independent_building_verification", "licence_review_completed", "model_input_approved", "provider_network_access"):
            self.assertFalse(result[key], key)
        self.assertTrue(result["graphql_cms_size_not_selected"])
        self.assertTrue(result["gspatial_archive_metadata_not_comparable_to_cms"])
        output = json.dumps(result)
        for forbidden in ("example.org", "native-id", "synthetic-cms", "98765", "12345"):
            self.assertNotIn(forbidden, output)

    def test_input_hashes_bind_exact_distinct_response_bytes(self):
        rest = json.dumps(rest_fixture()).encode()
        graphql = json.dumps(graphql_fixture()).encode()
        result = crosscheck_bytes(rest, graphql)
        self.assertEqual(result["rest_metadata_sha256"], hashlib.sha256(rest).hexdigest())
        self.assertEqual(result["graphql_metadata_sha256"], hashlib.sha256(graphql).hexdigest())
        self.assertEqual(result["rest_metadata_byte_count"], len(rest))
        self.assertEqual(result["graphql_metadata_byte_count"], len(graphql))

    def test_feature_order_does_not_change_set_agreement(self):
        graph = graphql_fixture()
        graph["data"]["citygmlDatasets"][0]["featureTypes"] = ["tran", "bldg"]
        self.assertEqual(compare(rest_fixture(), graph)["metadata_crosscheck"], "common_fields_structurally_consistent")

    def test_different_registration_year_blocks_comparison(self):
        graph = graphql_fixture()
        graph["data"]["citygmlDatasets"][0]["registrationYear"] = 2026
        with self.assertRaisesRegex(CataloguePreflightError, "registration years disagree"):
            compare(rest_fixture(), graph)

    def test_different_feature_types_blocks_comparison(self):
        graph = graphql_fixture()
        graph["data"]["citygmlDatasets"][0]["featureTypes"] = ["bldg", "dem"]
        with self.assertRaisesRegex(CataloguePreflightError, "feature types disagree"):
            compare(rest_fixture(), graph)

    def test_different_cms_url_blocks_without_echoing_url(self):
        graph = graphql_fixture()
        graph["data"]["citygmlDatasets"][0]["url"] = "https://example.org/synthetic-another-cms.zip"
        with self.assertRaisesRegex(CataloguePreflightError, "original CMS URL metadata disagree") as caught:
            compare(rest_fixture(), graph)
        self.assertNotIn("example.org", str(caught.exception))

    def test_composite_must_be_present_on_both_sides(self):
        for source in ("rest", "graphql"):
            with self.subTest(source=source):
                rest, graph = rest_fixture(), graphql_fixture()
                if source == "rest":
                    rest["citygml"][0]["composite_url"] = None
                else:
                    graph["data"]["citygmlDatasets"][0]["compositeUrl"] = None
                with self.assertRaisesRegex(CataloguePreflightError, "both views"):
                    compare(rest, graph)

    def test_wrong_city_or_fiscal_year_blocked_by_existing_preflights(self):
        for field, value in (("cityCode", "13105"), ("year", 2023), ("year", "latest")):
            with self.subTest(field=field, value=value):
                graph = graphql_fixture()
                graph["data"]["citygmlDatasets"][0][field] = value
                with self.assertRaises(CataloguePreflightError):
                    compare(rest_fixture(), graph)

    def test_rest_duplicate_selected_record_is_rejected(self):
        rest = rest_fixture()
        rest["citygml"].append(copy.deepcopy(rest["citygml"][0]))
        with self.assertRaises(CataloguePreflightError):
            compare(rest, graphql_fixture())

    def test_no_building_layer_is_rejected(self):
        rest = rest_fixture()
        rest["citygml"][0]["feature_types"] = ["tran"]
        with self.assertRaises(CataloguePreflightError):
            compare(rest, graphql_fixture())

    def test_rest_and_graphql_file_size_are_not_misidentified(self):
        rest = rest_fixture()
        rest["citygml"][0]["file_size"] = None
        result = compare(rest, graphql_fixture())
        self.assertFalse(result["rest_cms_size_metadata_known"])
        self.assertTrue(result["graphql_cms_size_not_selected"])

    def test_malformed_nonfinite_and_duplicate_keys_blocked(self):
        rest = json.dumps(rest_fixture()).encode("utf-8")
        graph = json.dumps(graphql_fixture()).encode("utf-8")
        for invalid in (b'{ "citygml": [], "citygml": [], "latest_citygml": [] }', b'{"citygml":NaN,"latest_citygml":[]}'):
            with self.subTest(invalid=invalid[:20]):
                with self.assertRaises(CataloguePreflightError):
                    crosscheck_bytes(invalid, graph)
        with self.assertRaises(CataloguePreflightError):
            crosscheck_bytes(rest, b'{"data": {"citygmlDatasets": NaN}}')

    def test_metadata_cli_works_offline_without_leaking_local_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            rest_path = Path(directory) / "rest.json"
            graph_path = Path(directory) / "graphql.json"
            rest_path.write_text(json.dumps(rest_fixture()), encoding="utf-8")
            graph_path.write_text(json.dumps(graphql_fixture()), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                status = main(["--rest-input", str(rest_path), "--graphql-input", str(graph_path)])
            self.assertEqual(status, 0)
            self.assertEqual(err.getvalue(), "")
            self.assertEqual(json.loads(out.getvalue())["target_fiscal_year"], 2024)
            self.assertNotIn(str(rest_path), out.getvalue())
            self.assertNotIn(str(graph_path), out.getvalue())
            self.assertNotIn("example.org", out.getvalue())

    def test_missing_input_fails_without_printing_file_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            rest_path = Path(directory) / "nonexistent-rest.json"
            graph_path = Path(directory) / "nonexistent-graphql.json"
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                status = main(["--rest-input", str(rest_path), "--graphql-input", str(graph_path)])
            self.assertEqual(status, 2)
            self.assertIn("BLOCKED:", err.getvalue())
            self.assertNotIn(str(rest_path), err.getvalue())
            self.assertEqual(out.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
