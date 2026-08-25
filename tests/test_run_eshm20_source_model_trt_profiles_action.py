# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from typing import Callable
from unittest import mock

from scripts import run_eshm20_source_model_trt_profiles_action as subject

EXECUTION_SHA = "1" * 40
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "eshm20-source-model-trt-profiles.yml"
)


class FakeResponse:
    def __init__(self, url: str, payload: bytes):
        self.status = 200
        self._url = url
        self._payload = payload
        self._offset = 0
        self.headers = {
            "Content-Type": "application/xml",
            "Content-Length": str(len(payload)),
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


class MappingOpener:
    def __init__(self, payloads: dict[str, bytes]):
        self.payloads = payloads
        self.calls: list[str] = []

    def __call__(self, request, timeout: float):
        self.calls.append(request.full_url)
        for path, payload in self.payloads.items():
            if subject._raw_url(path) == request.full_url:
                return FakeResponse(request.full_url, payload)
        raise AssertionError("unexpected provider URL")


def request_body(sha: str = EXECUTION_SHA) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )


def synthetic_receipt_comment(
    *,
    mutate: Callable[[dict], None] | None = None,
) -> dict:
    payload = b"x"
    identity_sha = hashlib.sha256(payload).hexdigest()
    receipts = [
        {
            "byte_count": len(payload),
            "commit_sha": subject.COMMIT_SHA,
            "external_bytes_persisted": False,
            "model_use_authorized": False,
            "parent_result_comment_id": subject.CHILD_PARENT_RESULT_COMMENT_ID,
            "project_id": subject.PROJECT_ID,
            "project_path": subject.PROJECT_PATH,
            "publication_authorized": False,
            "repository_path": path,
            "retrieved_at": "2026-08-16T10:09:01Z",
            "sha256": identity_sha,
        }
        for path in subject._canonical_paths()
    ]
    result = {
        "schema_version": "oc-action-result-v1",
        "action": "efehr_eshm20_source_model_child_receipts",
        "dataset_id": subject.DATASET_ID,
        "execution_sha": subject.RECEIPT_RESULT_EXECUTION_SHA,
        "target_sha": subject.RECEIPT_RESULT_EXECUTION_SHA,
        "run_id": subject.RECEIPT_RESULT_RUN_ID,
        "source_issue": subject.RECEIPT_ISSUE,
        "repository": subject.REPOSITORY,
        "status": "pass",
        "failure_class": None,
        "external_bytes_persisted": False,
        "evidence": {
            "ledger_scan_complete": True,
            "prior_result_reused": False,
            "request_validated": True,
            "efehr_eshm20_source_model_child_receipts": {
                "schema_version": "oc-eshm20-source-model-child-receipt-set-v1",
                "operation_id": (
                    "eshm20-source-model-child-receipts-v12e-region-main-v1"
                ),
                "source_issue": subject.SOURCE_ISSUE,
                "control_issue": subject.RECEIPT_ISSUE,
                "dataset_id": subject.DATASET_ID,
                "provider_host": subject.PROVIDER_HOST,
                "project_id": subject.PROJECT_ID,
                "project_path": subject.PROJECT_PATH,
                "commit_sha": subject.COMMIT_SHA,
                "child_count": subject.EXPECTED_CHILD_COUNT,
                "child_paths_sha256": subject.EXPECTED_PATHS_SHA256,
                "dependency_inventory_authorized": False,
                "dependency_receipt_authorized": False,
                "external_bytes_persisted": False,
                "publication_authorized": False,
                "model_use_authorized": False,
                "receipts": receipts,
            },
        },
    }
    comment = {
        "id": subject.RECEIPT_RESULT_COMMENT_ID,
        "user": {"login": subject.TRUSTED_RESULT_LOGIN},
        "body": subject.ACTION_RESULT_MARKER
        + "\n"
        + json.dumps(result, sort_keys=True, separators=(",", ":")),
    }
    if mutate is not None:
        mutate(comment)
    return comment


def pure_aggregate() -> dict:
    count = subject.EXPECTED_CHILD_COUNT
    return {
        "schema_version": subject.profiler.AGGREGATE_SCHEMA_VERSION,
        "source_issue": subject.SOURCE_ISSUE,
        "control_issue": subject.profiler.CONTROL_ISSUE,
        "dataset_id": subject.DATASET_ID,
        "child_count": subject.EXPECTED_CHILD_COUNT,
        "child_paths_sha256": subject.EXPECTED_PATHS_SHA256,
        "source_count": count,
        "source_type_counts": {"pointSource": count},
        "tectonic_region_type_counts": {"Active Shallow Crust": count},
        "trt_provenance_counts": {"direct_source": count},
        "unique_source_types": ["pointSource"],
        "unique_tectonic_region_types": ["Active Shallow Crust"],
        "receipt_set_locator": {
            "result_comment_id": subject.RECEIPT_RESULT_COMMENT_ID,
            "run_id": subject.RECEIPT_RESULT_RUN_ID,
            "execution_sha": subject.RECEIPT_RESULT_EXECUTION_SHA,
            "provider_commit": subject.COMMIT_SHA,
        },
        "receipt_payload_identities_verified": True,
        "canonical_414_ledger_binding_verified": False,
        "source_structure_profile_verified": True,
        "source_physics_validity_verified": False,
        "source_gsim_trt_compatibility_verified": False,
        "branch_weight_validity_verified": False,
        "numerical_hazard_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def pass_result() -> dict:
    profile = pure_aggregate()
    profile["canonical_414_ledger_binding_verified"] = True
    return {
        **subject._base_result(execution_sha=EXECUTION_SHA),
        "status": "pass",
        "failure_class": None,
        "aggregate_profile": profile,
        "provider_file_bytes_read": True,
        "raw_xml_returned": False,
        "canonical_414_ledger_binding_verified": True,
    }


class Eshm20SourceModelTrtActionTests(unittest.TestCase):
    def test_fixed_contract_matches_exact_51_project197_authority(self) -> None:
        subject._assert_fixed_contract()
        self.assertEqual(len(subject._canonical_paths()), 51)
        self.assertEqual(
            subject.profiler.RECEIPT_SET_RESULT_COMMENT_ID,
            5306897047,
        )
        self.assertEqual(
            subject.profiler.RECEIPT_SET_EXECUTION_SHA,
            "473f03765fd63d2da7e48d0c22b1618d4e1254d8",
        )

    def test_request_is_exact_head_bound_and_duplicate_keys_fail(self) -> None:
        parsed = subject.validate_request(
            request_body(),
            expected_issue=subject.SOURCE_ISSUE,
            execution_sha=EXECUTION_SHA,
        )
        self.assertEqual(parsed["target_sha"], EXECUTION_SHA)
        with self.assertRaises(subject.Eshm20SourceModelTrtActionError):
            subject.validate_request(
                request_body("2" * 40),
                expected_issue=subject.SOURCE_ISSUE,
                execution_sha=EXECUTION_SHA,
            )
        duplicate = (
            subject.REQUEST_MARKER
            + '\n{"schema_version":"'
            + subject.REQUEST_SCHEMA_VERSION
            + '","schema_version":"'
            + subject.REQUEST_SCHEMA_VERSION
            + '","action":"'
            + subject.ACTION
            + '","issue":281,"target_sha":"'
            + EXECUTION_SHA
            + '","dataset_id":"'
            + subject.DATASET_ID
            + '","requester":"unit-test"}'
        )
        with self.assertRaises(subject.Eshm20SourceModelTrtActionError):
            subject.validate_request(
                duplicate,
                expected_issue=subject.SOURCE_ISSUE,
                execution_sha=EXECUTION_SHA,
            )

    def test_canonical_ledger_parser_builds_only_exact_51_receipts(self) -> None:
        receipts = subject._parse_canonical_receipt_comment(
            synthetic_receipt_comment()
        )
        self.assertEqual(len(receipts), subject.EXPECTED_CHILD_COUNT)
        self.assertEqual(
            tuple(item.repository_path for item in receipts),
            subject._canonical_paths(),
        )
        self.assertTrue(
            all(type(item.byte_count) is int for item in receipts)
        )

    def test_canonical_ledger_parser_rejects_wrong_author_and_float_count(self) -> None:
        wrong_author = synthetic_receipt_comment(
            mutate=lambda comment: comment["user"].update({"login": "owner"})
        )
        with self.assertRaisesRegex(
            subject.Eshm20SourceModelTrtActionError,
            "trusted GitHub Actions",
        ):
            subject._parse_canonical_receipt_comment(wrong_author)

        def mutate_count(comment: dict) -> None:
            result = json.loads(
                comment["body"].split(subject.ACTION_RESULT_MARKER, 1)[1]
            )
            result["evidence"][
                "efehr_eshm20_source_model_child_receipts"
            ]["receipts"][0]["byte_count"] = 1.0
            comment["body"] = (
                subject.ACTION_RESULT_MARKER
                + "\n"
                + json.dumps(result, sort_keys=True, separators=(",", ":"))
            )

        with self.assertRaisesRegex(
            subject.Eshm20SourceModelTrtActionError,
            "byte count",
        ):
            subject._parse_canonical_receipt_comment(
                synthetic_receipt_comment(mutate=mutate_count)
            )

    def test_canonical_ledger_parser_rejects_duplicate_or_foreign_path(self) -> None:
        def duplicate_path(comment: dict) -> None:
            result = json.loads(
                comment["body"].split(subject.ACTION_RESULT_MARKER, 1)[1]
            )
            receipts = result["evidence"][
                "efehr_eshm20_source_model_child_receipts"
            ]["receipts"]
            receipts[1]["repository_path"] = receipts[0]["repository_path"]
            comment["body"] = (
                subject.ACTION_RESULT_MARKER
                + "\n"
                + json.dumps(result, sort_keys=True, separators=(",", ":"))
            )

        with self.assertRaises(subject.Eshm20SourceModelTrtActionError):
            subject._parse_canonical_receipt_comment(
                synthetic_receipt_comment(mutate=duplicate_path)
            )

        def foreign_path(comment: dict) -> None:
            result = json.loads(
                comment["body"].split(subject.ACTION_RESULT_MARKER, 1)[1]
            )
            result["evidence"][
                "efehr_eshm20_source_model_child_receipts"
            ]["receipts"][0]["repository_path"] = "../../foreign.xml"
            comment["body"] = (
                subject.ACTION_RESULT_MARKER
                + "\n"
                + json.dumps(result, sort_keys=True, separators=(",", ":"))
            )

        with self.assertRaisesRegex(
            subject.Eshm20SourceModelTrtActionError,
            "outside exact 51",
        ):
            subject._parse_canonical_receipt_comment(
                synthetic_receipt_comment(mutate=foreign_path)
            )

    def test_provider_payload_is_verified_against_receipt(self) -> None:
        path = subject._canonical_paths()[0]
        payload = b"<nrml/>"
        receipt = subject.profiler.ExpectedChildReceipt(
            repository_path=path,
            byte_count=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
        )
        observed = subject._fetch_verified_payload(
            receipt,
            deadline=10.0,
            opener=MappingOpener({path: payload}),
            monotonic=lambda: 0.0,
        )
        self.assertEqual(observed, payload)

        bad = subject.profiler.ExpectedChildReceipt(
            repository_path=path,
            byte_count=len(payload),
            sha256=hashlib.sha256(b"different").hexdigest(),
        )
        with self.assertRaisesRegex(
            subject.Eshm20SourceModelTrtActionError,
            "SHA-256",
        ):
            subject._fetch_verified_payload(
                bad,
                deadline=10.0,
                opener=MappingOpener({path: payload}),
                monotonic=lambda: 0.0,
            )

    def test_composition_promotes_only_canonical_ledger_binding(self) -> None:
        payload = b"x"
        receipts = subject._parse_canonical_receipt_comment(
            synthetic_receipt_comment()
        )
        payloads = {
            item.repository_path: payload
            for item in receipts
        }
        called = False

        def aggregate(pairs):
            nonlocal called
            called = True
            observed = list(pairs)
            self.assertEqual(len(observed), subject.EXPECTED_CHILD_COUNT)
            for observed_payload, receipt in observed:
                self.assertEqual(observed_payload, payload)
                self.assertEqual(
                    hashlib.sha256(observed_payload).hexdigest(),
                    receipt.sha256,
                )
            return pure_aggregate()

        result = subject._acquire_bound_aggregate(
            receipts,
            opener=MappingOpener(payloads),
            monotonic=lambda: 0.0,
            aggregate=aggregate,
        )
        self.assertTrue(called)
        self.assertTrue(result["canonical_414_ledger_binding_verified"])
        self.assertTrue(result["receipt_payload_identities_verified"])
        self.assertFalse(result["source_gsim_trt_compatibility_verified"])
        self.assertFalse(result["numerical_hazard_reproduction_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_pure_profiler_cannot_preclaim_ledger_binding(self) -> None:
        receipts = subject._parse_canonical_receipt_comment(
            synthetic_receipt_comment()
        )

        def aggregate(pairs):
            list(pairs)
            result = pure_aggregate()
            result["canonical_414_ledger_binding_verified"] = True
            return result

        with self.assertRaisesRegex(
            subject.Eshm20SourceModelTrtActionError,
            "unexpectedly widened",
        ):
            subject._acquire_bound_aggregate(
                receipts,
                opener=MappingOpener(
                    {item.repository_path: b"x" for item in receipts}
                ),
                monotonic=lambda: 0.0,
                aggregate=aggregate,
            )

    def test_execute_pass_blocked_and_duplicate_remain_fail_closed(self) -> None:
        with (
            mock.patch.object(subject, "has_terminal_result", return_value=False),
            mock.patch.object(
                subject,
                "acquire_bound_aggregate",
                return_value=pass_result()["aggregate_profile"],
            ),
        ):
            result = subject.execute(
                repository=subject.REPOSITORY,
                token="token",
                execution_sha=EXECUTION_SHA,
            )
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["canonical_414_ledger_binding_verified"])
        self.assertFalse(result["source_gsim_trt_compatibility_verified"])

        with (
            mock.patch.object(subject, "has_terminal_result", return_value=False),
            mock.patch.object(
                subject,
                "acquire_bound_aggregate",
                side_effect=subject.Eshm20SourceModelTrtActionError("blocked"),
            ),
        ):
            result = subject.execute(
                repository=subject.REPOSITORY,
                token="token",
                execution_sha=EXECUTION_SHA,
            )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["aggregate_profile"])
        self.assertFalse(result["canonical_414_ledger_binding_verified"])

        with (
            mock.patch.object(subject, "has_terminal_result", return_value=True),
            mock.patch.object(subject, "acquire_bound_aggregate") as acquire,
        ):
            result = subject.execute(
                repository=subject.REPOSITORY,
                token="token",
                execution_sha=EXECUTION_SHA,
            )
        self.assertEqual(result["status"], "duplicate")
        acquire.assert_not_called()

    def test_terminal_result_rejects_authority_widening(self) -> None:
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            pass_result(),
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertTrue(
            subject.parse_terminal_result(body, execution_sha=EXECUTION_SHA)
        )
        widened = pass_result()
        widened["publication_authorized"] = True
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            widened,
            sort_keys=True,
            separators=(",", ":"),
        )
        with self.assertRaises(subject.Eshm20SourceModelTrtActionError):
            subject.parse_terminal_result(body, execution_sha=EXECUTION_SHA)

    def test_contract_mutation_fails_before_provider_work(self) -> None:
        with mock.patch.object(subject.profiler, "COMMIT_SHA", "0" * 40):
            with self.assertRaisesRegex(
                subject.Eshm20SourceModelTrtActionError,
                "provider commit",
            ):
                subject._assert_fixed_contract()

    def test_workflow_is_default_branch_only_and_publisher_has_no_checkout(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("issue_comment:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn(
            "ref: ${{ github.event.repository.default_branch }}",
            workflow,
        )
        publish = workflow.split("publish-profile:", 1)[1]
        self.assertNotIn("actions/checkout", publish)
        self.assertIn(
            "canonical_414_ledger_binding_verified == true",
            publish,
        )


if __name__ == "__main__":
    unittest.main()
