# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

from scripts import acquire_efehr_esrm20_athens_sibling_receipts as worker

EXECUTION_SHA = "a" * 40
FIXED_TIME = "2026-08-23T19:00:00Z"


class FakeResponse:
    def __init__(self, url: str, payload: bytes, *, content_type: str) -> None:
        self.status = 200
        self._url = url
        self._payload = payload
        self._offset = 0
        self.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": content_type,
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
    for index, (role, path) in enumerate(worker.INPUTS, start=1):
        receipts.append(
            {
                "role": role,
                "repository_path": path,
                "retrieved_at": FIXED_TIME,
                "byte_count": index,
                "sha256": f"{index:064x}",
                "content_type": "application/xml",
                "etag": None,
                "provider_file_bytes_read": True,
                "external_bytes_persisted": False,
                "publication_authorized": False,
            }
        )
    return receipts


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


class AthensSiblingReceiptTests(unittest.TestCase):
    def test_fixed_identity_and_inputs_match_handoff(self) -> None:
        self.assertEqual(worker.PROJECT_ID, 269)
        self.assertEqual(worker.PROJECT_PATH, "efehr/esrm20")
        self.assertEqual(worker.RELEASE_TAG, "v1.0")
        self.assertEqual(worker.CONSUMER_EVENT_ID, "Greece_07-9-1999")
        self.assertEqual(
            worker.COMMIT_SHA,
            "05f83bbc9df81d02ee8ddb1801d9d781355ce783",
        )
        self.assertEqual(
            worker.INPUTS,
            (
                ("exposure", "Exposure/OQ_Exposure_Input_Greece.xml"),
                ("site_model", "Vs30/Site_model_Greece.xml"),
                (
                    "exposure_vulnerability_mapping",
                    "Vulnerability/esrm20_exposure_vulnerability_mapping.csv",
                ),
            ),
        )

    def test_success_hashes_exactly_three_fixed_siblings(self) -> None:
        raw_by_path = {
            worker.INPUTS[0][1]: b"<exposure/>\n",
            worker.INPUTS[1][1]: b"<site/>\n",
            worker.INPUTS[2][1]: b"taxonomy,vulnerability\nA,B\n",
        }
        requested_urls: list[str] = []

        def opener(request, timeout):  # noqa: ANN001, ARG001
            requested_urls.append(request.full_url)
            for _role, path in worker.INPUTS:
                if urllib.parse.quote(path, safe="") in request.full_url:
                    content_type = (
                        "text/csv" if path.endswith(".csv") else "application/xml"
                    )
                    return FakeResponse(
                        request.full_url,
                        raw_by_path[path],
                        content_type=content_type,
                    )
            raise AssertionError("unexpected fixed URL")

        result = worker._acquire_sibling_receipts_for_test(
            opener=opener,
            now=lambda: FIXED_TIME,
            monotonic=lambda: 0.0,
        )

        self.assertEqual(worker.validate_acquisition(result), result)
        self.assertEqual(len(requested_urls), 3)
        self.assertEqual(
            [item["repository_path"] for item in result["receipts"]],
            [item[1] for item in worker.INPUTS],
        )
        for receipt in result["receipts"]:
            path = receipt["repository_path"]
            self.assertEqual(receipt["byte_count"], len(raw_by_path[path]))
            self.assertEqual(
                receipt["sha256"], hashlib.sha256(raw_by_path[path]).hexdigest()
            )
        self.assertIs(result["provider_file_bytes_read"], True)
        self.assertIs(result["provider_file_content_profiled"], False)
        self.assertIs(result["content_semantics_verified"], False)
        self.assertIs(result["benchmark_agreement_inspected"], False)
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_noncanonical_path_is_not_admitted(self) -> None:
        for path in (
            "Exposure/OQ_Exposure_Input_Kosovo.xml",
            "../Exposure/OQ_Exposure_Input_Greece.xml",
            "Vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml",
        ):
            with self.subTest(path=path):
                with self.assertRaisesRegex(
                    worker.AthensSiblingReceiptError, "outside the fixed set"
                ):
                    worker._raw_file_url(path)

    def test_raw_urls_are_frozen_to_project_and_commit(self) -> None:
        for _role, path in worker.INPUTS:
            url = worker._raw_file_url(path)
            self.assertTrue(
                url.startswith(
                    "https://gitlab.seismo.ethz.ch/api/v4/projects/269/"
                    "repository/files/"
                )
            )
            self.assertIn(urllib.parse.quote(path, safe=""), url)
            self.assertTrue(url.endswith(f"?ref={worker.COMMIT_SHA}"))

    def test_authority_alias_drift_fails_before_network(self) -> None:
        called = False

        def opener(request, timeout):  # noqa: ANN001, ARG001
            nonlocal called
            called = True
            raise AssertionError("network must not run after authority drift")

        with mock.patch.object(worker, "PROJECT_ID", 999):
            with self.assertRaisesRegex(
                worker.AthensSiblingReceiptError, "project id authority drifted"
            ):
                worker._acquire_sibling_receipts_for_test(
                    opener=opener,
                    now=lambda: FIXED_TIME,
                    monotonic=lambda: 0.0,
                )
        self.assertIs(called, False)

    def test_production_transport_alias_drift_fails_closed(self) -> None:
        with mock.patch.object(worker, "_open_fixed", object()):
            with self.assertRaisesRegex(
                worker.AthensSiblingReceiptError, "production transport drifted"
            ):
                worker.acquire_sibling_receipts()

    def test_request_validation_rejects_drift_and_duplicate_keys(self) -> None:
        invalid = [
            _request_body("b" * 40),
            worker.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"oc-esrm20-athens-sibling-receipts-request-v1",'
            '"issue":285,"target_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
            '"requester":"one","requester":"two"}',
            "prefix\n" + _request_body(),
            _request_body() + "\n" + worker.REQUEST_MARKER,
        ]
        for body in invalid:
            with self.subTest(body=body):
                with self.assertRaises(worker.AthensSiblingReceiptError):
                    worker.validate_request(
                        body,
                        expected_issue=285,
                        execution_sha=EXECUTION_SHA,
                    )

    def test_result_rejects_semantic_or_authority_uplift(self) -> None:
        for field in (
            "provider_file_content_profiled",
            "content_semantics_verified",
            "benchmark_agreement_inspected",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            result = _valid_result()
            result[field] = True
            with self.subTest(field=field):
                with self.assertRaisesRegex(
                    worker.AthensSiblingReceiptError, field
                ):
                    worker.validate_result(result)

    def test_result_rejects_receipt_path_drift(self) -> None:
        result = _valid_result()
        receipts = result["receipts"]
        self.assertIsInstance(receipts, list)
        receipts[0]["repository_path"] = "Exposure/OQ_Exposure_Input_Kosovo.xml"
        with self.assertRaisesRegex(
            worker.AthensSiblingReceiptError, "repository_path"
        ):
            worker.validate_result(result)

    def test_blocked_result_cannot_assert_partial_byte_evidence(self) -> None:
        result = {
            **worker._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "athens_sibling_receipt_failure",
            "receipts": _valid_receipts(),
            "provider_file_bytes_read": None,
        }
        with self.assertRaisesRegex(
            worker.AthensSiblingReceiptError, "partial byte evidence"
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

    def test_prepare_result_blocks_without_partial_receipts(self) -> None:
        with mock.patch.object(
            worker,
            "_ACQUIRE",
            side_effect=worker.AthensSiblingReceiptError("synthetic failure"),
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
            result["failure_class"], "athens_sibling_receipt_failure"
        )
        self.assertIsNone(result["receipts"])
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertIs(result["content_semantics_verified"], False)
        self.assertIs(result["benchmark_agreement_inspected"], False)
        self.assertIs(result["external_bytes_persisted"], False)

    def test_publisher_key_fence_keeps_jq_lexicographic_order(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github/workflows/esrm20-athens-sibling-receipts.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '"benchmark_agreement_inspected","commit_sha","consumer_event_id",\n'
            '              "content_semantics_verified",',
            workflow,
        )

    def test_malformed_trusted_historical_result_blocks_ledger(self) -> None:
        comment = {
            "id": 322,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER + "\n" + '{"schema_version":"bad"}',
        }
        with self.assertRaises(worker.AthensSiblingReceiptError):
            worker.find_existing_terminal([comment], execution_sha=EXECUTION_SHA)


if __name__ == "__main__":
    unittest.main()
