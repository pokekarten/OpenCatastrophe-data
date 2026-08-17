# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from scripts import run_esrm20_kosovo_site_domain_profile_action as subject

SHA = "a" * 40


def _request(**overrides: object) -> str:
    payload = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "unit-test",
    }
    payload.update(overrides)
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    )


def _common(*, contract: str) -> dict[str, object]:
    return {
        "occurrence_count": subject.EXPECTED_SITE_COUNT,
        "static_domain_match_count": subject.EXPECTED_SITE_COUNT,
        "static_domain_reject_count": 0,
        "static_contract": contract,
    }


def _payload() -> dict[str, object]:
    count = subject.EXPECTED_SITE_COUNT
    domain_profile = {
        "schema_version": subject._domain.SCHEMA_VERSION,
        "openquake_reference": {
            "tag": subject._domain.OPENQUAKE_TAG,
            "commit": subject._domain.OPENQUAKE_COMMIT,
        },
        "required_site_parameter_names": list(subject._domain.REQUIRED_PARAMETERS),
        "site_count": count,
        "parameter_domains": {
            "vs30": {
                **_common(contract="finite_decimal_and_gt_zero"),
                "finite_decimal_count": count,
                "positive_finite_count": count,
            },
            "xvf": {
                **_common(contract="finite_decimal_only"),
                "finite_decimal_count": count,
                "branch_specific_semantics_required": True,
            },
            "region": {
                **_common(contract="integral_numeric_inclusive_0_to_5"),
                "finite_decimal_count": count,
                "integral_numeric_count": count,
                "inclusive_min": subject._domain.REGION_MIN,
                "inclusive_max": subject._domain.REGION_MAX,
            },
            "slope": {
                **_common(contract="finite_decimal_with_model_clamping"),
                "finite_decimal_count": count,
                "below_clamp_floor_count": 0,
                "within_clamp_interval_count": count,
                "above_clamp_ceiling_count": 0,
                "clamp_floor": str(subject._domain.SLOPE_CLAMP_FLOOR),
                "clamp_ceiling": str(subject._domain.SLOPE_CLAMP_CEILING),
            },
            "geology": {
                **_common(contract="nonempty_label_with_fixed_effects_fallback"),
                "nonempty_count": count,
                "recognized_calibrated_label_count": count,
                "fixed_effects_fallback_label_count": 0,
                "recognized_calibrated_labels": sorted(subject._domain.RECOGNIZED_GEOLOGY_LABELS),
            },
        },
        "static_domain_reject_total": 0,
        "static_domain_classification_complete": True,
        "raw_xml_returned": False,
        "raw_attribute_values_returned": False,
        "raw_site_rows_returned": False,
        "openquake_runtime_value_acceptance_verified": False,
        "crs_coordinate_semantics_verified": False,
        "missingness_semantics_verified": False,
        "gsim_site_parameter_sufficiency_verified": False,
        "site_adjusted_reference_authorized": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    return {
        "schema_version": subject._domain.SCHEMA_VERSION,
        "source_issue": subject.CONTROL_ISSUE,
        "site_profile_issue": subject.SITE_PROFILE_ISSUE,
        "site_structure_result_comment_id": subject._domain.SITE_STRUCTURE_RESULT_COMMENT_ID,
        "required_parameter_handoff_comment_id": subject._domain.REQUIRED_PARAMETER_HANDOFF_COMMENT_ID,
        "xvf_semantics_comment_id": subject._domain.XVF_SEMANTICS_COMMENT_ID,
        "site_identity": {
            "project_id": subject.PROJECT_ID,
            "project_path": subject.PROJECT_PATH,
            "commit_sha": subject.COMMIT_SHA,
            "repository_path": subject.REPOSITORY_PATH,
            "byte_count": subject.EXPECTED_BYTE_COUNT,
            "sha256": subject.EXPECTED_SHA256,
            "receipt_comment_id": subject.RECEIPT_COMMENT_ID,
        },
        "domain_profile": domain_profile,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class KosovoSiteDomainActionTests(unittest.TestCase):
    def test_request_is_exactly_bound_to_issue_dataset_and_execution_sha(self) -> None:
        parsed = subject.validate_request(
            _request(), expected_issue=subject.CONTROL_ISSUE, execution_sha=SHA
        )
        self.assertEqual(parsed["action"], subject.ACTION)
        for bad in (
            _request(issue=459),
            _request(dataset_id="other"),
            _request(target_sha="b" * 40),
        ):
            with self.subTest(bad=bad), self.assertRaises(subject.SiteDomainActionError):
                subject.validate_request(
                    bad, expected_issue=subject.CONTROL_ISSUE, execution_sha=SHA
                )

    def test_valid_count_only_payload_preserves_all_authority_ceilings(self) -> None:
        result = subject._run_site_domain(execution_sha=SHA, acquirer=_payload)
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["failure_class"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["openquake_runtime_value_acceptance_verified"])
        self.assertFalse(result["crs_coordinate_semantics_verified"])
        self.assertFalse(result["missingness_semantics_verified"])
        self.assertFalse(result["gsim_site_parameter_sufficiency_verified"])
        self.assertFalse(result["site_adjusted_reference_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        profile = result["profile"]["domain_profile"]
        self.assertFalse(profile["raw_xml_returned"])
        self.assertFalse(profile["raw_attribute_values_returned"])
        self.assertFalse(profile["raw_site_rows_returned"])

    def test_count_relationship_mutation_fails_closed(self) -> None:
        payload = _payload()
        payload["domain_profile"]["parameter_domains"]["vs30"]["positive_finite_count"] = 36
        with self.assertRaisesRegex(subject.SiteDomainActionError, "vs30 count relationship"):
            subject._validate_domain_payload(payload)

        payload = _payload()
        payload["domain_profile"]["parameter_domains"]["slope"]["within_clamp_interval_count"] = 36
        with self.assertRaisesRegex(subject.SiteDomainActionError, "slope count relationship"):
            subject._validate_domain_payload(payload)

    def test_raw_or_runtime_authority_mutation_fails_closed(self) -> None:
        for field in (
            "raw_xml_returned",
            "raw_attribute_values_returned",
            "raw_site_rows_returned",
            "openquake_runtime_value_acceptance_verified",
            "gsim_site_parameter_sufficiency_verified",
            "site_adjusted_reference_authorized",
            "publication_authorized",
            "model_use_authorized",
        ):
            payload = _payload()
            payload["domain_profile"][field] = True
            with self.subTest(field=field), self.assertRaises(subject.SiteDomainActionError):
                subject._validate_domain_payload(payload)

    def test_xvf_branch_specific_semantics_cannot_be_promoted_away(self) -> None:
        payload = _payload()
        payload["domain_profile"]["parameter_domains"]["xvf"][
            "branch_specific_semantics_required"
        ] = False
        with self.assertRaisesRegex(subject.SiteDomainActionError, "xvf semantics"):
            subject._validate_domain_payload(payload)

    def test_acquisition_and_content_failures_are_distinct_and_bounded(self) -> None:
        def acquisition_failure() -> dict[str, object]:
            raise subject.SiteDomainAcquisitionError("provider unavailable")

        result = subject._run_site_domain(execution_sha=SHA, acquirer=acquisition_failure)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["profile"])

        def content_failure() -> dict[str, object]:
            raise subject.SiteDomainContentError("exact bytes failed bounded classifier")

        result = subject._run_site_domain(execution_sha=SHA, acquirer=content_failure)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "domain_profile_failure")
        self.assertIsNone(result["profile"])

    def test_dedup_trusts_only_actions_bot_and_exact_execution(self) -> None:
        result = subject._run_site_domain(execution_sha=SHA, acquirer=_payload)
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        comments = [
            {"id": 1, "user": {"login": "pokekarten"}, "body": body},
            {"id": 2, "user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": body},
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                subject.has_terminal_site_domain_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )
            )

    def test_trusted_malformed_terminal_result_fails_closed(self) -> None:
        comments = [
            {
                "id": 2,
                "user": {"login": subject.TRUSTED_RESULT_LOGIN},
                "body": subject.RESULT_MARKER + "\n{}",
            }
        ]
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            with self.assertRaises(subject.SiteDomainActionError):
                subject.has_terminal_site_domain_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="x",
                    execution_sha=SHA,
                )

    def test_contract_binds_merged_domain_and_existing_fixed_transport(self) -> None:
        subject._require_contract()
        self.assertEqual(subject.EXPECTED_BYTE_COUNT, 5_891)
        self.assertEqual(
            subject.EXPECTED_SHA256,
            "746cf75d91507da8b55a9476c61bb5d884eed42c6268a36b1179f432e8850edd",
        )
        self.assertEqual(subject.EXPECTED_SITE_COUNT, 37)
        self.assertEqual(
            subject._domain.OPENQUAKE_COMMIT,
            "9f044c93d72846421a8faa90ebf0a6afacdf3c20",
        )

    def test_workflow_isolates_trusted_request_from_comment_noise_before_job_gate(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "esrm20-kosovo-site-domain-profile.yml"
        ).read_text(encoding="utf-8")
        header, jobs = workflow.split("\njobs:\n", 1)
        self.assertTrue(jobs)
        self.assertIn("concurrency:", header)
        self.assertIn("github.event.issue.number == 291", header)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            header,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", header)
        self.assertIn(subject.REQUEST_MARKER, header)
        self.assertIn("'trusted-request'", header)
        self.assertIn("format('noise-{0}', github.event.comment.id)", header)
        self.assertIn("cancel-in-progress: false", header)


if __name__ == "__main__":
    unittest.main()
