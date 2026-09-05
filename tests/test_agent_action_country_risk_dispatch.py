# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

from scripts import agent_action_protocol_country_risk as protocol
from scripts import prepare_agent_action_result_country_risk as prepare
from scripts import profile_esrm20_country_risk_schema as schema_profiler
from scripts import validate_agent_action_request_country_risk as request_validator
from scripts import validate_agent_action_result_country_risk as result_validator

MAIN_SHA = "a" * 40
REPOSITORY = "pokekarten/OpenCatastrophe-data"
COUNTRY_BYTES = b"Country,Loss\nAL,1\n"
COUNTRY_SHA256 = hashlib.sha256(COUNTRY_BYTES).hexdigest()
COUNTRY_GIT_SHA1 = hashlib.sha1(
    f"blob {len(COUNTRY_BYTES)}\0".encode("ascii") + COUNTRY_BYTES,
    usedforsecurity=False,
).hexdigest()
STARTED_AT = "2026-09-05T09:00:00Z"
FINISHED_AT = "2026-09-05T09:01:00Z"
RETRIEVED_AT = "2026-09-05T09:00:30Z"


def _request(**overrides):
    value = {
        "schema_version": request_validator.SCHEMA_VERSION,
        "action": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ACTION,
        "issue": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ISSUE,
        "target_sha": MAIN_SHA,
        "dataset_id": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID,
        "requester": "pokekarten",
    }
    value.update(overrides)
    return value


def _tree_profile(**overrides):
    value = {
        "schema_version": result_validator.RISK_TREE_PROFILE_SCHEMA_VERSION,
        "dataset_id": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID,
        "source_issue": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ISSUE,
        "project_id": 278,
        "project_path": "EFEHR/ESRM20",
        "release_tag": "v1.0",
        "commit_sha": "0f2980097a62f62f1c8a11f93e2e801d70ad05d4",
        "risk_tree_sha1": "b" * 40,
        "risk_entry_count": 1,
        "risk_blob_count": 1,
        "risk_tree_count": 0,
        "country_risk_path": "Risk/European_Risk_Country.csv",
        "country_risk_path_status": "blob",
        "country_risk_path_entry": {
            "path": "Risk/European_Risk_Country.csv",
            "type": "blob",
            "object_sha1": COUNTRY_GIT_SHA1,
            "mode": "100644",
        },
        "external_bytes_persisted": False,
        "provider_file_bytes_read": False,
        "country_risk_file_profiled": False,
        "country_risk_schema_profiled": False,
        "country_risk_numeric_values_exposed": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    value.update(overrides)
    return value


def _receipt(**overrides):
    value = {
        "schema_version": result_validator.COUNTRY_RISK_RECEIPT_SCHEMA_VERSION,
        "operation_id": "esrm20_country_risk_receipt",
        "source_issue": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ISSUE,
        "dataset_id": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID,
        "project_id": 278,
        "project_path": "EFEHR/ESRM20",
        "release_tag": "v1.0",
        "commit_sha": "0f2980097a62f62f1c8a11f93e2e801d70ad05d4",
        "repository_path": "Risk/European_Risk_Country.csv",
        "requested_url": "https://gitlab.seismo.ethz.ch/efehr/esrm20/-/raw/0f2980097a62f62f1c8a11f93e2e801d70ad05d4/Risk/European_Risk_Country.csv",
        "final_url": "https://gitlab.seismo.ethz.ch/efehr/esrm20/-/raw/0f2980097a62f62f1c8a11f93e2e801d70ad05d4/Risk/European_Risk_Country.csv",
        "retrieved_at": RETRIEVED_AT,
        "http_status": 200,
        "media_type": "text/plain",
        "content_length_header": len(COUNTRY_BYTES),
        "byte_count": len(COUNTRY_BYTES),
        "sha256": COUNTRY_SHA256,
        "external_bytes_persisted": False,
        "provider_rows_exposed": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    value.update(overrides)
    return value


def _schema_profile(**overrides):
    value = {
        "schema_version": result_validator.COUNTRY_RISK_SCHEMA_PROFILE_SCHEMA_VERSION,
        "dataset_id": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_DATASET_ID,
        "source_issue": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ISSUE,
        "repository_path": "Risk/European_Risk_Country.csv",
        "byte_count": len(COUNTRY_BYTES),
        "sha256": COUNTRY_SHA256,
        "encoding": "utf-8",
        "line_ending": "lf",
        "header": ["Country", "Loss"],
        "column_count": 2,
        "row_count": 1,
        "duplicate_headers": [],
        "blank_headers": [],
        "rows_have_uniform_column_count": True,
        "trusted_source_receipt_bound": False,
        "numeric_values_exposed": False,
        "external_bytes_persisted": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    value.update(overrides)
    return value


def _run_request(
    *,
    comments=None,
    tree_profiler=None,
    country_acquirer=None,
    schema_profiler=None,
):
    request = request_validator.validate_request(_request(), expected_issue=778)
    kwargs = {
        "repository": REPOSITORY,
        "execution_sha": MAIN_SHA,
        "source_comment_id": 1,
        "run_id": 2,
        "run_attempt": 1,
        "started_at": STARTED_AT,
        "risk_tree_profiler": tree_profiler or _tree_profile,
        "country_risk_acquirer": country_acquirer or (lambda: (_receipt(), COUNTRY_BYTES)),
        "schema_profiler": schema_profiler
        or (
            lambda payload, *, expected_sha256, expected_byte_count: _schema_profile(
                sha256=expected_sha256,
                byte_count=expected_byte_count,
            )
        ),
    }
    with mock.patch.object(prepare._legacy, "utc_now", return_value=FINISHED_AT):
        return prepare.prepare_completed_result(request, comments or [], **kwargs)


class CountryRiskRequestTests(unittest.TestCase):
    def test_fixed_request_contract_and_network_identity(self) -> None:
        request = _request()
        self.assertIs(request_validator.validate_request(request, expected_issue=778), request)
        self.assertIn(request["action"], request_validator.ALLOWED_ACTIONS)
        self.assertIn(request["action"], protocol.NETWORK_ACQUISITION_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(request), 778)

        for mutation in (
            {"issue": 777},
            {"dataset_id": "other-dataset"},
            {"target_sha": "v1.0"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(_request(**mutation), expected_issue=778)

        with self.assertRaises(protocol.ProtocolError):
            protocol.semantic_request_id(
                _request(target_sha="0" * 40), MAIN_SHA, REPOSITORY
            )


class CountryRiskResultTests(unittest.TestCase):
    def test_success_binds_tree_blob_receipt_and_schema_to_same_bytes(self) -> None:
        result = _run_request()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["phase"], "acquisition_receipt")
        evidence = result["evidence"]
        binding = evidence[prepare.COUNTRY_RISK_GIT_BLOB_BINDING_FIELD]
        profile = evidence[prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD]
        self.assertTrue(binding["verified"])
        self.assertEqual(binding["tree_object_sha1"], COUNTRY_GIT_SHA1)
        self.assertEqual(binding["payload_git_blob_sha1"], COUNTRY_GIT_SHA1)
        self.assertEqual(binding["payload_sha256"], COUNTRY_SHA256)
        self.assertEqual(profile["sha256"], COUNTRY_SHA256)
        self.assertTrue(profile["trusted_source_receipt_bound"])
        self.assertFalse(profile["numeric_values_exposed"])
        self.assertFalse(result["external_bytes_persisted"])

    def test_complete_ledger_dedup_stops_before_provider_and_tree_work(self) -> None:
        first = _run_request()
        prior = {
            "id": 900,
            "body": protocol.canonical_result_comment(first),
            "user": {"login": "github-actions[bot]"},
        }
        tree = mock.Mock(return_value=_tree_profile())
        acquire = mock.Mock(return_value=(_receipt(), COUNTRY_BYTES))
        duplicate = _run_request(comments=[prior], tree_profiler=tree, country_acquirer=acquire)
        self.assertEqual(duplicate["status"], "duplicate")
        self.assertEqual(duplicate["duplicate_result_comment_id"], 900)
        tree.assert_not_called()
        acquire.assert_not_called()

    def test_non_blob_tree_stops_before_provider(self) -> None:
        acquire = mock.Mock(return_value=(_receipt(), COUNTRY_BYTES))
        result = _run_request(
            tree_profiler=lambda: _tree_profile(
                country_risk_path_status="tree",
                country_risk_path_entry={
                    "path": "Risk/European_Risk_Country.csv",
                    "type": "tree",
                    "object_sha1": "c" * 40,
                    "mode": "040000",
                },
                risk_blob_count=0,
                risk_tree_count=1,
            ),
            country_acquirer=acquire,
        )
        self.assertEqual(result["status"], "blocked")
        acquire.assert_not_called()

    def test_mismatched_tree_blob_identity_is_blocked_before_schema(self) -> None:
        schema = mock.Mock(return_value=_schema_profile())
        result = _run_request(
            tree_profiler=lambda: _tree_profile(
                country_risk_path_entry={
                    "path": "Risk/European_Risk_Country.csv",
                    "type": "blob",
                    "object_sha1": "d" * 40,
                    "mode": "100644",
                }
            ),
            schema_profiler=schema,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_GIT_BLOB_BINDING_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD])
        schema.assert_not_called()

    def test_tree_schema_and_receipt_contracts_fail_closed(self) -> None:
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_esrm20_risk_v10_tree_profile(
                _tree_profile(reference_loss_agreement_verified=True)
            )
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_esrm20_country_risk_receipt(
                _receipt(provider_rows_exposed=True)
            )
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_esrm20_country_risk_schema_profile(
                _schema_profile(numeric_values_exposed=True)
            )

    def test_schema_receipt_binding_rejects_wrong_bytes(self) -> None:
        profile = _schema_profile(sha256="0" * 64)
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_schema_receipt_binding(profile, _receipt())

    def test_post_dispatch_tampering_is_rejected(self) -> None:
        result = _run_request()
        tampered = json.loads(json.dumps(result))
        tampered["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD][
            "trusted_source_receipt_bound"
        ] = False
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_result(tampered)

    def test_profiler_cannot_self_promote_trusted_receipt_binding(self) -> None:
        def overclaiming(payload, *, expected_sha256, expected_byte_count):
            profile = _schema_profile(
                sha256=expected_sha256,
                byte_count=expected_byte_count,
            )
            profile["trusted_source_receipt_bound"] = True
            return profile

        result = _run_request(schema_profiler=overclaiming)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_GIT_BLOB_BINDING_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD])


class CountryRiskWorkflowTests(unittest.TestCase):
    def test_shared_dispatcher_preserves_country_risk_through_cems_extension(self) -> None:
        text = Path(".github/workflows/agent-action-dispatch.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_agent_action_result_cems_rp10.py", text)
        self.assertIn("post_agent_action_result_cems_rp10.py", text)
        self.assertIn(request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ACTION, prepare.NETWORK_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(_request()), 778)


if __name__ == "__main__":
    unittest.main()
