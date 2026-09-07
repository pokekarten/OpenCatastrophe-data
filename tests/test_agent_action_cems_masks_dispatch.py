# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
from pathlib import Path
import unittest
from unittest import mock

from scripts import acquire_cems_europe_mask_receipts as worker
from scripts import agent_action_protocol_cems_masks as protocol
from scripts import prepare_agent_action_result_cems_masks as prepare
from scripts import validate_agent_action_request_cems_masks as request_validator
from scripts import validate_agent_action_result_cems_masks as result_validator

MAIN_SHA = "a" * 40
REPOSITORY = "pokekarten/OpenCatastrophe-data"
STARTED_AT = "2026-09-06T18:30:00Z"
RETRIEVED_AT = "2026-09-06T18:31:00Z"
FINISHED_AT = "2026-09-06T18:32:00Z"


def _request(**overrides):
    value = {
        "schema_version": request_validator.SCHEMA_VERSION,
        "action": request_validator.CEMS_MASK_RECEIPTS_ACTION,
        "issue": 809,
        "target_sha": MAIN_SHA,
        "dataset_id": request_validator.CEMS_MASK_RECEIPTS_DATASET_ID,
        "requester": "pokekarten",
    }
    value.update(overrides)
    return value


def _aggregate():
    receipts = []
    for index, (kind, filename) in enumerate(worker.ASSETS, start=1):
        url = worker.BASE_URL + filename
        receipts.append({
            "schema_version": worker.RECEIPT_SCHEMA_VERSION,
            "dataset_id": worker.DATASET_ID,
            "source_issue": 809,
            "release": worker.RELEASE,
            "release_date": worker.RELEASE_DATE,
            "doi": worker.DOI,
            "mask_kind": kind,
            "filename": filename,
            "requested_url": url,
            "final_url": url,
            "retrieved_at": RETRIEVED_AT,
            "http_status": 200,
            "media_type": "image/tiff",
            "content_length_header": 100 + index,
            "byte_count": 100 + index,
            "sha256": str(index) * 64,
            "external_bytes_persisted": False,
            "geotiff_semantics_verified": False,
            "mask_values_inspected": False,
            "benchmark_use_authorized": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        })
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "dataset_id": worker.DATASET_ID,
        "source_issue": 809,
        "release": worker.RELEASE,
        "receipts": receipts,
        "external_bytes_persisted": False,
        "geotiff_semantics_verified": False,
        "mask_values_inspected": False,
        "benchmark_use_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _run(*, comments=None, mask_acquirer=None):
    validated = request_validator.validate_request(_request(), expected_issue=809)
    with mock.patch.object(prepare._base, "utc_now", return_value=FINISHED_AT):
        return prepare.prepare_completed_result(
            validated,
            comments or [],
            repository=REPOSITORY,
            execution_sha=MAIN_SHA,
            source_comment_id=1,
            run_id=2,
            run_attempt=1,
            started_at=STARTED_AT,
            mask_acquirer=mask_acquirer or _aggregate,
        )


class CemsMaskDispatchTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_exact_execution_sha(self) -> None:
        request = _request()
        self.assertIs(request_validator.validate_request(request, expected_issue=809), request)
        self.assertIn(request["action"], protocol.NETWORK_ACQUISITION_ACTIONS)
        self.assertIn(request["action"], prepare.NETWORK_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(request), 809)
        for selector in ("url", "filename", "mask", "provider", "reader", "parser"):
            selected = _request()
            selected[selector] = "forbidden"
            with self.subTest(selector=selector), self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(selected, expected_issue=809)
        with self.assertRaises(protocol.ProtocolError):
            protocol.semantic_request_id(_request(target_sha="0" * 40), MAIN_SHA, REPOSITORY)

    def test_aggregate_receipt_is_fixed_order_and_authority_closed(self) -> None:
        receipt = _aggregate()
        self.assertIs(result_validator.validate_cems_mask_receipts(receipt), receipt)
        reversed_receipt = copy.deepcopy(receipt)
        reversed_receipt["receipts"].reverse()
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_mask_receipts(reversed_receipt)
        tampered = copy.deepcopy(receipt)
        tampered["receipts"][0]["mask_values_inspected"] = True
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_cems_mask_receipts(tampered)

    def test_success_revalidates_and_dedup_stops_before_worker(self) -> None:
        first = _run()
        self.assertEqual(first["status"], "pass")
        self.assertIs(result_validator.validate_result(first), first)
        aggregate = first["evidence"][prepare.CEMS_MASK_RECEIPTS_FIELD]
        self.assertEqual([x["mask_kind"] for x in aggregate["receipts"]], ["permanent_water", "spurious_depth"])
        self.assertFalse(aggregate["external_bytes_persisted"])
        self.assertFalse(aggregate["mask_values_inspected"])

        prior = {
            "id": 900,
            "user": {"login": "github-actions[bot]"},
            "body": protocol.canonical_result_comment(first),
        }
        acquirer = mock.Mock(return_value=_aggregate())
        duplicate = _run(comments=[prior], mask_acquirer=acquirer)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 900)
        acquirer.assert_not_called()

    def test_worker_failure_is_closed(self) -> None:
        def fail():
            raise RuntimeError("provider detail must not persist")
        result = _run(mask_acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["evidence"][prepare.CEMS_MASK_RECEIPTS_FIELD])
        self.assertIs(result_validator.validate_result(result), result)

    def test_shared_dispatcher_uses_mask_aware_entrypoints_and_retains_legacy_breadcrumbs(self) -> None:
        text = Path(".github/workflows/agent-action-dispatch.yml").read_text(encoding="utf-8")
        self.assertIn("python -m scripts.prepare_agent_action_result_cems_masks", text)
        self.assertIn("python -m scripts.post_agent_action_result_cems_masks", text)
        for legacy in (
            "prepare_agent_action_result_cems_rp10.py",
            "post_agent_action_result_cems_rp10.py",
            "prepare_agent_action_result_country_risk.py",
            "post_agent_action_result_country_risk.py",
        ):
            self.assertIn(legacy, text)
        self.assertEqual(text.count("issue_comment:"), 1)


if __name__ == "__main__":
    unittest.main()
