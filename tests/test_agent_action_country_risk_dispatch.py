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


def _tree_profile(status: str = "blob", **overrides):
    if status == "blob":
        inventory = [_tree_entry(risk_tree.COUNTRY_RISK_PATH, "1" * 40)]
    elif status == "tree":
        inventory = [
            _tree_entry(risk_tree.COUNTRY_RISK_PATH, "2" * 40, entry_type="tree")
        ]
    elif status == "absent":
        inventory = [_tree_entry("Risk/European_Risk_Admin1.csv", "3" * 40)]
    else:
        raise ValueError(status)
    canonical = "".join(
        f"{entry['type']}\t{entry['mode']}\t{entry['object_sha1']}\t{entry['path']}\n"
        for entry in inventory
    ).encode("utf-8")
    country_matches = [
        entry for entry in inventory if entry["path"] == risk_tree.COUNTRY_RISK_PATH
    ]
    country_entry = country_matches[0] if country_matches else None
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
        "country_risk_path_entry": country_entry,
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
    def test_request_is_exactly_bound_to_issue_dataset_and_action(self) -> None:
        request = _request()
        self.assertIs(
            request_validator.validate_request(request, expected_issue=778),
            request,
        )
        self.assertIn(
            request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ACTION,
            request_validator.ALLOWED_ACTIONS,
        )
        self.assertIn(
            request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ACTION,
            protocol.NETWORK_ACQUISITION_ACTIONS,
        )

        for mutation in (
            {"issue": 777},
            {"dataset_id": "efehr.esrm20.european-exposure-model.v1.0"},
            {"target_sha": "v1.0"},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(
                request_validator.RequestError
            ):
                request_validator.validate_request(_request(**mutation), expected_issue=778)

    def test_request_cannot_add_target_selectors(self) -> None:
        request = _request()
        request["repository_path"] = country.REPOSITORY_PATH
        with self.assertRaises(request_validator.RequestError):
            request_validator.validate_request(request, expected_issue=778)

    def test_semantic_identity_rejects_non_execution_target(self) -> None:
        with self.assertRaises(protocol.ProtocolError):
            protocol.semantic_request_id(
                _request(target_sha="0" * 40),
                MAIN_SHA,
                "pokekarten/OpenCatastrophe-data",
            )


class CountryRiskResultTests(unittest.TestCase):
    def test_tree_profile_contract_recomputes_identity_and_path_state(self) -> None:
        profile = _tree_profile()
        self.assertIs(
            result_validator.validate_esrm20_risk_v10_tree_profile(profile),
            profile,
        )
        for mutation in (
            {"tree_identity_sha256": "0" * 64},
            {"country_risk_path_status": "absent"},
            {"provider_file_bytes_read": True},
        ):
            with self.subTest(mutation=mutation), self.assertRaises(
                result_validator.ResultError
            ):
                result_validator.validate_esrm20_risk_v10_tree_profile(
                    _tree_profile(**mutation)
                )

    def test_pure_schema_profile_is_structural_and_unbound(self) -> None:
        profile = schema.profile_country_risk_schema_bytes(
            SCHEMA_PAYLOAD,
            expected_sha256=hashlib.sha256(SCHEMA_PAYLOAD).hexdigest(),
            expected_byte_count=len(SCHEMA_PAYLOAD),
        )
        self.assertIs(
            result_validator.validate_esrm20_country_risk_schema_profile(profile),
            profile,
        )
        self.assertFalse(profile["trusted_source_receipt_bound"])
        self.assertTrue(profile["residential_reference_schema_candidate"])
        self.assertNotIn("987654.321", str(profile))
        self.assertNotIn("654.987", str(profile))

    def test_receipt_contract_is_identity_only_and_fail_closed(self) -> None:
        receipt = _receipt()
        self.assertIs(
            result_validator.validate_esrm20_country_risk_receipt(receipt),
            receipt,
        )
        for field in (
            "external_bytes_persisted",
            "provider_rows_exposed",
            "reference_loss_agreement_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            bad = _receipt(**{field: True})
            with self.subTest(field=field), self.assertRaises(
                result_validator.ResultError
            ):
                result_validator.validate_esrm20_country_risk_receipt(bad)

    def test_success_binds_schema_to_same_receipted_bytes(self) -> None:
        result = _run_request()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["phase"], "acquisition_receipt")
        self.assertEqual(
            result["evidence"][prepare.RISK_TREE_PROFILE_FIELD][
                "country_risk_path_status"
            ],
            "blob",
        )
        receipt = result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD]
        profile = result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD]
        self.assertEqual(receipt["repository_path"], country.REPOSITORY_PATH)
        self.assertEqual(profile["sha256"], receipt["sha256"])
        self.assertEqual(profile["byte_count"], receipt["byte_count"])
        self.assertTrue(profile["trusted_source_receipt_bound"])
        self.assertTrue(profile["residential_reference_schema_candidate"])
        self.assertNotIn("987654.321", str(result))
        self.assertNotIn("654.987", str(result))

    def test_result_rejects_execution_sha_drift(self) -> None:
        result = _run_request()
        drifted = copy.deepcopy(result)
        drifted["execution_sha"] = "0" * 40
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_result(drifted)

    def test_result_rejects_tree_profile_tampering_after_dispatch(self) -> None:
        result = _run_request()
        drifted = copy.deepcopy(result)
        drifted["evidence"][prepare.RISK_TREE_PROFILE_FIELD][
            "tree_identity_sha256"
        ] = "0" * 64
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_result(drifted)

    def test_result_rejects_schema_receipt_binding_tampering(self) -> None:
        result = _run_request()
        drifted = copy.deepcopy(result)
        drifted["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD][
            "sha256"
        ] = "0" * 64
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_result(drifted)

    def test_worker_failure_retains_blob_profile_and_returns_blocked(self) -> None:
        def blocked():
            raise country.Esrm20CountryRiskReceiptError("provider detail must not escape")

        result = _run_request(country_risk_acquirer=blocked)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], prepare.ACQUISITION_FAILURE_CLASS)
        self.assertEqual(
            result["evidence"][prepare.RISK_TREE_PROFILE_FIELD][
                "country_risk_path_status"
            ],
            "blob",
        )
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD])
        self.assertIsNone(
            result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD]
        )

    def test_non_blob_precondition_never_invokes_byte_worker(self) -> None:
        for status in ("absent", "tree"):
            with self.subTest(status=status):
                byte_worker = mock.Mock(return_value=_acquired())
                result = _run_request(
                    risk_tree_profiler=lambda status=status: _tree_profile(status),
                    country_risk_acquirer=byte_worker,
                )
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(
                    result["failure_class"], prepare.ACQUISITION_FAILURE_CLASS
                )
                self.assertEqual(
                    result["evidence"][prepare.RISK_TREE_PROFILE_FIELD][
                        "country_risk_path_status"
                    ],
                    status,
                )
                self.assertIsNone(
                    result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD]
                )
                self.assertIsNone(
                    result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD]
                )
                byte_worker.assert_not_called()

    def test_tree_profile_failure_never_invokes_byte_worker(self) -> None:
        def blocked_profile():
            raise risk_tree.RiskTreeProfileError("provider detail must not escape")

        byte_worker = mock.Mock(return_value=_acquired())
        result = _run_request(
            risk_tree_profiler=blocked_profile,
            country_risk_acquirer=byte_worker,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], prepare.ACQUISITION_FAILURE_CLASS)
        self.assertIsNone(result["evidence"][prepare.RISK_TREE_PROFILE_FIELD])
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD])
        self.assertIsNone(
            result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD]
        )
        byte_worker.assert_not_called()

    def test_schema_failure_retains_receipt_but_never_publishes_payload(self) -> None:
        def blocked_schema(*args, **kwargs):
            del args, kwargs
            raise schema.CountryRiskSchemaProfileError("provider value must not escape")

        byte_worker = mock.Mock(return_value=_acquired())
        result = _run_request(
            country_risk_acquirer=byte_worker,
            schema_profiler=blocked_schema,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNotNone(result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD])
        self.assertIsNone(
            result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD]
        )
        self.assertNotIn("987654.321", str(result))
        byte_worker.assert_called_once_with()

    def test_pure_schema_profiler_cannot_pre_promote_receipt_authority(self) -> None:
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
        self.assertIsNotNone(result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD])
        self.assertIsNone(
            result["evidence"][prepare.COUNTRY_RISK_SCHEMA_PROFILE_FIELD]
        )


class CountryRiskWorkflowTests(unittest.TestCase):
    def test_shared_dispatcher_uses_country_risk_aware_entrypoints(self) -> None:
        text = Path(".github/workflows/agent-action-dispatch.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("prepare_agent_action_result_country_risk.py", text)
        self.assertIn("post_agent_action_result_country_risk.py", text)
        self.assertIn(
            request_validator.ESRM20_COUNTRY_RISK_RECEIPT_ACTION,
            prepare.NETWORK_ACTIONS,
        )
        self.assertEqual(prepare.ledger_issue_for_request(_request()), 778)


if __name__ == "__main__":
    unittest.main()
