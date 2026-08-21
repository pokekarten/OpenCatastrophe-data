# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import check_esrm20_gsim_runtime_dedup as subject


EXECUTION_SHA = "1" * 40
OTHER_SHA = "2" * 40
IMAGE_DIGEST = "sha256:" + "a" * 64


def _trusted_comment(comment_id: int, body: str) -> dict[str, object]:
    return {
        "id": comment_id,
        "body": body,
        "user": {"login": subject.TRUSTED_RESULT_LOGIN},
    }


def _exact_branches() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for (branch_set_id, branch_id), (
        tectonic_region_type,
        requested_gsim_token,
        request_form,
        argument_keys,
    ) in sorted(subject._expected_branch_requests().items()):
        keys = list(argument_keys)
        rows.append(
            {
                "branch_set_id": branch_set_id,
                "branch_id": branch_id,
                "tectonic_region_type": tectonic_region_type,
                "requested_gsim_token": requested_gsim_token,
                "resolved_gsim_class": requested_gsim_token,
                "request_form": request_form,
                "alias_definition_present": False,
                "alias_expansion_applied": False,
                "registry_alias_key_used": False,
                "argument_keys": keys,
                "runtime_argument_keys_after_alias": keys,
                "constructor_accepted": True,
            }
        )
    return rows


def _argument_evidence() -> dict[str, object]:
    keys = list(subject._runtime.EXPECTED_SOURCE_ARGUMENT_KEYS)
    return {
        "source_argument_keys": keys,
        "runtime_argument_keys_after_alias": keys,
        "external_resource_argument_keys": [],
        "argument_values_returned": False,
        "source_profile_result_comment_id": subject._runtime.CANONICAL_PROFILE_RESULT_COMMENT_ID,
    }


def _site_evidence() -> dict[str, object]:
    return {
        "per_resolved_gsim_class": subject._EXPECTED_SITE_ROWS,
        "required_site_parameters": subject._EXPECTED_SITE_REQUIREMENTS,
        "source": subject._SITE_SOURCE,
    }


def _component_evidence() -> dict[str, object]:
    rows = [
        {
            "resolved_gsim_class": name,
            "component": subject._runtime.EXPECTED_COMPONENTS_BY_GSIM[name],
        }
        for name in sorted(subject._runtime.EXPECTED_COMPONENTS_BY_GSIM)
    ]
    return {
        "per_resolved_gsim_class": rows,
        "unique_components": ["GEOMETRIC_MEAN", "RotD50"],
        "mixed_component_basis": True,
        "component_conversion_request_absent": True,
        "component_conversion_activated": False,
        "component_conversion_wrapper": subject._runtime.COMPONENT_CONVERSION_WRAPPER,
        "component_conversion_argument": subject._runtime.COMPONENT_CONVERSION_ARGUMENT,
        "reference_component_semantics": subject._runtime.REFERENCE_COMPONENT_SEMANTICS,
        "source": subject._COMPONENT_SOURCE,
    }


def _terminal_result(*, execution_sha: str = EXECUTION_SHA, legacy: bool = False) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": subject._runtime.SCHEMA_VERSION,
        "source_issue": subject._runtime.SOURCE_ISSUE,
        "dataset_id": subject._runtime.DATASET_ID,
        "status": "pass",
        "target_sha": execution_sha,
        "execution_sha": execution_sha,
        "execution_container_image_digest": IMAGE_DIGEST,
        "gmm_identity": {
            "project_id": subject._runtime.PROJECT_ID,
            "project_path": subject._runtime.PROJECT_PATH,
            "commit_sha": subject._runtime.COMMIT_SHA,
            "repository_path": subject._runtime.REPOSITORY_PATH,
            "byte_count": subject._runtime.EXPECTED_BYTE_COUNT,
            "sha256": subject._runtime.EXPECTED_SHA256,
        },
        "openquake_reference": {
            "repository": subject._runtime._gate.OPENQUAKE_REPOSITORY,
            "tag": subject._runtime._gate.OPENQUAKE_TAG,
            "commit": subject._runtime.OPENQUAKE_COMMIT,
            "version": subject._runtime._gate.OPENQUAKE_VERSION,
        },
        "reference_runtime_fingerprint": {},
        "branch_count": subject._runtime.EXPECTED_BRANCH_COUNT,
        "branches": _exact_branches(),
        "unique_resolved_gsim_classes": list(subject._runtime.EXPECTED_REQUESTED_TOKENS),
        "alias_requested_tokens": [],
        "same_process_runtime_observation_collected": True,
        "executing_environment_matches_reconstructed_reference_recipe_fields": True,
        "gsim_request_reference_recipe_runtime_compatibility_verified": True,
        "historical_environment_verified": False,
        "reference_base_image_byte_identity_verified": False,
        "wheel_byte_identity_verified": False,
        "numerical_hazard_agreement_verified": False,
        "imt_component_unit_compatibility_verified": False,
        "full_hazard_compatibility_verified": False,
        "site_model_compatibility_verified": False,
        "vulnerability_compatibility_verified": False,
        "reference_run_verified": False,
        "scientific_validity_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
        "source_profile_result_comment_id": subject._runtime.CANONICAL_PROFILE_RESULT_COMMENT_ID,
        "source_receipt_result_comment_id": subject._runtime.CANONICAL_RECEIPT_RESULT_COMMENT_ID,
        "requested_gsim_tokens": list(subject._runtime.EXPECTED_REQUESTED_TOKENS),
        "gsim_argument_evidence": _argument_evidence(),
        "site_parameter_requirements": _site_evidence(),
        "site_parameter_requirements_derived": True,
    }
    if not legacy:
        result["component_evidence"] = _component_evidence()
        result["component_evidence_derived"] = True
    return result


def _terminal_body(result: dict[str, object]) -> str:
    return subject._runtime.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


class Esrm20RuntimeDedupFullLedgerTests(unittest.TestCase):
    def test_matching_terminal_does_not_short_circuit_later_trusted_validation(
        self,
    ) -> None:
        comments = [
            _trusted_comment(1, "matching-terminal"),
            _trusted_comment(2, "later-malformed-terminal"),
        ]
        malformed = subject._error("trusted ESRM20 runtime result JSON is malformed")

        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=comments,
        ), mock.patch.object(
            subject,
            "_parse_terminal",
            side_effect=[EXECUTION_SHA, malformed],
        ) as parse_terminal:
            with self.assertRaisesRegex(
                subject._runtime.Esrm20GsimReferenceRuntimeError,
                "result JSON is malformed",
            ):
                subject.has_terminal_runtime_result(
                    repository="owner/repo",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )

        self.assertEqual(parse_terminal.call_count, 2)

    def test_match_is_returned_only_after_all_trusted_terminals_validate(self) -> None:
        comments = [
            _trusted_comment(1, "matching-terminal"),
            _trusted_comment(2, "different-valid-terminal"),
        ]

        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=comments,
        ), mock.patch.object(
            subject,
            "_parse_terminal",
            side_effect=[EXECUTION_SHA, OTHER_SHA],
        ) as parse_terminal:
            found = subject.has_terminal_runtime_result(
                repository="owner/repo",
                token="token",
                execution_sha=EXECUTION_SHA,
            )

        self.assertTrue(found)
        self.assertEqual(parse_terminal.call_count, 2)

    def test_full_ledger_ignores_untrusted_comments_and_forwards_bounded_fetch(self) -> None:
        opener = object()
        comments = [
            {"id": 1, "body": "forged", "user": {"login": "attacker"}},
            _trusted_comment(2, "valid-different-terminal"),
        ]
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=comments,
        ) as fetch, mock.patch.object(
            subject,
            "_parse_terminal",
            return_value=OTHER_SHA,
        ) as parse_terminal:
            found = subject.has_terminal_runtime_result(
                repository="owner/repo",
                token="token",
                execution_sha=EXECUTION_SHA,
                opener=opener,
                max_pages=7,
            )
        self.assertFalse(found)
        fetch.assert_called_once_with(
            "owner/repo", "token", issue=subject._runtime.SOURCE_ISSUE, max_pages=7, opener=opener
        )
        parse_terminal.assert_called_once_with("valid-different-terminal", comment_id=2)

    def test_full_ledger_fails_closed_on_invalid_sha_and_incomplete_ledger(self) -> None:
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError,
            "invalid ESRM20 execution SHA",
        ):
            subject.has_terminal_runtime_result(
                repository="owner/repo", token="token", execution_sha="not-a-sha"
            )

        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            side_effect=subject.LedgerError("truncated"),
        ):
            with self.assertRaisesRegex(
                subject._runtime.Esrm20GsimReferenceRuntimeError,
                "result ledger is incomplete",
            ):
                subject.has_terminal_runtime_result(
                    repository="owner/repo", token="token", execution_sha=EXECUTION_SHA
                )


class Esrm20RuntimeDedupDirectValidatorTests(unittest.TestCase):
    def test_branch_projection_preserves_frozen_identity_and_expected_alias_renames(self) -> None:
        expected = subject._expected_branch_requests()
        self.assertEqual(len(expected), subject._runtime.EXPECTED_BRANCH_COUNT)
        tokens = {contract[1] for contract in expected.values()}
        self.assertIn("KothaEtAl2020ESHM20SlopeGeology", tokens)
        self.assertNotIn("KothaEtAl2020ESHM20", tokens)
        argument_keys = {key for contract in expected.values() for key in contract[3]}
        self.assertIn("theta_6_adjustment", argument_keys)
        self.assertNotIn("theta6_adjustment", argument_keys)

    def test_branch_validator_accepts_exact_projection_and_rejects_order_and_contract_drift(self) -> None:
        exact = {
            "branch_count": subject._runtime.EXPECTED_BRANCH_COUNT,
            "branches": _exact_branches(),
            "unique_resolved_gsim_classes": list(subject._runtime.EXPECTED_REQUESTED_TOKENS),
            "alias_requested_tokens": [],
        }
        subject._validate_branches(exact)

        reversed_order = dict(exact)
        reversed_order["branches"] = list(reversed(exact["branches"]))
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "branch order drifted"
        ):
            subject._validate_branches(reversed_order)

        mutated = dict(exact)
        rows = [dict(row) for row in exact["branches"]]
        rows[0]["constructor_accepted"] = False
        mutated["branches"] = rows
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "branch contract drifted"
        ):
            subject._validate_branches(mutated)

    def test_argument_site_and_component_evidence_fail_closed_on_authority_drift(self) -> None:
        subject._validate_argument_evidence({"gsim_argument_evidence": _argument_evidence()})
        subject._validate_site_evidence(
            {
                "site_parameter_requirements_derived": True,
                "site_parameter_requirements": _site_evidence(),
            }
        )
        subject._validate_component_evidence(
            {
                "component_evidence_derived": True,
                "component_evidence": _component_evidence(),
            },
            legacy=False,
        )

        arguments = _argument_evidence()
        arguments["argument_values_returned"] = True
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "argument evidence drifted"
        ):
            subject._validate_argument_evidence({"gsim_argument_evidence": arguments})

        site = _site_evidence()
        site["source"] = "untrusted-source"
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "site evidence drifted"
        ):
            subject._validate_site_evidence(
                {"site_parameter_requirements_derived": True, "site_parameter_requirements": site}
            )

        component = _component_evidence()
        component["component_conversion_activated"] = True
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "component evidence drifted"
        ):
            subject._validate_component_evidence(
                {"component_evidence_derived": True, "component_evidence": component},
                legacy=False,
            )

    def test_legacy_component_contract_rejects_new_component_fields(self) -> None:
        subject._validate_component_evidence({}, legacy=True)
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError,
            "legacy ESRM20 runtime component fields drifted",
        ):
            subject._validate_component_evidence(
                {"component_evidence_derived": True}, legacy=True
            )

    def test_terminal_parser_rejects_envelope_duplicate_key_sha_and_authority_widening(self) -> None:
        self.assertIsNone(subject._parse_terminal("ordinary comment", comment_id=1))
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "result marker is malformed"
        ):
            subject._parse_terminal(
                subject._runtime.RESULT_MARKER + "\n{}\n" + subject._runtime.RESULT_MARKER,
                comment_id=1,
            )
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "result envelope is malformed"
        ):
            subject._parse_terminal("prefix\n" + subject._runtime.RESULT_MARKER + "\n{}", comment_id=1)
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "result JSON is malformed"
        ):
            subject._parse_terminal(
                subject._runtime.RESULT_MARKER + '\n{"target_sha":"a","target_sha":"b"}',
                comment_id=1,
            )

        mismatch = _terminal_result()
        mismatch["execution_sha"] = OTHER_SHA
        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "SHA identity drifted"
        ):
            subject._parse_terminal(_terminal_body(mismatch), comment_id=1)

        for field in (
            "historical_environment_verified",
            "numerical_hazard_agreement_verified",
            "imt_component_unit_compatibility_verified",
            "scientific_validity_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field):
                widened = _terminal_result()
                widened[field] = True
                with self.assertRaisesRegex(
                    subject._runtime.Esrm20GsimReferenceRuntimeError,
                    "result contract drifted",
                ):
                    subject._parse_terminal(_terminal_body(widened), comment_id=1)

    def test_terminal_parser_accepts_structural_contract_when_deep_validators_pass(self) -> None:
        result = _terminal_result()
        with mock.patch.object(
            subject._base, "_validate_trusted_runtime_fingerprint"
        ) as fingerprint, mock.patch.object(subject, "_validate_branches") as branches, mock.patch.object(
            subject, "_validate_argument_evidence"
        ) as arguments, mock.patch.object(subject, "_validate_site_evidence") as site, mock.patch.object(
            subject, "_validate_component_evidence"
        ) as component:
            observed = subject._parse_terminal(_terminal_body(result), comment_id=1)
        self.assertEqual(observed, EXECUTION_SHA)
        fingerprint.assert_called_once_with({}, image_digest=IMAGE_DIGEST)
        branches.assert_called_once_with(result)
        arguments.assert_called_once_with(result)
        site.assert_called_once_with(result)
        component.assert_called_once_with(result, legacy=False)

    def test_legacy_terminal_field_set_is_scoped_to_exact_historical_comment_and_sha(self) -> None:
        legacy = _terminal_result(
            execution_sha=subject.LEGACY_EXECUTION_SHA,
            legacy=True,
        )
        with mock.patch.object(
            subject._base, "_validate_trusted_runtime_fingerprint"
        ), mock.patch.object(subject, "_validate_branches"), mock.patch.object(
            subject, "_validate_argument_evidence"
        ), mock.patch.object(subject, "_validate_site_evidence"), mock.patch.object(
            subject, "_validate_component_evidence"
        ) as component:
            observed = subject._parse_terminal(
                _terminal_body(legacy), comment_id=subject.LEGACY_TERMINAL_COMMENT_ID
            )
        self.assertEqual(observed, subject.LEGACY_EXECUTION_SHA)
        component.assert_called_once_with(legacy, legacy=True)

        with self.assertRaisesRegex(
            subject._runtime.Esrm20GsimReferenceRuntimeError, "result fields drifted"
        ):
            subject._parse_terminal(_terminal_body(legacy), comment_id=1)


if __name__ == "__main__":
    unittest.main()
