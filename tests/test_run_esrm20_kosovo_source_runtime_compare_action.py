# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_kosovo_source_runtime_compare_action as subject


SHA = "a" * 40


def request_body(
    *,
    source_sha256: str = subject.SOURCE_EXPECTED_SHA256,
    runtime_sha256: str = subject.RUNTIME_EXPECTED_SHA256,
) -> str:
    request = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": SHA,
        "source_dataset_id": subject.SOURCE_DATASET_ID,
        "source_receipt_sha256": source_sha256,
        "runtime_dataset_id": subject.RUNTIME_DATASET_ID,
        "runtime_receipt_sha256": runtime_sha256,
        "requester": "test-agent",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(request, separators=(",", ":"))


def good_comparison() -> dict[str, object]:
    numeric = []
    for index, (source_field, runtime_field) in enumerate(subject.NUMERIC_FIELD_PAIRS):
        numeric.append(
            {
                "source_field": source_field,
                "runtime_field": runtime_field,
                "record_count": subject.EXPECTED_RECORD_COUNT,
                "exact_decimal_equal_count": subject.EXPECTED_RECORD_COUNT,
                "non_equal_count": 0,
                "all_exact_decimal_equal": True,
                "maximum_absolute_difference": "0",
                "relation_sha256": format(index + 1, "064x"),
            }
        )
    return {
        "schema_version": subject.COMPARISON_SCHEMA_VERSION,
        "record_count": subject.EXPECTED_RECORD_COUNT,
        "canonical_receipt_pair_verified": True,
        "source_identity": subject._expected_identity(subject.source_profile),
        "runtime_identity": subject._expected_identity(subject.runtime_profile),
        "comparison_key": {
            "source_fields": [source for source, _runtime in subject.KEY_FIELD_PAIRS],
            "runtime_fields": [runtime for _source, runtime in subject.KEY_FIELD_PAIRS],
            "provider_business_key_authorized": False,
            "source_unique_count": subject.EXPECTED_RECORD_COUNT,
            "runtime_unique_count": subject.EXPECTED_RECORD_COUNT,
            "exact_key_set_equal": True,
            "key_set_sha256": "f" * 64,
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


class KosovoSourceRuntimeCompareActionTests(unittest.TestCase):
    def test_request_is_bound_to_both_exact_receipt_hashes(self):
        parsed = subject.validate_request(
            request_body(),
            expected_issue=subject.SOURCE_ISSUE,
            execution_sha=SHA,
        )
        self.assertEqual(parsed["source_receipt_sha256"], subject.SOURCE_EXPECTED_SHA256)
        self.assertEqual(parsed["runtime_receipt_sha256"], subject.RUNTIME_EXPECTED_SHA256)
        for kwargs in (
            {"source_sha256": "0" * 64},
            {"runtime_sha256": "0" * 64},
        ):
            with self.assertRaises(subject.KosovoSourceRuntimeCompareActionError):
                subject.validate_request(
                    request_body(**kwargs),
                    expected_issue=subject.SOURCE_ISSUE,
                    execution_sha=SHA,
                )

    def test_duplicate_json_key_is_rejected(self):
        body = (
            subject.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"x","schema_version":"y"}'
        )
        with self.assertRaises(subject.KosovoSourceRuntimeCompareActionError):
            subject.validate_request(
                body,
                expected_issue=subject.SOURCE_ISSUE,
                execution_sha=SHA,
            )

    def test_pass_publishes_only_bounded_comparison_with_authority_false(self):
        comparison = good_comparison()
        with mock.patch.object(
            subject,
            "acquire_and_compare_kosovo_exposure_runtime",
            return_value=comparison,
        ):
            result = subject.run_comparison(execution_sha=SHA)
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["exact_decimal_comparison_completed"], True)
        self.assertIs(result["comparison"], comparison)
        for field in (
            "project186_equivalence_verified",
            "value_structural_wiring_verified",
            "source_crs_datum_epsg_verified",
            "insured_value_semantics_verified",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)
        self.assertEqual(subject._validate_terminal_result(result), SHA)

    def test_comparison_failure_blocks_without_partial_comparison(self):
        with mock.patch.object(
            subject,
            "acquire_and_compare_kosovo_exposure_runtime",
            side_effect=subject.ExposureRuntimeComparisonError("blocked"),
        ):
            result = subject.run_comparison(execution_sha=SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "comparison_failure")
        self.assertIsNone(result["comparison"])
        self.assertIs(result["exact_decimal_comparison_completed"], False)
        self.assertEqual(subject._validate_terminal_result(result), SHA)

    def test_terminal_rejects_authority_promotion(self):
        result = subject._base_result(SHA)
        result["project186_equivalence_verified"] = True
        with self.assertRaises(subject.KosovoSourceRuntimeCompareActionError):
            subject._validate_terminal_result(result)

    def test_comparison_rejects_noncanonical_or_type_drifted_identity(self):
        comparison = good_comparison()
        comparison["source_identity"] = dict(comparison["source_identity"])
        comparison["source_identity"]["project_id"] = float(subject.source_profile.PROJECT_ID)
        with self.assertRaises(subject.KosovoSourceRuntimeCompareActionError):
            subject._validate_comparison(comparison)

    def test_comparison_rejects_inconsistent_equality_counts(self):
        comparison = good_comparison()
        comparison["numeric_comparisons"] = [
            dict(item) for item in comparison["numeric_comparisons"]
        ]
        comparison["numeric_comparisons"][0]["non_equal_count"] = 1
        with self.assertRaises(subject.KosovoSourceRuntimeCompareActionError):
            subject._validate_comparison(comparison)

    def test_comparison_rejects_nonfinite_maximum_difference(self):
        comparison = good_comparison()
        comparison["numeric_comparisons"] = [
            dict(item) for item in comparison["numeric_comparisons"]
        ]
        comparison["numeric_comparisons"][0]["maximum_absolute_difference"] = "NaN"
        with self.assertRaises(subject.KosovoSourceRuntimeCompareActionError):
            subject._validate_comparison(comparison)

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

    def test_dedup_rejects_malformed_bot_terminal_instead_of_skipping_provider(self):
        bad = subject._base_result(SHA)
        bad["external_bytes_persisted"] = True
        body = subject.RESULT_MARKER + "\n" + json.dumps(
            bad,
            sort_keys=True,
            separators=(",", ":"),
        )
        with mock.patch.object(
            subject,
            "fetch_repository_comments",
            return_value=[{"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": body}],
        ):
            with self.assertRaises(subject.KosovoSourceRuntimeCompareActionError):
                subject.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test",
                    execution_sha=SHA,
                )


if __name__ == "__main__":
    unittest.main()
