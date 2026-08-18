# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import contextlib
import io
import unittest

from scripts import profile_esrm20_scenario_v10_workbook_identity as profile
from scripts import run_esrm20_scenario_v10_workbook_identity_action as action

EXECUTION_SHA = "d" * 40


class WorkbookFailureStageTests(unittest.TestCase):
    def test_failure_messages_map_only_to_closed_static_stages(self) -> None:
        cases = (
            ("scenario tree receipt is not an object", "tree_identity"),
            ("workbook acquisition failed closed", "provider_transport"),
            (
                "workbook bytes do not match immutable tree Git blob",
                "git_blob_identity",
            ),
            ("workbook is not a valid ZIP package", "xlsx_package"),
            (
                "workbook sheet relationship is unresolved",
                "workbook_relationships",
            ),
            ("sharedStrings namespace/root is invalid", "shared_strings"),
            ("worksheet cell reference is invalid", "worksheet_scan"),
            ("unclassified provider detail must not escape", "unknown"),
        )
        for message, expected in cases:
            with self.subTest(message=message):
                error = profile.ScenarioWorkbookIdentityError(message)
                stage = action._closed_failure_stage(error)
                self.assertIn(stage, action._FAILURE_STAGES)
                self.assertEqual(stage, expected)

    def test_traceback_context_refines_relationship_and_shared_string_failures(self) -> None:
        def capture(function, *args):
            try:
                function(*args)
            except profile.ScenarioWorkbookIdentityError as error:
                return error
            self.fail("expected workbook identity failure")

        relationship_error = capture(
            profile._referenced_worksheets,
            None,
            {},
        )
        self.assertEqual(
            action._closed_failure_stage(relationship_error),
            "workbook_relationships",
        )

        class MissingSharedStrings(dict):
            def get(self, key, default=None):
                if key == "xl/sharedStrings.xml":
                    raise profile.ScenarioWorkbookIdentityError(
                        "XLSX member read failed closed"
                    )
                return super().get(key, default)

        shared_error = capture(profile._shared_strings, None, MissingSharedStrings())
        self.assertEqual(action._closed_failure_stage(shared_error), "shared_strings")

    def test_blocked_log_emits_only_closed_stage_and_preserves_result_contract(self) -> None:
        secret = "provider-row-secret:Greece_07-9-1999:Athens"
        error = profile.ScenarioWorkbookIdentityError(secret)
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream):
            result = action._blocked_result_for_failure(
                error,
                execution_sha=EXECUTION_SHA,
            )

        emitted = stream.getvalue()
        self.assertEqual(emitted, "WORKBOOK_IDENTITY_FAILURE_STAGE=unknown\n")
        self.assertNotIn(secret, emitted)
        self.assertEqual(set(result), action._RESULT_FIELDS)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["failure_class"], "workbook_identity_failure")
        self.assertIsNone(result["profile"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["event_location_inference_authorized"])
        self.assertFalse(result["scenario_selection_authorized"])
        self.assertFalse(result["independent_validation_established"])
        self.assertFalse(result["holdout_status_established"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertTrue(
            action.parse_terminal_result(
                action.RESULT_MARKER + "\n" + __import__("json").dumps(
                    result, sort_keys=True, separators=(",", ":")
                ),
                execution_sha=EXECUTION_SHA,
            )
        )


if __name__ == "__main__":
    unittest.main()
