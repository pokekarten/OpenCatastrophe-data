# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target
from scripts import run_esrm20_tr002_content_scan_action as subject

EXECUTION_SHA = "1" * 40
OTHER_EXECUTION_SHA = "2" * 40
RETRIEVED_AT = "2026-08-21T21:50:00Z"


class FakeResponse:
    def __init__(self, payload: bytes, url: str):
        self._stream = io.BytesIO(payload)
        self._url = url
        self.status = 200
        self.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "application/pdf",
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


def add_source(scan: dict[str, object]) -> dict[str, object]:
    scan["source"] = {
        "dataset_id": subject.DATASET_ID,
        "project_id": subject.PROJECT_ID,
        "project_path": subject.PROJECT_PATH,
        "commit_sha": subject.COMMIT_SHA,
        "repository_path": subject.REPOSITORY_PATH,
        "retrieved_at": RETRIEVED_AT,
        "byte_count": subject.EXPECTED_BYTE_COUNT,
        "sha256": subject.EXPECTED_SHA256,
    }
    return scan


def synthetic_scan() -> dict[str, object]:
    pages = [
        "Geometric mean horizontal component. RotD50 is mentioned here.",
        "horizontal only; geometric   mean repeated. RotD is separate.",
    ]
    raw = "\f".join(pages).encode("utf-8")
    scan = subject.summarize_pages(
        pages,
        extracted_text_bytes=len(raw),
        extracted_text_sha256=hashlib.sha256(raw).hexdigest(),
        extractor_identity="pdftotext version 25.06.0",
    )
    return add_source(scan)


def fixed_context_pages() -> list[str]:
    pages = ["synthetic page"] * 84
    pages[52] = "Vulnerability ground motion intensity measure uses a horizontal component. Geometric mean RotD50."
    pages[78] = "Average spectral acceleration before horizontal direction and response."
    pages[79] = "Fragility and loss context around horizontal orientation."
    pages[80] = "Hazard discussion near horizontal component direction."
    return pages


def synthetic_context_scan() -> dict[str, object]:
    pages = fixed_context_pages()
    raw = "\f".join(pages).encode("utf-8")
    scan = subject.summarize_pages(
        pages,
        extracted_text_bytes=len(raw),
        extracted_text_sha256=hashlib.sha256(raw).hexdigest(),
        extractor_identity="pdftotext version 25.06.0",
        include_context_classification=True,
    )
    return add_source(scan)


def terminal_body(execution_sha: str) -> str:
    result = subject.run_scan(execution_sha=execution_sha, scanner=synthetic_scan)
    return subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))


class Tr002ContentScanActionTests(unittest.TestCase):
    def test_request_is_exact_main_bound_and_has_no_provider_selector(self) -> None:
        parsed = subject.validate_request(
            request_body(), expected_issue=subject.CONTROL_ISSUE, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(set(parsed), subject._REQUEST_FIELDS)
        for selector in ("path", "url", "project_id", "commit_sha", "ref", "host", "terms"):
            with self.subTest(selector=selector), self.assertRaises(subject.Tr002ContentScanError):
                subject.validate_request(
                    request_body(extra={selector: "attacker-controlled"}),
                    expected_issue=subject.CONTROL_ISSUE,
                    execution_sha=EXECUTION_SHA,
                )
        with self.assertRaisesRegex(subject.Tr002ContentScanError, "target_sha"):
            subject.validate_request(
                request_body(sha="2" * 40),
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=EXECUTION_SHA,
            )

    def test_term_scan_is_bounded_to_predeclared_counts_and_pages(self) -> None:
        scan = synthetic_scan()
        self.assertEqual(set(scan["terms"]), {"geometric_mean", "horizontal", "rotd", "rotd50"})
        self.assertEqual(scan["terms"]["geometric_mean"], {"count": 2, "pages": [1, 2]})
        self.assertEqual(scan["terms"]["horizontal"], {"count": 2, "pages": [1, 2]})
        self.assertEqual(scan["terms"]["rotd50"], {"count": 1, "pages": [1]})
        self.assertEqual(scan["terms"]["rotd"], {"count": 1, "pages": [2]})
        self.assertFalse(scan["page_text_returned"])
        self.assertFalse(scan["snippets_returned"])
        self.assertNotIn("horizontal_context_classification", scan)
        serialized = json.dumps(scan)
        self.assertNotIn("Geometric mean horizontal", serialized)
        self.assertNotIn("horizontal only", serialized)
        subject._validate_scan(scan)

    def test_fixed_context_classification_is_non_text_and_exact_page_bounded(self) -> None:
        scan = synthetic_context_scan()
        context = scan["horizontal_context_classification"]
        self.assertEqual(context["pages"], list(subject.CONTEXT_PAGES))
        self.assertFalse(context["raw_context_returned"])
        self.assertEqual([record["page"] for record in context["records"]], list(subject.CONTEXT_PAGES))
        self.assertEqual(scan["terms"]["horizontal"], {"count": 4, "pages": [53, 79, 80, 81]})
        self.assertEqual(context["records"][0]["nearby_terms"]["vulnerability"], 1)
        self.assertEqual(context["records"][0]["nearby_terms"]["component"], 1)
        self.assertEqual(context["records"][1]["nearby_terms"]["spectral_acceleration"], 1)
        serialized = json.dumps(context)
        for raw_text in (
            "Vulnerability ground motion intensity measure",
            "Average spectral acceleration before horizontal",
            "Fragility and loss context around horizontal",
            "Hazard discussion near horizontal",
        ):
            self.assertNotIn(raw_text, serialized)
        subject._validate_scan(scan)

    def test_fixed_context_classification_fails_closed_on_localization_drift(self) -> None:
        pages = fixed_context_pages()
        pages[0] = "unexpected horizontal occurrence"
        raw = "\f".join(pages).encode("utf-8")
        with self.assertRaisesRegex(subject.Tr002ContentScanExtractionError, "localization drifted"):
            subject.summarize_pages(
                pages,
                extracted_text_bytes=len(raw),
                extracted_text_sha256=hashlib.sha256(raw).hexdigest(),
                extractor_identity="pdftotext version 25.06.0",
                include_context_classification=True,
            )

    def test_context_validation_rejects_unknown_output_and_vocabulary(self) -> None:
        scan = synthetic_context_scan()
        tampered = json.loads(json.dumps(scan))
        tampered["horizontal_context_classification"]["records"][0]["snippet"] = "forbidden raw text"
        with self.assertRaisesRegex(subject.Tr002ContentScanError, "record shape"):
            subject._validate_scan(tampered)

        tampered = json.loads(json.dumps(scan))
        tampered["horizontal_context_classification"]["records"][0]["nearby_terms"]["attacker_term"] = 1
        with self.assertRaisesRegex(subject.Tr002ContentScanError, "nearby-term set"):
            subject._validate_scan(tampered)

        tampered = json.loads(json.dumps(scan))
        tampered["unexpected_top_level"] = "forbidden"
        with self.assertRaisesRegex(subject.Tr002ContentScanError, "fields drifted"):
            subject._validate_scan(tampered)

    def test_exact_receipt_identity_is_reproved_before_extraction(self) -> None:
        payload = b"%PDF-1.7\nsynthetic exact bytes\n%%EOF\n"
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
            return FakeResponse(payload, expected_url)

        extracted = ("\f".join(fixed_context_pages()) + "\f").encode("utf-8")

        def runner(args, **kwargs):
            if args == [subject.PDFTOTEXT, "-v"]:
                return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"pdftotext version 25.06.0\n")
            self.assertEqual(args[:4], [subject.PDFTOTEXT, "-enc", "UTF-8", "-layout"])
            return subprocess.CompletedProcess(args, 0, stdout=extracted, stderr=b"")

        with (
            mock.patch.object(subject, "EXPECTED_BYTE_COUNT", len(payload)),
            mock.patch.object(subject, "MAX_PDF_BYTES", len(payload)),
            mock.patch.object(subject, "EXPECTED_SHA256", hashlib.sha256(payload).hexdigest()),
            mock.patch.object(subject, "utc_now", return_value=RETRIEVED_AT),
        ):
            scan = subject._scan_exact_pdf(opener=opener, monotonic=lambda: 0.0, runner=runner)
        self.assertEqual(calls, [expected_url])
        self.assertEqual(scan["source"]["byte_count"], len(payload))
        self.assertEqual(scan["source"]["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(scan["terms"]["horizontal"], {"count": 4, "pages": [53, 79, 80, 81]})
        self.assertEqual(scan["terms"]["geometric_mean"], {"count": 1, "pages": [53]})
        self.assertEqual(scan["terms"]["rotd50"], {"count": 1, "pages": [53]})
        self.assertEqual(scan["extracted_text_sha256"], hashlib.sha256(extracted).hexdigest())
        self.assertEqual(scan["horizontal_context_classification"]["pages"], [53, 79, 80, 81])
        self.assertFalse(scan["horizontal_context_classification"]["raw_context_returned"])

    def test_wrong_pdf_hash_fails_before_extractor_invocation(self) -> None:
        payload = b"%PDF-1.7\nwrong bytes\n%%EOF\n"
        target = validate_target(
            source_issue=subject.SOURCE_SCIENCE_ISSUE,
            dataset_id=subject.DATASET_ID,
            project_id=subject.PROJECT_ID,
            commit_sha=subject.COMMIT_SHA,
            repository_path=subject.REPOSITORY_PATH,
        )
        expected_url = raw_file_api_url(target)
        runner = mock.Mock()

        def opener(request, timeout):
            return FakeResponse(payload, expected_url)

        with (
            mock.patch.object(subject, "EXPECTED_BYTE_COUNT", len(payload)),
            mock.patch.object(subject, "MAX_PDF_BYTES", len(payload)),
            mock.patch.object(subject, "EXPECTED_SHA256", "0" * 64),
            self.assertRaisesRegex(subject.Tr002ContentScanAcquisitionError, "SHA-256"),
        ):
            subject._scan_exact_pdf(opener=opener, monotonic=lambda: 0.0, runner=runner)
        runner.assert_not_called()

    def test_pass_keeps_science_and_model_authority_false(self) -> None:
        result = subject.run_scan(execution_sha=EXECUTION_SHA, scanner=synthetic_context_scan)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["text_location_scan_verified"])
        self.assertFalse(result["component_semantics_verified"])
        self.assertFalse(result["horizontal_component_interoperability_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_extraction_failure_is_atomic_but_preserves_verified_byte_gate(self) -> None:
        def fail():
            raise subject.Tr002ContentScanExtractionError("secret provider text")

        result = subject.run_scan(execution_sha=EXECUTION_SHA, scanner=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "content_extraction_failure")
        self.assertTrue(result["byte_identity_verified"])
        self.assertFalse(result["text_location_scan_verified"])
        self.assertIsNone(result["scan"])
        self.assertNotIn("secret", json.dumps(result))

    def test_terminal_parser_rejects_authority_widening_and_scan_tamper(self) -> None:
        result = subject.run_scan(execution_sha=EXECUTION_SHA, scanner=synthetic_context_scan)
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertTrue(subject._parse_terminal_result(body, execution_sha=EXECUTION_SHA))

        widened = json.loads(json.dumps(result))
        widened["component_semantics_verified"] = True
        body = subject.RESULT_MARKER + "\n" + json.dumps(widened, sort_keys=True, separators=(",", ":"))
        with self.assertRaisesRegex(subject.Tr002ContentScanError, "component_semantics_verified"):
            subject._parse_terminal_result(body, execution_sha=EXECUTION_SHA)

        tampered = json.loads(json.dumps(result))
        tampered["scan"]["terms"]["horizontal"]["pages"] = [999]
        body = subject.RESULT_MARKER + "\n" + json.dumps(tampered, sort_keys=True, separators=(",", ":"))
        with self.assertRaises(subject.Tr002ContentScanError):
            subject._parse_terminal_result(body, execution_sha=EXECUTION_SHA)

    def test_terminal_dedup_skips_valid_prior_sha_and_finds_current_sha(self) -> None:
        prior = {
            "id": 1,
            "user": {"login": subject.TRUSTED_RESULT_LOGIN},
            "body": terminal_body(OTHER_EXECUTION_SHA),
        }
        current = {
            "id": 2,
            "user": {"login": subject.TRUSTED_RESULT_LOGIN},
            "body": terminal_body(EXECUTION_SHA),
        }
        with mock.patch.object(subject, "fetch_repository_comments", return_value=[prior]):
            self.assertFalse(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data", token="token", execution_sha=EXECUTION_SHA
                )
            )
        with mock.patch.object(subject, "fetch_repository_comments", return_value=[prior, current]):
            self.assertTrue(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data", token="token", execution_sha=EXECUTION_SHA
                )
            )

    def test_prior_sha_result_with_mismatched_target_sha_fails_closed(self) -> None:
        result = subject.run_scan(execution_sha=OTHER_EXECUTION_SHA, scanner=synthetic_scan)
        result["target_sha"] = EXECUTION_SHA
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True, separators=(",", ":"))
        comments = [{"id": 1, "user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": body}]
        with (
            mock.patch.object(subject, "fetch_repository_comments", return_value=comments),
            self.assertRaisesRegex(subject.Tr002ContentScanError, "target_sha"),
        ):
            subject.has_terminal_result(
                repository="pokekarten/OpenCatastrophe-data", token="token", execution_sha=EXECUTION_SHA
            )

    def test_workflow_serializes_dedup_provider_and_publication_in_one_job(self) -> None:
        workflow = Path(".github/workflows/esrm20-tr002-content-scan.yml").read_text(encoding="utf-8")
        pre_jobs, jobs = workflow.split("\njobs:\n", 1)
        self.assertNotIn("\nconcurrency:\n", pre_jobs)
        self.assertIn("github.event.issue.number == 596", workflow)
        self.assertIn("github.event.comment.user.login == github.event.repository.owner.login", workflow)
        self.assertNotIn("pull_request_target:", workflow)
        self.assertNotIn("workflow_dispatch:", workflow)
        execute = jobs.split("\n  execute-and-publish-scan:\n", 1)[1]
        self.assertIn("\n    concurrency:\n", execute)
        self.assertIn("group: esrm20-tr002-content-scan-${{ github.repository }}", execute)
        self.assertIn("has_terminal_result(", execute)
        self.assertIn("Run exact fixed TR002 content scan", execute)
        self.assertIn('"repos/$GITHUB_REPOSITORY/issues/596/comments"', execute)
        self.assertNotIn("actions/upload-artifact", workflow)


if __name__ == "__main__":
    unittest.main()
