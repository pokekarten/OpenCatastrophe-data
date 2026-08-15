# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import unittest

from scripts import acquire_eshm20_first_order_receipts as authority
from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target
from scripts.validate_eq1_eshm20_first_order_receipts import (
    Eq1FirstOrderBridgeError,
    TRUSTED_EXECUTION_SHA,
    TRUSTED_RUN_ID,
    TRUSTED_SOURCE_COMMENT_ID,
    validate_and_reduce,
)


TRUSTED = (
    (
        authority.DEPENDENCIES[0],
        3_873_324,
        "d4d95f3e482a0361a90d1b0796545eaf075d0e212d66d025f975973497b29529",
        "2026-08-15T10:40:14Z",
    ),
    (
        authority.DEPENDENCIES[1],
        33_760,
        "e2c53f11174b8cd4de1f65af4dafc5af2e7a6848563e8a4c0ada44a54f22ff62",
        "2026-08-15T10:40:16Z",
    ),
    (
        authority.DEPENDENCIES[2],
        17_579,
        "97a37911f9eae73766f386686b112e5a4e111965da3e4e1543627c28d4201867",
        "2026-08-15T10:40:16Z",
    ),
)


def trusted_receipt_set() -> dict[str, object]:
    receipts = []
    for spec, byte_count, sha256, retrieved_at in TRUSTED:
        target = validate_target(
            source_issue=authority.SOURCE_ISSUE,
            dataset_id=authority.DATASET_ID,
            project_id=authority.PROJECT_ID,
            commit_sha=authority.COMMIT_SHA,
            repository_path=spec.repository_path,
        )
        url = raw_file_api_url(target)
        receipts.append(
            {
                "schema_version": "oc-efehr-gitlab-artifact-receipt-v1",
                "source_issue": authority.SOURCE_ISSUE,
                "dataset_id": authority.DATASET_ID,
                "provider_host": authority.PROVIDER_HOST,
                "project_id": authority.PROJECT_ID,
                "project_path": authority.PROJECT_PATH,
                "commit_sha": authority.COMMIT_SHA,
                "repository_path": spec.repository_path,
                "requested_url": url,
                "final_url": url,
                "retrieved_at": retrieved_at,
                "byte_count": byte_count,
                "sha256": sha256,
                "content_type": "text/plain; charset=utf-8",
                "etag": None,
                "external_bytes_persisted": False,
                "publication_authorized": False,
                "parent_result_comment_id": authority.SELECTION_RESULT_COMMENT_ID,
                "parent_section": spec.parent_section,
                "parent_option": spec.parent_option,
            }
        )
    return {
        "schema_version": authority.SCHEMA_VERSION,
        "operation_id": authority.OPERATION_ID,
        "control_issue": authority.CONTROL_ISSUE,
        "source_issue": authority.SOURCE_ISSUE,
        "dataset_id": authority.DATASET_ID,
        "provider_host": authority.PROVIDER_HOST,
        "project_id": authority.PROJECT_ID,
        "project_path": authority.PROJECT_PATH,
        "commit_sha": authority.COMMIT_SHA,
        "selection_request_comment_id": authority.SELECTION_REQUEST_COMMENT_ID,
        "selection_result_comment_id": authority.SELECTION_RESULT_COMMENT_ID,
        "selection_run_id": authority.SELECTION_RUN_ID,
        "selection_execution_sha": authority.SELECTION_EXECUTION_SHA,
        "retrieved_at": "2026-08-15T10:40:16Z",
        "receipts": receipts,
        "dependency_inventory_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def trusted_result() -> dict[str, object]:
    return {
        "schema_version": "oc-action-result-v1",
        "semantic_request_id": "e0bbfc07692e250a3f9e49314b2f7562fa6a593c4a5b821e97e80ccda171b8e7",
        "repository": "pokekarten/OpenCatastrophe-data",
        "action": "efehr_eshm20_first_order_receipts",
        "source_issue": 361,
        "source_comment_id": TRUSTED_SOURCE_COMMENT_ID,
        "target_sha": TRUSTED_EXECUTION_SHA,
        "dataset_id": authority.DATASET_ID,
        "execution_sha": TRUSTED_EXECUTION_SHA,
        "run_id": TRUSTED_RUN_ID,
        "run_attempt": 1,
        "started_at": "2026-08-15T10:40:12Z",
        "finished_at": "2026-08-15T10:40:16Z",
        "phase": "acquisition_receipt",
        "status": "pass",
        "external_bytes_persisted": False,
        "evidence": {
            "request_validated": True,
            "ledger_scan_complete": True,
            "prior_result_reused": False,
            "efehr_eshm20_first_order_receipts": trusted_receipt_set(),
        },
        "duplicate_result_comment_id": None,
        "failure_class": None,
    }


class Eq1FirstOrderReceiptBridgeTests(unittest.TestCase):
    def test_actual_trusted_pass_shape_reduces_through_unmocked_canonical_validator(self) -> None:
        reduced = validate_and_reduce(trusted_result())
        self.assertEqual(reduced["authority"]["run_id"], TRUSTED_RUN_ID)
        self.assertEqual(reduced["authority"]["execution_sha"], TRUSTED_EXECUTION_SHA)
        self.assertEqual(
            [artifact["role"] for artifact in reduced["artifacts"]],
            ["site_model", "gmm_logic_tree", "source_model_logic_tree"],
        )
        self.assertIs(reduced["dependency_closure_authorized"], False)
        self.assertIs(reduced["model_use_authorized"], False)
        self.assertNotIn("requested_url", str(reduced))
        self.assertNotIn("final_url", str(reduced))

    def test_stale_execution_and_run_identity_fail_closed(self) -> None:
        for field, value in (
            ("execution_sha", "b" * 40),
            ("target_sha", "b" * 40),
            ("run_id", TRUSTED_RUN_ID + 1),
            ("source_comment_id", TRUSTED_SOURCE_COMMENT_ID + 1),
        ):
            with self.subTest(field=field):
                result = trusted_result()
                result[field] = value
                with self.assertRaises(Eq1FirstOrderBridgeError):
                    validate_and_reduce(result)

    def test_exact_hash_and_byte_count_are_trusted_evidence_not_shape_only(self) -> None:
        for field, value in (("sha256", "1" * 64), ("byte_count", 1)):
            with self.subTest(field=field):
                result = trusted_result()
                result["evidence"]["efehr_eshm20_first_order_receipts"]["receipts"][1][field] = value
                with self.assertRaises(Eq1FirstOrderBridgeError):
                    validate_and_reduce(result)

    def test_reorder_extra_or_missing_receipt_fails_closed(self) -> None:
        mutations = []
        reordered = trusted_result()
        receipts = reordered["evidence"]["efehr_eshm20_first_order_receipts"]["receipts"]
        receipts[0], receipts[1] = receipts[1], receipts[0]
        mutations.append(reordered)

        missing = trusted_result()
        missing["evidence"]["efehr_eshm20_first_order_receipts"]["receipts"].pop()
        mutations.append(missing)

        extra = trusted_result()
        extra["evidence"]["efehr_eshm20_first_order_receipts"]["receipts"].append(
            copy.deepcopy(extra["evidence"]["efehr_eshm20_first_order_receipts"]["receipts"][-1])
        )
        mutations.append(extra)

        for result in mutations:
            with self.subTest(receipt_count=len(result["evidence"]["efehr_eshm20_first_order_receipts"]["receipts"])):
                with self.assertRaises(Eq1FirstOrderBridgeError):
                    validate_and_reduce(result)

    def test_parent_selection_drift_fails_closed(self) -> None:
        result = trusted_result()
        receipt = result["evidence"]["efehr_eshm20_first_order_receipts"]["receipts"][2]
        receipt["parent_option"] = "other"
        with self.assertRaises(Eq1FirstOrderBridgeError):
            validate_and_reduce(result)

    def test_authority_ceiling_widening_fails_closed(self) -> None:
        for location, field in (
            ("outer", "external_bytes_persisted"),
            ("set", "dependency_inventory_authorized"),
            ("set", "publication_authorized"),
            ("member", "external_bytes_persisted"),
            ("member", "publication_authorized"),
        ):
            with self.subTest(location=location, field=field):
                result = trusted_result()
                if location == "outer":
                    result[field] = True
                elif location == "set":
                    result["evidence"]["efehr_eshm20_first_order_receipts"][field] = True
                else:
                    result["evidence"]["efehr_eshm20_first_order_receipts"]["receipts"][0][field] = True
                with self.assertRaises(Eq1FirstOrderBridgeError):
                    validate_and_reduce(result)

    def test_bool_int_confusion_fails_closed(self) -> None:
        result = trusted_result()
        result["run_id"] = True
        with self.assertRaises(Eq1FirstOrderBridgeError):
            validate_and_reduce(result)

        result = trusted_result()
        result["evidence"]["efehr_eshm20_first_order_receipts"]["receipts"][0]["byte_count"] = True
        with self.assertRaises(Eq1FirstOrderBridgeError):
            validate_and_reduce(result)

    def test_canonical_validator_failure_is_not_bypassed(self) -> None:
        result = trusted_result()
        result["semantic_request_id"] = "0" * 64
        with self.assertRaises(Eq1FirstOrderBridgeError):
            validate_and_reduce(result)


if __name__ == "__main__":
    unittest.main()
