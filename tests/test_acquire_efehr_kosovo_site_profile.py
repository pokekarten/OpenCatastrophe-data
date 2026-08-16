# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from unittest import mock

from scripts import acquire_efehr_kosovo_site_profile as subject


class _Response:
    headers = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class KosovoSiteProfileAcquisitionTests(unittest.TestCase):
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
            "commit_sha": p.COMMIT_SHA,
            "repository_path": p.REPOSITORY_PATH,
            "worker_operation_id": p.WORKER_OPERATION_ID,
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
                "root": {"namespace": None, "local_name": "root"},
                "element_count": 1,
                "leaf_element_count": 1,
                "max_depth": 1,
                "tag_counts": [{"name": {"namespace": None, "local_name": "root"}, "count": 1}],
                "namespace_counts": [],
                "attribute_profiles": [],
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
        captured = {}

        def validate_target(**kwargs):
            captured.update(kwargs)
            return object()

        with (
            mock.patch.object(subject, "validate_target", side_effect=validate_target),
            mock.patch.object(subject, "raw_file_api_url", return_value="https://gitlab.seismo.ethz.ch/fixed"),
            mock.patch.object(subject, "_validate_exact_response"),
            mock.patch.object(subject, "_declared_length"),
            mock.patch.object(subject, "_read_bounded", return_value=raw),
            mock.patch.object(subject.profile, "profile_verified_kosovo_site_model", return_value=self._bounded_profile()) as profiler,
        ):
            result = subject._acquire_and_profile_kosovo_site(
                opener=lambda request, timeout: _Response(),
                monotonic=lambda: 1.0,
            )

        self.assertEqual(captured["source_issue"], 284)
        self.assertEqual(captured["dataset_id"], "efehr.esrm20.risk-inputs.v1.0")
        self.assertEqual(captured["project_id"], 269)
        self.assertEqual(captured["commit_sha"], "05f83bbc9df81d02ee8ddb1801d9d781355ce783")
        self.assertEqual(captured["repository_path"], "Vs30/Site_model_Kosovo.xml")
        profiler.assert_called_once_with(raw)
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_profile_authority_widening_is_rejected(self):
        result = self._bounded_profile()
        result["profile"]["model_use_authorized"] = True
        with self.assertRaisesRegex(subject.SiteProfileContractError, "model_use_authorized"):
            subject._validate_profile_result(result)

    def test_merged_profiler_receipt_identity_is_frozen(self):
        with mock.patch.object(subject.profile, "EXPECTED_BYTE_COUNT", 5892):
            with self.assertRaisesRegex(subject.SiteProfileContractError, "byte count"):
                subject._require_profile_contract()

    def test_production_transport_rebinding_fails_closed(self):
        with mock.patch.object(subject, "_open_fixed", object()):
            with self.assertRaisesRegex(subject.SiteProfileContractError, "transport drifted"):
                subject.acquire_and_profile_kosovo_site()


if __name__ == "__main__":
    unittest.main()
