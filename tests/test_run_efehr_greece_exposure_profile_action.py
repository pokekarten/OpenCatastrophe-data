# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts import acquire_efehr_greece_exposure_profile as worker
from scripts import run_efehr_greece_exposure_profile_action as action


SHA = "a" * 40
WORKFLOW = Path(".github/workflows/esrm20-greece-exposure-profile.yml")


def _profile():
    return {
        "nrml_namespace": "http://openquake.org/xmlns/nrml/0.5",
        "exposure_model": {
            "id": "Greece",
            "category": "buildings",
            "taxonomy_source": "ESRM20",
            "description": "synthetic declaration fixture",
        },
        "asset_references": ["Exposure_Model_Greece.csv"],
        "cost_types": [
            {"name": "structural", "type": "aggregated", "unit": "EUR"}
        ],
        "area": None,
        "occupancy_periods": [],
        "tag_names": ["taxonomy"],
        "exposure_fields": [
            {"oq": "id", "input": "id"},
            {"oq": "taxonomy", "input": "taxonomy"},
        ],
        "structural_cost_type_declared": True,
        "structural_value_inputs": ["structural"],
    }


def _evidence():
    return {
        "schema_version": worker.profile.SCHEMA_VERSION,
        "source_issue": worker._CANONICAL_SOURCE_ISSUE,
        "receipt_issue": worker._CANONICAL_RECEIPT_ISSUE,
        "dataset_id": worker._CANONICAL_DATASET_ID,
        "project_id": worker._CANONICAL_PROJECT_ID,
        "project_path": worker._CANONICAL_PROJECT_PATH,
        "release": worker._CANONICAL_RELEASE,
        "commit_sha": worker._CANONICAL_COMMIT_SHA,
        "consumer_event": worker._CANONICAL_CONSUMER_EVENT,
        "repository_path": worker._CANONICAL_REPOSITORY_PATH,
        "receipt_comment_id": worker._CANONICAL_RECEIPT_COMMENT_ID,
        "receipt_execution_sha": worker._CANONICAL_RECEIPT_EXECUTION_SHA,
        "receipt_retrieved_at": worker._CANONICAL_RECEIPT_RETRIEVED_AT,
        "byte_count": worker._CANONICAL_BYTE_COUNT,
        "sha256": worker._CANONICAL_SHA256,
        "content_profile": {
            "schema_version": worker.profile.SCHEMA_VERSION,
            "parser": "profile_esrm20_runtime_exposure_xml.profile_xml_bytes",
            "profile": _profile(),
            "source_declarations_profiled": True,
            "raw_xml_returned": False,
            "referenced_dependency_bytes_receipted": False,
            "referenced_dependency_content_profiled": False,
            "crs_semantics_verified": False,
            "taxonomy_semantics_verified": False,
            "replacement_cost_semantics_verified": False,
            "benchmark_agreement_inspected": False,
            "independent_validation_established": False,
            "holdout_status_established": False,
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        },
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _request(target_sha=SHA):
    payload = {
        "schema_version": action.REQUEST_SCHEMA_VERSION,
        "action": action.ACTION,
        "issue": action.CONTROL_ISSUE,
        "target_sha": target_sha,
        "dataset_id": worker._CANONICAL_DATASET_ID,
        "receipt_sha256": worker._CANONICAL_SHA256,
        "requester": "unit-test",
    }
    return action.REQUEST_MARKER + "\n" + json.dumps(
        payload, separators=(",", ":")
    )


class GreeceExposureProfileActionTests(unittest.TestCase):
    def test_request_is_exact_sha_and_receipt_bound(self):
        request = action.validate_request(
            _request(), expected_issue=285, execution_sha=SHA
        )
        self.assertEqual(request["target_sha"], SHA)
        self.assertEqual(request["receipt_sha256"], worker._CANONICAL_SHA256)

        with self.assertRaises(action.GreeceExposureProfileActionError):
            action.validate_request(
                _request("b" * 40), expected_issue=285, execution_sha=SHA
            )

    def test_duplicate_request_key_fails_closed(self):
        body = (
            action.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"%s","schema_version":"%s"}'
            % (action.REQUEST_SCHEMA_VERSION, action.REQUEST_SCHEMA_VERSION)
        )
        with self.assertRaises(action.GreeceExposureProfileActionError):
            action.validate_request(body, expected_issue=285, execution_sha=SHA)

    def test_pass_preserves_dependency_and_science_ceilings(self):
        result = action._run(execution_sha=SHA, acquirer=_evidence)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["source_declarations_profiled"])
        self.assertEqual(
            result["evidence"]["content_profile"]["profile"]["asset_references"],
            ["Exposure_Model_Greece.csv"],
        )
        for field in (
            "referenced_dependency_bytes_receipted",
            "referenced_dependency_content_profiled",
            "crs_semantics_verified",
            "taxonomy_semantics_verified",
            "replacement_cost_semantics_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertFalse(result[field])

    def test_acquisition_failure_is_bounded(self):
        def fail():
            raise worker.GreeceExposureAcquisitionError("blocked")

        result = action._run(execution_sha=SHA, acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertFalse(result["source_declarations_profiled"])
        self.assertIsNone(result["evidence"])

    def test_profile_failure_records_byte_read_without_declarations(self):
        def fail():
            raise worker.GreeceExposureContentError("bad exact XML")

        result = action._run(execution_sha=SHA, acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["source_declarations_profiled"])
        self.assertIsNone(result["evidence"])

    def test_evidence_authority_uplift_fails_closed(self):
        evidence = _evidence()
        evidence["content_profile"]["referenced_dependency_bytes_receipted"] = True
        with self.assertRaises(action.GreeceExposureProfileActionError):
            action._validate_evidence(evidence)

    def test_terminal_parser_rejects_unbounded_envelope(self):
        body = action.RESULT_MARKER + "\n" + ("x" * action.MAX_TERMINAL_UTF8_BYTES)
        with self.assertRaises(action.GreeceExposureProfileActionError):
            action._parse_terminal(body, execution_sha=SHA)

    def test_publisher_refences_live_default_branch_before_post(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        publisher = text.split("  publish-profile:", 1)[1]
        self.assertIn("contents: read", publisher)
        self.assertIn("issues: write", publisher)
        self.assertIn(
            "DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}",
            publisher,
        )
        self.assertIn(
            "gh api \"repos/$GITHUB_REPOSITORY/commits/$DEFAULT_BRANCH\" --jq '.sha'",
            publisher,
        )
        self.assertIn('test "$LATEST_SHA" = "$EXECUTION_SHA"', publisher)
        self.assertLess(
            publisher.index('test "$LATEST_SHA" = "$EXECUTION_SHA"'),
            publisher.index('"repos/$GITHUB_REPOSITORY/issues/285/comments"'),
        )
        self.assertNotIn("actions/checkout", publisher)


if __name__ == "__main__":
    unittest.main()
