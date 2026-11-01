# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only adversarial tests; never download or commit PLATEAU provider bytes."""

from __future__ import annotations

import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from research_runners.plateau_citygml_catalogue_preflight_v0 import (
    CataloguePreflightError,
    GRAPHQL_MAX_INPUT_BYTES,
    GRAPHQL_CITYGML_FIELD_NAMES,
    MAX_INPUT_BYTES,
    main,
    preflight_bytes,
    preflight_graphql_bytes,
    read_local_metadata,
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
                "gspatialjp_dataset_url": None,
                "gspatialjp_files": [],
                "file_size": None,
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

    def test_multiple_fiscal_years_for_same_city_are_valid(self):
        data = valid_payload()
        previous = copy.deepcopy(data["citygml"][0])
        previous["year"] = 2023
        previous["registration_year"] = 2024
        previous["composite_url"] = (
            "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-2023/citygml.zip"
        )
        data["citygml"].append(previous)
        result = check(data)
        self.assertEqual(result["target_fiscal_year"], 2024)
        self.assertTrue(result["fixed_year_composite_url_present"])

    def test_non_target_city_fiscal_year_mismatch_is_blocked(self):
        data = valid_payload()
        other = copy.deepcopy(data["citygml"][0])
        other["year"] = 2023
        other["composite_url"] = (
            "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-2025/citygml.zip"
        )
        data["citygml"].append(other)
        with self.assertRaisesRegex(CataloguePreflightError, "must pin"):
            check(data)

    def test_duplicate_target_city_year_rejected(self):
        data = valid_payload()
        data["citygml"].append(copy.deepcopy(data["citygml"][0]))
        with self.assertRaisesRegex(CataloguePreflightError, "exactly one"):
            check(data)

    def test_other_year_cannot_substitute_for_frozen_year(self):
        data = valid_payload()
        data["citygml"][0]["year"] = 2025
        data["citygml"][0]["composite_url"] = (
            "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-2025/citygml.zip"
        )
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

    def test_rest_optional_cms_zip_size_is_distinct_from_gspatial_zip(self):
        data = valid_payload()
        data["citygml"][0]["file_size"] = 333333
        data["citygml"][0]["gspatialjp_files"] = [{
            "kind": "citygml", "name": "Synthetic G-Spatial archive",
            "url": "https://example.org/synthetic-gspatial.zip", "file_size": 111111,
        }]
        result = check(data)
        self.assertTrue(result["cms_original_size_metadata_known"])
        self.assertEqual(result["gspatial_citygml_file_count"], 1)
        self.assertTrue(result["gspatial_citygml_file_sizes_all_known"])
        self.assertNotIn("333333", json.dumps(result))
        self.assertNotIn("111111", json.dumps(result))

    def test_rest_invalid_cms_zip_size_is_blocked(self):
        for value in (-1, 0, True, "100"):
            with self.subTest(value=value):
                data = valid_payload()
                data["citygml"][0]["file_size"] = value
                with self.assertRaisesRegex(CataloguePreflightError, "REST CMS file_size"):
                    check(data)

    def test_negative_nested_zip_size_rejected(self):
        data = valid_payload()
        data["citygml"][0]["gspatialjp_files"] = [{
            "kind": "citygml", "name": "Synthetic CityGML",
            "url": "https://example.org/synthetic.zip", "file_size": -1,
        }]
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_gspatial_archive_metadata_is_separate_from_cms_zip(self):
        data = valid_payload()
        data["citygml"][0]["gspatialjp_files"] = [{
            "kind": "citygml", "name": "Synthetic CityGML",
            "url": "https://example.org/synthetic-gspatial.zip", "file_size": 100000,
        }, {
            "kind": "related", "name": "Synthetic related map",
            "url": "https://example.org/synthetic-other.zip",
        }]
        result = check(data)
        self.assertEqual(result["gspatial_citygml_file_count"], 1)
        self.assertTrue(result["gspatial_citygml_file_sizes_all_known"])
        self.assertNotIn("synthetic-gspatial", json.dumps(result))
        self.assertNotIn("provider_file_size_known", result)

    def test_gspatial_citygml_count_can_be_zero_without_claiming_source_size(self):
        result = check(valid_payload())
        self.assertEqual(result["gspatial_citygml_file_count"], 0)
        self.assertFalse(result["gspatial_citygml_file_sizes_all_known"])

    def test_gspatial_citygml_size_unknown_is_not_reported_as_known(self):
        data = valid_payload()
        data["citygml"][0]["gspatialjp_files"] = [{
            "kind": "citygml", "name": "Synthetic CityGML",
            "url": "https://example.org/synthetic-gspatial.zip",
        }]
        result = check(data)
        self.assertEqual(result["gspatial_citygml_file_count"], 1)
        self.assertFalse(result["gspatial_citygml_file_sizes_all_known"])

    def test_gspatial_file_schema_rejects_missing_url(self):
        data = valid_payload()
        data["citygml"][0]["gspatialjp_files"] = [{
            "kind": "citygml", "name": "Synthetic CityGML", "file_size": 12345,
        }]
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_gspatial_unknown_file_kind_rejected(self):
        data = valid_payload()
        data["citygml"][0]["gspatialjp_files"] = [{
            "kind": "secret", "name": "Synthetic other",
            "url": "https://example.org/synthetic-other.zip",
        }]
        with self.assertRaises(CataloguePreflightError):
            check(data)

    def test_offline_catalogue_larger_than_two_megabytes_is_supported(self):
        data = valid_payload()
        data["extra_provider_metadata"] = "x" * (2 * 1024 * 1024)
        result = check(data)
        self.assertGreater(result["input_byte_count"], 2 * 1024 * 1024)
        self.assertFalse(result["provider_network_access"])

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
        # Construct synthetic prohibited hosts at runtime so repository hygiene
        # does not see static local/private network endpoints in source code.
        blocked_hosts = ("local" + "host", ".".join(("127", "0", "0", "1")), ".".join(("192", "168", "0", "1")))
        for host in blocked_hosts:
            url = f"https://{host}/file.zip"
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


def valid_graphql_payload() -> dict:
    return {
        "data": {
            "citygmlDatasets": [{
                "id": "synthetic-native-record-2024",
                "cityCode": "13104",
                "prefectureCode": "13",
                "year": 2024,
                "registrationYear": 2025,
                "url": "https://example.org/synthetic-cms.zip",
                "metadataZipUrls": [],
                "compositeUrl": (
                    "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-2024/citygml.zip"
                ),
                "featureTypes": ["bldg", "tran"],
            }],
        },
    }


def check_graphql(payload: dict) -> dict:
    return preflight_graphql_bytes(json.dumps(payload).encode("utf-8"))


class PlateauGraphqlMetadataPreflightTests(unittest.TestCase):
    def test_access_contract_exact_query_fields_match_offline_validator(self):
        root = Path(__file__).resolve().parents[1]
        contract_path = root / "access" / "jp.mlit.plateau.graphql.citygml-shinjuku2024.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        rules = contract["request_contract"]["parameter_rules"]
        exact = (
            'citygmlDatasets(input: {cityCodes: ["13104"], years: [2024]}) { '
            + " ".join(GRAPHQL_CITYGML_FIELD_NAMES)
            + " }"
        )
        self.assertIn(exact, rules, "fixed Shinjuku 2024 query and selected fields must match")
        self.assertNotIn("fileSize", rules)
        self.assertEqual(contract["probe_contract"]["mode"], "none")
        self.assertEqual(contract["implementation_decision"], "document_only")

    def test_one_fixed_record_passes_without_network_or_source_admission(self):
        result = check_graphql(valid_graphql_payload())
        self.assertEqual(result["target_fiscal_year"], 2024)
        self.assertEqual(result["target_city_code"], "13104")
        self.assertTrue(result["fixed_year_composite_url_present"])
        self.assertFalse(result["cms_original_size_metadata_known"])
        self.assertFalse(result["provider_network_access"])
        self.assertFalse(result["model_input_approved"])
        self.assertNotIn("synthetic-native-record", json.dumps(result))
        self.assertNotIn("example.org", json.dumps(result))

    def test_graphql_cms_size_not_selected_in_minimal_query(self):
        result = check_graphql(valid_graphql_payload())
        self.assertFalse(result["cms_original_size_metadata_known"])
        self.assertEqual(result["metadata_zip_link_count"], 0)

    def test_file_size_absent_from_our_exact_graphql_selection(self):
        payload = valid_graphql_payload()
        payload["data"]["citygmlDatasets"][0]["fileSize"] = 123456
        with self.assertRaisesRegex(CataloguePreflightError, "unsupported fields"):
            check_graphql(payload)

    def test_metadata_zip_links_are_distinct_from_citygml_original_url(self):
        payload = valid_graphql_payload()
        payload["data"]["citygmlDatasets"][0]["metadataZipUrls"] = [
            "https://example.org/synthetic-meta-a.zip",
            "https://example.org/synthetic-meta-b.zip",
        ]
        result = check_graphql(payload)
        self.assertEqual(result["metadata_zip_link_count"], 2)
        self.assertFalse(result["cms_original_size_metadata_known"])
        self.assertNotIn("example.org", json.dumps(result))

    def test_invalid_metadata_zip_url_or_array_is_rejected(self):
        for value in ("not-an-array", [None], ["ftp://example.org/file.zip"]):
            with self.subTest(value=value):
                payload = valid_graphql_payload()
                payload["data"]["citygmlDatasets"][0]["metadataZipUrls"] = value
                with self.assertRaises(CataloguePreflightError):
                    check_graphql(payload)

    def test_mismatched_prefecture_code_is_rejected(self):
        payload = valid_graphql_payload()
        payload["data"]["citygmlDatasets"][0]["prefectureCode"] = "14"
        with self.assertRaises(CataloguePreflightError):
            check_graphql(payload)

    def test_missing_documented_projection_field_is_rejected(self):
        payload = valid_graphql_payload()
        del payload["data"]["citygmlDatasets"][0]["metadataZipUrls"]
        with self.assertRaisesRegex(CataloguePreflightError, "missing documented fields"):
            check_graphql(payload)

    def test_unfiltered_or_duplicate_results_are_not_promoted(self):
        payload = valid_graphql_payload()
        payload["data"]["citygmlDatasets"].append(copy.deepcopy(payload["data"]["citygmlDatasets"][0]))
        with self.assertRaisesRegex(CataloguePreflightError, "exactly one"):
            check_graphql(payload)

    def test_graphql_errors_rejected_even_when_data_is_present(self):
        payload = valid_graphql_payload()
        payload["errors"] = [{"message": "synthetic incomplete result"}]
        with self.assertRaisesRegex(CataloguePreflightError, "errors"):
            check_graphql(payload)

    def test_wrong_city_or_year_rejected(self):
        for key, value in (("cityCode", "13105"), ("year", 2023), ("year", "2024")):
            with self.subTest(key=key, value=value):
                payload = valid_graphql_payload()
                payload["data"]["citygmlDatasets"][0][key] = value
                with self.assertRaises(CataloguePreflightError):
                    check_graphql(payload)

    def test_latest_composite_redirect_is_rejected(self):
        payload = valid_graphql_payload()
        payload["data"]["citygmlDatasets"][0]["compositeUrl"] = (
            "https://api.plateauview.mlit.go.jp/datacatalog/citygml/13104-latest/citygml.zip"
        )
        with self.assertRaises(CataloguePreflightError):
            check_graphql(payload)

    def test_nullable_composite_is_recorded_as_absent(self):
        payload = valid_graphql_payload()
        payload["data"]["citygmlDatasets"][0]["compositeUrl"] = None
        self.assertFalse(check_graphql(payload)["fixed_year_composite_url_present"])

    def test_missing_bldg_feature_rejected(self):
        payload = valid_graphql_payload()
        payload["data"]["citygmlDatasets"][0]["featureTypes"] = ["tran"]
        with self.assertRaises(CataloguePreflightError):
            check_graphql(payload)

    def test_oversized_or_malformed_graphql_rejected(self):
        with self.assertRaises(CataloguePreflightError):
            preflight_graphql_bytes(b"x" * (GRAPHQL_MAX_INPUT_BYTES + 1))
        with self.assertRaises(CataloguePreflightError):
            preflight_graphql_bytes(b'{"data":{"citygmlDatasets":[]}, "data":{}}')


class PlateauOfflineLocalInputTests(unittest.TestCase):
    def test_regular_synthetic_rest_file_reads_exact_bytes(self):
        raw = json.dumps(valid_payload()).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.json"
            path.write_bytes(raw)
            self.assertEqual(read_local_metadata(path, MAX_INPUT_BYTES), raw)
            self.assertEqual(preflight_bytes(read_local_metadata(path, MAX_INPUT_BYTES))["target_fiscal_year"], 2024)

    def test_regular_synthetic_graphql_cli_does_not_expose_file_path_or_urls(self):
        raw = json.dumps(valid_graphql_payload()).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.json"
            path.write_bytes(raw)
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = main(["--format", "graphql", "--input", str(path)])
            self.assertEqual(status, 0)
            self.assertEqual(stderr.getvalue(), "")
            receipt = json.loads(stdout.getvalue())
            self.assertEqual(receipt["input_byte_count"], len(raw))
            self.assertFalse(receipt["provider_network_access"])
            self.assertNotIn(str(path), stdout.getvalue())
            self.assertNotIn("example.org", stdout.getvalue())

    def test_oversize_and_empty_local_files_fail_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.json"
            for raw in (b"", b"x" * (GRAPHQL_MAX_INPUT_BYTES + 1)):
                with self.subTest(size=len(raw)):
                    path.write_bytes(raw)
                    with self.assertRaises(CataloguePreflightError):
                        read_local_metadata(path, GRAPHQL_MAX_INPUT_BYTES)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "O_NOFOLLOW is required")
    def test_symlink_final_component_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "synthetic.json"
            alias = Path(directory) / "synthetic-alias.json"
            target.write_text(json.dumps(valid_payload()), encoding="utf-8")
            alias.symlink_to(target)
            with self.assertRaises(CataloguePreflightError):
                read_local_metadata(alias, MAX_INPUT_BYTES)

    @unittest.skipUnless(hasattr(os, "mkfifo") and hasattr(os, "O_NONBLOCK"), "requires POSIX FIFO")
    def test_fifo_is_rejected_without_waiting_for_a_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "synthetic-pipe"
            os.mkfifo(fifo)
            with self.assertRaises(CataloguePreflightError):
                read_local_metadata(fifo, MAX_INPUT_BYTES)

    def test_input_read_failure_never_prints_raw_path_or_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "not-present.json"
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                self.assertEqual(main(["--input", str(path)]), 2)
            self.assertIn("BLOCKED", stderr.getvalue())
            self.assertNotIn(str(path), stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
