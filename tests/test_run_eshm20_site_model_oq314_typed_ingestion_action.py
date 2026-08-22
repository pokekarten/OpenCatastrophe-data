# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from scripts import acquire_eshm20_site_model_profile as site_authority
from scripts import run_eshm20_site_model_oq314_typed_ingestion_action as subject

SHA = "a" * 40
OTHER_SHA = "b" * 40
RUNTIME_DIGEST = "sha256:" + "c" * 64
BOOTSTRAP_DIGEST = "openquake/engine@sha256:" + "d" * 64


def request(**updates: object) -> str:
    value = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.CONTROL_ISSUE,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "requester": "test-281",
    }
    value.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        value, sort_keys=True, separators=(",", ":")
    )


def runtime(**updates: str) -> dict[str, str]:
    value = {
        "commit": subject.OPENQUAKE_COMMIT,
        "version": "3.14.0-git-test",
        "runtime_image_digest": RUNTIME_DIGEST,
        "bootstrap_repo_digest": BOOTSTRAP_DIGEST,
    }
    value.update(updates)
    return value


def evidence(**updates: object) -> dict[str, object]:
    value: dict[str, object] = {
        "parser": "openquake.commonlib.readinput.get_site_model/csv",
        "record_count": subject.EXPECTED_RECORD_COUNT,
        "input_header": list(subject.EXPECTED_HEADER),
        "typed_fields": [
            {"name": name, "dtype": subject.EXPECTED_DTYPES[name]}
            for name in subject.EXPECTED_HEADER
        ],
        "mode_a_required_site_parameters": list(
            subject.MODE_A_REQUIRED_SITE_PARAMETERS
        ),
        "mode_a_required_fields_typed": True,
        "rounded_coordinate_duplicate_check_passed": True,
        "site_collection_construction_passed": True,
        "longitude_point_domain_valid": True,
        "latitude_point_domain_valid": True,
        "vs30_positive_finite": True,
        "vs30measured_boolean_typed": True,
        "region_observed_support_exact_0_through_5": True,
        "xvf_finite": True,
        "raw_values_returned": False,
    }
    value.update(updates)
    return value


def run_result(execution_sha: str = SHA) -> dict[str, object]:
    return subject.run_typed_ingestion(
        execution_sha=execution_sha,
        runtime_image_digest=RUNTIME_DIGEST,
        bootstrap_repo_digest=BOOTSTRAP_DIGEST,
        acquirer=lambda: b"synthetic-exact-site-bytes",
        identity_verifier=lambda _payload: site_authority.EXPECTED_SHA256,
        runtime_inspector=lambda **_kwargs: runtime(),
        ingestor=lambda _payload: evidence(),
    )


def terminal_body(execution_sha: str = SHA) -> str:
    return subject.RESULT_MARKER + "\n" + json.dumps(
        run_result(execution_sha), sort_keys=True, separators=(",", ":")
    )


class TypedSiteIngestionActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_execution_sha(self):
        parsed = subject.validate_request(
            request(), expected_issue=subject.CONTROL_ISSUE, execution_sha=SHA
        )
        self.assertEqual(parsed["action"], subject.ACTION)
        for mutated in (
            request(issue=282),
            request(dataset_id="other"),
            request(target_sha=OTHER_SHA),
        ):
            with self.assertRaises(subject.TypedSiteIngestionActionError):
                subject.validate_request(
                    mutated,
                    expected_issue=subject.CONTROL_ISSUE,
                    execution_sha=SHA,
                )

    def test_request_duplicate_key_and_nonfinite_constant_fail_closed(self):
        duplicate = subject.REQUEST_MARKER + '\n{"issue":281,"issue":281}'
        with self.assertRaises(subject.TypedSiteIngestionActionError):
            subject.validate_request(
                duplicate,
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=SHA,
            )
        nonfinite = request().replace('"issue":281', '"issue":NaN')
        with self.assertRaises(subject.TypedSiteIngestionActionError):
            subject.validate_request(
                nonfinite,
                expected_issue=subject.CONTROL_ISSUE,
                execution_sha=SHA,
            )

    def test_pass_is_exact_byte_and_runtime_bound_with_authority_closed(self):
        result = run_result()
        subject._validate_terminal_result(result, execution_sha=SHA)
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["exact_site_bytes_verified"], True)
        self.assertIs(result["openquake_typed_ingestion_verified"], True)
        self.assertIs(
            result["bounded_dtype_value_and_observed_support_verified"], True
        )
        self.assertEqual(
            result["source_identity"]["sha256"], site_authority.EXPECTED_SHA256
        )
        self.assertEqual(
            result["openquake_reference"]["commit"], subject.OPENQUAKE_COMMIT
        )
        for field in subject._FALSE_CEILINGS:
            self.assertIs(result[field], False)

    def test_region_evidence_is_observed_support_not_oq_validity_domain(self):
        result = run_result()
        typed = result["typed_ingestion"]
        self.assertIsInstance(typed, dict)
        self.assertIs(typed["region_observed_support_exact_0_through_5"], True)
        self.assertNotIn("region_domain_exact_0_through_5", typed)
        self.assertIn("bounded_dtype_value_and_observed_support_verified", result)
        self.assertNotIn("mode_a_required_field_dtype_domain_verified", result)

    def test_byte_identity_failure_blocks_before_ingestor_and_leaks_no_reason(self):
        calls: list[str] = []

        def reject_identity(_payload: bytes) -> str:
            calls.append("identity")
            raise site_authority.Eshm20SiteModelProfileError(
                "secret-provider-value"
            )

        def forbidden_ingestor(_payload: bytes) -> dict[str, object]:
            calls.append("ingestor")
            return evidence()

        result = subject.run_typed_ingestion(
            execution_sha=SHA,
            runtime_image_digest=RUNTIME_DIGEST,
            bootstrap_repo_digest=BOOTSTRAP_DIGEST,
            acquirer=lambda: b"mutated",
            identity_verifier=reject_identity,
            runtime_inspector=lambda **_kwargs: runtime(),
            ingestor=forbidden_ingestor,
        )
        self.assertEqual(calls, ["identity"])
        self.assertEqual(
            result["failure_class"],
            "site_byte_identity_or_acquisition_rejected",
        )
        self.assertIs(result["exact_site_bytes_verified"], False)
        self.assertIs(result["openquake_typed_ingestion_verified"], False)
        self.assertIsNone(result["typed_ingestion"])
        self.assertNotIn(
            "secret-provider-value", json.dumps(result, sort_keys=True)
        )
        subject._validate_terminal_result(result, execution_sha=SHA)

    def test_parser_rejection_preserves_proven_byte_identity(self):
        def rejected(_payload: bytes) -> dict[str, object]:
            raise subject.TypedSiteIngestionBlocked("raw-value-must-not-leak")

        blocked = subject.run_typed_ingestion(
            execution_sha=SHA,
            runtime_image_digest=RUNTIME_DIGEST,
            bootstrap_repo_digest=BOOTSTRAP_DIGEST,
            acquirer=lambda: b"payload",
            identity_verifier=lambda _payload: site_authority.EXPECTED_SHA256,
            runtime_inspector=lambda **_kwargs: runtime(),
            ingestor=rejected,
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(
            blocked["failure_class"], "typed_site_ingestion_rejected"
        )
        self.assertIs(blocked["exact_site_bytes_verified"], True)
        self.assertIs(blocked["openquake_typed_ingestion_verified"], False)
        self.assertIs(
            blocked["bounded_dtype_value_and_observed_support_verified"], False
        )
        self.assertIsNone(blocked["typed_ingestion"])
        self.assertNotIn(
            "raw-value-must-not-leak", json.dumps(blocked, sort_keys=True)
        )
        subject._validate_terminal_result(blocked, execution_sha=SHA)

    def test_runtime_contract_drift_is_not_downgraded_to_blocked(self):
        with self.assertRaises(subject.TypedSiteIngestionActionError):
            subject.run_typed_ingestion(
                execution_sha=SHA,
                runtime_image_digest=RUNTIME_DIGEST,
                bootstrap_repo_digest=BOOTSTRAP_DIGEST,
                acquirer=lambda: b"payload",
                identity_verifier=lambda _payload: site_authority.EXPECTED_SHA256,
                runtime_inspector=lambda **_kwargs: runtime(commit="f" * 40),
                ingestor=lambda _payload: evidence(),
            )

    def test_scientifically_material_evidence_mutations_fail_closed(self):
        mutations: dict[str, object] = {
            "parser": "pandas.read_csv",
            "record_count": subject.EXPECTED_RECORD_COUNT - 1,
            "input_header": list(reversed(subject.EXPECTED_HEADER)),
            "mode_a_required_site_parameters": ["vs30"],
            "mode_a_required_fields_typed": False,
            "rounded_coordinate_duplicate_check_passed": False,
            "site_collection_construction_passed": False,
            "longitude_point_domain_valid": False,
            "latitude_point_domain_valid": False,
            "vs30_positive_finite": False,
            "vs30measured_boolean_typed": False,
            "region_observed_support_exact_0_through_5": False,
            "xvf_finite": False,
            "raw_values_returned": True,
        }
        for field, bad in mutations.items():
            with self.subTest(field=field), self.assertRaises(
                subject.TypedSiteIngestionActionError
            ):
                subject._validate_evidence(evidence(**{field: bad}))

        bad_dtype = evidence()
        bad_dtype["typed_fields"][2]["dtype"] = "int64"
        with self.assertRaises(subject.TypedSiteIngestionActionError):
            subject._validate_evidence(bad_dtype)

    def test_terminal_parser_and_issue_local_dedup_are_sha_specific(self):
        body = terminal_body(SHA)
        self.assertTrue(
            subject._parse_trusted_terminal_result(body, execution_sha=SHA)
        )
        self.assertFalse(
            subject._parse_trusted_terminal_result(body, execution_sha=OTHER_SHA)
        )
        self.assertFalse(
            subject._parse_trusted_terminal_result(
                "ordinary comment", execution_sha=SHA
            )
        )
        with self.assertRaises(subject.TypedSiteIngestionActionError):
            subject._parse_trusted_terminal_result(
                body + "\n" + subject.RESULT_MARKER,
                execution_sha=SHA,
            )

        prior = {
            "user": {"login": subject.TRUSTED_RESULT_LOGIN},
            "body": terminal_body(OTHER_SHA),
        }
        current = {
            "user": {"login": subject.TRUSTED_RESULT_LOGIN},
            "body": terminal_body(SHA),
        }
        with patch.object(
            subject, "fetch_repository_comments", return_value=[prior]
        ):
            self.assertFalse(
                subject.has_terminal_typed_ingestion_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=SHA,
                )
            )
        with patch.object(
            subject,
            "fetch_repository_comments",
            return_value=[prior, current],
        ):
            self.assertTrue(
                subject.has_terminal_typed_ingestion_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=SHA,
                )
            )


if __name__ == "__main__":
    unittest.main()
