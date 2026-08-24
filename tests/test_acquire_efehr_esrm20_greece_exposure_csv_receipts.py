# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

from scripts import acquire_efehr_esrm20_greece_exposure_csv_receipts as worker
from scripts import run_efehr_esrm20_greece_exposure_csv_receipts_action as runner

EXECUTION_SHA = "a" * 40
FIXED_TIME = "2026-08-24T10:16:00Z"
PAYLOADS = {
    "Exposure/OQ_Exposure_Input_Greece_Com.csv": b"id,taxonomy,structural\nC1,CR/LWAL,100000\n",
    "Exposure/OQ_Exposure_Input_Greece_Ind.csv": b"id,taxonomy,structural\nI1,CR/LWAL,200000\n",
    "Exposure/OQ_Exposure_Input_Greece_Res.csv": b"id,taxonomy,structural\nR1,CR/LWAL,300000\n",
}


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


def _valid_receipts() -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for path in worker.REPOSITORY_PATHS:
        payload = PAYLOADS[path]
        receipts.append(
            {
                "repository_path": path,
                "retrieved_at": FIXED_TIME,
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "content_type": "text/csv",
                "etag": None,
                "provider_file_bytes_read": True,
                "external_bytes_persisted": False,
                "publication_authorized": False,
            }
        )
    return worker.validate_receipts(receipts)


def _valid_result() -> dict[str, object]:
    return worker.validate_result(
        {
            **worker._base_result(execution_sha=EXECUTION_SHA),
            "status": "pass",
            "failure_class": None,
            "receipts": _valid_receipts(),
            "provider_file_bytes_read": True,
        }
    )


class GreeceExposureCsvReceiptsTests(unittest.TestCase):
    def test_source_terminal_and_exact_three_dependencies_are_frozen(self) -> None:
        self.assertEqual(worker.SOURCE_ISSUE, 285)
        self.assertEqual(worker.PARENT_CONSUMER_ISSUE, 287)
        self.assertEqual(worker.SOURCE_DECLARATION_COMMENT_ID, 5393778961)
        self.assertEqual(
            worker.SOURCE_DECLARATION_EXECUTION_SHA,
            "64df54ef071937b49dac40650ef9e1cc93e014fb",
        )
        self.assertEqual(
            worker.PARENT_RECEIPT_SHA256,
            "f66dd2623a29a1ec6066e4daf9e1c40df14acca24d1643c545d8fac5c38a2556",
        )
        self.assertEqual(
            worker.SOURCE_ASSET_REFERENCES,
            (
                "OQ_Exposure_Input_Greece_Com.csv",
                "OQ_Exposure_Input_Greece_Ind.csv",
                "OQ_Exposure_Input_Greece_Res.csv",
            ),
        )
        self.assertEqual(
            worker.REPOSITORY_PATHS,
            (
                "Exposure/OQ_Exposure_Input_Greece_Com.csv",
                "Exposure/OQ_Exposure_Input_Greece_Ind.csv",
                "Exposure/OQ_Exposure_Input_Greece_Res.csv",
            ),
        )
        self.assertEqual(worker._expected_repository_paths(), worker.REPOSITORY_PATHS)

    def test_obsolete_single_csv_premise_is_not_admitted(self) -> None:
        self.assertNotIn("Exposure_Model_Greece.csv", worker.SOURCE_ASSET_REFERENCES)
        self.assertNotIn("Exposure/Exposure_Model_Greece.csv", worker.REPOSITORY_PATHS)
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvReceiptsError,
            "left frozen dependency set",
        ):
            worker._raw_file_url("Exposure/Exposure_Model_Greece.csv")

    def test_success_hashes_exact_three_files_and_returns_no_provider_bytes(self) -> None:
        requested_paths: list[str] = []

        def opener(request, timeout):  # noqa: ANN001, ARG001
            encoded = request.full_url.split("/repository/files/", 1)[1].split("/raw?", 1)[0]
            path = urllib.parse.unquote(encoded)
            requested_paths.append(path)
            return FakeResponse(request.full_url, PAYLOADS[path])

        receipts = worker._acquire_for_test(
            opener=opener,
            now=lambda: FIXED_TIME,
            monotonic=lambda: 0.0,
        )
        self.assertEqual(requested_paths, list(worker.REPOSITORY_PATHS))
        self.assertEqual(len(receipts), 3)
        for receipt, path in zip(receipts, worker.REPOSITORY_PATHS, strict=True):
            self.assertEqual(receipt["repository_path"], path)
            self.assertEqual(receipt["sha256"], hashlib.sha256(PAYLOADS[path]).hexdigest())
            self.assertNotIn("raw", receipt)
            self.assertIs(receipt["external_bytes_persisted"], False)
            self.assertIs(receipt["publication_authorized"], False)

    def test_authority_drift_fails_before_network(self) -> None:
        called = False

        def opener(request, timeout):  # noqa: ANN001, ARG001
            nonlocal called
            called = True
            raise AssertionError("network must not run after authority drift")

        cases = (
            ("PROJECT_ID", 999, "project id authority drifted"),
            (
                "SOURCE_ASSET_REFERENCES",
                ("Exposure_Model_Greece.csv",),
                "source asset references authority drifted",
            ),
            (
                "REPOSITORY_PATHS",
                ("Exposure/Exposure_Model_Greece.csv",),
                "repository paths authority drifted",
            ),
        )
        for field, value, message in cases:
            with self.subTest(field=field), mock.patch.object(worker, field, value):
                with self.assertRaisesRegex(worker.GreeceExposureCsvReceiptsError, message):
                    worker._acquire_for_test(
                        opener=opener,
                        now=lambda: FIXED_TIME,
                        monotonic=lambda: 0.0,
                    )
        self.assertIs(called, False)

    def test_production_transport_alias_drift_fails_closed(self) -> None:
        with mock.patch.object(worker, "_open_fixed", object()):
            with self.assertRaisesRegex(
                worker.GreeceExposureCsvReceiptsError,
                "production transport drifted",
            ):
                worker.acquire_receipts()

    def test_request_rejects_sha_drift_duplicate_keys_and_prefix(self) -> None:
        invalid = [
            _request_body("b" * 40),
            worker.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"oc-esrm20-greece-exposure-csv-receipts-request-v1",'
            '"issue":285,"target_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
            '"requester":"one","requester":"two"}',
            "prefix\n" + _request_body(),
            _request_body() + "\n" + worker.REQUEST_MARKER,
        ]
        for body in invalid:
            with self.subTest(body=body):
                with self.assertRaises(worker.GreeceExposureCsvReceiptsError):
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
                with self.assertRaisesRegex(worker.GreeceExposureCsvReceiptsError, field):
                    worker.validate_result(result)

    def test_result_rejects_missing_reordered_or_wrong_path_receipts(self) -> None:
        for mutate in ("missing", "reordered", "wrong_path"):
            result = _valid_result()
            receipts = result["receipts"]
            self.assertIsInstance(receipts, list)
            if mutate == "missing":
                result["receipts"] = receipts[:-1]
            elif mutate == "reordered":
                result["receipts"] = [receipts[1], receipts[0], receipts[2]]
            else:
                receipts[0]["repository_path"] = "Exposure/Other.csv"
            with self.subTest(mutate=mutate):
                with self.assertRaises(worker.GreeceExposureCsvReceiptsError):
                    worker.validate_result(result)

    def test_blocked_result_cannot_assert_partial_byte_evidence(self) -> None:
        result = {
            **worker._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "greece_exposure_csv_receipts_failure",
            "receipts": _valid_receipts()[:1],
            "provider_file_bytes_read": None,
        }
        with self.assertRaisesRegex(
            worker.GreeceExposureCsvReceiptsError,
            "partial byte evidence",
        ):
            worker.validate_result(result)

    def test_prepare_result_deduplicates_before_provider_work(self) -> None:
        existing = _valid_result()
        comment = {
            "id": 321,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER + "\n" + json.dumps(existing, separators=(",", ":")),
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
        self.assertEqual(result, {"status": "duplicate", "duplicate_result_comment_id": 321})

    def test_acquisition_failure_publishes_no_partial_receipts(self) -> None:
        with mock.patch.object(
            worker,
            "_ACQUIRE",
            side_effect=worker.GreeceExposureCsvReceiptsError("synthetic third-file failure"),
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
        self.assertEqual(result["failure_class"], "greece_exposure_csv_receipts_failure")
        self.assertIsNone(result["receipts"])
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
        with self.assertRaises(worker.GreeceExposureCsvReceiptsError):
            worker.find_existing_terminal([comment], execution_sha=EXECUTION_SHA)

    def test_runner_terminalizes_only_complete_ledger_failure(self) -> None:
        with mock.patch.object(
            runner.worker,
            "prepare_result",
            side_effect=worker.GreeceExposureCsvReceiptsError(
                "cannot read complete Greece exposure CSV receipts result ledger"
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
        self.assertIsNone(result["receipts"])
        self.assertIsNone(result["provider_file_bytes_read"])

        with mock.patch.object(
            runner.worker,
            "prepare_result",
            side_effect=worker.GreeceExposureCsvReceiptsError("other failure"),
        ):
            with self.assertRaisesRegex(worker.GreeceExposureCsvReceiptsError, "other failure"):
                runner.prepare_action_result(
                    _request_body(),
                    expected_issue=285,
                    execution_sha=EXECUTION_SHA,
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                )

    def test_workflow_is_trusted_main_owner_gated_and_live_refenced(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github/workflows/esrm20-greece-exposure-csv-receipts.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 285", workflow)
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn(
            "python -m scripts.run_efehr_esrm20_greece_exposure_csv_receipts_action",
            workflow,
        )
        self.assertIn("DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn(
            'gh api "repos/$GITHUB_REPOSITORY/commits/$DEFAULT_BRANCH" --jq \'.sha\'',
            workflow,
        )
        self.assertIn('test "$LATEST_SHA" = "$EXECUTION_SHA"', workflow)
        publish = workflow.split("publish-greece-exposure-csv-receipts:", 1)[1]
        self.assertIn("contents: read", publish)
        self.assertIn("issues: write", publish)
        self.assertNotIn("actions/checkout", publish)
        self.assertIn("length == 3", publish)
        self.assertNotIn("Exposure_Model_Greece.csv", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("github.event.pull_request", workflow)


if __name__ == "__main__":
    unittest.main()
