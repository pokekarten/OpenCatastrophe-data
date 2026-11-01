# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Strict synthetic-only QA for CAL FIRE inspection-frame aggregates."""

from __future__ import annotations

import json
import unittest

from scripts.calfire_dins_aggregate_qc_v0 import (
    DAMAGE_STATES,
    DinsAggregateError,
    MAX_BYTES,
    evaluate_aggregate,
)


def sample(year: int = 2022, n: int = 10) -> dict:
    return {
        "schema_version": "1.0.0",
        "source_id": "us.calfire.dins.structure-damage",
        "event_year": year,
        "origin": "synthetic",
        "source_snapshot_sha256": None,
        "inspection_frame": "calfire_dins_inspected_structures",
        "hazard_type": "Fire",
        "event_year_basis": "INCIDENTSTARTDATE",
        "contains_feature_rows": False,
        "damage_counts": {state: n for state in DAMAGE_STATES},
    }


def parsed(payload: dict) -> dict:
    return evaluate_aggregate(json.dumps(payload, sort_keys=True).encode())


class DinsAggregateTests(unittest.TestCase):
    def test_visible_inspected_counts_are_not_loss(self):
        out = parsed(sample())
        self.assertFalse(out["counts_suppressed"])
        self.assertEqual(out["inspected_record_count_not_exposure_denominator"], 60)
        self.assertFalse(out["financial_loss_inferred"])
        self.assertFalse(out["vulnerability_probability_inferred"])
        self.assertTrue(out["selection_bias_unresolved"])
        self.assertFalse(out["model_data_admitted"])

    def test_year_2013_with_no_damage_zero_is_valid_but_biased(self):
        obj = sample(year=2013)
        obj["damage_counts"]["No Damage"] = 0
        out = parsed(obj)
        self.assertTrue(out["pre_2018_non_damage_records_not_collected"])
        self.assertFalse(out["exposure_population_denominator_available"])

    def test_year_2017_with_no_damage_positive_rejected(self):
        with self.assertRaises(DinsAggregateError):
            parsed(sample(year=2017))

    def test_year_2018_does_not_remove_bias_flag(self):
        out = parsed(sample(year=2018))
        self.assertTrue(out["selection_bias_unresolved"])

    def test_suppress_whole_table_if_one_cell_small(self):
        obj = sample()
        obj["damage_counts"]["Inaccessible"] = 1
        out = parsed(obj)
        self.assertTrue(out["counts_suppressed"])
        self.assertNotIn("damage_counts_within_inspected_frame", out)
        self.assertNotIn("inspected_record_count_not_exposure_denominator", out)

    def test_suppress_small_total(self):
        obj = sample(n=0)
        obj["damage_counts"]["Destroyed (>50%)"] = 1
        out = parsed(obj)
        self.assertTrue(out["counts_suppressed"])
        self.assertNotIn("damage_counts_within_inspected_frame", out)

    def test_reject_zero_total(self):
        with self.assertRaises(DinsAggregateError):
            parsed(sample(n=0))

    def test_reject_extra_address(self):
        obj = sample()
        obj["SITEADDRESS"] = "synthetic 1"
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_reject_non_fire_hazard(self):
        obj = sample()
        obj["hazard_type"] = "Flood"
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_reject_edit_time_as_event_year(self):
        obj = sample()
        obj["event_year_basis"] = "EDIT_DATE"
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_reject_raw_row_flag(self):
        obj = sample()
        obj["contains_feature_rows"] = True
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_reject_extra_damage_class(self):
        obj = sample()
        obj["damage_counts"]["Unknown"] = 15
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_reject_missing_inaccessible(self):
        obj = sample()
        del obj["damage_counts"]["Inaccessible"]
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_reject_bool_as_count(self):
        obj = sample()
        obj["damage_counts"]["No Damage"] = True
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_reject_negative_and_float_counts(self):
        for bad in (-1, 2.5):
            obj = sample()
            obj["damage_counts"]["Inaccessible"] = bad
            with self.assertRaises(DinsAggregateError):
                parsed(obj)

    def test_reject_bool_as_year(self):
        obj = sample()
        obj["event_year"] = True
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_reject_unidentified_external_aggregate(self):
        obj = sample()
        obj["origin"] = "externally_prepared_aggregate"
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_external_hash_is_only_syntax_checked(self):
        obj = sample()
        obj["origin"] = "externally_prepared_aggregate"
        obj["source_snapshot_sha256"] = "a" * 64
        out = parsed(obj)
        self.assertTrue(out["source_snapshot_hash_supplied_but_not_verified"])
        self.assertFalse(out["model_data_admitted"])

    def test_reject_fabricated_synthetic_snapshot_claim(self):
        obj = sample()
        obj["source_snapshot_sha256"] = "b" * 64
        with self.assertRaises(DinsAggregateError):
            parsed(obj)

    def test_reject_duplicate_json_keys(self):
        with self.assertRaises(DinsAggregateError):
            evaluate_aggregate(b'{"source_id":"x","source_id":"y"}')

    def test_reject_nonfinite_constant(self):
        with self.assertRaises(DinsAggregateError):
            evaluate_aggregate(b'{"event_year":NaN}')

    def test_reject_oversize(self):
        with self.assertRaises(DinsAggregateError):
            evaluate_aggregate(b"x" * (MAX_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
