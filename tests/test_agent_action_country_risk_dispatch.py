# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest

from scripts import acquire_efehr_esrm20_country_risk_receipt as country
from scripts import agent_action_protocol_country_risk as protocol
from scripts import prepare_agent_action_result_country_risk as prepare
from scripts import validate_agent_action_request_country_risk as request_validator
from scripts import validate_agent_action_result_country_risk as result_validator
from scripts.efehr_gitlab_receipt import raw_file_api_url, validate_target

MAIN_SHA = "7226582160bd129fb15a0d46db777be826f24d84"
DATASET = "efehr.esrm20.risk-inputs.v1.0"
RETRIEVED_AT = "2026-08-29T10:00:00Z"


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


def _receipt(**overrides):
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
        "byte_count": 123,
        "sha256": "a" * 64,
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

    def test_result_rejects_execution_sha_drift(self) -> None:
        request = request_validator.validate_request(_request(), expected_issue=778)
        result = prepare.prepare_completed_result(
            request,
            [],
            repository="pokekarten/OpenCatastrophe-data",
            execution_sha=MAIN_SHA,
            source_comment_id=1,
            run_id=2,
            run_attempt=1,
            started_at="2026-08-29T09:59:00Z",
            country_risk_acquirer=_receipt,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["phase"], "acquisition_receipt")
        self.assertEqual(
            result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD]["repository_path"],
            country.REPOSITORY_PATH,
        )

        drifted = dict(result)
        drifted["execution_sha"] = "0" * 40
        with self.assertRaises(result_validator.ResultError):
            result_validator.validate_result(drifted)

    def test_worker_failure_returns_bounded_blocked_result(self) -> None:
        request = request_validator.validate_request(_request(), expected_issue=778)

        def blocked():
            raise country.Esrm20CountryRiskReceiptError("provider detail must not escape")

        result = prepare.prepare_completed_result(
            request,
            [],
            repository="pokekarten/OpenCatastrophe-data",
            execution_sha=MAIN_SHA,
            source_comment_id=1,
            run_id=2,
            run_attempt=1,
            started_at="2026-08-29T09:59:00Z",
            country_risk_acquirer=blocked,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], prepare.ACQUISITION_FAILURE_CLASS)
        self.assertIsNone(result["evidence"][prepare.COUNTRY_RISK_RECEIPT_FIELD])


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
