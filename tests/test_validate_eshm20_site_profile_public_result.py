# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import acquire_eshm20_site_model_profile as worker
from scripts import run_eshm20_site_model_profile_action as action
from scripts import validate_eshm20_site_profile_public_result as subject

SHA = "a" * 40
OTHER_SHA = "b" * 40


def column(name: str) -> dict[str, object]:
    return {
        "name": name,
        "record_count": 2,
        "empty_count": 0,
        "nonempty_count": 2,
        "distinct_count": 2,
        "exact_value_set_sha256": "c" * 64,
        "decimal_summary": {
            "all_nonempty_decimal": True,
            "finite_decimal_count": 2,
            "leading_or_trailing_whitespace_count": 0,
        },
    }


def worker_profile() -> dict[str, object]:
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


def terminal(execution_sha: str = SHA) -> dict[str, object]:
    return action._run_site_profile(
        execution_sha=execution_sha,
        acquirer=worker_profile,
    )


def redacted(value: dict[str, object]) -> dict[str, object]:
    result = copy.deepcopy(value)
    for item in result["profile"]["profile"]["columns"]:
        item.pop(subject.VALUE_SET_DIGEST_FIELD)
    return result


def body(value: dict[str, object]) -> str:
    return action.RESULT_MARKER + "\n" + json.dumps(
        value, sort_keys=True, separators=(",", ":")
    )


class Eshm20PublicSiteProfileResultTests(unittest.TestCase):
    def test_legacy_and_fully_redacted_passes_are_both_valid_public_evidence(self):
        legacy = terminal()
        public = redacted(legacy)

        self.assertIs(
            subject.validate_public_terminal_result(legacy, execution_sha=SHA),
            legacy,
        )
        self.assertIs(
            subject.validate_public_terminal_result(public, execution_sha=SHA),
            public,
        )
        self.assertTrue(
            subject.parse_trusted_public_terminal_result(body(legacy), execution_sha=SHA)
        )
        self.assertTrue(
            subject.parse_trusted_public_terminal_result(body(public), execution_sha=SHA)
        )
        self.assertFalse(
            subject.parse_trusted_public_terminal_result(
                body(public), execution_sha=OTHER_SHA
            )
        )

    def test_redacted_public_shape_does_not_weaken_active_action_validation(self):
        public = redacted(terminal())
        with self.assertRaises(action.SiteModelProfileActionError):
            action._validate_terminal_result(public, execution_sha=SHA)
        subject.validate_public_terminal_result(public, execution_sha=SHA)

    def test_mixed_redaction_fails_closed(self):
        value = terminal()
        value["profile"]["profile"]["columns"][0].pop(
            subject.VALUE_SET_DIGEST_FIELD
        )
        with self.assertRaisesRegex(
            subject.PublicSiteProfileResultError,
            "mixes legacy hashed and redacted",
        ):
            subject.validate_public_terminal_result(value, execution_sha=SHA)

    def test_extra_or_mutated_evidence_still_fails_closed(self):
        public = redacted(terminal())
        public["profile"]["profile"]["columns"][0]["raw_value"] = "secret"
        with self.assertRaises(subject.PublicSiteProfileResultError):
            subject.validate_public_terminal_result(public, execution_sha=SHA)

        public = redacted(terminal())
        public["model_use_authorized"] = True
        with self.assertRaises(subject.PublicSiteProfileResultError):
            subject.validate_public_terminal_result(public, execution_sha=SHA)

    def test_dedup_accepts_legacy_and_redacted_trusted_bot_comments(self):
        legacy_prior = {
            "user": {"login": action.TRUSTED_RESULT_LOGIN},
            "body": body(terminal(OTHER_SHA)),
        }
        redacted_current = {
            "user": {"login": action.TRUSTED_RESULT_LOGIN},
            "body": body(redacted(terminal(SHA))),
        }
        with patch.object(
            action,
            "fetch_repository_comments",
            return_value=[legacy_prior, redacted_current],
        ):
            self.assertTrue(
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=SHA,
                )
            )

    def test_untrusted_comments_and_malformed_trusted_results_do_not_bypass(self):
        untrusted = {
            "user": {"login": "someone-else"},
            "body": body(redacted(terminal(SHA))),
        }
        with patch.object(
            action,
            "fetch_repository_comments",
            return_value=[untrusted],
        ):
            self.assertFalse(
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=SHA,
                )
            )

        malformed = {
            "user": {"login": action.TRUSTED_RESULT_LOGIN},
            "body": action.RESULT_MARKER + "\n{}",
        }
        with patch.object(
            action,
            "fetch_repository_comments",
            return_value=[malformed],
        ):
            with self.assertRaises(subject.PublicSiteProfileResultError):
                subject.has_terminal_site_profile_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="test-token",
                    execution_sha=SHA,
                )

    def test_workflow_redacts_only_after_strict_validation_and_publishes_redacted_json(self):
        text = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "eshm20-site-model-profile.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "subject._validate_terminal_result(result, execution_sha=os.environ[\"EXECUTION_SHA\"])",
            text,
        )
        self.assertIn(
            "from scripts import validate_eshm20_site_profile_public_result as public_result",
            text,
        )
        self.assertIn("PUBLIC_RESULT_JSON=", text)
        self.assertIn("del(.exact_value_set_sha256)", text)
        self.assertIn('has("exact_value_set_sha256") | not', text)
        self.assertIn('BODY="$RESULT_MARKER\n          $PUBLIC_RESULT_JSON"', text)
        self.assertNotIn('BODY="$RESULT_MARKER\n          $RESULT_JSON"', text)


if __name__ == "__main__":
    unittest.main()
