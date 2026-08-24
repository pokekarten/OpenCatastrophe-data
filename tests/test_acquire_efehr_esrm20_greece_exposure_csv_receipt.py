# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

from scripts import acquire_efehr_esrm20_greece_exposure_csv_receipt as worker
from scripts import run_efehr_esrm20_greece_exposure_csv_receipt_action as runner

EXECUTION_SHA = "a" * 40
FIXED_TIME = "2026-08-24T08:30:00Z"
PAYLOAD = b"id,lon,lat,taxonomy,structural\nA1,23.7,38.0,CR/LWAL,100000\n"


class FakeResponse:
    def __init__(self, url: str, payload: bytes) -> None:
        self.status = 200
        self._url = url
        self._payload = payload
        self._offset = 0
        self.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "text/csv",
            "ETag": '"fixture"',
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        if size < 0:
            size = len(self._payload) - self._offset
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


def _request_body(target_sha: str = EXECUTION_SHA) -> str:
    payload = {
        "schema_version": worker.REQUEST_SCHEMA_VERSION,
        "issue": 285,
        "target_sha": target_sha,
        "requester": "TEST-AGENT",
    }
    return worker.REQUEST_MARKER + "\n" + json.dumps(payload, separators=(",", ":"))


def _valid_receipt() -> dict[str, object]:
    return {
        "repository_path": worker.REPOSITORY_PATH,
        "retrieved_at": FIXED_TIME,
        "byte_count": len(PAYLOAD),
        "sha256": hashlib.sha256(PAYLOAD).hexdigest(),
        "content_type": "text/csv",
        "etag": None,
        "provider_file_bytes_read": True,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def _valid_result() -> dict[str, object]:
    return worker.validate_result(
        {
            **worker._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "receipt": _valid_receipt(),
            "provider_file_bytes_read": True,
        }
    )


class GreeceExposureCsvReceiptTests(unittest.TestCase):
    def test_fixed_identity_and_source_derived_path_are_frozen(self) -> None:
        self.assertEqual(worker.SOURCE_ISSUE, 285)
        self.assertEqual(worker.PREDECESSOR_ISSUE, 662)
        self.assertEqual(worker.PROJECT_ID, 269)
        self.assertEqual(worker.PROJECT_PATH, "efehr/esrm20")
        self.assertEqual(worker.RELEASE_TAG, "v1.0")
        self.assertEqual(
            worker.COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(worker.CONSUMER_EVENT_ID, "Greece_07-9-1999")
        self.assertEqual(
            worker.PARENT_EXPOSURE_PATH, "Exposure/OQ_Exposure_Input_Greece.xml"
        )
        self.assertEqual(worker.SOURCE_ASSET_REFERENCE, "Exposure_Model_Greece.csv")
        self.assertEqual(worker.REPOSITORY_PATH, "Exposure/Exposure_Model_Greece.csv")
        self.assertEqual(worker._expected_repository_path(), worker.REPOSITORY_PATH)

    def test_success_hashes_only_the_fixed_csv_and_never_returns_bytes(self) -> None:
        requested_urls: list[str] = []

        def opener(request, timeout):  # noqa: ANN001, ARG001
            requested_urls.append(request.full_url)
            return FakeResponse(request.full_url, PAYLOAD)

        receipt = worker._acquire_for_test(
            opener=opener,
            now=lambda: FIXED_TIME,
            monotonic=lambda: 0.0,
        )
        self.assertEqual(worker.validate_receipt(receipt), receipt)
        self.assertEqual(len(requested_urls), 1)
        self.assertIn(
            urllib.parse.quote(worker.REPOSITORY_PATH, safe=""), requested_urls[0]
        )
        self.assertTrue(requested_urls[0].endswith(f"?ref={worker.COMMIT_SHA}"))
        self.assertEqual(receipt["byte_count"], len(PAYLOAD))
        self.assertEqual(receipt["sha256"], hashlib.sha256(PAYLOAD).hexdigest())
        self.assertNotIn("raw", receipt)
        self.assertIs(receipt["external_bytes_persisted"], False)
        self.assertIs(receipt["publication_authorized"], False)

    def test_authority_or_path_drift_fails_before_network(self) -> None:
        called = False

        def opener(request, timeout):  # noqa: ANN001, ARG001
            nonlocal called
            called = True
            raise AssertionError("network must not run after authority drift")

        cases = (
            ("PROJECT_ID", 999, "project id authority drifted"),
            (
                "SOURCE_ASSET_REFERENCE",
                "../Exposure_Model_Greece.csv",
                "source asset reference authority drifted",
            ),
            (
                "REPOSITORY_PATH",
                "Exposure/Other.csv",
                "repository path authority drifted",
            ),
        )
        for field, value, message in cases:
            with self.subTest(field=field), mock.patch.object(worker, field, value):
                with self.assertRaisesRegex(worker.GreeceExposureCsvReceiptError, message):
                    worker._acquire_for_test(
                        opener=opener,
                        now=lambda: FIXED_TIME,
                        monotonic=lambda: 0.0,
                    )
        self.assertIs(called, False)

    def test_production_transport_alias_drift_fails_closed(self) -> None:
        with mock.patch.object(worker, "_open_fixed", object()):
            with self.assertRaisesRegex(
                worker.GreeceExposureCsvReceiptError,
                "production transport drifted",
            ):
                worker.acquire_receipt()

    def test_request_validation_rejects_sha_drift_duplicate_keys_and_prefix(self) -> None:
        invalid = [
            _request_body("b" * 40),
            worker.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"oc-esrm20-greece-exposure-csv-receipt-request-v1",'
            '"issue":285,"target_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
            '"requester":"one","requester":"two"}',
            "prefix\n" + _request_body(),
            _request_body() + "\n" + worker.REQUEST_MARKER,
        ]
        for body in invalid:
            with self.subTest(body=body):
                with self.assertRaises(worker.GreeceExposureCsvReceiptError):
                    worker.validate_request(
                        body,
                        expected_issue=285,
                        execution_sha=EXECUTION_SHA,
                    )

    def test_result_rejects_scientific_authority_uplift(self) -> None:
        for field in (
            "provider_file_content_profiled",
            "content_semantics_verified",
            "crs_semantics_verified",
            "taxonomy_semantics_verified",
            "replacement_cost_semantics_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            result = _valid_result()
            result[field] = True
            with self.subTest(field=field):
                with self.assertRaisesRegex(worker.GreeceExposureCsvReceiptError, field):
                    worker.validate_result(result)

    def test_result_rejects_receipt_path_drift(self) -> None:
        result = _valid_result()
        receipt = result["receipt"]
        self.assertIsInstance(receipt, dict)
        receipt["repository_path"] = "Exposure/Other.csv"
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvReceiptError, "repository_path"
        ):
            worker.validate_result(result)

    def test_blocked_result_cannot_assert_partial_byte_evidence(self) -> None:
        result = {
            **worker._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "greece_exposure_csv_receipt_failure",
            "receipt": _valid_receipt(),
            "provider_file_bytes_read": None,
        }
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvReceiptError, "partial byte evidence"
        ):
            worker.validate_result(result)

    def test_prepare_result_deduplicates_before_provider_work(self) -> None:
        existing = _valid_result()
        comment = {
            "id": 321,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER
            + "\n"
            + json.dumps(existing, separators=(",", ":")),
        }
        with mock.patch.object(
            worker,
            "_ACQUIRE",
            side_effect=AssertionError("provider must not run after dedup"),
        ):
            result = worker.prepare_result(
                _request_body(),
                expected_issue=285,
                execution_sha=EXECUTION_SHA,
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                comments=[comment],
            )
        self.assertEqual(
            result, {"status": "duplicate", "duplicate_result_comment_id": 321}
        )

    def test_prepare_result_blocks_without_partial_receipt(self) -> None:
        with mock.patch.object(
            worker,
            "_ACQUIRE",
            side_effect=worker.GreeceExposureCsvReceiptError("synthetic failure"),
        ):
            result = worker.prepare_result(
                _request_body(),
                expected_issue=285,
                execution_sha=EXECUTION_SHA,
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                comments=[],
            )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["failure_class"], "greece_exposure_csv_receipt_failure"
        )
        self.assertIsNone(result["receipt"])
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertIs(result["content_semantics_verified"], False)
        self.assertIs(result["taxonomy_semantics_verified"], False)
        self.assertIs(result["external_bytes_persisted"], False)

    def test_malformed_trusted_historical_result_blocks_ledger(self) -> None:
        comment = {
            "id": 322,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER + "\n" + '{"schema_version":"bad"}',
        }
        with self.assertRaises(worker.GreeceExposureCsvReceiptError):
            worker.find_existing_terminal([comment], execution_sha=EXECUTION_SHA)

    def test_runner_terminalizes_only_complete_ledger_failure(self) -> None:
        with mock.patch.object(
            runner.worker,
            "prepare_result",
            side_effect=worker.GreeceExposureCsvReceiptError(
                "cannot read complete Greece exposure CSV result ledger"
            ),
        ):
            result = runner.prepare_action_result(
                _request_body(),
                expected_issue=285,
                execution_sha=EXECUTION_SHA,
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
            )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "ledger_incomplete")
        self.assertIsNone(result["receipt"])
        self.assertIsNone(result["provider_file_bytes_read"])

        with mock.patch.object(
            runner.worker,
            "prepare_result",
            side_effect=worker.GreeceExposureCsvReceiptError("other failure"),
        ):
            with self.assertRaisesRegex(
                worker.GreeceExposureCsvReceiptError, "other failure"
            ):
                runner.prepare_action_result(
                    _request_body(),
                    expected_issue=285,
                    execution_sha=EXECUTION_SHA,
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                )

    def test_workflow_is_owner_gated_trusted_main_and_publish_fenced(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github/workflows/esrm20-greece-exposure-csv-receipt.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 285", workflow)
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn(
            "python -m scripts.run_efehr_esrm20_greece_exposure_csv_receipt_action",
            workflow,
        )
        self.assertIn('.target_sha == $sha and .execution_sha == $sha', workflow)
        self.assertIn(
            '.repository_path == "Exposure/Exposure_Model_Greece.csv"', workflow
        )
        self.assertIn(".provider_file_content_profiled == false", workflow)
        self.assertIn(".publication_authorized == false", workflow)
        self.assertIn(".model_use_authorized == false", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("github.event.pull_request", workflow)


if __name__ == "__main__":
    unittest.main()
