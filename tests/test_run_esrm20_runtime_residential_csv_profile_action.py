# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import run_esrm20_runtime_residential_csv_profile_action as subject


SHA = "a" * 40


def request_body(*, receipt_sha256: str = subject.EXPECTED_SHA256) -> str:
    request = {
        "schema_version": subject.REQUEST_SCHEMA_VERSION,
        "action": subject.ACTION,
        "issue": subject.SOURCE_ISSUE,
        "target_sha": SHA,
        "dataset_id": subject.DATASET_ID,
        "receipt_sha256": receipt_sha256,
        "requester": "test-agent",
    }
    return subject.REQUEST_MARKER + "\n" + json.dumps(request, separators=(",", ":"))


def column(name: str, digest_character: str) -> dict[str, object]:
    return {
        "name": name,
        "record_count": 2,
        "empty_count": 0,
        "nonempty_count": 2,
        "distinct_count": 2,
        "exact_value_set_sha256": digest_character * 64,
        "decimal_summary": {
            "all_nonempty_decimal": True,
            "finite_decimal_count": 2,
            "leading_or_trailing_whitespace_count": 0,
        },
    }


def good_profile() -> dict[str, object]:
    return {
        "schema_version": subject.PROFILE_SCHEMA_VERSION,
        "parser": {
            "encoding": "utf-8",
            "bom_present": False,
            "delimiter": ",",
            "line_endings": {"crlf_count": 0, "lf_count": 3, "cr_count": 0},
        },
        "record_count": 2,
        "header": ["lon", "lat"],
        "columns": [column("lon", "a"), column("lat", "b")],
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "publication_authorized": False,
    }


def pass_evidence() -> dict[str, object]:
    return {
        "receipt": {
            "retrieved_at": "2026-08-21T11:18:50Z",
            "byte_count": subject.EXPECTED_BYTE_COUNT,
            "sha256": subject.EXPECTED_SHA256,
            "content_type": "text/plain; charset=utf-8",
            "etag": None,
        },
        "profile": good_profile(),
    }


class RuntimeResidentialCsvProfileActionTests(unittest.TestCase):
    def test_request_is_bound_to_exact_receipt_hash(self):
        parsed = subject.validate_request(
            request_body(),
            expected_issue=282,
            execution_sha=SHA,
        )
        self.assertEqual(parsed["receipt_sha256"], subject.EXPECTED_SHA256)
        with self.assertRaises(subject.RuntimeResidentialCsvProfileActionError):
            subject.validate_request(
                request_body(receipt_sha256="0" * 64),
                expected_issue=282,
                execution_sha=SHA,
            )

    def test_duplicate_json_key_is_rejected(self):
        body = (
            subject.REQUEST_MARKER
            + "\n"
            + '{"schema_version":"x","schema_version":"y"}'
        )
        with self.assertRaises(subject.RuntimeResidentialCsvProfileActionError):
            subject.validate_request(body, expected_issue=282, execution_sha=SHA)

    def test_profile_schema_version_drift_is_rejected(self):
        profile = good_profile()
        profile["schema_version"] = "oc-esrm20-exposure-content-profile-v999"
        with self.assertRaises(subject.RuntimeResidentialCsvProfileActionError):
            subject._validate_profile(profile)

    def test_profile_column_record_count_rejects_float_type_confusion(self):
        profile = good_profile()
        profile["columns"][0]["record_count"] = 2.0
        with self.assertRaisesRegex(
            subject.RuntimeResidentialCsvProfileActionError,
            "column identity drifted",
        ):
            subject._validate_profile(profile)

    def test_pass_profiles_structure_but_keeps_scientific_authority_false(self):
        with mock.patch.object(
            subject,
            "profile_runtime_residential_csv",
            return_value=pass_evidence(),
        ):
            result = subject.run_profile(execution_sha=SHA)
        self.assertEqual(result["status"], "pass")
        self.assertIs(result["csv_content_profiled"], True)
        for field in (
            "taxonomy_semantics_verified",
            "crs_semantics_verified",
            "value_semantics_verified",
            "project186_equivalence_verified",
            "external_bytes_persisted",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)
        self.assertEqual(subject._validate_terminal_result(result), SHA)

    def test_terminal_rejects_json_numeric_type_confusion(self):
        with mock.patch.object(
            subject,
            "profile_runtime_residential_csv",
            return_value=pass_evidence(),
        ):
            canonical = subject.run_profile(execution_sha=SHA)

        mutations = (
            (
                "source_issue_float",
                lambda result: result.__setitem__(
                    "source_issue", float(subject.SOURCE_ISSUE)
                ),
            ),
            (
                "authority_zero",
                lambda result: result.__setitem__("publication_authorized", 0),
            ),
            (
                "identity_project_id_float",
                lambda result: result["runtime_residential_identity"].__setitem__(
                    "project_id", float(subject.PROJECT_ID)
                ),
            ),
            (
                "identity_receipt_comment_id_float",
                lambda result: result["runtime_residential_identity"].__setitem__(
                    "receipt_comment_id", float(subject.RECEIPT_COMMENT_ID)
                ),
            ),
            (
                "identity_byte_count_float",
                lambda result: result["runtime_residential_identity"].__setitem__(
                    "receipt_byte_count", float(subject.EXPECTED_BYTE_COUNT)
                ),
            ),
            (
                "receipt_byte_count_float",
                lambda result: result["receipt"].__setitem__(
                    "byte_count", float(subject.EXPECTED_BYTE_COUNT)
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                result = json.loads(json.dumps(canonical))
                mutate(result)
                body = subject.RESULT_MARKER + "\n" + json.dumps(
                    result, separators=(",", ":")
                )
                with self.assertRaises(subject.RuntimeResidentialCsvProfileActionError):
                    subject.parse_terminal_result(body)

    def test_run_profile_rejects_float_receipt_byte_count_before_pass(self):
        evidence = pass_evidence()
        evidence["receipt"]["byte_count"] = float(subject.EXPECTED_BYTE_COUNT)
        with mock.patch.object(
            subject,
            "profile_runtime_residential_csv",
            return_value=evidence,
        ):
            result = subject.run_profile(execution_sha=SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "byte_identity_mismatch")
        self.assertIsNone(result["receipt"])
        self.assertIsNone(result["profile"])

    def test_byte_identity_mismatch_blocks_without_profile_evidence(self):
        with mock.patch.object(
            subject,
            "profile_runtime_residential_csv",
            side_effect=subject.ByteIdentityMismatch("drift"),
        ):
            result = subject.run_profile(execution_sha=SHA)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "byte_identity_mismatch")
        self.assertIsNone(result["receipt"])
        self.assertIsNone(result["profile"])
        self.assertIs(result["csv_content_profiled"], False)

    def test_dedup_trusts_only_bot_terminal_for_exact_execution_sha(self):
        terminal = subject._base_result(SHA)
        terminal["status"] = "blocked"
        terminal["failure_class"] = "profile_failure"
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


if __name__ == "__main__":
    unittest.main()
