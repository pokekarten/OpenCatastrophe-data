# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

from scripts import run_esrm20_ebrisk_risk_config_receipts_action as subject

EXECUTION_SHA = "1" * 40
RETRIEVED_AT = "2026-08-18T11:45:00Z"
WORKFLOW_PATH = Path(".github/workflows/esrm20-ebrisk-risk-config-receipts.yml")


def request_body(*, sha: str = EXECUTION_SHA) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    )


def receipt(*, path: str, operation: str, payload: bytes) -> dict[str, object]:
    return {
        "schema_version": "oc-efehr-trusted-acquisition-v1",
        "operation_id": operation,
        "source_issue": subject.SOURCE_SCIENCE_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "repository_path": path,
        "requested_url": "https://example.invalid/fixed",
        "final_url": "https://example.invalid/fixed",
        "retrieved_at": RETRIEVED_AT,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "content_type": "text/plain",
        "etag": None,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def three_receipts() -> tuple[dict[str, object], ...]:
    return tuple(
        receipt(path=path, operation=operation, payload=path.encode())
        for path, operation, _worker in subject._CANONICAL_RECEIPT_TARGETS
    )


def blocked_result_body(sha: str) -> str:
    result = subject._base_result(execution_sha=sha)
    result.update(
        {
            "status": "blocked",
            "failure_class": "acquisition_failure",
            "receipts": None,
        }
    )
    return subject.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


def trusted_comment(sha: str) -> dict[str, object]:
    return {
        "user": {"login": subject.TRUSTED_RESULT_LOGIN},
        "body": blocked_result_body(sha),
    }


class EbriskRiskConfigReceiptsActionTests(unittest.TestCase):
    def test_request_is_exact_main_bound_and_has_no_provider_selector(self) -> None:
        parsed = subject.validate_request(
            request_body(), expected_issue=281, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(set(parsed), subject._REQUEST_FIELDS)
        for forbidden in (
            "path",
            "url",
            "project_id",
            "group",
            "candidate",
            "transport",
            "parser",
        ):
            self.assertNotIn(forbidden, parsed)
        with self.assertRaisesRegex(
            subject.EbriskRiskConfigReceiptsActionError, "target_sha"
        ):
            subject.validate_request(
                request_body(sha="2" * 40),
                expected_issue=281,
                execution_sha=EXECUTION_SHA,
            )

    def test_request_rejects_duplicate_keys_and_wrong_issue(self) -> None:
        duplicate = (
            subject.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"%s","schema_version":"%s"}'
            % (subject.REQUEST_SCHEMA_VERSION, subject.REQUEST_SCHEMA_VERSION)
        )
        with self.assertRaisesRegex(
            subject.EbriskRiskConfigReceiptsActionError, "duplicate JSON key"
        ):
            subject.validate_request(
                duplicate, expected_issue=281, execution_sha=EXECUTION_SHA
            )
        with self.assertRaisesRegex(
            subject.EbriskRiskConfigReceiptsActionError, "wrong runtime issue"
        ):
            subject.validate_request(
                request_body(), expected_issue=287, execution_sha=EXECUTION_SHA
            )

    def test_receipt_identity_is_exact_for_all_three_candidates(self) -> None:
        for path, operation, _worker in subject._CANONICAL_RECEIPT_TARGETS:
            with self.subTest(path=path):
                candidate = receipt(path=path, operation=operation, payload=path.encode())
                subject._validate_receipt(
                    candidate, repository_path=path, operation_id=operation
                )
                mutated = dict(candidate)
                mutated["repository_path"] = path.swapcase()
                with self.assertRaises(subject.EbriskRiskConfigReceiptsActionError):
                    subject._validate_receipt(
                        mutated, repository_path=path, operation_id=operation
                    )

    def test_run_is_atomic_and_orders_exact_three_fixed_receipts(self) -> None:
        values = three_receipts()
        fake_targets = tuple(
            (path, operation, mock.Mock(return_value=value))
            for (path, operation, _worker), value in zip(
                subject._CANONICAL_RECEIPT_TARGETS, values
            )
        )
        result = subject._run_receipts(
            execution_sha=EXECUTION_SHA, targets=fake_targets
        )
        self.assertEqual(set(result), subject._RESULT_FIELDS)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(
            [row["repository_path"] for row in result["receipts"]],
            [
                subject.GROUP1_REPOSITORY_PATH,
                subject.GROUP2_REPOSITORY_PATH,
                subject.ICELAND_REPOSITORY_PATH,
            ],
        )
        self.assertFalse(result["historical_group_assignment_verified"])
        self.assertFalse(result["config_content_interpreted"])
        self.assertFalse(result["dependency_closure_verified"])
        self.assertFalse(result["runtime_compatibility_verified"])
        self.assertFalse(result["model_use_authorized"])

    def test_late_failure_cannot_publish_partial_authoritative_receipts(self) -> None:
        values = three_receipts()
        fake_targets = (
            (
                subject.GROUP1_REPOSITORY_PATH,
                subject.GROUP1_OPERATION_ID,
                mock.Mock(return_value=values[0]),
            ),
            (
                subject.GROUP2_REPOSITORY_PATH,
                subject.GROUP2_OPERATION_ID,
                mock.Mock(return_value=values[1]),
            ),
            (
                subject.ICELAND_REPOSITORY_PATH,
                subject.ICELAND_OPERATION_ID,
                mock.Mock(
                    side_effect=subject.EfehrAcquisitionError("secret provider detail")
                ),
            ),
        )
        result = subject._run_receipts(
            execution_sha=EXECUTION_SHA, targets=fake_targets
        )
        self.assertEqual(set(result), subject._RESULT_FIELDS)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["receipts"])
        self.assertNotIn("secret", json.dumps(result))

    def test_trusted_terminal_parser_requires_three_exact_rows(self) -> None:
        result = subject._base_result(execution_sha=EXECUTION_SHA)
        rows = []
        for index, (path, operation, _worker) in enumerate(
            subject._CANONICAL_RECEIPT_TARGETS, 1
        ):
            rows.append(
                {
                    "repository_path": path,
                    "operation_id": operation,
                    "retrieved_at": RETRIEVED_AT,
                    "byte_count": index * 10,
                    "sha256": format(index, "x") * 64,
                    "content_type": "text/plain",
                    "etag": None,
                }
            )
        result.update({"status": "pass", "failure_class": None, "receipts": rows})
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(
            subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA)
        )
        result["receipts"] = rows[:2]
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(
            subject.EbriskRiskConfigReceiptsActionError, "three receipts"
        ):
            subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA)

    def test_trusted_terminal_parser_rejects_extra_scientific_claim(self) -> None:
        result = subject._base_result(execution_sha=EXECUTION_SHA)
        result.update(
            {
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "receipts": None,
                "historical_group_assignment": "Kosovo Group1",
            }
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(
            subject.EbriskRiskConfigReceiptsActionError, "fields drifted"
        ):
            subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA)

    def test_cross_sha_ledger_ignores_valid_old_result_and_finds_current(self) -> None:
        sha_a = "a" * 40
        sha_b = "b" * 40
        old_only = mock.Mock(return_value=[trusted_comment(sha_a)])
        self.assertFalse(
            subject._has_terminal_result(
                repository="owner/repo",
                token="token",
                execution_sha=sha_b,
                fetcher=old_only,
                max_pages=subject.MAX_LEDGER_PAGES,
            )
        )
        old_and_current = mock.Mock(
            return_value=[trusted_comment(sha_a), trusted_comment(sha_b)]
        )
        self.assertTrue(
            subject._has_terminal_result(
                repository="owner/repo",
                token="token",
                execution_sha=sha_b,
                fetcher=old_and_current,
                max_pages=subject.MAX_LEDGER_PAGES,
            )
        )

    def test_trusted_result_target_execution_sha_mismatch_fails_closed(self) -> None:
        sha_a = "a" * 40
        result = subject._base_result(execution_sha=sha_a)
        result.update(
            {
                "execution_sha": "b" * 40,
                "status": "blocked",
                "failure_class": "acquisition_failure",
                "receipts": None,
            }
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        with self.assertRaisesRegex(
            subject.EbriskRiskConfigReceiptsActionError, "SHA identity drifted"
        ):
            subject._parse_trusted_terminal_result(body, execution_sha=sha_a)

    def test_public_execution_rejects_worker_and_ledger_rebinding(self) -> None:
        with mock.patch.object(subject, "_RECEIPT_TARGETS", tuple()):
            with self.assertRaisesRegex(
                subject.EbriskRiskConfigReceiptsActionError, "worker targets drifted"
            ):
                subject.run_receipts(execution_sha=EXECUTION_SHA)
        with mock.patch.object(subject, "fetch_repository_comments", mock.Mock()):
            with self.assertRaisesRegex(
                subject.EbriskRiskConfigReceiptsActionError, "ledger fetcher drifted"
            ):
                subject.has_terminal_result(
                    repository="owner/repo", token="token", execution_sha=EXECUTION_SHA
                )

    def test_public_execution_rejects_fixed_identity_rebinding(self) -> None:
        with mock.patch.object(subject, "DATASET_ID", "drifted.dataset"):
            with self.assertRaisesRegex(
                subject.EbriskRiskConfigReceiptsActionError, "fixed authority drifted"
            ):
                subject.run_receipts(execution_sha=EXECUTION_SHA)

    def test_workflow_publisher_has_exact_result_and_receipt_fences(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("keys == [", workflow)
        self.assertIn('"historical_group_assignment_verified",', workflow)
        self.assertIn('"target_sha"\n            ] and', workflow)
        self.assertIn("_parse_trusted_terminal_result", workflow)
        self.assertIn('"Configuration_files/config_ebrisk_Group1.ini"', workflow)
        self.assertIn('"Configuration_files/config_ebrisk_Group2.ini"', workflow)
        self.assertIn('"Configuration_files/config_ebrisk_Iceland.ini"', workflow)
        self.assertIn('"esrm20-ebrisk-group1-config-candidate-v1"', workflow)
        self.assertIn('"esrm20-ebrisk-group2-config-candidate-v1"', workflow)
        self.assertIn('"esrm20-ebrisk-iceland-config-candidate-v1"', workflow)
        self.assertIn('(.byte_count | floor) == .byte_count', workflow)
        self.assertIn('test("^[0-9a-f]{64}$")', workflow)


if __name__ == "__main__":
    unittest.main()
