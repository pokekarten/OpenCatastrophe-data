# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_mapping_join_action as subject

EXECUTION_SHA = "7" * 40


def _request(**updates):
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": EXECUTION_SHA,
        "requester": "test-owner",
    }
    payload.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _join_result():
    records = [
        {
            "taxonomy": f"TAX-{index:03d}",
            "status": "resolved",
            "reason_code": "exact_mapping_rows_valid",
            "targets": [{"risk_id": f"RISK-{index:03d}", "weight": "1"}],
        }
        for index in range(subject.EXPECTED_TAXONOMY_COUNT)
    ]
    return {
        "schema_version": subject.join_kernel.SCHEMA_VERSION,
        "source_issue": 283,
        "semantic_decision_issue": 410,
        "taxonomy_source": {
            "dataset_id": subject._EXPOSURE["dataset_id"],
            "project_id": subject._EXPOSURE["project_id"],
            "project_path": subject._EXPOSURE["project_path"],
            "commit_sha": subject._EXPOSURE["commit_sha"],
            "repository_path": subject._EXPOSURE["repository_path"],
            "byte_count": subject._EXPOSURE["byte_count"],
            "sha256": subject._EXPOSURE["sha256"],
            "taxonomy_count": subject.EXPECTED_TAXONOMY_COUNT,
            "taxonomy_value_set_sha256": subject.EXPECTED_TAXONOMY_VALUE_SET_SHA256,
        },
        "mapping_source": {
            "dataset_id": subject._MAPPING["dataset_id"],
            "project_id": subject._MAPPING["project_id"],
            "project_path": subject._MAPPING["project_path"],
            "commit_sha": subject._MAPPING["commit_sha"],
            "repository_path": subject._MAPPING["repository_path"],
            "byte_count": subject._MAPPING["byte_count"],
            "sha256": subject._MAPPING["sha256"],
            "headers": ["taxonomy", "conversion", "weight"],
        },
        "rights": {
            "provider": subject.join_kernel.RIGHTS_PROVIDER,
            "license_id": subject.join_kernel.RIGHTS_LICENSE_ID,
            "attribution_required": True,
            "source_reviews": list(subject.join_kernel.RIGHTS_SOURCE_REVIEWS),
            "transformation_notice": subject.join_kernel.RIGHTS_TRANSFORMATION_NOTICE,
        },
        "classification_counts": {
            "resolved": subject.EXPECTED_TAXONOMY_COUNT,
            "unsupported": 0,
            "ambiguous": 0,
        },
        "records": records,
        "taxonomy_matching": "exact_literal_equality_only",
        "normalization_applied": False,
        "wildcard_or_fallback_matching_applied": False,
        "mapping_weight_rule": "positive_finite_float_sum_within_openquake_1e-7",
        "bounded_derived_disclosure_authorized": True,
        "vulnerability_file_selection_authorized": False,
        "raw_mapping_rows_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _execution_result():
    return {
        "schema_version": subject.SCHEMA_VERSION,
        "source_issue": subject.SOURCE_ISSUE,
        "status": "pass",
        "target_sha": EXECUTION_SHA,
        "execution_sha": EXECUTION_SHA,
        "join": _join_result(),
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class RequestTests(unittest.TestCase):
    def test_request_is_bound_to_issue_and_trusted_sha(self):
        request = subject.validate_request(
            _request(),
            expected_issue=subject.SOURCE_ISSUE,
            execution_sha=EXECUTION_SHA,
        )
        self.assertEqual(request["target_sha"], EXECUTION_SHA)

    def test_request_rejects_scope_and_identity_drift(self):
        cases = [
            (_request(extra="forbidden"), subject.SOURCE_ISSUE, EXECUTION_SHA),
            (_request(issue=282), subject.SOURCE_ISSUE, EXECUTION_SHA),
            (_request(target_sha="6" * 40), subject.SOURCE_ISSUE, EXECUTION_SHA),
            (_request(), 282, EXECUTION_SHA),
            ("prefix\n" + _request(), subject.SOURCE_ISSUE, EXECUTION_SHA),
        ]
        for body, issue, sha in cases:
            with self.subTest(issue=issue, sha=sha):
                with self.assertRaises(subject.KosovoMappingJoinExecutionError):
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
            + '","issue":283,"target_sha":"'
            + EXECUTION_SHA
            + '","requester":"a","requester":"b"}'
        )
        with self.assertRaises(subject.KosovoMappingJoinExecutionError):
            subject.validate_request(
                body,
                expected_issue=subject.SOURCE_ISSUE,
                execution_sha=EXECUTION_SHA,
            )


class LedgerTests(unittest.TestCase):
    def test_only_trusted_actions_result_is_terminal(self):
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            _execution_result(), separators=(",", ":")
        )
        comments = [
            {"user": {"login": "pokekarten"}, "body": body},
            {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": body},
        ]
        with mock.patch.object(subject, "_FETCH_COMMENTS", return_value=comments):
            self.assertTrue(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
            )

    def test_trusted_result_authority_widening_fails_closed(self):
        result = _execution_result()
        result["join"]["model_use_authorized"] = True
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        with self.assertRaises(subject.KosovoMappingJoinExecutionError):
            subject._parse_terminal_result(body, execution_sha=EXECUTION_SHA)

    def test_trusted_result_record_count_tamper_fails_closed(self):
        result = _execution_result()
        result["join"]["records"].pop()
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        with self.assertRaisesRegex(
            subject.KosovoMappingJoinExecutionError, "record set"
        ):
            subject._parse_terminal_result(body, execution_sha=EXECUTION_SHA)

    def test_trusted_result_source_identity_tamper_fails_closed(self):
        result = _execution_result()
        result["join"]["mapping_source"]["sha256"] = "0" * 64
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        with self.assertRaisesRegex(
            subject.KosovoMappingJoinExecutionError, "source identity drifted"
        ):
            subject._parse_terminal_result(body, execution_sha=EXECUTION_SHA)

    def test_trusted_result_taxonomy_count_float_fails_closed(self):
        result = _execution_result()
        result["join"]["taxonomy_source"]["taxonomy_count"] = float(
            subject.EXPECTED_TAXONOMY_COUNT
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        with self.assertRaisesRegex(
            subject.KosovoMappingJoinExecutionError, "taxonomy count"
        ):
            subject._parse_terminal_result(body, execution_sha=EXECUTION_SHA)


class ExecutionTests(unittest.TestCase):
    def test_duplicate_stops_before_provider_acquisition(self):
        with (
            mock.patch.object(subject, "_require_authority"),
            mock.patch.object(subject, "has_terminal_result", return_value=True),
            mock.patch.object(subject, "_acquire_exact") as acquire,
        ):
            result = subject.execute_join(
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                execution_sha=EXECUTION_SHA,
            )
        self.assertEqual(result["status"], "duplicate")
        acquire.assert_not_called()

    def test_execution_publishes_only_bounded_join(self):
        join = _join_result()
        with (
            mock.patch.object(subject, "_require_authority"),
            mock.patch.object(subject, "has_terminal_result", return_value=False),
            mock.patch.object(subject, "_acquire_exact", side_effect=[b"exposure", b"mapping"]) as acquire,
            mock.patch.object(subject, "_JOIN", return_value=join),
        ):
            result = subject.execute_join(
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                execution_sha=EXECUTION_SHA,
            )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            result["join"]["classification_counts"]["resolved"],
            subject.EXPECTED_TAXONOMY_COUNT,
        )
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertEqual(acquire.call_count, 2)

    def test_authority_rebinding_is_detected_before_network(self):
        with mock.patch.object(subject.transport, "_open_fixed", object()):
            with self.assertRaisesRegex(
                subject.KosovoMappingJoinExecutionError, "transport authority drifted"
            ):
                subject._require_authority()

    def test_result_size_limit_fails_closed(self):
        join = _join_result()
        for index, record in enumerate(join["records"]):
            record["targets"][0]["risk_id"] = (
                f"R{index:03d}-" + "X" * 795
            )
        with (
            mock.patch.object(subject, "_require_authority"),
            mock.patch.object(subject, "has_terminal_result", return_value=False),
            mock.patch.object(subject, "_acquire_exact", side_effect=[b"exposure", b"mapping"]),
            mock.patch.object(subject, "_JOIN", return_value=join),
        ):
            with self.assertRaisesRegex(
                subject.KosovoMappingJoinExecutionError, "publication limit"
            ):
                subject.execute_join(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )


class CliEntryPointTests(unittest.TestCase):
    def test_validate_only_cli_supports_direct_script_execution(self):
        env = os.environ.copy()
        env["OC_JOIN_REQUEST_BODY"] = _request()
        repo_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts" / "run_esrm20_kosovo_mapping_join_action.py"),
                "--comment-body-env",
                "OC_JOIN_REQUEST_BODY",
                "--expected-issue",
                str(subject.SOURCE_ISSUE),
                "--execution-sha",
                EXECUTION_SHA,
                "--validate-request-only",
            ],
            cwd=repo_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
