# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import http.client
import json
import unittest
from unittest import mock

from scripts import acquire_efehr_esrm20_athens_job_config_profile as job


SHA = "a" * 40


def _ini(structural_key: str = "structural_vulnerability_file") -> bytes:
    return (
        "[general]\n"
        "calculation_mode = scenario_risk\n"
        "random_seed = 45\n"
        "\n"
        "[risk]\n"
        f"{structural_key} = ../vulnerability/"
        "vulnerability_total-repl-cost_ESRM20_VariousIM.xml\n"
        "occupants_vulnerability_file = ../vulnerability/"
        "vulnerability_loss-of-life_ESRM20_VariousIM_day.xml\n"
    ).encode("utf-8")


class ProfileBindingsTests(unittest.TestCase):
    def test_accepts_explicit_structural_and_occupants_bindings(self) -> None:
        profile = job.profile_bindings(_ini())
        self.assertTrue(profile["vulnerability_binding_verified"])
        self.assertEqual(
            profile["bindings"],
            [
                {
                    "config_key": "structural_vulnerability_file",
                    "role": "structural",
                    "repository_path": job.STRUCTURAL_TARGET,
                },
                {
                    "config_key": "occupants_vulnerability_file",
                    "role": "occupants",
                    "repository_path": job.OCCUPANTS_TARGET,
                },
            ],
        )
        self.assertFalse(profile["raw_config_returned"])
        self.assertFalse(profile["vulnerability_model_content_verified"])
        self.assertFalse(profile["benchmark_agreement_inspected"])
        self.assertFalse(profile["independent_validation_established"])
        self.assertFalse(profile["holdout_status_established"])
        self.assertFalse(profile["publication_authorized"])
        self.assertFalse(profile["model_use_authorized"])

    def test_rejects_generic_vulnerability_file_as_structural_alias(self) -> None:
        with self.assertRaises(job.AthensJobConfigContentError):
            job.profile_bindings(_ini("vulnerability_file"))

    def test_rejects_repeated_structural_binding(self) -> None:
        raw = _ini() + (
            b"structural_vulnerability_file = ../vulnerability/"
            b"vulnerability_total-repl-cost_ESRM20_VariousIM.xml\n"
        )
        with self.assertRaises(job.AthensJobConfigContentError):
            job.profile_bindings(raw)

    def test_rejects_unknown_vulnerability_key(self) -> None:
        raw = _ini().replace(
            b"occupants_vulnerability_file",
            b"fatalities_vulnerability_file",
        )
        with self.assertRaises(job.AthensJobConfigContentError):
            job.profile_bindings(raw)

    def test_rejects_wrong_case_vulnerability_key(self) -> None:
        raw = _ini().replace(
            b"occupants_vulnerability_file",
            b"Occupants_vulnerability_file",
        )
        with self.assertRaises(job.AthensJobConfigContentError):
            job.profile_bindings(raw)

    def test_rejects_repeated_binding_across_sections(self) -> None:
        raw = _ini() + (
            b"\n[duplicate]\n"
            b"occupants_vulnerability_file = ../vulnerability/"
            b"vulnerability_loss-of-life_ESRM20_VariousIM_day.xml\n"
        )
        with self.assertRaises(job.AthensJobConfigContentError):
            job.profile_bindings(raw)

    def test_rejects_swapped_targets(self) -> None:
        raw = _ini().replace(
            b"vulnerability_total-repl-cost_ESRM20_VariousIM.xml",
            b"vulnerability_loss-of-life_ESRM20_VariousIM_day.xml",
        )
        with self.assertRaises(job.AthensJobConfigContentError):
            job.profile_bindings(raw)

    def test_rejects_path_traversal_to_other_repository_object(self) -> None:
        raw = _ini().replace(
            b"../vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml",
            b"../../README.md",
        )
        with self.assertRaises(job.AthensJobConfigContentError):
            job.profile_bindings(raw)

    def test_rejects_absolute_and_scheme_paths(self) -> None:
        for target in (b"/tmp/value.xml", b"https://example.invalid/value.xml"):
            with self.subTest(target=target):
                raw = _ini().replace(
                    b"../vulnerability/"
                    b"vulnerability_total-repl-cost_ESRM20_VariousIM.xml",
                    target,
                )
                with self.assertRaises(job.AthensJobConfigContentError):
                    job.profile_bindings(raw)

    def test_rejects_windows_style_path(self) -> None:
        raw = _ini().replace(
            b"../vulnerability/vulnerability_total-repl-cost_ESRM20_VariousIM.xml",
            b"..\\vulnerability\\value.xml",
        )
        with self.assertRaises(job.AthensJobConfigContentError):
            job.profile_bindings(raw)

    def test_rejects_non_utf8_and_nul(self) -> None:
        for raw in (b"[general]\nkey=\xff\n", b"[general]\nkey=a\x00b\n"):
            with self.subTest(raw=raw):
                with self.assertRaises(job.AthensJobConfigContentError):
                    job.profile_bindings(raw)

    def test_rejects_utf8_bom(self) -> None:
        with self.assertRaises(job.AthensJobConfigContentError):
            job.profile_bindings(b"\xef\xbb\xbf" + _ini())

    def test_rejects_malformed_and_empty_ini(self) -> None:
        for raw in (b"not-an-ini\n", b""):
            with self.subTest(raw=raw):
                with self.assertRaises(job.AthensJobConfigContentError):
                    job.profile_bindings(raw)


class IdentityTests(unittest.TestCase):
    def test_git_blob_identity_matches_git_object_definition(self) -> None:
        raw = b"abc"
        expected = hashlib.sha1(b"blob 3\x00abc").hexdigest()  # noqa: S324
        self.assertEqual(job.git_blob_sha1(raw), expected)

    def test_identity_rejects_byte_count_drift_before_content_parse(self) -> None:
        with self.assertRaises(job.AthensJobConfigAcquisitionError):
            job.verify_exact_identity(_ini())

    def test_identity_accepts_matching_synthetic_contract_when_fenced(self) -> None:
        raw = _ini()
        blob = job.git_blob_sha1(raw)
        with (
            mock.patch.object(job, "_require_contract", return_value=None),
            mock.patch.object(job, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(job, "GIT_BLOB_SHA1", blob),
        ):
            observed = job.verify_exact_identity(raw)
        self.assertEqual(observed, hashlib.sha256(raw).hexdigest())

    def test_identity_rejects_matching_length_wrong_blob(self) -> None:
        raw = _ini()
        with (
            mock.patch.object(job, "_require_contract", return_value=None),
            mock.patch.object(job, "EXPECTED_BYTE_COUNT", len(raw)),
            mock.patch.object(job, "GIT_BLOB_SHA1", "0" * 40),
        ):
            with self.assertRaises(job.AthensJobConfigAcquisitionError):
                job.verify_exact_identity(raw)


class RequestTests(unittest.TestCase):
    def _body(self, **updates: object) -> str:
        payload: dict[str, object] = {
            "schema_version": job.REQUEST_SCHEMA_VERSION,
            "action": job.ACTION,
            "issue": job.SOURCE_ISSUE,
            "target_sha": SHA,
            "dataset_id": job.DATASET_ID,
            "requester": "test-agent",
        }
        payload.update(updates)
        return job.REQUEST_MARKER + "\n" + json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        )

    def test_accepts_exact_request(self) -> None:
        request = job.validate_request(
            self._body(),
            expected_issue=job.SOURCE_ISSUE,
            execution_sha=SHA,
        )
        self.assertEqual(request["target_sha"], SHA)

    def test_rejects_target_sha_drift(self) -> None:
        with self.assertRaises(job.AthensJobConfigContractError):
            job.validate_request(
                self._body(target_sha="b" * 40),
                expected_issue=job.SOURCE_ISSUE,
                execution_sha=SHA,
            )

    def test_rejects_extra_field(self) -> None:
        with self.assertRaises(job.AthensJobConfigContractError):
            job.validate_request(
                self._body(extra="no"),
                expected_issue=job.SOURCE_ISSUE,
                execution_sha=SHA,
            )

    def test_rejects_duplicate_json_key(self) -> None:
        body = (
            job.REQUEST_MARKER
            + '\n{"schema_version":"'
            + job.REQUEST_SCHEMA_VERSION
            + '","schema_version":"'
            + job.REQUEST_SCHEMA_VERSION
            + '","action":"'
            + job.ACTION
            + '","issue":285,"target_sha":"'
            + SHA
            + '","dataset_id":"'
            + job.DATASET_ID
            + '","requester":"test-agent"}'
        )
        with self.assertRaises(job.AthensJobConfigContractError):
            job.validate_request(
                body,
                expected_issue=job.SOURCE_ISSUE,
                execution_sha=SHA,
            )

    def test_rejects_non_finite_json(self) -> None:
        body = self._body().replace('"requester":"test-agent"', '"requester":NaN')
        with self.assertRaises(job.AthensJobConfigContractError):
            job.validate_request(
                body,
                expected_issue=job.SOURCE_ISSUE,
                execution_sha=SHA,
            )


class ResultTests(unittest.TestCase):
    def _evidence(self) -> dict[str, object]:
        return {
            "schema_version": "oc-esrm20-athens-job-config-profile-evidence-v1",
            "source_issue": job.SOURCE_ISSUE,
            "parent_consumer_issue": job.PARENT_CONSUMER_ISSUE,
            "dataset_id": job.DATASET_ID,
            **job._identity(),
            "sha256": "1" * 64,
            "profile": job.profile_bindings(_ini()),
            "provider_file_bytes_read": True,
            "provider_file_content_profiled": True,
            "external_bytes_persisted": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }

    def test_pass_result_preserves_authority_ceilings(self) -> None:
        result = job._run(execution_sha=SHA, acquirer=self._evidence)
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["failure_class"])
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["provider_file_content_profiled"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["vulnerability_model_content_verified"])
        self.assertFalse(result["benchmark_agreement_inspected"])
        self.assertFalse(result["independent_validation_established"])
        self.assertFalse(result["holdout_status_established"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_acquisition_failure_is_static_and_does_not_overclaim_reads(self) -> None:
        def fail() -> dict[str, object]:
            raise job.AthensJobConfigAcquisitionError("provider detail")

        result = job._run(execution_sha=SHA, acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertFalse(result["provider_file_content_profiled"])
        self.assertIsNone(result["evidence"])
        self.assertNotIn("provider detail", json.dumps(result))

    def test_incomplete_http_read_is_bounded_acquisition_failure(self) -> None:
        response = mock.MagicMock()
        response_context = mock.MagicMock()
        response_context.__enter__.return_value = response
        opener = mock.Mock(return_value=response_context)

        with (
            mock.patch.object(job, "_require_contract", return_value=None),
            mock.patch.object(job, "_validate_exact_response", return_value=None),
            mock.patch.object(
                job,
                "_read_bounded",
                side_effect=http.client.IncompleteRead(b"provider detail", 7),
            ),
        ):
            result = job._run(
                execution_sha=SHA,
                acquirer=lambda: job._acquire_and_profile_for_test(
                    opener=opener,
                    monotonic=lambda: 0.0,
                ),
            )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertIsNone(result["provider_file_bytes_read"])
        self.assertFalse(result["provider_file_content_profiled"])
        self.assertIsNone(result["evidence"])
        encoded = json.dumps(result)
        self.assertNotIn("provider detail", encoded)
        self.assertNotIn("IncompleteRead", encoded)

    def test_profile_failure_is_static_after_verified_read(self) -> None:
        def fail() -> dict[str, object]:
            raise job.AthensJobConfigContentError("provider content detail")

        result = job._run(execution_sha=SHA, acquirer=fail)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["provider_file_content_profiled"])
        self.assertIsNone(result["evidence"])
        self.assertNotIn("provider content detail", json.dumps(result))

    def test_trusted_terminal_parser_matches_only_exact_execution_sha(self) -> None:
        result = job._run(execution_sha=SHA, acquirer=self._evidence)
        body = job.RESULT_MARKER + "\n" + json.dumps(
            result, sort_keys=True, separators=(",", ":")
        )
        self.assertTrue(job._parse_terminal(body, execution_sha=SHA))
        self.assertFalse(job._parse_terminal(body, execution_sha="b" * 40))

    def test_malformed_trusted_terminal_fails_closed(self) -> None:
        with self.assertRaises(job.AthensJobConfigContractError):
            job._parse_terminal(
                job.RESULT_MARKER + "\n{}",
                execution_sha=SHA,
            )


if __name__ == "__main__":
    unittest.main()
