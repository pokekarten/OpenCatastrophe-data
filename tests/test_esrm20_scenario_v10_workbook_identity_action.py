# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import profile_esrm20_scenario_v10_workbook_identity as profile
from scripts import run_esrm20_scenario_v10_workbook_identity_action as action

EXECUTION_SHA = "b" * 40
FOREIGN_SHA = "c" * 40


def _valid_profile() -> dict:
    return {
        "schema_version": profile.SCHEMA_VERSION,
        "source_issue": 285,
        "project_id": 273,
        "project_path": "efehr/esrm20_scenario_tests",
        "release_tag": "v1.0",
        "commit_sha": profile.COMMIT_SHA,
        "workbook_path": profile.WORKBOOK_PATH,
        "tree_identity_sha256": "1" * 64,
        "workbook_git_blob_sha1": "2" * 40,
        "retrieved_at": "2026-08-17T22:20:00Z",
        "byte_count": 4096,
        "sha256": "3" * 64,
        "target_event_id": profile.TARGET_EVENT_ID,
        "zip_member_count": 12,
        "total_uncompressed_bytes": 16384,
        "worksheet_count": 1,
        "shared_string_count": 8,
        "scanned_row_count": 3,
        "scanned_cell_count": 6,
        "target_event_id_exact_cell_count": 1,
        "target_event_id_row_count": 1,
        "name_literal_cell_counts": {"athens": 1, "thessaloniki": 1},
        "name_literal_row_counts": {"athens": 1, "thessaloniki": 1},
        "target_same_row_name_literal_counts": {"athens": 1, "thessaloniki": 0},
        "same_row_name_literal_binding": "athens",
        "raw_workbook_cells_returned": False,
        "raw_workbook_rows_returned": False,
        "provider_file_bytes_read": True,
        "external_bytes_persisted": False,
        "rupture_or_shakemap_payload_bytes_read": False,
        "event_location_inference_authorized": False,
        "scenario_selection_authorized": False,
        "independent_validation_established": False,
        "holdout_status_established": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


def _result(
    *, execution_sha: str, status: str = "pass", evidence: dict | None = None
) -> dict:
    value = {
        **action._base_result(execution_sha=execution_sha),
        "status": status,
        "failure_class": None,
        "profile": evidence,
    }
    if status == "blocked":
        value["failure_class"] = "workbook_identity_failure"
        value["profile"] = None
    if status == "duplicate":
        value["profile"] = None
    return value


def _body(value: dict) -> str:
    return action.RESULT_MARKER + "\n" + json.dumps(
        value, sort_keys=True, separators=(",", ":")
    )


class WorkbookIdentityActionTests(unittest.TestCase):
    def test_request_is_exact_and_caller_cannot_choose_path_ref_or_event(self) -> None:
        request = {
            "schema_version": action.REQUEST_SCHEMA_VERSION,
            "issue": 285,
            "target_sha": EXECUTION_SHA,
            "requester": "test-runner",
        }
        body = action.REQUEST_MARKER + "\n" + json.dumps(
            request, separators=(",", ":")
        )
        parsed = action.validate_request(
            body, expected_issue=285, execution_sha=EXECUTION_SHA
        )
        self.assertEqual(parsed, request)

        for injected in (
            {"path": "other.xlsx"},
            {"ref": "v1.1"},
            {"event": "Athens"},
        ):
            with self.subTest(injected=injected):
                mutated = dict(request, **injected)
                with self.assertRaisesRegex(
                    action.ScenarioWorkbookIdentityExecutionError,
                    "request fields drifted",
                ):
                    action.validate_request(
                        action.REQUEST_MARKER + "\n" + json.dumps(mutated),
                        expected_issue=285,
                        execution_sha=EXECUTION_SHA,
                    )

        duplicate = (
            action.REQUEST_MARKER
            + '\n{"schema_version":"'
            + action.REQUEST_SCHEMA_VERSION
            + '","issue":285,"target_sha":"'
            + EXECUTION_SHA
            + '","requester":"a","requester":"b"}'
        )
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "duplicate JSON key",
        ):
            action.validate_request(
                duplicate, expected_issue=285, execution_sha=EXECUTION_SHA
            )

    def test_profile_validation_preserves_closed_scientific_authority(self) -> None:
        valid = _valid_profile()
        self.assertIs(action.validate_profile(valid), valid)

        for field in (
            "event_location_inference_authorized",
            "scenario_selection_authorized",
            "independent_validation_established",
            "holdout_status_established",
            "publication_authorized",
            "model_use_authorized",
            "external_bytes_persisted",
        ):
            with self.subTest(field=field):
                mutated = copy.deepcopy(valid)
                mutated[field] = True
                with self.assertRaisesRegex(
                    action.ScenarioWorkbookIdentityExecutionError,
                    field,
                ):
                    action.validate_profile(mutated)

        raw = copy.deepcopy(valid)
        raw["raw_workbook_cells_returned"] = True
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "raw_workbook_cells_returned",
        ):
            action.validate_profile(raw)

        extra = copy.deepcopy(valid)
        extra["provider_row"] = {"event": "secret"}
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "profile fields drifted",
        ):
            action.validate_profile(extra)

    def test_profile_binding_counts_must_be_self_consistent_and_bounded(self) -> None:
        contradictory = _valid_profile()
        contradictory["target_same_row_name_literal_counts"]["thessaloniki"] = 1
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "same-row name binding is contradictory",
        ):
            action.validate_profile(contradictory)

        mismatched = _valid_profile()
        mismatched["same_row_name_literal_binding"] = "thessaloniki"
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "same-row name binding is contradictory",
        ):
            action.validate_profile(mismatched)

        impossible_target = _valid_profile()
        impossible_target["target_event_id_row_count"] = 2
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "target row/cell counts disagree",
        ):
            action.validate_profile(impossible_target)

        inflated_target = _valid_profile()
        inflated_target["target_event_id_exact_cell_count"] = 7
        inflated_target["target_event_id_row_count"] = 1
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "target row/cell counts disagree",
        ):
            action.validate_profile(inflated_target)

        inflated_name_cells = _valid_profile()
        inflated_name_cells["name_literal_cell_counts"]["athens"] = 7
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "name cell counts exceed scanned evidence",
        ):
            action.validate_profile(inflated_name_cells)

        inflated_name_rows = _valid_profile()
        inflated_name_rows["name_literal_cell_counts"]["athens"] = 4
        inflated_name_rows["name_literal_row_counts"]["athens"] = 4
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "name row/cell counts disagree",
        ):
            action.validate_profile(inflated_name_rows)

    def test_terminal_results_are_closed_and_blocked_result_carries_no_profile(self) -> None:
        passed = _result(execution_sha=EXECUTION_SHA, evidence=_valid_profile())
        self.assertTrue(
            action.parse_terminal_result(_body(passed), execution_sha=EXECUTION_SHA)
        )

        blocked = _result(execution_sha=EXECUTION_SHA, status="blocked")
        self.assertTrue(
            action.parse_terminal_result(_body(blocked), execution_sha=EXECUTION_SHA)
        )

        widened = copy.deepcopy(blocked)
        widened["profile"] = _valid_profile()
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "blocked result widened workbook evidence",
        ):
            action.parse_terminal_result(_body(widened), execution_sha=EXECUTION_SHA)

        foreign_target = _result(
            execution_sha=FOREIGN_SHA, evidence=_valid_profile()
        )
        with self.assertRaisesRegex(
            action.ScenarioWorkbookIdentityExecutionError,
            "target_sha",
        ):
            action.parse_terminal_result(
                _body(foreign_target), execution_sha=EXECUTION_SHA
            )

    def test_foreign_sha_terminal_is_validated_before_dedup_skip(self) -> None:
        original = action._FETCH_COMMENTS
        foreign = _result(execution_sha=FOREIGN_SHA, evidence=_valid_profile())
        action._FETCH_COMMENTS = lambda *args, **kwargs: [
            {
                "user": {"login": action.TRUSTED_RESULT_LOGIN},
                "body": _body(foreign),
            }
        ]
        try:
            self.assertFalse(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
            )
        finally:
            action._FETCH_COMMENTS = original

        malformed = copy.deepcopy(foreign)
        malformed["profile"]["publication_authorized"] = True
        action._FETCH_COMMENTS = lambda *args, **kwargs: [
            {
                "user": {"login": action.TRUSTED_RESULT_LOGIN},
                "body": _body(malformed),
            }
        ]
        try:
            with self.assertRaisesRegex(
                action.ScenarioWorkbookIdentityExecutionError,
                "publication_authorized",
            ):
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
        finally:
            action._FETCH_COMMENTS = original

    def test_workflow_is_owner_fenced_and_publication_is_checkoutless_closed_shape(self) -> None:
        workflow = Path(
            ".github/workflows/esrm20-scenario-v10-workbook-identity.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("github.event.issue.number == 285", workflow)
        self.assertIn(
            "github.event.comment.user.login == github.event.repository.owner.login",
            workflow,
        )
        self.assertIn("github.event.comment.author_association == 'OWNER'", workflow)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        publish = workflow.split("publish-workbook-identity:", 1)[1]
        self.assertNotIn("actions/checkout", publish)
        self.assertIn('keys == [', publish)
        self.assertIn('"testing_scenarios.xlsx"', publish)
        self.assertIn('"Greece_07-9-1999"', publish)
        self.assertIn("event_location_inference_authorized == false", publish)
        self.assertIn(
            ".profile.target_event_id_exact_cell_count <= .profile.scanned_cell_count",
            publish,
        )
        self.assertIn(
            ".profile.name_literal_cell_counts.athens <= .profile.scanned_cell_count",
            publish,
        )
        self.assertNotIn("all(.profile.name_literal_cell_counts[];", publish)
        self.assertNotIn("upload-artifact", workflow)


if __name__ == "__main__":
    unittest.main()
