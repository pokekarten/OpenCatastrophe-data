# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_scenario_v10_greece_rupture_profile_action as subject

SHA = "a" * 40


def request_body(**updates):
    value = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": 285,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "receipt_sha256": subject.EXPECTED_SHA256,
        "requester": "CHAT-TEST",
    }
    value.update(updates)
    return subject.REQUEST_MARKER + "\n" + json.dumps(value, separators=(",", ":"))


def receipt():
    return {
        "retrieved_at": "2026-08-20T10:00:00Z",
        "byte_count": 666,
        "sha256": subject.EXPECTED_SHA256,
        "git_blob_sha1": "fa3bfd7aedfb63869c5808785b0ca712b6e45859",
        "content_type": "text/plain; charset=utf-8",
        "etag": None,
    }


def profile(**updates):
    value = {
        "schema_version": "oc-esrm20-scenario-v10-greece-rupture-profile-v1",
        "byte_count": 666,
        "sha256": subject.EXPECTED_SHA256,
        "nrml_namespace": "http://openquake.org/xmlns/nrml/0.5",
        "rupture_element_local_name": "singlePlaneRupture",
        "element_count": 8,
        "max_depth": 4,
        "magnitude_element_count": 1,
        "rake_element_count": 1,
        "hypocenter_element_count": 1,
        "provider_file_content_profiled": True,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }
    value.update(updates)
    return value


class ActionTests(unittest.TestCase):
    def test_request_is_exact_head_and_receipt_bound(self):
        parsed = subject.validate_request(
            request_body(),
            expected_issue=285,
            execution_sha=SHA,
        )
        self.assertEqual(parsed["requester"], "CHAT-TEST")
        for updates in (
            {"target_sha": "b" * 40},
            {"receipt_sha256": "0" * 64},
            {"issue": 999},
            {"dataset_id": "other"},
        ):
            with self.subTest(updates=updates), self.assertRaises(
                subject.GreeceRuptureProfileActionError
            ):
                subject.validate_request(
                    request_body(**updates),
                    expected_issue=285,
                    execution_sha=SHA,
                )

    def test_request_has_no_provider_ref_path_or_event_selector(self):
        parsed = subject.validate_request(
            request_body(),
            expected_issue=285,
            execution_sha=SHA,
        )
        for forbidden in ("provider", "project_id", "ref", "path", "event_id", "url"):
            self.assertNotIn(forbidden, parsed)

    def test_duplicate_json_keys_fail_closed(self):
        body = (
            subject.REQUEST_MARKER
            + '\n{"schema_version":"x","schema_version":"y"}'
        )
        with self.assertRaisesRegex(
            subject.GreeceRuptureProfileActionError,
            "duplicate JSON key",
        ):
            subject.validate_request(body, expected_issue=285, execution_sha=SHA)

    def test_pass_profiles_only_in_memory_and_preserves_ceilings(self):
        raw = b"not-provider-bytes"
        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=lambda: (raw, receipt()),
            profiler=lambda observed: profile()
            if observed is raw
            else self.fail("raw byte object was replaced"),
        )
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertTrue(result["provider_file_content_profiled"])
        self.assertFalse(result["output_payload_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["event_location_inference_authorized"])
        self.assertFalse(result["scenario_selection_authorized"])
        self.assertFalse(result["independent_validation_established"])
        self.assertFalse(result["holdout_status_established"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertNotIn("raw", result)
        self.assertEqual(subject._validate_terminal_result(result), SHA)

    def test_acquisition_failure_has_no_partial_evidence(self):
        def fail():
            raise subject.EfehrAcquisitionError("provider secret")

        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=fail,
            profiler=lambda _: profile(),
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "acquisition_failure")
        self.assertFalse(result["provider_file_bytes_read"])
        self.assertIsNone(result["receipt"])
        self.assertIsNone(result["profile"])
        self.assertNotIn("provider secret", json.dumps(result, sort_keys=True))

    def test_byte_identity_failure_is_bounded(self):
        def fail():
            raise subject.RuptureByteIdentityError("mutated bytes: secret")

        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=fail,
            profiler=lambda _: profile(),
        )
        self.assertEqual(result["failure_class"], "byte_identity_mismatch")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["provider_file_content_profiled"])
        self.assertIsNone(result["failure_code"])
        self.assertNotIn("secret", json.dumps(result, sort_keys=True))

    def test_profile_rejection_cannot_leak_parser_text(self):
        secret = "provider-derived-xml-value"

        def reject(_):
            raise subject.RuptureProfileError(secret)

        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x", receipt()),
            profiler=reject,
        )
        self.assertEqual(result["failure_class"], "profile_failure")
        self.assertEqual(result["failure_code"], "rupture_profile_rejected")
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["provider_file_content_profiled"])
        self.assertNotIn(secret, json.dumps(result, sort_keys=True))

    def test_terminal_rejects_authority_widening(self):
        result = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x", receipt()),
            profiler=lambda _: profile(),
        )
        for field in (
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            mutated = dict(result)
            mutated[field] = True
            with self.subTest(field=field), self.assertRaises(
                subject.GreeceRuptureProfileActionError
            ):
                subject._validate_terminal_result(mutated)

    def test_profile_rejects_nested_authority_widening(self):
        for field in (
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
        ):
            with self.subTest(field=field), self.assertRaises(
                subject.GreeceRuptureProfileActionError
            ):
                subject._validate_profile(profile(**{field: True}))

    def test_terminal_rejects_arbitrary_failure_code(self):
        result = subject._base_result(SHA)
        result["failure_class"] = "profile_failure"
        result["provider_file_bytes_read"] = True
        result["failure_code"] = "provider-derived-secret"
        with self.assertRaisesRegex(
            subject.GreeceRuptureProfileActionError,
            "invalid profile failure code",
        ):
            subject._validate_terminal_result(result)

    def test_dedup_counts_only_trusted_bot_same_sha(self):
        terminal = subject._run_profile_with(
            execution_sha=SHA,
            fetcher=lambda: (b"x", receipt()),
            profiler=lambda _: profile(),
        )
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            terminal,
            sort_keys=True,
            separators=(",", ":"),
        )
        comments = [
            {"user": {"login": "someone"}, "body": body},
            {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": "noise"},
            {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": body},
        ]
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=comments,
        ):
            self.assertTrue(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=SHA,
                )
            )

    def test_profile_shape_is_closed(self):
        bad = profile(extra_field=True)
        with self.assertRaisesRegex(
            subject.GreeceRuptureProfileActionError,
            "profile fields drifted",
        ):
            subject._validate_profile(bad)


if __name__ == "__main__":
    unittest.main()
