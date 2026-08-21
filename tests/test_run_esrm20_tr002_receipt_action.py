# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import io
import json
import unittest
from pathlib import Path
from unittest import mock

from scripts.efehr_gitlab_receipt import EfehrReceiptError, raw_file_api_url, validate_target
from scripts import run_esrm20_tr002_receipt_action as subject

EXECUTION_SHA = "1" * 40
RETRIEVED_AT = "2026-08-21T15:20:00Z"


class FakeResponse:
    def __init__(self, payload: bytes, url: str, *, content_type: str = "application/pdf"):
        self._stream = io.BytesIO(payload)
        self._url = url
        self.status = 200
        self.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": content_type,
            "ETag": '"synthetic"',
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def geturl(self) -> str:
        return self._url


def request_body(*, sha: str = EXECUTION_SHA, extra: dict[str, object] | None = None) -> str:
    payload: dict[str, object] = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    if extra:
        payload.update(extra)
    return subject.REQUEST_MARKER + "\n" + json.dumps(payload, sort_keys=True, separators=(",", ":"))


def trusted_receipt(payload: bytes = b"%PDF-1.7\nsynthetic\n") -> dict[str, object]:
    return {
        "schema_version": "oc-efehr-trusted-acquisition-v1",
        "operation_id": subject.WORKER_OPERATION_ID,
        "source_issue": subject.SOURCE_SCIENCE_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "repository_path": subject.REPOSITORY_PATH,
        "requested_url": "https://example.invalid/fixed",
        "final_url": "https://example.invalid/fixed",
        "retrieved_at": RETRIEVED_AT,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "content_type": "application/pdf",
        "etag": '"synthetic"',
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


class Tr002ReceiptActionTests(unittest.TestCase):
    def test_exact_release_report_is_allowlisted_and_near_paths_fail_closed(self) -> None:
        target = validate_target(
            source_issue=subject.SOURCE_SCIENCE_ISSUE,
            dataset_id=subject.DATASET_ID,
            project_id=subject.PROJECT_ID,
            commit_sha=subject.COMMIT_SHA,
            repository_path=subject.REPOSITORY_PATH,
        )
        self.assertEqual(target.project_path, "efehr/esrm20")
        self.assertIn("Documentation%2FEFEHR_TR002_ESRM20.pdf", raw_file_api_url(target))
        for path in (
            "Documentation/EFEHR_TR002_ESRM20_v1.0.1.pdf",
            "Documentation/EFEHR_TR002_ESRM20.docx",
            "Documentation/../EFEHR_TR002_ESRM20.pdf",
            "README.md",
        ):
            with self.subTest(path=path), self.assertRaises(EfehrReceiptError):
                validate_target(
                    source_issue=subject.SOURCE_SCIENCE_ISSUE,
                    dataset_id=subject.DATASET_ID,
                    project_id=subject.PROJECT_ID,
                    commit_sha=subject.COMMIT_SHA,
                    repository_path=path,
                )

    def test_fixed_worker_hashes_only_exact_immutable_pdf(self) -> None:
        payload = b"%PDF-1.7\nsynthetic-test-only\n%%EOF\n"
        target = validate_target(
            source_issue=subject.SOURCE_SCIENCE_ISSUE,
            dataset_id=subject.DATASET_ID,
            project_id=subject.PROJECT_ID,
            commit_sha=subject.COMMIT_SHA,
            repository_path=subject.REPOSITORY_PATH,
        )
        expected_url = raw_file_api_url(target)
        calls: list[str] = []

        def opener(request, timeout):
            self.assertGreater(timeout, 0)
            calls.append(request.full_url)
            return FakeResponse(payload, expected_url, content_type="application/octet-stream")

        receipt = subject._acquire_tr002_receipt(
            opener=opener,
            now=lambda: RETRIEVED_AT,
            monotonic=lambda: 0.0,
        )
        self.assertEqual(calls, [expected_url])
        self.assertEqual(receipt["commit_sha"], subject.COMMIT_SHA)
        self.assertEqual(receipt["repository_path"], subject.REPOSITORY_PATH)
        self.assertEqual(receipt["byte_count"], len(payload))
        self.assertEqual(receipt["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["publication_authorized"])

    def test_non_pdf_200_response_fails_closed_before_receipt(self) -> None:
        payload = b"<html>not a pdf</html>"
        target = validate_target(
            source_issue=subject.SOURCE_SCIENCE_ISSUE,
            dataset_id=subject.DATASET_ID,
            project_id=subject.PROJECT_ID,
            commit_sha=subject.COMMIT_SHA,
            repository_path=subject.REPOSITORY_PATH,
        )
        expected_url = raw_file_api_url(target)

        def opener(request, timeout):
            return FakeResponse(payload, expected_url, content_type="text/html")

        with self.assertRaises(subject.EfehrAcquisitionError):
            subject._acquire_tr002_receipt(
                opener=opener,
                now=lambda: RETRIEVED_AT,
                monotonic=lambda: 0.0,
            )

    def test_request_is_exact_main_bound_and_has_no_provider_selector(self) -> None:
        parsed = subject.validate_request(
            request_body(), expected_issue=subject.CONTROL_ISSUE, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(set(parsed), subject._REQUEST_FIELDS)
        for selector in ("path", "url", "project_id", "commit_sha", "ref", "host"):
            self.assertNotIn(selector, parsed)
            with self.assertRaises(subject.Tr002ReceiptActionError):
                subject.validate_request(
                    request_body(extra={selector: "attacker-controlled"}),
                    expected_issue=subject.CONTROL_ISSUE,
                    execution_sha=EXECUTION_SHA,
                )
        with self.assertRaisesRegex(subject.Tr002ReceiptActionError, "target_sha"):
            subject.validate_request(
                request_body(sha="2" * 40),
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=EXECUTION_SHA,
            )

    def test_receipt_identity_bounds_and_authority_drift_fail_closed(self) -> None:
        base = trusted_receipt()
        subject._validate_receipt(base)
        for field, value in (
            ("source_issue", 287),
            ("project_id", 188),
            ("commit_sha", "2" * 40),
            ("repository_path", "Documentation/other.pdf"),
            ("external_bytes_persisted", True),
            ("publication_authorized", True),
            ("sha256", "A" * 64),
            ("byte_count", True),
            ("byte_count", subject.MAX_PDF_BYTES + 1),
        ):
            with self.subTest(field=field, value=value):
                mutated = dict(base)
                mutated[field] = value
                with self.assertRaises(subject.Tr002ReceiptActionError):
                    subject._validate_receipt(mutated)

    def test_run_receipt_publishes_bounded_identity_only(self) -> None:
        receipt = trusted_receipt()
        with mock.patch.object(subject, "acquire_tr002_receipt", return_value=receipt):
            result = subject.run_receipt(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["failure_class"])
        self.assertEqual(
            set(result["receipt"]),
            {"retrieved_at", "byte_count", "sha256", "content_type", "etag"},
        )
        self.assertFalse(result["report_content_verified"])
        self.assertFalse(result["component_semantics_verified"])
        self.assertFalse(result["scientific_applicability_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_acquisition_failure_is_atomic_and_sanitized(self) -> None:
        with mock.patch.object(
            subject,
            "acquire_tr002_receipt",
            side_effect=subject.EfehrAcquisitionError("secret provider payload"),
        ):
            result = subject.run_receipt(execution_sha=EXECUTION_SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["receipt"])
        self.assertNotIn("secret", json.dumps(result))

    def test_trusted_terminal_parser_rejects_authority_widening(self) -> None:
        result = subject._base_result(execution_sha=EXECUTION_SHA)
        result.update(
            {
                "status": "pass",
                "failure_class": None,
                "receipt": {
                    "retrieved_at": RETRIEVED_AT,
                    "byte_count": 10,
                    "sha256": "a" * 64,
                    "content_type": "application/pdf",
                    "etag": None,
                },
            }
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertTrue(subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA))
        result["component_semantics_verified"] = True
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        with self.assertRaisesRegex(subject.Tr002ReceiptActionError, "component_semantics_verified"):
            subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA)

    def test_workflow_serializes_dedup_provider_and_terminal_publication_in_one_job(self) -> None:
        workflow = Path(".github/workflows/esrm20-tr002-receipt.yml").read_text(encoding="utf-8")
        pre_jobs, jobs = workflow.split("\njobs:\n", 1)
        self.assertNotIn("\nconcurrency:\n", pre_jobs)
        self.assertIn("github.event.issue.number == 596", workflow)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", workflow)
        self.assertNotIn("pull_request_target:", workflow)
        self.assertNotIn("workflow_dispatch:", workflow)
        execute = jobs.split("\n  execute-and-publish-receipt:\n", 1)[1]
        self.assertIn("\n    concurrency:\n", execute)
        self.assertIn("group: esrm20-tr002-receipt-${{ github.repository }}", execute)
        self.assertIn("cancel-in-progress: false", execute)
        self.assertIn("has_terminal_result(", execute)
        self.assertIn("Run exact fixed TR002 receipt", execute)
        self.assertIn('"repos/$GITHUB_REPOSITORY/issues/596/comments"', execute)
        self.assertNotIn("\n  publish-receipt:\n", jobs)


if __name__ == "__main__":
    unittest.main()
