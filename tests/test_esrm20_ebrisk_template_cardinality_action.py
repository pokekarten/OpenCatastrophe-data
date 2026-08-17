# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock

from scripts import profile_esrm20_ebrisk_v10_tree as profile
from scripts import run_esrm20_ebrisk_template_cardinality_action as action

EXECUTION_SHA = "d" * 40


def _entry(name: str, object_id: str, *, entry_type: str = "blob") -> dict[str, str]:
    return {
        "id": object_id,
        "name": name,
        "type": entry_type,
        "path": f"Configuration_Files/{name}",
        "mode": "100644" if entry_type == "blob" else "040000",
    }


def _complete_entries() -> list[dict[str, str]]:
    return [
        _entry(profile.TEMPLATE_BASENAMES[0], "1" * 40),
        _entry(profile.TEMPLATE_BASENAMES[1], "2" * 40),
        _entry(profile.TEMPLATE_BASENAMES[2], "3" * 40),
    ]


def _result(*, sha: str = EXECUTION_SHA, status: str = "pass", summary=None) -> dict:
    if summary is None and status == "pass":
        summary = action.summarize_template_resolution(_complete_entries())
    return {
        **action._base_result(execution_sha=sha),
        "status": status,
        "template_resolution": summary,
    }


def _body(result: dict) -> str:
    return action.RESULT_MARKER + "\n" + json.dumps(
        result, sort_keys=True, separators=(",", ":")
    )


class TemplateSummaryTests(unittest.TestCase):
    def test_complete_set_is_three_single_blobs_in_provider_order(self) -> None:
        self.assertEqual(
            action.summarize_template_resolution(_complete_entries()),
            [
                {"basename": profile.TEMPLATE_BASENAMES[0], "state": "single_blob"},
                {"basename": profile.TEMPLATE_BASENAMES[1], "state": "single_blob"},
                {"basename": profile.TEMPLATE_BASENAMES[2], "state": "single_blob"},
            ],
        )

    def test_each_fixed_basename_reports_missing_without_paths(self) -> None:
        for index, basename in enumerate(profile.TEMPLATE_BASENAMES):
            with self.subTest(basename=basename):
                entries = _complete_entries()
                entries.pop(index)
                summary = action.summarize_template_resolution(entries)
                self.assertEqual(summary[index], {"basename": basename, "state": "missing"})
                self.assertNotIn("path", summary[index])
                self.assertNotIn("object_sha1", summary[index])

    def test_each_fixed_basename_reports_multiple_without_exact_count(self) -> None:
        for index, basename in enumerate(profile.TEMPLATE_BASENAMES):
            with self.subTest(basename=basename):
                entries = _complete_entries()
                entries.append(_entry(basename, "a" * 40))
                summary = action.summarize_template_resolution(entries)
                self.assertEqual(summary[index], {"basename": basename, "state": "multiple"})

    def test_each_fixed_basename_reports_single_non_blob(self) -> None:
        for index, basename in enumerate(profile.TEMPLATE_BASENAMES):
            with self.subTest(basename=basename):
                entries = _complete_entries()
                entries[index] = _entry(basename, "b" * 40, entry_type="tree")
                summary = action.summarize_template_resolution(entries)
                self.assertEqual(
                    summary[index],
                    {"basename": basename, "state": "single_non_blob"},
                )

    def test_unrelated_entries_do_not_enter_public_summary(self) -> None:
        entries = _complete_entries() + [_entry("secret_other.ini", "f" * 40)]
        encoded = json.dumps(action.summarize_template_resolution(entries), sort_keys=True)
        self.assertNotIn("secret_other.ini", encoded)


class TemplateResultValidationTests(unittest.TestCase):
    def test_valid_result_round_trips(self) -> None:
        self.assertTrue(action.parse_terminal_result(_body(_result()), execution_sha=EXECUTION_SHA))

    def test_foreign_valid_result_is_fully_validated_then_not_duplicate(self) -> None:
        other = "a" * 40
        self.assertFalse(action.parse_terminal_result(_body(_result(sha=other)), execution_sha=EXECUTION_SHA))

    def test_authority_widening_fails_closed_even_for_foreign_sha(self) -> None:
        other = "a" * 40
        result = _result(sha=other)
        result["publication_authorized"] = True
        with self.assertRaisesRegex(action.EbriskTemplateDiagnosticError, "publication_authorized"):
            action.parse_terminal_result(_body(result), execution_sha=EXECUTION_SHA)

    def test_summary_reordering_unknown_state_and_extra_field_fail_closed(self) -> None:
        mutations = []
        reordered = _result()
        reordered["template_resolution"] = list(reversed(reordered["template_resolution"]))
        mutations.append(reordered)
        unknown = _result()
        unknown["template_resolution"][0]["state"] = "two"
        mutations.append(unknown)
        extra = _result()
        extra["template_resolution"][0]["path"] = "leak"
        mutations.append(extra)
        for result in mutations:
            with self.subTest(result=result):
                with self.assertRaises(action.EbriskTemplateDiagnosticError):
                    action.parse_terminal_result(_body(result), execution_sha=EXECUTION_SHA)

    def test_duplicate_carries_no_evidence(self) -> None:
        duplicate = _result(status="duplicate", summary=None)
        self.assertTrue(action.parse_terminal_result(_body(duplicate), execution_sha=EXECUTION_SHA))
        duplicate["template_resolution"] = []
        with self.assertRaisesRegex(action.EbriskTemplateDiagnosticError, "carries evidence"):
            action.parse_terminal_result(_body(duplicate), execution_sha=EXECUTION_SHA)

    def test_untrusted_author_is_ignored(self) -> None:
        comment = {"user": {"login": "attacker"}, "body": _body(_result())}
        with mock.patch.object(action, "_FETCH_COMMENTS", return_value=[comment]):
            self.assertFalse(
                action.has_terminal_result(
                    repository="pokekarten/OpenCatastrophe-data",
                    token="token",
                    execution_sha=EXECUTION_SHA,
                )
            )


class TemplateExecutionTests(unittest.TestCase):
    def test_runtime_reuses_fixed_profiler_and_restores_resolver(self) -> None:
        entries = _complete_entries()
        entries.pop(2)

        def fake_profile():
            return profile._exact_template_paths(entries)

        original_profile = profile.profile_v10_tree
        try:
            with mock.patch.object(action, "_PROFILE", fake_profile), mock.patch.object(
                profile, "profile_v10_tree", fake_profile
            ):
                summary = action.run_template_diagnostic()
            self.assertEqual(summary[2]["state"], "missing")
            self.assertIs(profile._exact_template_paths, action._TEMPLATE_RESOLVER)
        finally:
            profile.profile_v10_tree = original_profile

    def test_upstream_metadata_failure_is_not_published_as_template_evidence(self) -> None:
        def failing_profile():
            raise profile.EbriskTreeProfileError(
                "synthetic transport failure",
                failure_class="tree_metadata_acquisition_failure",
            )

        original_profile = profile.profile_v10_tree
        try:
            with mock.patch.object(action, "_PROFILE", failing_profile), mock.patch.object(
                profile, "profile_v10_tree", failing_profile
            ):
                with self.assertRaisesRegex(
                    action.EbriskTemplateDiagnosticError,
                    "did not reach template resolution",
                ):
                    action.run_template_diagnostic()
            self.assertIs(profile._exact_template_paths, action._TEMPLATE_RESOLVER)
        finally:
            profile.profile_v10_tree = original_profile


if __name__ == "__main__":
    unittest.main()
