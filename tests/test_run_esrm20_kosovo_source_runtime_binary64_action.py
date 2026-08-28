# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_source_runtime_binary64_action as subject

SHA = "a" * 40


def request_body(
    *,
    target_sha: str = SHA,
    source_sha256: str = subject.source_profile.EXPECTED_SHA256,
    runtime_sha256: str = subject.runtime_profile.EXPECTED_SHA256,
) -> str:
    request = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": target_sha,
        "source_receipt_sha256": source_sha256,
        "runtime_receipt_sha256": runtime_sha256,
        "requester": "test-agent",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(
        request, separators=(",", ":"), sort_keys=True
    )


def good_profile() -> dict[str, object]:
    numeric = []
    for index, (source_field, runtime_field) in enumerate(
        subject.comparison.NUMERIC_FIELD_PAIRS
    ):
        numeric.append(
            {
                "source_field": source_field,
                "runtime_field": runtime_field,
                "record_count": subject.comparison.EXPECTED_RECORD_COUNT,
                "source_runtime_exact_equal_count": (
                    subject.comparison.EXPECTED_RECORD_COUNT - index
                ),
                "binary64_projection_match_count": (
                    subject.comparison.EXPECTED_RECORD_COUNT
                ),
                "binary64_projection_mismatch_count": 0,
                "all_runtime_values_match_binary64_projection": True,
                "projection_relation_sha256": f"{index + 1:x}" * 64,
            }
        )
    return {
        "schema_version": subject.profiler.SCHEMA_VERSION,
        "hypothesis": {
            "id": subject.profiler.HYPOTHESIS_ID,
            "source_parse": "python-float-from-decimal-text-ieee754-binary64",
            "render": "python-repr-shortest-roundtrip-decimal",
            "comparison": "exact-decimal-equality-to-runtime-token",
            "provider_transform_claimed": False,
        },
        "record_count": subject.comparison.EXPECTED_RECORD_COUNT,
        "canonical_receipt_pair_verified": True,
        "comparison_key_set_sha256": "a" * 64,
        "numeric_fields": numeric,
        "all_fields_numerically_consistent_with_hypothesis": True,
        "source_to_runtime_transform_lineage_verified": False,
        "provider_generator_identity_verified": False,
        "runtime_values_substitutable_with_source_values": False,
        "source_runtime_semantic_equivalence_verified": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class SourceRuntimeBinary64ActionTests(unittest.TestCase):
    def test_request_is_bound_to_current_main_and_both_receipts(self):
        parsed = subject.validate_request(
            request_body(),
            expected_issue=282,
            execution_sha=SHA,
        )
        self.assertEqual(parsed["target_sha"], SHA)
        self.assertEqual(
            parsed["source_receipt_sha256"],
            subject.source_profile.EXPECTED_SHA256,
        )
        self.assertEqual(
            parsed["runtime_receipt_sha256"],
            subject.runtime_profile.EXPECTED_SHA256,
        )
        for body in (
            request_body(target_sha="b" * 40),
            request_body(source_sha256="0" * 64),
            request_body(runtime_sha256="0" * 64),
        ):
            with self.subTest(body=body):
                with self.assertRaises(subject.SourceRuntimeBinary64ActionError):
                    subject.validate_request(
                        body,
                        expected_issue=282,
                        execution_sha=SHA,
                    )

    def test_duplicate_json_key_and_noncanonical_envelope_are_rejected(self):
        duplicate = (
            subject.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"x","schema_version":"y"}'
        )
        with self.assertRaises(subject.SourceRuntimeBinary64ActionError):
            subject.validate_request(
                duplicate,
                expected_issue=282,
                execution_sha=SHA,
            )
        with self.assertRaises(subject.SourceRuntimeBinary64ActionError):
            subject.validate_request(
                "prefix\n" + request_body(),
                expected_issue=282,
                execution_sha=SHA,
            )

    def test_pass_keeps_all_authority_ceilings_false(self):
        evidence = good_profile()
        with mock.patch.object(subject, "_acquire_profile", return_value=evidence):
            result = subject.run_profile(execution_sha=SHA)
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["profile_executed"], True)
        self.assertIs(result["canonical_receipt_pair_verified"], True)
        self.assertEqual(subject._validate_terminal_result(result), SHA)
        for field in subject._AUTHORITY_FALSE_FIELDS:
            self.assertIs(result[field], False)
            self.assertIs(result["profile"][field], False)

    def test_acquisition_failure_blocks_without_profile_evidence(self):
        with mock.patch.object(
            subject,
            "_acquire_profile",
            side_effect=subject.comparison.ExposureRuntimeComparisonError("drift"),
        ):
            result = subject.run_profile(execution_sha=SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "binary64_profile_failure")
        self.assertIsNone(result["profile"])
        self.assertIs(result["profile_executed"], False)
        self.assertIs(result["canonical_receipt_pair_verified"], False)

    def test_profile_rejects_count_relation_and_authority_drift(self):
        for mutate in ("count", "relation", "authority", "all_match"):
            evidence = good_profile()
            if mutate == "count":
                evidence["numeric_fields"][0]["binary64_projection_mismatch_count"] = 1
            elif mutate == "relation":
                evidence["numeric_fields"][0]["projection_relation_sha256"] = "bad"
            elif mutate == "authority":
                evidence["source_to_runtime_transform_lineage_verified"] = True
            else:
                evidence["numeric_fields"][0][
                    "all_runtime_values_match_binary64_projection"
                ] = False
            with self.subTest(mutate=mutate):
                with self.assertRaises(subject.SourceRuntimeBinary64ActionError):
                    subject._validate_profile(evidence)

    def test_acquire_profile_uses_only_frozen_receipt_targets(self):
        source_bytes = b"source"
        runtime_bytes = b"runtime"
        with (
            mock.patch.object(
                subject.comparison,
                "_fetch_fixed_payload",
                side_effect=[source_bytes, runtime_bytes],
            ) as fetch,
            mock.patch.object(
                subject.profiler,
                "profile_verified_exposure_binary64_projection",
                return_value=good_profile(),
            ) as profile,
        ):
            result = subject._acquire_profile()
        self.assertEqual(result["schema_version"], subject.profiler.SCHEMA_VERSION)
        self.assertEqual(fetch.call_count, 2)
        first = fetch.call_args_list[0].kwargs
        second = fetch.call_args_list[1].kwargs
        self.assertEqual(first["project_id"], subject.source_profile.PROJECT_ID)
        self.assertEqual(first["commit_sha"], subject.source_profile.COMMIT_SHA)
        self.assertEqual(
            first["repository_path"],
            subject.source_profile.REPOSITORY_PATH,
        )
        self.assertEqual(second["project_id"], subject.runtime_profile.PROJECT_ID)
        self.assertEqual(second["commit_sha"], subject.runtime_profile.COMMIT_SHA)
        self.assertEqual(
            second["repository_path"],
            subject.runtime_profile.REPOSITORY_PATH,
        )
        profile.assert_called_once_with(source_bytes, runtime_bytes)

    def test_dedup_trusts_only_bot_terminal_for_exact_execution_sha(self):
        terminal = subject._base_result(SHA)
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            terminal,
            sort_keys=True,
            separators=(",", ":"),
        )
        comments = [
            {"user": {"login": "pokekarten"}, "body": body},
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
                    token="test",
                    execution_sha=SHA,
                )
            )

    def test_incomplete_dedup_ledger_fails_before_provider_access(self):
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            side_effect=subject.LedgerError("incomplete"),
        ):
            with self.assertRaises(subject.SourceRuntimeBinary64ActionError):
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=SHA,
                )

    def test_workflow_is_owner_only_fixed_target_and_publisher_has_no_checkout(self):
        text = Path(
            ".github/workflows/esrm20-kosovo-source-runtime-binary64.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 282", text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn("ref: ${{ github.sha }}", text)
        self.assertNotIn("workflow_dispatch", text)
        self.assertNotIn("inputs:", text)
        self.assertNotIn("curl ", text)
        self.assertIn(subject.source_profile.COMMIT_SHA, text)
        self.assertIn(subject.source_profile.REPOSITORY_PATH, text)
        self.assertIn(subject.source_profile.EXPECTED_SHA256, text)
        self.assertIn(subject.runtime_profile.COMMIT_SHA, text)
        self.assertIn(subject.runtime_profile.REPOSITORY_PATH, text)
        self.assertIn(subject.runtime_profile.EXPECTED_SHA256, text)
        publisher = text.split("publish-profile:", 1)[1]
        self.assertNotIn("actions/checkout", publisher)
        self.assertIn("(.profile | keys)", publisher)
        self.assertIn("map([.source_field,.runtime_field])", publisher)
        for field in subject._AUTHORITY_FALSE_FIELDS:
            self.assertIn(f".{field} == false", publisher)

    def test_workflow_deduplicates_before_provider_access(self):
        text = Path(
            ".github/workflows/esrm20-kosovo-source-runtime-binary64.yml"
        ).read_text(encoding="utf-8")
        execute = text.split("execute-profile:", 1)[1].split(
            "publish-profile:", 1
        )[0]
        self.assertLess(
            execute.index("Prove complete issue-local dedup before provider access"),
            execute.index(
                "Test binary64 hypothesis against only the fixed receipt pair"
            ),
        )


if __name__ == "__main__":
    unittest.main()
