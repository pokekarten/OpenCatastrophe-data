# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest
from unittest import mock

from scripts import acquire_efehr_greece_site_profile as subject


class _Response:
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class GreeceSiteProfileAcquisitionTests(unittest.TestCase):
    def _bounded_profile(self):
        p = subject.profile
        return {
            "schema_version": p.SCHEMA_VERSION,
            "source_issue": p.SOURCE_ISSUE,
            "source_science_issue": p.SOURCE_SCIENCE_ISSUE,
            "receipt_issue": p.RECEIPT_ISSUE,
            "dataset_id": p.DATASET_ID,
            "project_id": p.PROJECT_ID,
            "project_path": p.PROJECT_PATH,
            "release": p.RELEASE,
            "commit_sha": p.COMMIT_SHA,
            "consumer_event": p.CONSUMER_EVENT,
            "repository_path": p.REPOSITORY_PATH,
            "receipt_comment_id": p.RECEIPT_COMMENT_ID,
            "receipt_execution_sha": p.RECEIPT_EXECUTION_SHA,
            "receipt_retrieved_at": p.RECEIPT_RETRIEVED_AT,
            "byte_count": p.EXPECTED_BYTE_COUNT,
            "sha256": p.EXPECTED_SHA256,
            "profile": {
                "schema_version": p.SCHEMA_VERSION,
                "parser": {
                    "xml_parser": "strict-utf8-text->xml.etree.ElementTree.fromstring",
                    "verified_encoding": "utf-8",
                    "bom_present": False,
                    "dtd_or_entity_allowed": False,
                },
                "root": {"namespace": "urn:test", "local_name": "root"},
                "element_count": 2,
                "leaf_element_count": 1,
                "max_depth": 2,
                "tag_counts": [
                    {
                        "name": {"namespace": "urn:test", "local_name": "root"},
                        "count": 2,
                    }
                ],
                "namespace_counts": [{"namespace": "urn:test", "element_count": 2}],
                "attribute_profiles": [
                    {
                        "name": {"namespace": None, "local_name": "vs30"},
                        "occurrence_count": 2,
                        "empty_count": 0,
                        "leading_or_trailing_whitespace_count": 0,
                        "distinct_count": 2,
                        "exact_value_set_sha256": "0" * 64,
                        "finite_decimal_lexical_count": 2,
                        "true_lexical_count": 0,
                        "false_lexical_count": 0,
                    }
                ],
                "non_whitespace_text_element_count": 0,
                "raw_xml_returned": False,
                "raw_attribute_values_returned": False,
                "crs_coordinate_semantics_verified": False,
                "site_parameter_units_verified": False,
                "missingness_semantics_verified": False,
                "gsim_site_parameter_sufficiency_verified": False,
                "site_adjusted_reference_authorized": False,
                "external_bytes_persisted": False,
                "publication_authorized": False,
                "model_use_authorized": False,
            },
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }

    def test_fixed_target_bytes_are_forwarded_only_to_reviewed_profiler(self):
        raw = b"verified-provider-bytes"
        requests = []

        def opener(request, timeout):
            requests.append((request, timeout))
            return _Response()

        with (
            mock.patch.object(subject, "_validate_exact_response"),
            mock.patch.object(subject, "_declared_length"),
            mock.patch.object(subject, "_read_bounded", return_value=raw),
            mock.patch.object(
                subject.profile,
                "profile_verified_greece_site_model",
                return_value=self._bounded_profile(),
            ) as profiler,
        ):
            result = subject._acquire_and_profile_greece_site(
                opener=opener,
                monotonic=lambda: 1.0,
            )

        self.assertEqual(len(requests), 1)
        request = requests[0][0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(
            request.full_url,
            "https://gitlab.seismo.ethz.ch/api/v4/projects/269/repository/files/"
            "Vs30%2FSite_model_Greece.xml/raw?"
            "ref=05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        profiler.assert_called_once_with(raw)
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_profile_authority_widening_is_rejected(self):
        result = self._bounded_profile()
        result["profile"]["model_use_authorized"] = True
        with self.assertRaisesRegex(
            subject.GreeceSiteProfileContractError,
            "model_use_authorized",
        ):
            subject._validate_profile_result(result)

    def test_unknown_nested_fields_are_rejected_fail_closed(self):
        mutations = (
            ("root", lambda p: p["profile"]["root"].__setitem__("raw_values", [])),
            (
                "tag_counts",
                lambda p: p["profile"]["tag_counts"][0].__setitem__("raw_values", []),
            ),
            (
                "namespace_counts",
                lambda p: p["profile"]["namespace_counts"][0].__setitem__(
                    "raw_values", []
                ),
            ),
            (
                "attribute_profiles",
                lambda p: p["profile"]["attribute_profiles"][0].__setitem__(
                    "raw_values", []
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                result = copy.deepcopy(self._bounded_profile())
                mutate(result)
                with self.assertRaises(subject.GreeceSiteProfileContractError):
                    subject._validate_profile_result(result)

    def test_nested_counts_reject_bool_and_out_of_bounds_values(self):
        result = self._bounded_profile()
        result["profile"]["tag_counts"][0]["count"] = True
        with self.assertRaisesRegex(
            subject.GreeceSiteProfileContractError,
            "tag_counts",
        ):
            subject._validate_profile_result(result)

        result = self._bounded_profile()
        result["profile"]["attribute_profiles"][0]["empty_count"] = 3
        with self.assertRaisesRegex(
            subject.GreeceSiteProfileContractError,
            "empty_count",
        ):
            subject._validate_profile_result(result)

    def test_attribute_fingerprint_requires_lowercase_sha256(self):
        result = self._bounded_profile()
        result["profile"]["attribute_profiles"][0]["exact_value_set_sha256"] = "A" * 64
        with self.assertRaisesRegex(
            subject.GreeceSiteProfileContractError,
            "lowercase SHA-256",
        ):
            subject._validate_profile_result(result)

    def test_provider_root_is_frozen(self):
        with mock.patch.object(subject, "PROVIDER_ROOT", "https://example.invalid"):
            with self.assertRaisesRegex(
                subject.GreeceSiteProfileContractError,
                "provider root",
            ):
                subject._require_profile_contract()

    def test_merged_profiler_receipt_identity_is_frozen(self):
        with mock.patch.object(subject.profile, "EXPECTED_BYTE_COUNT", 235_016):
            with self.assertRaisesRegex(
                subject.GreeceSiteProfileContractError,
                "byte count",
            ):
                subject._require_profile_contract()

    def test_production_transport_rebinding_fails_closed(self):
        with mock.patch.object(subject, "_open_fixed", object()):
            with self.assertRaisesRegex(
                subject.GreeceSiteProfileContractError,
                "transport drifted",
            ):
                subject.acquire_and_profile_greece_site()

    def test_control_characters_in_content_length_fail_closed(self):
        response = _Response()
        response.headers = {"Content-Length": "235015\nX"}
        with self.assertRaisesRegex(
            subject.EfehrAcquisitionError,
            "control characters",
        ):
            subject._declared_length(response, subject._CANONICAL_BYTE_COUNT)

    def test_response_header_validation_precedes_payload_read(self):
        events = []

        def validate_response(response, url):
            events.append("headers")
            raise subject.EfehrAcquisitionError("bad response")

        with (
            mock.patch.object(
                subject,
                "_validate_exact_response",
                side_effect=validate_response,
            ),
            mock.patch.object(
                subject,
                "_read_bounded",
                side_effect=lambda *args, **kwargs: events.append("read"),
            ),
        ):
            with self.assertRaises(subject.GreeceSiteProfileAcquisitionError):
                subject._acquire_and_profile_greece_site(
                    opener=lambda request, timeout: _Response(),
                    monotonic=lambda: 1.0,
                )
        self.assertEqual(events, ["headers"])


if __name__ == "__main__":
    unittest.main()
