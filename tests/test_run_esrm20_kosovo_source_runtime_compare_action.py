# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_source_runtime_compare_action as subject


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
    return subject.REQUEST_MARKER + "\n" + json.dumps(request, separators=(",", ":"))


def good_comparison() -> dict[str, object]:
    numeric: list[dict[str, object]] = []
    for index, (source_field, runtime_field) in enumerate(
        subject.comparison.NUMERIC_FIELD_PAIRS
    ):
        numeric.append(
            {
                "source_field": source_field,
                "runtime_field": runtime_field,
                "record_count": subject.comparison.EXPECTED_RECORD_COUNT,
                "exact_decimal_equal_count": subject.comparison.EXPECTED_RECORD_COUNT,
                "non_equal_count": 0,
                "all_exact_decimal_equal": True,
                "maximum_absolute_difference": "0",
                "relation_sha256": f"{index + 1:x}" * 64,
            }
        )
    return {
        "schema_version": subject.comparison.SCHEMA_VERSION,
        "record_count": subject.comparison.EXPECTED_RECORD_COUNT,
        "canonical_receipt_pair_verified": True,
        "source_identity": subject._comparison_identity(subject.source_profile),
        "runtime_identity": subject._comparison_identity(subject.runtime_profile),
        "comparison_key": {
            "source_fields": [
                source for source, _runtime in subject.comparison.KEY_FIELD_PAIRS
            ],
            "runtime_fields": [
                runtime for _source, runtime in subject.comparison.KEY_FIELD_PAIRS
            ],
            "provider_business_key_authorized": False,
            "source_unique_count": subject.comparison.EXPECTED_RECORD_COUNT,
            "runtime_unique_count": subject.comparison.EXPECTED_RECORD_COUNT,
            "exact_key_set_equal": True,
            "key_set_sha256": "a" * 64,
        },
        "numeric_comparisons": numeric,
        "project186_equivalence_verified": False,
        "value_structural_wiring_verified": False,
        "source_crs_datum_epsg_verified": False,
        "insured_value_semantics_verified": False,
        "external_bytes_persisted": False,
        "raw_rows_returned": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class SourceRuntimeCompareActionTests(unittest.TestCase):
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
            with self.assertRaises(subject.SourceRuntimeCompareActionError):
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
        with self.assertRaises(subject.SourceRuntimeCompareActionError):
            subject.validate_request(duplicate, expected_issue=282, execution_sha=SHA)
        with self.assertRaises(subject.SourceRuntimeCompareActionError):
            subject.validate_request(
                "prefix\n" + request_body(),
                expected_issue=282,
                execution_sha=SHA,
            )

    def test_pass_keeps_all_authority_ceilings_false(self):
        evidence = good_comparison()
        with mock.patch.object(
            subject.comparison,
            "acquire_and_compare_kosovo_exposure_runtime",
            return_value=evidence,
        ):
            result = subject.run_comparison(execution_sha=SHA)
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["comparison_executed"], True)
        self.assertIs(result["canonical_receipt_pair_verified"], True)
        for field in (
            "project186_equivalence_verified",
            "value_structural_wiring_verified",
            "source_crs_datum_epsg_verified",
            "insured_value_semantics_verified",
            "external_bytes_persisted",
            "raw_rows_returned",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)
        self.assertEqual(subject._validate_terminal_result(result), SHA)

    def test_comparison_failure_blocks_without_aggregate_evidence(self):
        with mock.patch.object(
            subject.comparison,
            "acquire_and_compare_kosovo_exposure_runtime",
            side_effect=subject.comparison.ExposureRuntimeComparisonError("drift"),
        ):
            result = subject.run_comparison(execution_sha=SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "comparison_failure")
        self.assertIsNone(result["comparison"])
        self.assertIs(result["comparison_executed"], False)
        self.assertIs(result["canonical_receipt_pair_verified"], False)

    def test_comparison_rejects_receipt_or_authority_drift(self):
        for mutate in ("source_sha", "raw_rows", "count"):
            evidence = good_comparison()
            if mutate == "source_sha":
                evidence["source_identity"]["sha256"] = "0" * 64
            elif mutate == "raw_rows":
                evidence["raw_rows_returned"] = True
            else:
                evidence["numeric_comparisons"][0]["non_equal_count"] = 1
            with self.subTest(mutate=mutate):
                with self.assertRaises(subject.SourceRuntimeCompareActionError):
                    subject._validate_comparison(evidence)

    def test_comparison_allows_observed_decimal_mismatch_without_promoting_semantics(self):
        evidence = good_comparison()
        first = evidence["numeric_comparisons"][0]
        first["exact_decimal_equal_count"] = subject.comparison.EXPECTED_RECORD_COUNT - 1
        first["non_equal_count"] = 1
        first["all_exact_decimal_equal"] = False
        first["maximum_absolute_difference"] = "0.0001"
        subject._validate_comparison(evidence)
        self.assertIs(evidence["project186_equivalence_verified"], False)
        self.assertIs(evidence["value_structural_wiring_verified"], False)

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
        with mock.patch.object(subject, "fetch_repository_comments", return_value=comments):
            self.assertTrue(
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=SHA,
                )
            )

    def test_incomplete_dedup_ledger_fails_before_comparison(self):
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            side_effect=subject.LedgerError("incomplete"),
        ):
            with self.assertRaises(subject.SourceRuntimeCompareActionError):
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=SHA,
                )

    def test_workflow_is_owner_only_fixed_target_and_publisher_has_no_checkout(self):
        text = Path(
            ".github/workflows/esrm20-kosovo-source-runtime-compare.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 282", text)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            text,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", text)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", text)
        self.assertIn("Checkout exact trusted execution commit", text)
        self.assertNotIn("workflow_dispatch", text)
        self.assertNotIn("inputs:", text)
        self.assertNotIn("curl ", text)
        self.assertIn(subject.source_profile.COMMIT_SHA, text)
        self.assertIn(subject.source_profile.REPOSITORY_PATH, text)
        self.assertIn(subject.source_profile.EXPECTED_SHA256, text)
        self.assertIn(subject.runtime_profile.COMMIT_SHA, text)
        self.assertIn(subject.runtime_profile.REPOSITORY_PATH, text)
        self.assertIn(subject.runtime_profile.EXPECTED_SHA256, text)
        publisher = text.split("publish-comparison:", 1)[1]
        self.assertNotIn("actions/checkout", publisher)
        for field in (
            "project186_equivalence_verified",
            "value_structural_wiring_verified",
            "source_crs_datum_epsg_verified",
            "insured_value_semantics_verified",
            "external_bytes_persisted",
            "raw_rows_returned",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIn(f".{field} == false", publisher)

    def test_workflow_deduplicates_before_provider_comparison(self):
        text = Path(
            ".github/workflows/esrm20-kosovo-source-runtime-compare.yml"
        ).read_text(encoding="utf-8")
        execute = text.split("execute-comparison:", 1)[1].split(
            "publish-comparison:", 1
        )[0]
        self.assertLess(
            execute.index("Prove complete issue-local dedup before provider access"),
            execute.index("Compare only the two fixed receipted exposure objects"),
        )


if __name__ == "__main__":
    unittest.main()
