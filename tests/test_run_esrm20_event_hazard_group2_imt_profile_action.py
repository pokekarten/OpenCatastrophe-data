# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import acquire_esrm20_event_hazard_dependencies as acquisition
from scripts import run_esrm20_event_hazard_group2_imt_profile_action as subject
from scripts import verify_esrm20_event_hazard_dependencies as bridge

EXECUTION_SHA = "2" * 40


def _profile() -> dict[str, object]:
    spec = bridge._root_spec(2)
    return {
        "schema_version": bridge.IMT_PROFILE_SCHEMA_VERSION,
        "source_issue": subject.CONTROL_ISSUE,
        "control_issue": bridge.CONTROL_ISSUE,
        "dataset_id": bridge.DATASET_ID,
        "project_id": bridge.PROJECT_ID,
        "project_path": bridge.PROJECT_PATH,
        "commit_sha": bridge.COMMIT_SHA,
        "group": 2,
        "operation_id": spec.operation_id,
        "repository_path": spec.repository_path,
        "byte_count": spec.byte_count,
        "sha256": spec.sha256,
        "receipt_comment_id": spec.receipt_comment_id,
        "imt_option": "intensity_measure_types",
        "imt_names": ["PGA", "SA(0.3)", "SA(0.6)", "SA(1.0)"],
        "imt_count": 4,
        "levels_returned": False,
        "raw_config_returned": False,
        "component_semantics_verified": False,
        "unit_semantics_verified": False,
        "hazard_vulnerability_imt_compatibility_verified": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _request(*, target_sha: str = EXECUTION_SHA) -> str:
    body = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": target_sha,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(body, separators=(",", ":"))


class Group2ImtProfileActionTests(unittest.TestCase):
    def test_contract_is_bound_to_exact_group2_receipt(self) -> None:
        subject._require_contract()
        spec = bridge._root_spec(2)
        self.assertEqual(spec.repository_path, "Configuration_files/config_event_hazard_Group2.ini")
        self.assertEqual(spec.byte_count, 1673)
        self.assertEqual(
            spec.sha256,
            "eb74edd2168bad20c23d4b0e1a99f5ed97ef28606a9ebfef6b8c8191d35dd34c",
        )
        self.assertEqual(spec.receipt_comment_id, 5301299581)

    def test_validates_exact_trusted_main_request(self) -> None:
        request = subject.validate_request(
            _request(),
            expected_issue=subject.CONTROL_ISSUE,
            execution_sha=EXECUTION_SHA,
        )
        self.assertEqual(request["target_sha"], EXECUTION_SHA)

    def test_rejects_request_bound_to_other_execution_sha(self) -> None:
        with self.assertRaisesRegex(subject.Group2ImtProfileActionError, "target_sha drifted"):
            subject.validate_request(
                _request(target_sha="3" * 40),
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=EXECUTION_SHA,
            )

    def test_pass_result_preserves_false_authority_ceiling(self) -> None:
        result = subject._run_profile(
            execution_sha=EXECUTION_SHA,
            acquirer=_profile,
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["profile"]["group"], 2)
        self.assertFalse(result["component_semantics_verified"])
        self.assertFalse(result["unit_semantics_verified"])
        self.assertFalse(result["hazard_vulnerability_imt_compatibility_verified"])
        self.assertFalse(result["numerical_hazard_agreement_verified"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_acquisition_failure_returns_bounded_blocked_result(self) -> None:
        def fail() -> dict[str, object]:
            raise acquisition.EventHazardDependencyAcquisitionError("provider unavailable")

        result = subject._run_profile(execution_sha=EXECUTION_SHA, acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertIsNone(result["profile"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["publication_authorized"])

    def test_profile_cannot_widen_component_or_unit_authority(self) -> None:
        widened = _profile()
        widened["unit_semantics_verified"] = True
        with self.assertRaisesRegex(
            subject.Group2ImtProfileActionError,
            "drifted at unit_semantics_verified",
        ):
            subject._validate_profile(widened)

    def test_profile_rejects_boolean_imt_count(self) -> None:
        malformed = _profile()
        malformed["imt_names"] = ["PGA"]
        malformed["imt_count"] = True
        with self.assertRaisesRegex(subject.Group2ImtProfileActionError, "IMT count drifted"):
            subject._validate_profile(malformed)

    def test_terminal_parser_accepts_only_exact_execution_result(self) -> None:
        result = subject._run_profile(execution_sha=EXECUTION_SHA, acquirer=_profile)
        body = subject.RESULT_MARKER + "\n" + json.dumps(result, separators=(",", ":"))
        self.assertTrue(subject._parse_trusted_terminal_result(body, execution_sha=EXECUTION_SHA))
        self.assertFalse(subject._parse_trusted_terminal_result(body, execution_sha="3" * 40))


if __name__ == "__main__":
    unittest.main()
