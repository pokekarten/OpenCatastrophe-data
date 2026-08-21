# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from scripts import acquire_eshm20_site_model_profile as worker
from scripts import run_eshm20_site_model_profile_action as subject

SHA = "a" * 40
OTHER_SHA = "c" * 40


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
    return subject.REQUEST_MARKER + "\n" + json.dumps(value, sort_keys=True, separators=(",", ":"))


def column(name: str, *, record_count: int = 2) -> dict[str, object]:
    return {
        "name": name,
        "record_count": record_count,
        "empty_count": 0,
        "nonempty_count": record_count,
        "distinct_count": record_count,
        "exact_value_set_sha256": "b" * 64,
        "decimal_summary": {
            "all_nonempty_decimal": True,
            "finite_decimal_count": record_count,
            "leading_or_trailing_whitespace_count": 0,
        },
    }


def profile() -> dict[str, object]:
    headers = ["lon", "lat", "vs30"]
    return {
        "schema_version": worker.SCHEMA_VERSION,
        "source_issue": worker.SOURCE_ISSUE,
        "control_issue": worker.CONTROL_ISSUE,
        "receipt_source_issue": worker.RECEIPT_SOURCE_ISSUE,
        "dataset_id": worker.DATASET_ID,
        "project_id": worker.PROJECT_ID,
        "project_path": worker.PROJECT_PATH,
        "commit_sha": worker.COMMIT_SHA,
        "repository_path": worker.REPOSITORY_PATH,
        "byte_count": worker.EXPECTED_BYTE_COUNT,
        "sha256": worker.EXPECTED_SHA256,
        "parser": {
            "encoding": "utf-8",
            "bom_present": False,
            "line_endings": {"crlf_count": 0, "lf_count": 3, "cr_count": 0},
        },
        "inventory_receipt_comment_id": worker.INVENTORY_RECEIPT_COMMENT_ID,
        "root_dependency_result_comment_id": worker.ROOT_DEPENDENCY_RESULT_COMMENT_ID,
        "root_dependency_section": worker.ROOT_DEPENDENCY_SECTION,
        "root_dependency_option": worker.ROOT_DEPENDENCY_OPTION,
        "first_order_receipt_request_comment_id": worker.FIRST_ORDER_RECEIPT_REQUEST_COMMENT_ID,
        "first_order_receipt_run_id": worker.FIRST_ORDER_RECEIPT_RUN_ID,
        "first_order_receipt_execution_sha": worker.FIRST_ORDER_RECEIPT_EXECUTION_SHA,
        "profile": {
            "delimiter": ",",
            "record_count": 2,
            "header": headers,
            "columns": [column(name) for name in headers],
        },
        "raw_rows_returned": False,
        "schema_interpretation_authorized": False,
        "crs_authorized": False,
        "coordinate_semantics_authorized": False,
        "site_response_authorized": False,
        "site_semantics_authorized": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def terminal_body(execution_sha: str) -> str:
    terminal = subject._run_site_profile(execution_sha=execution_sha, acquirer=profile)
    return subject.RESULT_MARKER + "\n" + json.dumps(terminal, sort_keys=True, separators=(",", ":"))


class Eshm20SiteModelProfileActionTests(unittest.TestCase):
    def test_request_is_closed_to_issue_dataset_and_execution_sha(self):
        parsed = subject.validate_request(request(), expected_issue=281, execution_sha=SHA)
        self.assertEqual(parsed["action"], subject.ACTION)
        with self.assertRaises(subject.SiteModelProfileActionError):
            subject.validate_request(request(issue=282), expected_issue=281, execution_sha=SHA)
        with self.assertRaises(subject.SiteModelProfileActionError):
            subject.validate_request(request(dataset_id="other"), expected_issue=281, execution_sha=SHA)
        with self.assertRaises(subject.SiteModelProfileActionError):
            subject.validate_request(request(target_sha="b" * 40), expected_issue=281, execution_sha=SHA)

    def test_request_duplicate_keys_and_nonfinite_constants_fail_closed(self):
        duplicate = subject.REQUEST_MARKER + '\n{"schema_version":"x","schema_version":"y"}'
        with self.assertRaises(subject.SiteModelProfileActionError):
            subject.validate_request(duplicate, expected_issue=281, execution_sha=SHA)
        nonfinite = request().replace('"issue":281', '"issue":NaN')
        with self.assertRaises(subject.SiteModelProfileActionError):
            subject.validate_request(nonfinite, expected_issue=281, execution_sha=SHA)

    def test_success_is_exactly_receipt_bound_and_authority_closed(self):
        result = subject._run_site_profile(execution_sha=SHA, acquirer=profile)
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["failure_class"])
        self.assertEqual(result["profile"]["sha256"], worker.EXPECTED_SHA256)
        for field in (
            "schema_interpretation_authorized",
            "crs_authorized",
            "coordinate_semantics_authorized",
            "site_response_authorized",
            "site_semantics_authorized",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)

    def test_worker_failure_is_bounded_and_does_not_persist_payload(self):
        sentinel = "provider-payload-must-not-persist"

        def blocked() -> dict[str, object]:
            raise worker.Eshm20SiteModelProfileError(sentinel)

        result = subject._run_site_profile(execution_sha=SHA, acquirer=blocked)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "site_profile_failure")
        self.assertIsNone(result["profile"])
        self.assertNotIn(sentinel, json.dumps(result, sort_keys=True))

    def test_worker_contract_drift_is_not_downgraded_to_safe_blocked_result(self):
        mutations = {
            "commit_sha": "b" * 40,
            "repository_path": "other.csv",
            "byte_count": worker.EXPECTED_BYTE_COUNT + 1,
            "sha256": "c" * 64,
            "crs_authorized": True,
            "site_response_authorized": True,
            "publication_authorized": True,
            "model_use_authorized": True,
        }
        for field, bad in mutations.items():
            value = profile()
            value[field] = bad
            with self.subTest(field=field), self.assertRaises(subject.SiteModelProfileActionError):
                subject._run_site_profile(execution_sha=SHA, acquirer=lambda value=value: value)

    def test_header_column_and_numeric_summary_mutations_fail_closed(self):
        cases: list[dict[str, object]] = []

        duplicate_header = profile()
        duplicate_header["profile"]["header"][1] = "lon"
        cases.append(duplicate_header)

        wrong_order = profile()
        wrong_order["profile"]["columns"][0]["name"] = "lat"
        cases.append(wrong_order)

        impossible_counts = profile()
        impossible_counts["profile"]["columns"][0]["nonempty_count"] = 3
        cases.append(impossible_counts)

        bad_digest = profile()
        bad_digest["profile"]["columns"][0]["exact_value_set_sha256"] = "not-a-digest"
        cases.append(bad_digest)

        bool_as_int = profile()
        bool_as_int["profile"]["record_count"] = True
        cases.append(bool_as_int)

        for value in cases:
            with self.assertRaises(subject.SiteModelProfileActionError):
                subject._validate_worker_profile(value)

    def test_terminal_result_parser_is_closed_and_deterministic(self):
        body = terminal_body(SHA)
        self.assertTrue(subject._parse_trusted_terminal_result(body, execution_sha=SHA))
        self.assertFalse(subject._parse_trusted_terminal_result(body, execution_sha=OTHER_SHA))
        self.assertFalse(subject._parse_trusted_terminal_result("ordinary comment", execution_sha=SHA))
        with self.assertRaises(subject.SiteModelProfileActionError):
            subject._parse_trusted_terminal_result(body + "\n" + subject.RESULT_MARKER, execution_sha=SHA)

    def test_dedup_skips_valid_prior_sha_result_and_finds_current_sha(self):
        prior = {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": terminal_body(OTHER_SHA)}
        current = {"user": {"login": subject.TRUSTED_RESULT_LOGIN}, "body": terminal_body(SHA)}
        with patch.object(subject, "fetch_repository_comments", return_value=[prior]):
            self.assertFalse(
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=SHA,
                )
            )
        with patch.object(subject, "fetch_repository_comments", return_value=[prior, current]):
            self.assertTrue(
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=SHA,
                )
            )


if __name__ == "__main__":
    unittest.main()
