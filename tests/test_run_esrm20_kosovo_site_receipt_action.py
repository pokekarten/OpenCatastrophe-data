# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_site_receipt_action as subject


EXECUTION_SHA = "7" * 40


def _request(**updates):
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": EXECUTION_SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "test-owner",
    }
    payload.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _receipt(**updates):
    payload = {
        "schema_version": "oc-efehr-trusted-acquisition-v1",
        "operation_id": subject.WORKER_OPERATION_ID,
        "source_issue": subject.SOURCE_SCIENCE_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "repository_path": subject.REPOSITORY_PATH,
        "requested_url": "https://gitlab.seismo.ethz.ch/raw/site.xml",
        "final_url": "https://gitlab.seismo.ethz.ch/raw/site.xml",
        "retrieved_at": "2026-08-16T14:00:00Z",
        "byte_count": 1234,
        "sha256": "8" * 64,
        "content_type": "application/xml",
        "etag": None,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }
    payload.update(updates)
    return payload


def _terminal_comment(*, status="pass"):
    result = subject._base_result(execution_sha=EXECUTION_SHA)
    if status == "pass":
        result.update(
            {
                "status": "pass",
                "failure_class": None,
                "receipt": {
                    "retrieved_at": "2026-08-16T14:00:00Z",
                    "byte_count": 1234,
                    "sha256": "8" * 64,
                    "content_type": "application/xml",
                    "etag": None,
                },
            }
        )
    else:
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "receipt": None,
            }
        )
    return {
        "id": 2001,
        "user": {"login": subject.TRUSTED_RESULT_LOGIN},
        "body": subject.RESULT_MARKER
        + "\n"
        + json.dumps(result, sort_keys=True, separators=(",", ":")),
    }


class RequestTests(unittest.TestCase):
    def test_request_is_exactly_bound_to_issue_dataset_and_execution_sha(self):
        parsed = subject.validate_request(
            _request(),
            expected_issue=subject.CONTROL_ISSUE,
            execution_sha=EXECUTION_SHA,
        )
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)

    def test_request_rejects_scope_and_selector_widening(self):
        cases = [
            _request(issue=291),
            _request(dataset_id="other.dataset"),
            _request(target_sha="6" * 40),
            _request(action="generic_site_receipt"),
            _request(path="Other.xml"),
            "prefix\n" + _request(),
        ]
        for body in cases:
            with self.subTest(body=body):
                with self.assertRaises(subject.SiteReceiptActionError):
                    subject.validate_request(
                        body,
                        expected_issue=subject.CONTROL_ISSUE,
                        execution_sha=EXECUTION_SHA,
                    )

    def test_request_rejects_duplicate_json_keys(self):
        body = (
            subject.REQUEST_MARKER
            + '\n{"schema_version":"'
            + subject.REQUEST_SCHEMA_VERSION
            + '","action":"'
            + subject.ACTION
            + '","issue":342,"target_sha":"'
            + EXECUTION_SHA
            + '","dataset_id":"'
            + subject.DATASET_ID
            + '","requester":"a","requester":"b"}'
        )
        with self.assertRaises(subject.SiteReceiptActionError):
            subject.validate_request(
                body,
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=EXECUTION_SHA,
            )


class LedgerTests(unittest.TestCase):
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
                subject.has_terminal_site_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
            )
        fetch.assert_called_once_with(
            "pokekarten/OpenCatastrophe-data",
            "token",
            issue=subject.CONTROL_ISSUE,
            max_pages=20,
        )

    def test_blocked_acquisition_result_is_also_terminal(self):
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=[_terminal_comment(status="blocked")],
        ):
            self.assertTrue(
                subject.has_terminal_site_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
            )

    def test_incomplete_or_over_bound_ledger_fails_closed(self):
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            side_effect=subject.LedgerError("scan bound exceeded"),
        ):
            with self.assertRaisesRegex(
                subject.SiteReceiptActionError, "ledger is incomplete"
            ):
                subject.has_terminal_site_result(
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
            with self.assertRaises(subject.SiteReceiptActionError):
                subject.has_terminal_site_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )


class ResultTests(unittest.TestCase):
    def test_pass_returns_only_bounded_receipt_and_false_science_authority(self):
        with mock.patch.object(
            subject, "acquire_kosovo_site_receipt", return_value=_receipt()
        ):
            result = subject.run_site_receipt(execution_sha=EXECUTION_SHA)

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["receipt"]["byte_count"], 1234)
        self.assertEqual(result["receipt"]["sha256"], "8" * 64)
        self.assertIs(result["site_xml_semantics_verified"], False)
        self.assertIs(result["gsim_site_parameter_sufficiency_verified"], False)
        self.assertIs(result["site_adjusted_reference_authorized"], False)
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)
        self.assertNotIn("requested_url", result["receipt"])
        self.assertNotIn("final_url", result["receipt"])

    def test_worker_identity_or_authority_drift_blocks_without_leaking_receipt(self):
        bad_receipts = [
            _receipt(project_id=270),
            _receipt(repository_path="Vs30/Other.xml"),
            _receipt(commit_sha="0" * 40),
            _receipt(external_bytes_persisted=True),
            _receipt(publication_authorized=True),
            _receipt(sha256="not-a-digest"),
            _receipt(byte_count=True),
        ]
        for receipt in bad_receipts:
            with self.subTest(receipt=receipt):
                with mock.patch.object(
                    subject, "acquire_kosovo_site_receipt", return_value=receipt
                ):
                    result = subject.run_site_receipt(execution_sha=EXECUTION_SHA)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["failure_class"], "acquisition_failure")
                self.assertIsNone(result["receipt"])

    def test_provider_failure_is_sanitized(self):
        with mock.patch.object(
            subject,
            "acquire_kosovo_site_receipt",
            side_effect=subject.EfehrAcquisitionError("secret provider payload"),
        ):
            result = subject.run_site_receipt(execution_sha=EXECUTION_SHA)
        encoded = json.dumps(result, sort_keys=True)
        self.assertEqual(result["status"], "blocked")
        self.assertNotIn("secret provider payload", encoded)


class CliEntryPointTests(unittest.TestCase):
    def test_validate_only_cli_supports_direct_script_execution(self):
        env = os.environ.copy()
        env["OC_SITE_REQUEST_BODY"] = _request()
        repo_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts" / "run_esrm20_kosovo_site_receipt_action.py"),
                "--comment-body-env",
                "OC_SITE_REQUEST_BODY",
                "--expected-issue",
                str(subject.CONTROL_ISSUE),
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
