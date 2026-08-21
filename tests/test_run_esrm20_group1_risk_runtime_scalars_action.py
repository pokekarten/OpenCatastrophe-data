# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import json
import unittest

from scripts import run_esrm20_group1_risk_runtime_scalars_action as subject


SHA = "1" * 40


def sample_evidence() -> dict:
    spec = subject.projector.GROUP1_SPEC
    return {
        "schema_version": subject.projector.SCHEMA_VERSION,
        "control_issue": subject.projector.CONTROL_ISSUE,
        "source_issue": subject.projector.SOURCE_ISSUE,
        "dataset_id": subject.projector.DATASET_ID,
        "project_id": subject.projector.PROJECT_ID,
        "project_path": subject.projector.PROJECT_PATH,
        "commit_sha": subject.projector.COMMIT_SHA,
        "candidate_key": subject.projector.GROUP1_KEY,
        "repository_path": spec.repository_path,
        "byte_count": spec.byte_count,
        "sha256": spec.sha256,
        "receipt_comment_id": subject.projector.risk_config.RECEIPT_COMMENT_ID,
        "openquake_reference": {
            "repository": subject.projector.OPENQUAKE_REPOSITORY,
            "tag": subject.projector.OPENQUAKE_TAG,
            "commit_sha": subject.projector.OPENQUAKE_COMMIT,
        },
        "runtime_scalars": {
            "calculation_mode": "ebrisk",
            "calculation_mode_present": True,
            "configured_seed_settings": [
                {
                    "key": "master_seed",
                    "purpose": "vulnerability_epsilon_sampling",
                    "section": "general",
                    "value": 42,
                }
            ],
            "seed_setting_present": True,
            "ignore_master_seed": False,
            "ignore_master_seed_present": True,
            "minimum_asset_loss_structural": "0",
            "minimum_asset_loss_structural_present": True,
            "defaults_inferred": False,
            "vulnerability_sampling_seed_semantics_verified": False,
        },
        "raw_config_returned": False,
        "historical_group_assignment_verified": False,
        "runtime_compatibility_verified": False,
        "numerical_loss_reproduction_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class Group1RuntimeScalarsActionTests(unittest.TestCase):
    def request(self, **updates: object) -> str:
        body = {
            "schema_version": subject.REQUEST_SCHEMA_VERSION,
            "action": subject.ACTION,
            "issue": subject.CONTROL_ISSUE,
            "target_sha": SHA,
            "dataset_id": subject.DATASET_ID,
            "requester": "unit-test",
        }
        body.update(updates)
        return subject.REQUEST_MARKER + "\n" + json.dumps(body, sort_keys=True)

    def test_request_is_exact_sha_bound(self):
        request = subject.validate_request(
            self.request(), expected_issue=subject.CONTROL_ISSUE, execution_sha=SHA
        )
        self.assertEqual(request["target_sha"], SHA)
        with self.assertRaises(subject.Group1RuntimeScalarsActionError):
            subject.validate_request(
                self.request(target_sha="2" * 40),
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=SHA,
            )

    def test_execute_publishes_only_bounded_projection(self):
        calls = []

        def acquire() -> bytes:
            calls.append("acquire")
            return b"receipt-bound-config"

        def project(payload: bytes) -> dict:
            self.assertEqual(payload, b"receipt-bound-config")
            calls.append("project")
            return sample_evidence()

        result = subject._execute_with(
            execution_sha=SHA, acquire_payload=acquire, project=project
        )
        self.assertEqual(calls, ["acquire", "project"])
        self.assertEqual(result["status"], "pass")
        self.assertNotIn("payload", result)
        self.assertIs(result["raw_config_returned"], False)
        self.assertIs(result["runtime_compatibility_verified"], False)
        self.assertIs(result["numerical_loss_reproduction_verified"], False)
        self.assertIs(result["publication_authorized"], False)
        self.assertIs(result["model_use_authorized"], False)

    def test_acquisition_or_projection_failure_is_bounded(self):
        def acquire_failure() -> bytes:
            raise subject.worker.EbriskDependencyAcquisitionError("nope")

        result = subject._execute_with(
            execution_sha=SHA,
            acquire_payload=acquire_failure,
            project=lambda payload: sample_evidence(),
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "projection_failure")
        self.assertIsNone(result["evidence"])

        result = subject._execute_with(
            execution_sha=SHA,
            acquire_payload=lambda: b"bytes",
            project=lambda payload: (_ for _ in ()).throw(
                subject.projector.RiskRuntimeScalarError("bad")
            ),
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["evidence"])

    def test_evidence_rejects_defaults_and_authority_widening(self):
        evidence = sample_evidence()
        evidence["runtime_scalars"]["defaults_inferred"] = True
        with self.assertRaises(subject.Group1RuntimeScalarsActionError):
            subject.validate_evidence(evidence)

        evidence = sample_evidence()
        evidence["runtime_compatibility_verified"] = True
        with self.assertRaises(subject.Group1RuntimeScalarsActionError):
            subject.validate_evidence(evidence)

    def test_minimum_asset_loss_terminal_contract_is_canonical_decimal(self):
        for invalid in ("abc", "-1", "NaN", "1.0"):
            with self.subTest(invalid=invalid):
                evidence = sample_evidence()
                evidence["runtime_scalars"]["minimum_asset_loss_structural"] = invalid
                with self.assertRaises(subject.Group1RuntimeScalarsActionError):
                    subject.validate_evidence(evidence)

                result = subject._base_result(execution_sha=SHA)
                result.update(
                    {"status": "pass", "failure_class": None, "evidence": evidence}
                )
                body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True)
                with self.assertRaises(subject.Group1RuntimeScalarsActionError):
                    subject.parse_terminal_result(body)

        evidence = sample_evidence()
        evidence["runtime_scalars"]["minimum_asset_loss_structural"] = "12.5"
        subject.validate_evidence(evidence)

    def test_evidence_preserves_missing_as_absent(self):
        evidence = sample_evidence()
        scalars = evidence["runtime_scalars"]
        scalars["calculation_mode"] = None
        scalars["calculation_mode_present"] = False
        scalars["configured_seed_settings"] = []
        scalars["seed_setting_present"] = False
        scalars["ignore_master_seed"] = None
        scalars["ignore_master_seed_present"] = False
        scalars["minimum_asset_loss_structural"] = None
        scalars["minimum_asset_loss_structural_present"] = False
        subject.validate_evidence(evidence)

    def test_terminal_parser_validates_result_under_its_own_sha(self):
        result = subject._base_result(execution_sha=SHA)
        result.update(
            {"status": "pass", "failure_class": None, "evidence": sample_evidence()}
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True)
        self.assertEqual(subject.parse_terminal_result(body), SHA)

        result["target_sha"] = "2" * 40
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, sort_keys=True)
        with self.assertRaises(subject.Group1RuntimeScalarsActionError):
            subject.parse_terminal_result(body)

    def test_terminal_parser_rejects_duplicate_json_keys(self):
        body = subject.RESULT_MARKER + '\n{"schema_version":"x","schema_version":"y"}'
        with self.assertRaises(subject.Group1RuntimeScalarsActionError):
            subject.parse_terminal_result(body)


if __name__ == "__main__":
    unittest.main()
