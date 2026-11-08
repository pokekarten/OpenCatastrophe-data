# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only negative and positive tests for the Oasis scenario intake gate."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research_runners.oasis_scenario_annualization_preflight_v0 import (
    ScenarioPreflightError,
    audit_event_set_options,
    audit_occurrences,
    git_blob_sha1,
    main,
    read_source,
)

EVENTS = "event_id\n101\n102\n103\n"
SAME_PERIOD = (
    "event_id,period_no,occ_year,occ_month,occ_day\n"
    "101,1,1,1,1\n"
    "102,1,1,1,1\n"
    "103,1,1,1,1\n"
)
MULTI_PERIOD = (
    "event_id,period_no,occ_year,occ_month,occ_day\n"
    "101,1,1,1,1\n"
    "102,2,2,1,1\n"
    "103,2,2,1,2\n"
)
SELECTOR = {
    "model_settings": {
        "event_set": {
            "default": "fictional_mismatch",
            "options": [
                {"id": "fictional_a", "number_of_events": 3},
                {"id": "fictional_b", "number_of_events": 3},
            ],
        }
    }
}


def audit(events: str = EVENTS, occurrences: str = SAME_PERIOD) -> dict[str, object]:
    return audit_occurrences(
        events, occurrences,
        events_blob=git_blob_sha1(events.encode("utf-8")),
        occurrences_blob=git_blob_sha1(occurrences.encode("utf-8")),
    )


class SyntheticOasisScenarioPreflightTests(unittest.TestCase):
    def test_single_period_is_never_annualized(self) -> None:
        result = audit()
        self.assertEqual(result["status"], "parsed_but_not_annualized")
        self.assertEqual(result["event_ids_count"], 3)
        self.assertEqual(result["represented_periods_count"], 1)
        self.assertEqual(result["max_occurrence_rows_in_one_period"], 3)
        self.assertTrue(result["all_rows_same_period"])
        self.assertFalse(result["annual_oep_aep_authorized"])
        self.assertFalse(result["annual_period_weights_verified"])
        self.assertFalse(result["physical_occurrence_identity_verified"])

    def test_two_periods_still_are_not_an_annual_probability_measure(self) -> None:
        result = audit(occurrences=MULTI_PERIOD)
        self.assertEqual(result["represented_periods_count"], 2)
        self.assertFalse(result["all_rows_same_period"])
        self.assertFalse(result["annual_oep_aep_authorized"])

    def test_identical_physical_event_id_in_different_periods_is_not_rejected(self) -> None:
        events = "event_id\n101\n"
        occurrences = (
            "event_id,period_no,occ_year,occ_month,occ_day\n"
            "101,1,1,1,1\n101,2,2,2,2\n"
        )
        result = audit(events, occurrences)
        self.assertEqual(result["occurrence_rows_count"], 2)
        self.assertEqual(result["event_ids_count"], 1)

    def test_duplicate_event_id_blocks(self) -> None:
        with self.assertRaisesRegex(ScenarioPreflightError, "duplicate event"):
            audit("event_id\n101\n101\n102\n103\n")

    def test_duplicate_occurrence_row_blocks(self) -> None:
        with self.assertRaisesRegex(ScenarioPreflightError, "identical occurrence"):
            audit(occurrences=SAME_PERIOD + "101,1,1,1,1\n")

    def test_event_not_in_event_list_blocks(self) -> None:
        with self.assertRaisesRegex(ScenarioPreflightError, "missing from events"):
            audit(occurrences=SAME_PERIOD.replace("103,1,1,1,1", "104,1,1,1,1"))

    def test_event_without_occurrence_blocks(self) -> None:
        with self.assertRaisesRegex(ScenarioPreflightError, "no matching occurrence"):
            audit(occurrences=SAME_PERIOD.replace("103,1,1,1,1\n", ""))

    def test_invalid_date_blocks(self) -> None:
        with self.assertRaisesRegex(ScenarioPreflightError, "invalid occurrence calendar date"):
            audit(occurrences=SAME_PERIOD.replace("101,1,1,1,1", "101,1,2026,2,30"))

    def test_unbounded_year_blocks(self) -> None:
        with self.assertRaises(ScenarioPreflightError):
            audit(occurrences=SAME_PERIOD.replace("102,1,1,1,1", "102,1,10000,1,1"))

    def test_zero_or_negative_integer_blocks(self) -> None:
        for value in ("0", "-3", "01", "1.0"):
            with self.subTest(value=value), self.assertRaises(ScenarioPreflightError):
                audit(occurrences=SAME_PERIOD.replace("101,1,1,1,1", f"101,{value},1,1,1"))

    def test_csv_header_reordering_and_extra_columns_block(self) -> None:
        with self.assertRaisesRegex(ScenarioPreflightError, "fields differ"):
            audit(events="other_id\n101\n")
        with self.assertRaisesRegex(ScenarioPreflightError, "missing or unexpected"):
            audit(occurrences=SAME_PERIOD.replace("101,1,1,1,1", "101,1,1,1,1,extra"))

    def test_event_set_options_flag_invalid_default_but_never_authorize_ep(self) -> None:
        text = json.dumps(SELECTOR)
        result = audit_event_set_options(text, settings_blob=git_blob_sha1(text.encode()))
        self.assertEqual(result["option_count"], 2)
        self.assertEqual(result["sum_declared_option_event_counts"], 6)
        self.assertFalse(result["default_matches_a_declared_option"])
        self.assertFalse(result["options_are_independent_physical_events"])
        self.assertFalse(result["annual_oep_aep_authorized"])

    def test_valid_selector_default_does_not_prove_events_independent(self) -> None:
        obj = json.loads(json.dumps(SELECTOR))
        obj["model_settings"]["event_set"]["default"] = "fictional_a"
        text = json.dumps(obj)
        result = audit_event_set_options(text, settings_blob=git_blob_sha1(text.encode()))
        self.assertTrue(result["default_matches_a_declared_option"])
        self.assertFalse(result["annual_oep_aep_authorized"])

    def test_duplicate_event_set_options_block(self) -> None:
        obj = json.loads(json.dumps(SELECTOR))
        obj["model_settings"]["event_set"]["options"][1]["id"] = "fictional_a"
        with self.assertRaisesRegex(ScenarioPreflightError, "duplicate event_set"):
            audit_event_set_options(json.dumps(obj), settings_blob="0" * 40)

    def test_boolean_count_and_nonfinite_json_block(self) -> None:
        obj = json.loads(json.dumps(SELECTOR))
        obj["model_settings"]["event_set"]["options"][0]["number_of_events"] = True
        with self.assertRaisesRegex(ScenarioPreflightError, "positive integer"):
            audit_event_set_options(json.dumps(obj), settings_blob="0" * 40)
        with self.assertRaisesRegex(ScenarioPreflightError, "non-finite"):
            audit_event_set_options(json.dumps(SELECTOR)[:-1] + ', "x": NaN}', settings_blob="0" * 40)

    def test_duplicate_json_key_blocks(self) -> None:
        with self.assertRaisesRegex(ScenarioPreflightError, "duplicate key"):
            audit_event_set_options('{"model_settings": {}, "model_settings": {}}', settings_blob="0" * 40)

    def test_git_blob_pinning_and_corruption_block(self) -> None:
        with TemporaryDirectory() as d:
            path = Path(d) / "synthetic_events.csv"
            path.write_text(EVENTS, encoding="utf-8")
            expected = git_blob_sha1(EVENTS.encode())
            self.assertEqual(read_source(path, expected)[1], expected)
            with self.assertRaisesRegex(ScenarioPreflightError, "differs from pinned"):
                read_source(path, "a" * 40)
            with self.assertRaisesRegex(ScenarioPreflightError, "40-character"):
                read_source(path, "ABC")
            path.write_bytes(b"\xff\xfe")
            with self.assertRaisesRegex(ScenarioPreflightError, "strict UTF-8"):
                read_source(path)

    def test_cli_returns_json_and_preserves_blocking_flag(self) -> None:
        with TemporaryDirectory() as d:
            root = Path(d)
            events = root / "events.csv"
            occurrence = root / "occurrence.csv"
            events.write_text(EVENTS, encoding="utf-8")
            occurrence.write_text(SAME_PERIOD, encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = main(["occurrences", str(events), str(occurrence), "--events-git-blob", git_blob_sha1(EVENTS.encode())])
            self.assertEqual(result, 0)
            parsed = json.loads(stdout.getvalue())
            self.assertFalse(parsed["annual_oep_aep_authorized"])
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                blocked = main(["occurrences", str(events), str(occurrence), "--events-git-blob", "f" * 40])
            self.assertEqual(blocked, 2)
            self.assertEqual(json.loads(stderr.getvalue())["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
