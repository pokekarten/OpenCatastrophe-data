# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest
from unittest import mock

from scripts import run_eshm20_gsim_reference_runtime as subject


EXECUTION_SHA = "7" * 40
IMAGE_DIGEST = "sha256:" + "8" * 64


def _request(**updates):
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": EXECUTION_SHA,
        "requester": "test-owner",
    }
    payload.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _gate_result():
    return {
        "gmm_identity": {
            "project_id": subject.gmm.PROJECT_ID,
            "project_path": subject.gmm.PROJECT_PATH,
            "commit_sha": subject.gmm.COMMIT_SHA,
            "repository_path": subject.gmm.REPOSITORY_PATH,
            "byte_count": subject.gmm.EXPECTED_BYTE_COUNT,
            "sha256": subject.gmm.EXPECTED_SHA256,
        },
        "openquake_reference": {
            "repository": subject.runtime.ENGINE_REPOSITORY,
            "tag": subject.runtime.ENGINE_TAG,
            "commit": subject.runtime.ENGINE_COMMIT,
            "version": subject.runtime.ENGINE_VERSION,
        },
        "reference_runtime_fingerprint": {
            "reference_recipe_match": True,
            "observation": {"container_image_digest": IMAGE_DIGEST},
        },
        "branch_count": 1,
        "branches": [
            {
                "branch_set_id": "bs1",
                "branch_id": "b1",
                "requested_gsim_token": "Example",
                "resolved_gsim_class": "Example",
                "constructor_accepted": True,
            }
        ],
        "unique_resolved_gsim_classes": ["Example"],
        "alias_requested_tokens": [],
        "engine_source_commit_verified": True,
        "reference_runtime_observation_validated": True,
        "alias_resolution_verified": True,
        "registry_resolution_verified": True,
        "constructor_compatibility_verified": True,
        "exact_source_constructor_compatibility_verified": True,
        "gsim_request_runtime_compatibility_verified": False,
        "full_hazard_compatibility_verified": False,
        "site_model_compatibility_verified": False,
        "vulnerability_compatibility_verified": False,
        "reference_run_verified": False,
        "scientific_validity_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "provider_secret": "must-not-copy",
    }


def _terminal_comment():
    result = subject._bounded_result(
        _gate_result(), execution_sha=EXECUTION_SHA, image_digest=IMAGE_DIGEST
    )
    return {
        "id": 2001,
        "user": {"login": subject.TRUSTED_RESULT_LOGIN},
        "body": subject.RESULT_MARKER
        + "\n"
        + json.dumps(result, sort_keys=True, separators=(",", ":")),
    }


class ReferenceRuntimeRequestTests(unittest.TestCase):
    def test_request_is_bound_to_issue_and_exact_trusted_sha(self):
        parsed = subject.validate_request(
            _request(),
            expected_issue=subject.SOURCE_ISSUE,
            execution_sha=EXECUTION_SHA,
        )
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)

    def test_request_fails_closed_on_scope_or_identity_drift(self):
        cases = [
            (_request(extra="forbidden"), subject.SOURCE_ISSUE, EXECUTION_SHA),
            (_request(issue=431), subject.SOURCE_ISSUE, EXECUTION_SHA),
            (_request(target_sha="6" * 40), subject.SOURCE_ISSUE, EXECUTION_SHA),
            (_request(), 431, EXECUTION_SHA),
            (_request(), subject.SOURCE_ISSUE, "not-a-sha"),
            ("prefix\n" + _request(), subject.SOURCE_ISSUE, EXECUTION_SHA),
        ]
        for body, issue, sha in cases:
            with self.subTest(body=body, issue=issue, sha=sha):
                with self.assertRaises(subject.ReferenceRuntimeExecutionError):
                    subject.validate_request(
                        body,
                        expected_issue=issue,
                        execution_sha=sha,
                    )

    def test_request_rejects_duplicate_json_keys(self):
        body = (
            subject.REQUEST_MARKER
            + '\n{"schema_version":"'
            + subject.REQUEST_SCHEMA_VERSION
            + '","issue":432,"target_sha":"'
            + EXECUTION_SHA
            + '","requester":"a","requester":"b"}'
        )
        with self.assertRaises(subject.ReferenceRuntimeExecutionError):
            subject.validate_request(
                body,
                expected_issue=subject.SOURCE_ISSUE,
                execution_sha=EXECUTION_SHA,
            )


class ReferenceRuntimeLedgerTests(unittest.TestCase):
    def test_terminal_result_beyond_first_100_comments_is_detected(self):
        comments = [
            {"id": index + 1, "user": {"login": "someone"}, "body": "noise"}
            for index in range(100)
        ]
        comments.append(_terminal_comment())
        with mock.patch.object(
            subject, "fetch_repository_comments", return_value=comments
        ) as fetch:
            self.assertTrue(
                subject.has_terminal_runtime_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
            )
        fetch.assert_called_once_with(
            "pokekarten/OpenCatastrophe-data",
            "token",
            issue=subject.SOURCE_ISSUE,
            max_pages=20,
        )

    def test_incomplete_or_over_bound_ledger_fails_closed(self):
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            side_effect=subject.LedgerError("scan bound exceeded"),
        ):
            with self.assertRaisesRegex(
                subject.ReferenceRuntimeExecutionError, "ledger is incomplete"
            ):
                subject.has_terminal_runtime_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )

    def test_malformed_trusted_terminal_result_fails_closed(self):
        malformed = _terminal_comment()
        malformed["body"] = subject.RESULT_MARKER + "\n{}"
        with mock.patch.object(
            subject, "fetch_repository_comments", return_value=[malformed]
        ):
            with self.assertRaises(subject.ReferenceRuntimeExecutionError):
                subject.has_terminal_runtime_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )

    def test_untrusted_matching_comment_does_not_deduplicate(self):
        comment = _terminal_comment()
        comment["user"] = {"login": "attacker"}
        with mock.patch.object(
            subject, "fetch_repository_comments", return_value=[comment]
        ):
            self.assertFalse(
                subject.has_terminal_runtime_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
            )


class ReferenceRuntimeResultTests(unittest.TestCase):
    def test_bounded_result_promotes_only_recipe_runtime_compatibility(self):
        result = subject._bounded_result(
            _gate_result(),
            execution_sha=EXECUTION_SHA,
            image_digest=IMAGE_DIGEST,
        )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["target_sha"], EXECUTION_SHA)
        self.assertEqual(result["execution_sha"], EXECUTION_SHA)
        self.assertIs(result["same_process_runtime_observation_collected"], True)
        self.assertIs(
            result["executing_environment_matches_reconstructed_reference_recipe_fields"],
            True,
        )
        self.assertIs(
            result["gsim_request_reference_recipe_runtime_compatibility_verified"],
            True,
        )
        self.assertIs(result["historical_environment_verified"], False)
        self.assertIs(result["numerical_hazard_agreement_verified"], False)
        self.assertIs(result["full_hazard_compatibility_verified"], False)
        self.assertIs(result["reference_run_verified"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)
        self.assertNotIn("provider_secret", result)

    def test_bounded_result_rejects_upstream_authority_widening(self):
        fields = [
            "full_hazard_compatibility_verified",
            "site_model_compatibility_verified",
            "vulnerability_compatibility_verified",
            "reference_run_verified",
            "scientific_validity_verified",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ]
        for field in fields:
            with self.subTest(field=field):
                upstream = _gate_result()
                upstream[field] = True
                with self.assertRaises(subject.ReferenceRuntimeExecutionError):
                    subject._bounded_result(
                        upstream,
                        execution_sha=EXECUTION_SHA,
                        image_digest=IMAGE_DIGEST,
                    )

    def test_acquisition_detects_authority_rebinding_before_network(self):
        with (
            mock.patch.object(subject.gmm, "EXPECTED_SHA256", "0" * 64),
            mock.patch.object(subject, "_OPEN_FIXED") as opener,
        ):
            with self.assertRaisesRegex(
                subject.ReferenceRuntimeExecutionError,
                "authority drifted",
            ):
                subject._acquire_exact_gmm()
            opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
