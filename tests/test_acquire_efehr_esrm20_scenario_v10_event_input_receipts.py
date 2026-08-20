# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_scenario_v10_event_input_receipts as worker

EXECUTION_SHA = "a" * 40
FIXED_TIME = "2026-08-19T18:20:00Z"


class FakeResponse:
    def __init__(self, url: str, payload: bytes) -> None:
        self.status = 200
        self._url = url
        self._payload = payload
        self._offset = 0
        self.headers = {
            "Content-Length": str(len(payload)),
            "Content-Type": "application/xml",
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
    for index, (role, path, blob_sha1) in enumerate(worker.INPUTS, start=1):
        receipts.append(
            {
                "role": role,
                "repository_path": path,
                "git_blob_sha1": blob_sha1,
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


class ScenarioV10EventInputReceiptTests(unittest.TestCase):
    def test_fixed_inputs_match_canonical_trusted_main_event_path_result(self) -> None:
        # Canonical machine evidence: #285 trusted-bot result comment 5346096945.
        self.assertEqual(
            worker.INPUTS,
            (
                (
                    "rupture_definition",
                    "ruptures/source_models/rupture_Greece_07-9-1999.xml",
                    "fa3bfd7aedfb63869c5808785b0ca712b6e45859",
                ),
                (
                    "usgs_shakemap_grid",
                    "shakemaps/shakemaps_USGS/Greece_07-9-1999/grid.xml",
                    "21e323dec41b8efb012b2595145fded5fb35fd3a",
                ),
                (
                    "usgs_shakemap_uncertainty",
                    "shakemaps/shakemaps_USGS/Greece_07-9-1999/uncertainty.xml",
                    "30d5635260a83cd0ac91ee559d0109ff126a7b57",
                ),
            ),
        )

    def test_git_blob_identity_uses_canonical_git_object_bytes(self) -> None:
        self.assertEqual(
            worker._git_blob_sha1(b"abc"),
            "f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f",
        )

    def test_success_receipts_exactly_three_fixed_inputs(self) -> None:
        import urllib.parse

        raw_by_path = {
            worker.INPUTS[0][1]: b"<rupture/>\n",
            worker.INPUTS[1][1]: b"<grid/>\n",
            worker.INPUTS[2][1]: b"<uncertainty/>\n",
        }
        expected_blob_by_raw = {
            raw_by_path[path]: blob_sha1 for _role, path, blob_sha1 in worker.INPUTS
        }
        requested_urls: list[str] = []

        def opener(request, timeout):  # noqa: ANN001, ARG001
            requested_urls.append(request.full_url)
            for _role, path, _blob in worker.INPUTS:
                if urllib.parse.quote(path, safe="") in request.full_url:
                    return FakeResponse(request.full_url, raw_by_path[path])
            raise AssertionError("unexpected fixed URL")

        with mock.patch.object(
            worker,
            "_git_blob_sha1",
            side_effect=lambda raw: expected_blob_by_raw[raw],
        ):
            result = worker.acquire_event_input_receipts(
                opener=opener,
                now=lambda: FIXED_TIME,
                monotonic=lambda: 0.0,
            )

        self.assertEqual(worker.validate_acquisition(result), result)
        self.assertEqual(
            [item["repository_path"] for item in result["receipts"]],
            [item[1] for item in worker.INPUTS],
        )
        self.assertEqual(len(requested_urls), 3)
        self.assertTrue(
            all("shakemaps%2Foutputs%2F" not in url for url in requested_urls)
        )
        self.assertIs(result["provider_file_bytes_read"], True)
        self.assertIs(result["provider_file_content_profiled"], False)
        self.assertIs(result["output_payload_bytes_read"], False)
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["event_location_inference_authorized"], False)
        self.assertIs(result["scenario_selection_authorized"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_blob_mismatch_fails_closed(self) -> None:
        role, path, expected_blob = worker.INPUTS[0]
        url = worker._raw_file_url(path)

        with self.assertRaisesRegex(
            worker.ScenarioEventInputReceiptError, "immutable tree Git blob"
        ):
            worker._acquire_one(
                role=role,
                repository_path=path,
                expected_git_blob_sha1=expected_blob,
                opener=lambda request, timeout: FakeResponse(
                    url, b"not-the-provider-object"
                ),
                now=lambda: FIXED_TIME,
                monotonic=lambda: 0.0,
                deadline=30.0,
            )

    def test_authority_alias_drift_fails_before_network(self) -> None:
        called = False

        def opener(request, timeout):  # noqa: ANN001, ARG001
            nonlocal called
            called = True
            raise AssertionError("network must not run after authority drift")

        with mock.patch.object(worker, "PROJECT_ID", 999):
            with self.assertRaisesRegex(
                worker.ScenarioEventInputReceiptError, "project id authority drifted"
            ):
                worker.acquire_event_input_receipts(opener=opener)
        self.assertIs(called, False)

    def test_output_path_is_not_an_admitted_target(self) -> None:
        with self.assertRaisesRegex(
            worker.ScenarioEventInputReceiptError, "outside the fixed set"
        ):
            worker._raw_file_url(
                "shakemaps/outputs/losses-Greece_07-9-1999.csv"
            )

    def test_request_validation_fails_closed(self) -> None:
        invalid_bodies = [
            worker.REQUEST_MARKER
            + "\n"
            + json.dumps(
                {
                    "schema_version": worker.REQUEST_SCHEMA_VERSION,
                    "issue": 285,
                    "target_sha": "b" * 40,
                    "requester": "TEST-AGENT",
                }
            ),
            worker.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"oc-esrm20-scenario-v10-event-input-receipts-request-v1",'
            '"issue":285,"target_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
            '"requester":"one","requester":"two"}',
            "prefix\n" + _request_body(),
            _request_body() + "\n" + worker.REQUEST_MARKER,
        ]
        for body in invalid_bodies:
            with self.subTest(body=body):
                with self.assertRaises(worker.ScenarioEventInputReceiptError):
                    worker.validate_request(
                        body,
                        expected_issue=285,
                        execution_sha=EXECUTION_SHA,
                    )

    def test_result_rejects_authority_widening(self) -> None:
        result = _valid_result()
        result["output_payload_bytes_read"] = True
        with self.assertRaisesRegex(
            worker.ScenarioEventInputReceiptError, "output_payload_bytes_read"
        ):
            worker.validate_result(result)

    def test_result_rejects_receipt_path_drift(self) -> None:
        result = _valid_result()
        receipts = result["receipts"]
        self.assertIsInstance(receipts, list)
        receipts[0]["repository_path"] = (
            "shakemaps/outputs/damages-Greece_07-9-1999.csv"
        )
        with self.assertRaisesRegex(
            worker.ScenarioEventInputReceiptError, "repository_path"
        ):
            worker.validate_result(result)

    def test_blocked_result_cannot_assert_partial_receipts(self) -> None:
        result = {
            **worker._base_result(execution_sha=EXECUTION_SHA),
            "status": "blocked",
            "failure_class": "event_input_receipt_failure",
            "receipts": _valid_receipts(),
            "provider_file_bytes_read": None,
        }
        with self.assertRaisesRegex(
            worker.ScenarioEventInputReceiptError, "partial byte evidence"
        ):
            worker.validate_result(result)

    def test_prepare_result_deduplicates_before_provider_work(self) -> None:
        existing = _valid_result()
        comment = {
            "id": 123,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER
            + "\n"
            + json.dumps(existing, separators=(",", ":")),
        }

        def forbidden_acquire():
            raise AssertionError("provider must not run for a valid exact-SHA terminal")

        with mock.patch.object(worker, "_ACQUIRE", side_effect=forbidden_acquire):
            result = worker.prepare_result(
                _request_body(),
                expected_issue=285,
                execution_sha=EXECUTION_SHA,
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                comments=[comment],
            )
        self.assertEqual(
            result, {"status": "duplicate", "duplicate_result_comment_id": 123}
        )

    def test_prepare_result_blocks_without_leaking_partial_receipts(self) -> None:
        def failing_acquire():
            raise worker.ScenarioEventInputReceiptError("synthetic provider failure")

        with mock.patch.object(worker, "_ACQUIRE", side_effect=failing_acquire):
            result = worker.prepare_result(
                _request_body(),
                expected_issue=285,
                execution_sha=EXECUTION_SHA,
                repository="pokekarten/OpenCatastrophe-data",
                token="token",
                comments=[],
            )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "event_input_receipt_failure")
        self.assertIsNone(result["receipts"])
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertIs(result["output_payload_bytes_read"], False)
        self.assertIs(result["external_bytes_persisted"], False)

    def test_malformed_trusted_historical_result_blocks_ledger(self) -> None:
        comment = {
            "id": 124,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER + "\n" + '{"schema_version":"bad"}',
        }
        with self.assertRaises(worker.ScenarioEventInputReceiptError):
            worker.find_existing_terminal([comment], execution_sha=EXECUTION_SHA)

    def test_matching_terminal_does_not_short_circuit_later_trusted_validation(
        self,
    ) -> None:
        existing = _valid_result()
        matching = {
            "id": 126,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER
            + "\n"
            + json.dumps(existing, separators=(",", ":")),
        }
        malformed = {
            "id": 127,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER + "\n" + '{"schema_version":"bad"}',
        }

        with mock.patch.object(
            worker,
            "_ACQUIRE",
            side_effect=AssertionError("provider must not run before full ledger validation"),
        ) as acquire:
            with self.assertRaises(worker.ScenarioEventInputReceiptError):
                worker.prepare_result(
                    _request_body(),
                    expected_issue=285,
                    execution_sha=EXECUTION_SHA,
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    comments=[matching, malformed],
                )
        acquire.assert_not_called()

    def test_foreign_sha_valid_result_does_not_deduplicate(self) -> None:
        result = _valid_result()
        foreign = "b" * 40
        result["target_sha"] = foreign
        result["execution_sha"] = foreign
        worker.validate_result(result)
        comment = {
            "id": 125,
            "user": {"login": worker.TRUSTED_RESULT_LOGIN},
            "body": worker.RESULT_MARKER
            + "\n"
            + json.dumps(result, separators=(",", ":")),
        }
        self.assertIsNone(
            worker.find_existing_terminal([comment], execution_sha=EXECUTION_SHA)
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
