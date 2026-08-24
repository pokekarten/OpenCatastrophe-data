# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest
from unittest import mock

from scripts import acquire_efehr_greece_exposure_profile as subject


class _Response:
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class GreeceExposureAcquisitionTests(unittest.TestCase):
    def _bounded_profile(self):
        p = subject.profile
        content = {
            "schema_version": p.SCHEMA_VERSION,
            "parser": "profile_esrm20_runtime_exposure_xml.profile_xml_bytes",
            "profile": {
                "nrml_namespace": "http://openquake.org/xmlns/nrml/0.5",
                "exposure_model": {
                    "id": "greece",
                    "category": "buildings",
                    "taxonomy_source": "GEM",
                    "description": "Greece exposure",
                },
                "asset_references": ["Exposure_Model_Greece.csv"],
                "cost_types": [
                    {"name": "structural", "type": "aggregated", "unit": "EUR"}
                ],
                "area": {"type": "aggregated", "unit": "SQM"},
                "occupancy_periods": ["day", "night"],
                "tag_names": ["occupancy", "admin"],
                "exposure_fields": [
                    {"oq": "taxonomy", "input": "TAXONOMY"},
                    {"oq": "value", "type": "structural", "input": "STRUCTURAL"},
                ],
                "structural_cost_type_declared": True,
                "structural_value_inputs": ["STRUCTURAL"],
            },
            "source_declarations_profiled": True,
        }
        for field in (
            "raw_xml_returned",
            "referenced_dependency_bytes_receipted",
            "referenced_dependency_content_profiled",
            "crs_semantics_verified",
            "taxonomy_semantics_verified",
            "replacement_cost_semantics_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            content[field] = False
        return {
            "schema_version": p.SCHEMA_VERSION,
            "source_issue": p.SOURCE_ISSUE,
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
            "content_profile": content,
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
                "profile_verified_greece_exposure_xml",
                return_value=self._bounded_profile(),
            ) as profiler,
        ):
            result = subject._acquire_and_profile_greece_exposure(
                opener=opener,
                monotonic=lambda: 1.0,
            )

        self.assertEqual(len(requests), 1)
        request = requests[0][0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(
            request.full_url,
            "https://gitlab.seismo.ethz.ch/api/v4/projects/269/repository/files/"
            "Exposure%2FOQ_Exposure_Input_Greece.xml/raw?"
            "ref=05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        profiler.assert_called_once_with(raw)
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_profile_authority_widening_is_rejected(self):
        result = self._bounded_profile()
        result["content_profile"]["model_use_authorized"] = True
        with self.assertRaisesRegex(
            subject.GreeceExposureContractError,
            "model_use_authorized",
        ):
            subject._validate_profile_result(result)

    def test_unknown_nested_fields_are_rejected_fail_closed(self):
        result = copy.deepcopy(self._bounded_profile())
        result["content_profile"]["profile"]["exposure_model"]["raw_values"] = []
        with self.assertRaisesRegex(
            subject.GreeceExposureContractError,
            "model fields drifted",
        ):
            subject._validate_profile_result(result)

    def test_boolean_type_confusion_is_rejected(self):
        result = self._bounded_profile()
        result["content_profile"]["profile"]["structural_cost_type_declared"] = 1
        with self.assertRaisesRegex(
            subject.GreeceExposureContractError,
            "structural_cost_type_declared",
        ):
            subject._validate_profile_result(result)

    def test_provider_root_is_frozen(self):
        with mock.patch.object(subject, "PROVIDER_ROOT", "https://example.invalid"):
            with self.assertRaisesRegex(
                subject.GreeceExposureContractError,
                "provider root",
            ):
                subject._require_profile_contract()

    def test_merged_profiler_receipt_identity_is_frozen(self):
        with mock.patch.object(subject.profile, "EXPECTED_BYTE_COUNT", 698):
            with self.assertRaisesRegex(
                subject.GreeceExposureContractError,
                "byte count",
            ):
                subject._require_profile_contract()

    def test_production_transport_rebinding_fails_closed(self):
        with mock.patch.object(subject, "_open_fixed", object()):
            with self.assertRaisesRegex(
                subject.GreeceExposureContractError,
                "transport drifted",
            ):
                subject.acquire_and_profile_greece_exposure()

    def test_control_characters_in_content_length_fail_closed(self):
        response = _Response()
        response.headers = {"Content-Length": "697\nX"}
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
            with self.assertRaises(subject.GreeceExposureAcquisitionError):
                subject._acquire_and_profile_greece_exposure(
                    opener=lambda request, timeout: _Response(),
                    monotonic=lambda: 1.0,
                )
        self.assertEqual(events, ["headers"])

    def test_profile_failure_is_distinct_from_transport_failure(self):
        raw = b"verified-provider-bytes"
        with (
            mock.patch.object(subject, "_validate_exact_response"),
            mock.patch.object(subject, "_declared_length"),
            mock.patch.object(subject, "_read_bounded", return_value=raw),
            mock.patch.object(
                subject.profile,
                "profile_verified_greece_exposure_xml",
                side_effect=subject.profile.GreeceExposureProfileError("bad xml"),
            ),
        ):
            with self.assertRaises(subject.GreeceExposureContentError):
                subject._acquire_and_profile_greece_exposure(
                    opener=lambda request, timeout: _Response(),
                    monotonic=lambda: 1.0,
                )


if __name__ == "__main__":
    unittest.main()
