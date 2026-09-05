# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_country_risk_receipt as country
from scripts import agent_action_protocol_country_risk as protocol
from scripts import prepare_agent_action_result_country_risk as prepare
from scripts import profile_esrm20_country_risk_schema as schema
from scripts import profile_esrm20_risk_v10_tree as risk_tree
from scripts import validate_agent_action_request_country_risk as request_validator
from scripts import validate_agent_action_result_country_risk as result_validator
from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target

MAIN_SHA = "7226582160bd129fb15a0d46db777be826f24d84"
DATASET = "efehr.esrm20.risk-inputs.v1.0"
RETRIEVED_AT = "2026-08-29T10:00:00Z"
SCHEMA_PAYLOAD = (
    b'Name,"AAL Residential (economic, M EUR)",'
    b'"AALR Residential (economic, per mille)"\n'
    b"Kosovo,987654.321,654.987\n"
)


def _git_blob_sha1(payload: bytes = SCHEMA_PAYLOAD) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload, usedforsecurity=False).hexdigest()


def _request(**overrides):
    value = {
        "schema_version": request_validator.SCHEMA_VERSION,
        "action": request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ACTION,
        "issue": 778,
        "target_sha": MAIN_SHA,
        "dataset_id": DATASET,
        "requester": "pokekarten",
    }
    value.update(overrides)
    return value


def _receipt(payload: bytes = SCHEMA_PAYLOAD, **overrides):
    target = validate_target(
        source_issue=country.SOURCE_ISSUE,
        dataset_id=country.DATASET_ID,
        project_id=country.PROJECT_ID,
        commit_sha=country.COMMIT_SHA,
        repository_path=country.REPOSITORY_PATH,
    )
    url = raw_file_api_url(target)
    value = {
        "schema_version": country.SCHEMA_VERSION,
        "operation_id": country.OPERATION_ID,
        "source_issue": country.SOURCE_ISSUE,
        "dataset_id": country.DATASET_ID,
        "provider_host": "gitlab.seismo.ethz.ch",
        "project_id": country.PROJECT_ID,
        "project_path": country.PROJECT_PATH,
        "commit_sha": country.COMMIT_SHA,
        "repository_path": country.REPOSITORY_PATH,
        "requested_url": url,
        "final_url": url,
        "retrieved_at": RETRIEVED_AT,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "content_type": "text/csv",
        "etag": '"synthetic"',
        "external_bytes_persisted": False,
        "provider_rows_exposed": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    value.update(overrides)
    return value


def _acquired(payload: bytes = SCHEMA_PAYLOAD):
    return _receipt(payload), payload


def _tree_entry(path: str, object_sha1: str, *, entry_type: str = "blob"):
    return {
        "mode": "040000" if entry_type == "tree" else "100644",
        "object_sha1": object_sha1,
        "path": path,
        "type": entry_type,
    }


def _tree_profile(status: str = "blob", *, blob_sha1: str | None = None, **overrides):
    if status == "blob":
        inventory = [_tree_entry(risk_tree.COUNTRY_RISK_PATH, blob_sha1 or _git_blob_sha1())]
    elif status == "tree":
        inventory = [_tree_entry(risk_tree.COUNTRY_RISK_PATH, "2" * 40, entry_type="tree")]
    elif status == "absent":
        inventory = [_tree_entry("Risk/European_Risk_Admin1.csv", "3" * 40)]
    else:
        raise ValueError(status)
    canonical = "".join(
        f"{entry['type']}\t{entry['mode']}\t{entry['object_sha1']}\t{entry['path']}\n"
        for entry in inventory
    ).encode("utf-8")
    matches = [entry for entry in inventory if entry["path"] == risk_tree.COUNTRY_RISK_PATH]
    value = {
        "schema_version": risk_tree.SCHEMA_VERSION,
        "source_issue": risk_tree.SOURCE_ISSUE,
        "dataset_id": risk_tree.DATASET_ID,
        "project_id": risk_tree.PROJECT_ID,
        "project_path": risk_tree.PROJECT_PATH,
        "release_tag": risk_tree.RELEASE_TAG,
        "commit_sha": risk_tree.EXPECTED_COMMIT_SHA,
        "subtree_path": risk_tree.SUBTREE_PATH,
        "pages_read": 1,
        "entry_count": len(inventory),
        "blob_count": sum(entry["type"] == "blob" for entry in inventory),
        "tree_count": sum(entry["type"] == "tree" for entry in inventory),
        "tree_identity_sha256": hashlib.sha256(canonical).hexdigest(),
        "risk_inventory": inventory,
        "country_risk_path": risk_tree.COUNTRY_RISK_PATH,
        "country_risk_path_status": status,
        "country_risk_path_entry": matches[0] if matches else None,
        "country_risk_blob_candidate_present": status == "blob",
        "provider_file_bytes_read": False,
        "external_bytes_persisted": False,
        "country_risk_bytes_verified": False,
        "country_risk_schema_verified": False,
        "reference_loss_agreement_verified": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    value.update(overrides)
    return value


def _run_request(**overrides):
    request = request_validator.validate_request(_request(), expected_issue=778)
    kwargs = {
        "repository": "pokekarten/OpenCatastrophe-data",
        "execution_sha": MAIN_SHA,
        "source_comment_id": 1,
        "run_id": 2,
        "run_attempt": 1,
        "started_at": "2026-08-29T09:59:00Z",
        "risk_tree_profiler": _tree_profile,
        "country_risk_acquirer": _acquired,
        "schema_profiler": schema.profile_country_risk_schema_bytes,
    }
    kwargs.update(overrides)
    return prepare.prepare_completed_result(request, [], **kwargs)


class CountryRiskRequestTests(unittest.TestCase):
    def test_fixed_request_contract_and_network_identity(self) -> None:
        request = _request()
        self.assertIs(request_validator.validate_request(request, expected_issue=778), request)
        self.assertIn(request["action"], request_validator.ALLOWED_ACTIONS)
        self.assertIn(request["action"], protocol.NETWORK_ACQUISITION_ACTIONS)
        for mutation in (
            {"issue": 777},
            {"dataset_id": "efehr.esrm20.european-exposure-model.v1.0"},
            {"target_sha": "v1.0"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(request_validator.RequestError):
                request_validator.validate_request(_request(**mutation), expected_issue=778)
        selected = _request()
        selected["repository_path"] = country.REPOSITORY_PATH
        with self.assertRaises(request_validator.RequestError):
            request_validator.validate_request(selected, expected_issue=778)
        with self.assertRaises(protocol.ProtocolError):
            protocol.semantic_request_id(
                _request(target_sha="0" * 40), MAIN_SHA, "pokekarten/OpenCatastrophe-data"
            )


class CountryRiskResultTests(unittest.TestCase):
    def test_tree_schema_and_receipt_contracts_fail_closed(self) -> None:
        profile = _tree_profile()
        self.assertIs(result_validator.validate_esrm20_risk_v10_tree_profile(profile), profile)
        for mutation in (
            {"tree_identity_sha256": "0" * 64},
            {"country_risk_path_status": "absent"},
            {"provider_file_bytes_read": True},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(result_validator.ResultError):
                result_validator.validate_esrm20_risk_v10_tree_profile(_tree_profile(**mutation))

        pure = schema.profile_country_risk_schema_bytes(
            SCHEMA_PAYLOAD,
            expected_sha256=hashlib.sha256(SCHEMA_PAYLOAD).hexdigest(),
            expected_byte_count=len(SCHEMA_PAYLOAD),
        )
        self.assertIs(result_validator.validate_esrm20_country_risk_schema_profile(pure), pure)
        self.assertFalse(pure["trusted_source_receipt_bound"])
        self.assertTrue(pure["residential_reference_schema_candidate"])
        self.assertNotIn("987654.321", str(pure))

        receipt = _receipt()
        self.assertIs(result_validator.validate_esrm20_country_risk_receipt(receipt), receipt)
        for field in (
            "external_bytes_persisted",
            "provider_rows_exposed",
            "reference_loss_agreement_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field), self.assertRaises(result_validator.ResultError):
                result_validator.validate_esrm20_country_risk_receipt(_receipt(**{field: True}))

    def test_success_binds_tree_blob_receipt_and_schema_to_same_bytes(self) -> None:
        result = _run_request()
        self.assertEqual(result["status"], "pass")
        receipt = result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD]
        binding = result["evidence"][prepare.COUNTRY_RISK_GIT_BLOB_BINDING_FIELD]
        profile = result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD]
        self.assertEqual(binding["tree_object_sha1"], _git_blob_sha1())
        self.assertEqual(binding["payload_git_blob_sha1"], _git_blob_sha1())
        self.assertEqual(binding["payload_byte_count"], receipt["byte_count"])
        self.assertEqual(binding["payload_sha256"], receipt["sha256"])
        self.assertTrue(binding["verified"])
        self.assertEqual(profile["sha256"], receipt["sha256"])
        self.assertTrue(profile["trusted_source_receipt_bound"])
        self.assertNotIn("987654.321", str(result))
        self.assertNotIn("654.987", str(result))

    def test_mismatched_tree_blob_identity_is_blocked_before_schema(self) -> None:
        result = _run_request(risk_tree_profiler=lambda: _tree_profile(blob_sha1="1" * 40))
        self.assertEqual(result["status"], "blocked")
        self.assertIsNotNone(result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_GIT_BLOB_BINDING_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD])

    def test_post_dispatch_tampering_is_rejected(self) -> None:
        for field, key, value in (
            (prepare.RISK_TREE_PROFILE_FIELD, "tree_identity_sha256", "0" * 64),
            (prepare.COUNTRY_RISK_GIT_BLOB_BINDING_FIELD, "payload_git_blob_sha1", "0" * 40),
            (prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD, "sha256", "0" * 64),
        ):
            result = _run_request()
            drifted = copy.deepcopy(result)
            drifted["evidence"][field][key] = value
            with self.subTest(field=field), self.assertRaises(result_validator.ResultError):
                result_validator.validate_result(drifted)
        drifted = copy.deepcopy(_run_request())
        drifted["execution_sha"] = "0" * 40
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_result(drifted)

    def test_failures_never_promote_later_evidence(self) -> None:
        def blocked_worker():
            raise country.Esrm20CountryRiskReceiptError("blocked")

        result = _run_request(country_risk_acquirer=blocked_worker)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_GIT_BLOB_BINDING_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD])

        for status in ("absent", "tree"):
            worker = mock.Mock(return_value=_acquired())
            result = _run_request(
                risk_tree_profiler=lambda status=status: _tree_profile(status),
                country_risk_acquirer=worker,
            )
            self.assertEqual(result["status"], "blocked")
            worker.assert_not_called()

        def blocked_profile():
            raise risk_tree.RiskTreeProfileError("blocked")

        worker = mock.Mock(return_value=_acquired())
        result = _run_request(risk_tree_profiler=blocked_profile, country_risk_acquirer=worker)
        self.assertEqual(result["status"], "blocked")
        worker.assert_not_called()

        def blocked_schema(*args, **kwargs):
            del args, kwargs
            raise schema.CountryRiskSchemaProfileError("blocked")

        result = _run_request(schema_profiler=blocked_schema)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNotNone(result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_GIT_BLOB_BINDING_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD])

        def overclaiming(payload, *, expected_sha256, expected_byte_count):
            profile = schema.profile_country_risk_schema_bytes(
                payload,
                expected_sha256=expected_sha256,
                expected_byte_count=expected_byte_count,
            )
            profile["trusted_source_receipt_bound"] = True
            return profile

        result = _run_request(schema_profiler=overclaiming)
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_GIT_BLOB_BINDING_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD])


class CountryRiskWorkflowTests(unittest.TestCase):
    def test_shared_dispatcher_uses_country_risk_aware_entrypoints(self) -> None:
        text = Path(".github/workflows/agent-action-dispatch.yml").read_text(encoding="utf-8")
        self.assertIn("prepare_agent_action_result_country_risk.py", text)
        self.assertIn("post_agent_action_result_country_risk.py", text)
        self.assertIn(request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ACTION, prepare.NETWORK_ACTIONS)
        self.assertEqual(prepare.ledger_issue_for_request(_request()), 778)


if __name__ == "__main__":
    unittest.main()
