# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_site_profile_action as subject


SHA = "a" * 40
OTHER_SHA = "c" * 40


def _request(**overrides):
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    payload.update(overrides)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _payload():
    return {
        "schema_version": "oc-esrm20-kosovo-site-content-profile-v0",
        "source_issue": 291,
        "source_science_issue": 284,
        "receipt_issue": 342,
        "dataset_id": subject.DATASET_ID,
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "repository_path": subject.REPOSITORY_PATH,
        "worker_operation_id": subject.WORKER_OPERATION_ID,
        "receipt_comment_id": subject.RECEIPT_COMMENT_ID,
        "receipt_execution_sha": "25719e731b0224ba4c9a656b1556db6a9fa76de2",
        "receipt_retrieved_at": "2026-08-16T14:56:37Z",
        "byte_count": subject.EXPECTED_BYTE_COUNT,
        "sha256": subject.EXPECTED_SHA256,
        "profile": {
            "schema_version": "oc-esrm20-kosovo-site-content-profile-v0",
            "parser": {
                "xml_parser": "strict-utf8-text->xml.etree.ElementTree.fromstring",
                "verified_encoding": "utf-8",
                "bom_present": False,
                "dtd_or_entity_allowed": False,
            },
            "root": {"namespace": "urn:test", "local_name": "nrml"},
            "element_count": 2,
            "leaf_element_count": 1,
            "max_depth": 2,
            "tag_counts": [{"name": {"namespace": "urn:test", "local_name": "nrml"}, "count": 2}],
            "namespace_counts": [],
            "attribute_profiles": [
                {
                    "name": {"namespace": None, "local_name": "vs30"},
                    "occurrence_count": 1,
                    "empty_count": 0,
                    "leading_or_trailing_whitespace_count": 0,
                    "distinct_count": 1,
                    "exact_value_set_sha256": "c" * 64,
                    "finite_decimal_lexical_count": 1,
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


def _terminal_body(execution_sha: str) -> str:
    result = subject._run_site_profile(execution_sha=execution_sha, acquirer=_payload)
    return subject.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))


class KosovoSiteProfileActionTests(unittest.TestCase):
    def test_request_is_exactly_bound_to_issue_dataset_and_execution_sha(self):
        result = subject.validate_request(_request(), expected_issue=459, execution_sha=SHA)
        self.assertEqual(result["action"], subject.ACTION)
        for bad in (
            _request(issue=291),
            _request(dataset_id="other"),
            _request(target_sha="b" * 40),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(subject.SiteProfileActionError):
                    subject.validate_request(bad, expected_issue=459, execution_sha=SHA)

    def test_pass_preserves_all_authority_ceilings(self):
        result = subject._run_site_profile(execution_sha=SHA, acquirer=_payload)
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)
        self.assertIs(result["profile"]["profile"]["raw_xml_returned"], False)

    def test_acquisition_failure_is_bounded(self):
        def fail():
            raise subject.SiteProfileAcquisitionError("provider unavailable")
        result = subject._run_site_profile(execution_sha=SHA, acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["profile"])

    def test_profile_failure_is_distinct_and_bounded(self):
        def fail():
            raise subject.SiteProfileContentError("exact bytes failed parser")
        result = subject._run_site_profile(execution_sha=SHA, acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertIsNone(result["profile"])

    def test_result_rejects_widened_profile_authority(self):
        payload = _payload()
        payload["profile"]["publication_authorized"] = True
        with self.assertRaisesRegex(subject.SiteProfileActionError, "reviewed worker contract"):
            subject._validate_profile_payload(payload)

    def test_dedup_trusts_only_actions_bot_and_exact_execution(self):
        body = _terminal_body(SHA)
        comments = [
            {"id": 1, "user": {"login": "pokekarten"}, "body": body},
            {"id": 2, "user": {"login": "github-actions[bot]"}, "body": body},
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )
            )

    def test_dedup_skips_valid_prior_sha_and_still_finds_current_sha(self):
        prior = {
            "id": 1,
            "user": {"login": subject.TRUSTED_RESULT_LOGIN},
            "body": _terminal_body(OTHER_SHA),
        }
        current = {
            "id": 2,
            "user": {"login": subject.TRUSTED_RESULT_LOGIN},
            "body": _terminal_body(SHA),
        }
        with mock.patch.object(subject, "fetch_repository_comments", return_value=[prior]):
            self.assertFalse(
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )
            )
        with mock.patch.object(
            subject, "fetch_repository_comments", return_value=[prior, current]
        ):
            self.assertTrue(
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )
            )

    def test_prior_sha_result_with_mismatched_target_sha_fails_closed(self):
        result = subject._run_site_profile(execution_sha=OTHER_SHA, acquirer=_payload)
        result["target_sha"] = SHA
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        comments = [
            {
                "id": 2,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": body,
            }
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            with self.assertRaises(subject.SiteProfileActionError):
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )

    def test_trusted_malformed_terminal_result_fails_closed(self):
        comments = [
            {
                "id": 2,
                "user": {"login": "github-actions[bot]"},
                "body": subject.RESULT_MARKER + "\n{}",
            }
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            with self.assertRaises(subject.SiteProfileActionError):
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )


if __name__ == "__main__":
    unittest.main()
