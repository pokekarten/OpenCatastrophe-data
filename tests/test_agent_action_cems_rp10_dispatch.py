# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from contextlib import redirect_stderr
import copy
import io
from pathlib import Path
import unittest
import urllib.error
from unittest import mock

from scripts import acquire_cems_europe_rp10_receipt as cems
from scripts import agent_action_protocol_cems_rp10 as protocol
from scripts import prepare_agent_action_result_cems_rp10 as prepare
from scripts import validate_agent_action_request_cems_rp10 as request_validator
from scripts import validate_agent_action_result_cems_rp10 as result_validator

MAIN_SHA = "a" * 40
REPOSITORY = "pokekarten/OpenCatastrophe-data"
STARTED_AT = "2026-09-05T13:19:00Z"
RETRIEVED_AT = "2026-09-05T13:20:00Z"
FINISHED_AT = "2026-09-05T13:21:00Z"
BYTE_COUNT = 260_000_000
SHA256 = "1" * 64


def _request(**overrides):
    value = {
        "schema_version": request_validator.SCHEMA_VERSION,
        "action": request_validator.CEMS_RP10_RECEIPT_ACTION,
        "issue": 793,
        "target_sha": MAIN_SHA,
        "dataset_id": request_validator.CEMS_RP10_RECEIPT_DATASET_ID,
        "requester": "pokekarten",
    }
    value.update(overrides)
    return value


def _receipt(**overrides):
    value = {
        "schema_version": cems.SCHEMA_VERSION,
        "dataset_id": cems.DATASET_ID,
        "source_issue": cems.SOURCE_ISSUE,
        "release": cems.RELEASE,
        "release_date": cems.RELEASE_DATE,
        "doi": cems.DOI,
        "return_period_years": cems.RETURN_PERIOD_YEARS,
        "filename": cems.FILENAME,
        "requested_url": cems.SOURCE_URL,
        "final_url": cems.SOURCE_URL,
        "retrieved_at": RETRIEVED_AT,
        "http_status": 200,
        "media_type": "image/tiff",
        "content_length_header": BYTE_COUNT,
        "byte_count": BYTE_COUNT,
        "sha256": SHA256,
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    value.update(overrides)
    return value


def _run(*, comments=None, cems_acquirer=None, request=None):
    validated = request_validator.validate_request(
        request or _request(), expected_issue=793
    )
    kwargs = {
        "repository": REPOSITORY,
        "execution_sha": MAIN_SHA,
        "source_comment_id": 1,
        "run_id": 2,
        "run_attempt": 1,
        "started_at": STARTED_AT,
        "cems_acquirer": cems_acquirer or _receipt,
    }
    with mock.patch.object(prepare._base, "utc_now", return_value=FINISHED_AT):
        return prepare.prepare_completed_result(validated, comments or [], **kwargs)


class CemsRp10RequestTests(unittest.TestCase):
    def test_fixed_request_contract_and_network_identity(self) -> None:
        request = _request()
        self.assertIs(
            request_validator.validate_request(request, expected_issue=793), request
        )
        self.assertIn(request["action"], request_validator.ALLOWED_ACTIONS)
        self.assertIn(request["action"], protocol.NETWORK_ACQUISITION_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(request), 793)

        for mutation in (
            {"issue": 792},
            {"issue": 793.0},
            {"issue": True},
            {"dataset_id": "other-dataset"},
            {"target_sha": "v3.1.1"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(
                request_validator.RequestError
            ):
                request_validator.validate_request(
                    _request(**mutation), expected_issue=793
                )

        with self.assertRaises(request_validator.RequestError):
            request_validator.validate_request(_request(), expected_issue=793.0)

        for selector in ("url", "filename", "return_period_years", "provider"):
            selected = _request()
            selected[selector] = "forbidden"
            with self.subTest(selector=selector), self.assertRaises(
                request_validator.RequestError
            ):
                request_validator.validate_request(selected, expected_issue=793)

        with self.assertRaises(protocol.ProtocolError):
            protocol.semantic_request_id(
                _request(target_sha="0" * 40), MAIN_SHA, REPOSITORY
            )

    def test_existing_country_risk_action_still_delegates(self) -> None:
        legacy = request_validator._legacy
        request = {
            "schema_version": legacy.SCHEMA_VERSION,
            "action": legacy.ESRM20_COUNTRY_RISK_RECEIPT_ACTION,
            "issue": legacy.ESRM20_COUNTRY_RISK_RECEIPT_ISSUE,
            "target_sha": MAIN_SHA,
            "dataset_id": legacy.ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID,
            "requester": "pokekarten",
        }
        self.assertIs(
            request_validator.validate_request(
                request, expected_issue=legacy.ESRM20_COUNTRY_RISK_RECEIPT_ISSUE
            ),
            request,
        )
        self.assertIn(request["action"], prepare.NETWORK_ACTIONS)


class CemsRp10ResultTests(unittest.TestCase):
    def test_receipt_contract_keeps_authority_ceiling_closed(self) -> None:
        receipt = _receipt()
        self.assertIs(result_validator.validate_cems_rp10_receipt(receipt), receipt)

        for field in (
            "external_bytes_persisted",
            "geotiff_semantics_verified",
            "benchmark_use_authorized",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field), self.assertRaises(
                result_validator.ResultError
            ):
                result_validator.validate_cems_rp10_receipt(
                    _receipt(**{field: True})
                )

        for mutation in (
            {"final_url": "https://example.com/other.tif"},
            {"return_period_years": 100},
            {"media_type": "text/html"},
            {"content_length_header": BYTE_COUNT + 1},
            {"sha256": "0" * 63},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(
                result_validator.ResultError
            ):
                result_validator.validate_cems_rp10_receipt(_receipt(**mutation))

    def test_success_is_receipt_only_and_revalidates_after_dispatch(self) -> None:
        result = _run()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["phase"], "acquisition_receipt")
        receipt = result["evidence"][prepare.CEMS_RP10_RECEIPT_FIELD]
        self.assertEqual(receipt["sha256"], SHA256)
        self.assertFalse(receipt["external_bytes_persisted"])
        self.assertFalse(receipt["geotiff_semantics_verified"])
        self.assertFalse(receipt["benchmark_use_authorized"])
        self.assertFalse(receipt["publication_authorized"])
        self.assertFalse(receipt["model_use_authorized"])
        self.assertNotIn("payload", result)
        self.assertNotIn("values", result)
        self.assertIs(result_validator.validate_result(result), result)

        drifted = copy.deepcopy(result)
        drifted["evidence"][prepare.CEMS_RP10_RECEIPT_FIELD][
            "geotiff_semantics_verified"
        ] = True
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_result(drifted)

        drifted = copy.deepcopy(result)
        drifted["execution_sha"] = "0" * 40
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_result(drifted)

    def test_worker_and_receipt_failures_publish_only_blocked_state(self) -> None:
        def blocked_worker():
            raise cems.CemsRp10ReceiptError("provider detail must not escape")

        result = _run(cems_acquirer=blocked_worker)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], prepare.ACQUISITION_FAILURE_CLASS)
        self.assertIsNone(result["evidence"][prepare.CEMS_RP10_RECEIPT_FIELD])

        result = _run(
            cems_acquirer=lambda: _receipt(geotiff_semantics_verified=True)
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["evidence"][prepare.CEMS_RP10_RECEIPT_FIELD])

    def test_closed_failure_stage_is_bounded_and_hides_provider_detail(self) -> None:
        cases = (
            ("trusted CEMS DNS resolution failed", "dns"),
            ("CEMS response media type is outside the fixed contract", "response_contract"),
            ("CEMS RP10 payload does not have a TIFF/BigTIFF signature", "payload_contract"),
            ("CEMS RP10 acquisition exceeded total deadline", "deadline"),
            ("provider detail must not escape", "unknown"),
        )
        for message, expected in cases:
            with self.subTest(message=message):
                self.assertEqual(
                    prepare._closed_cems_failure_stage(cems.CemsRp10ReceiptError(message)),
                    expected,
                )

        wrapped_http = cems.CemsRp10ReceiptError("CEMS RP10 acquisition failed")
        wrapped_http.__cause__ = urllib.error.HTTPError(
            cems.SOURCE_URL, 403, "Forbidden", None, None
        )
        self.assertEqual(
            prepare._closed_cems_failure_stage(wrapped_http), "response_contract"
        )
        self.assertEqual(
            prepare._closed_cems_failure_stage(
                cems.CemsRp10ReceiptError("CEMS RP10 acquisition failed")
            ),
            "transport",
        )

        def blocked_worker():
            raise cems.CemsRp10ReceiptError("provider detail must not escape")

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = _run(cems_acquirer=blocked_worker)
        diagnostic = stderr.getvalue()
        self.assertEqual(result["status"], "blocked")
        self.assertIn("CEMS_RP10_FAILURE_STAGE=unknown", diagnostic)
        self.assertNotIn("provider detail must not escape", diagnostic)

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = _run(
                cems_acquirer=lambda: _receipt(geotiff_semantics_verified=True)
            )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("CEMS_RP10_FAILURE_STAGE=receipt_validation", stderr.getvalue())

    def test_complete_ledger_dedup_stops_before_provider_worker(self) -> None:
        first = _run()
        prior = {
            "id": 900,
            "user": {"login": "github-actions[bot]"},
            "body": protocol.canonical_result_comment(first),
        }
        worker = mock.Mock(return_value=_receipt())
        duplicate = _run(comments=[prior], cems_acquirer=worker)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["phase"], "request_validation")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 900)
        worker.assert_not_called()


class CemsRp10WorkflowTests(unittest.TestCase):
    def test_shared_dispatcher_uses_cems_aware_entrypoints(self) -> None:
        text = Path(".github/workflows/agent-action-dispatch.yml").read_text(
            encoding="utf-8"
        )
        validate_job = text.split("  report-result:", 1)[0]
        self.assertIn("prepare_agent_action_result_cems_rp10.py", text)
        self.assertIn("post_agent_action_result_cems_rp10.py", text)
        self.assertIn(
            "python -m scripts.prepare_agent_action_result_cems_rp10", text
        )
        self.assertIn("python -m scripts.post_agent_action_result_cems_rp10", text)
        self.assertNotIn(
            "python scripts/prepare_agent_action_result_cems_rp10.py", text
        )
        self.assertNotIn("python scripts/post_agent_action_result_cems_rp10.py", text)
        self.assertIn("timeout-minutes: 15", validate_job)
        self.assertEqual(validate_job.count("timeout-minutes: 15"), 1)
        self.assertIn(request_validator.CEMS_RP10_RECEIPT_ACTION, prepare.NETWORK_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(_request()), 793)
        self.assertEqual(text.count("issue_comment:"), 1)


if __name__ == "__main__":
    unittest.main()
