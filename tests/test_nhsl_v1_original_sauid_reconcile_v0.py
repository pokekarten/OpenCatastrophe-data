# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only unit and negative tests for original NHSL SAUID reconciliation."""

from __future__ import annotations

import copy
import math
import unittest

from scripts.nhsl_v1_original_sauid_reconcile_v0 import (
    FIELDS, NHSLReconcileError, compare_aggregate_rows,
)


def fake_source_rows() -> tuple[list[dict], list[dict]]:
    # Entirely synthetic. Never include provider's original asset rows in CI.
    archetype_amounts = [
        ("SYNTH-A", [2, 1000, 60, 140, 200, 30, 230]),
        ("SYNTH-A", [1, 500, 30, 70, 100, 20, 120]),
        ("SYNTH-B", [4, 2000, 120, 280, 400, 100, 500]),
    ]
    polygon_amounts = [
        ("SYNTH-A", [3, 1500, 90, 210, 300, 50, 350]),
        ("SYNTH-B", [4, 2000, 120, 280, 400, 100, 500]),
    ]
    def make(id_: str, values: list[float], role: int) -> dict:
        return {"Sauid": id_, **{
            pair[role]: value for pair, value in zip(FIELDS.values(), values)
        }}
    return (
        [make(id_, values, 0) for id_, values in polygon_amounts],
        [make(id_, values, 1) for id_, values in archetype_amounts],
    )


class TestOriginalNHSLSourceConservation(unittest.TestCase):
    def test_per_sauid_conservation_and_non_admission(self) -> None:
        polygons, archetypes = fake_source_rows()
        r = compare_aggregate_rows(polygons, archetypes)
        self.assertEqual(r["settled_areas"], 2)
        self.assertEqual(r["archetype_records"], 3)
        self.assertEqual(r["unique_archetype_sauids"], 2)
        self.assertEqual(r["matched_sauids"], 2)
        self.assertEqual(r["unmatched_polygon_sauids"], 0)
        self.assertEqual(r["unmatched_archetype_sauids"], 0)
        self.assertTrue(r["numeric_conservation_passed"])
        self.assertEqual(r["metrics"]["building_count"]["polygon_total"], "7")
        self.assertEqual(r["metrics"]["assets_cad_2019"]["polygon_total"], "850")
        self.assertEqual(r["metrics"]["building_cost_cad_2019"]["archetype_total"], "700")
        for val in r["metrics"].values():
            self.assertEqual(val["sauids_exceeding_tolerance"], 0)
            self.assertEqual(val["max_abs_delta_per_sauid"], "0")
        for blocked in (
            "archetype_is_individual_rooftop",
            "observed_insured_values",
            "oed_insured_locations_exportable",
            "source_rights_for_model_use_reviewed",
            "scientific_fitness_reviewed",
            "model_input_approved",
        ):
            self.assertFalse(r[blocked], blocked)
        self.assertEqual(r["admission_status"], "not_admitted")
        self.assertNotIn("SYNTH-A", str(r))
        self.assertNotIn("SYNTH-B", str(r))

    def test_rounding_cent_threshold_explicit(self) -> None:
        p, a = fake_source_rows()
        a[0]["E_BldgValue"] += 0.01
        r = compare_aggregate_rows(p, a)
        self.assertTrue(r["numeric_conservation_passed"])
        self.assertEqual(r["metrics"]["building_cost_cad_2019"]["sauids_exceeding_tolerance"], 0)
        a[0]["E_BldgValue"] += 0.03
        r = compare_aggregate_rows(p, a)
        self.assertFalse(r["numeric_conservation_passed"])
        self.assertEqual(r["metrics"]["building_cost_cad_2019"]["sauids_exceeding_tolerance"], 1)
        self.assertEqual(r["admission_status"], "not_admitted")

    def test_tiny_integer_quantity_drift_fails(self) -> None:
        p, a = fake_source_rows()
        a[0]["E_BldgNum"] += 0.01
        r = compare_aggregate_rows(p, a)
        self.assertFalse(r["numeric_conservation_passed"])
        self.assertEqual(r["metrics"]["building_count"]["sauids_exceeding_tolerance"], 1)

    def test_duplicate_polygon_sauid_cannot_pass(self) -> None:
        p, a = fake_source_rows()
        p.append(copy.deepcopy(p[0]))
        with self.assertRaisesRegex(NHSLReconcileError, "duplicate polygon"):
            compare_aggregate_rows(p, a)

    def test_orphan_polygon_and_orphan_archetype_fail(self) -> None:
        p, a = fake_source_rows()
        r = compare_aggregate_rows(p + [{"Sauid": "SYNTH-X", **{
            pair[0]: 0 for pair in FIELDS.values()
        }}], a)
        self.assertFalse(r["numeric_conservation_passed"])
        self.assertEqual(r["unmatched_polygon_sauids"], 1)
        r = compare_aggregate_rows(p, a + [{"Sauid": "SYNTH-Y", **{
            pair[1]: 0 for pair in FIELDS.values()
        }}])
        self.assertFalse(r["numeric_conservation_passed"])
        self.assertEqual(r["unmatched_archetype_sauids"], 1)

    def test_archetype_group_moved_to_wrong_sauid_fails(self) -> None:
        p, a = fake_source_rows()
        a[0]["Sauid"] = "SYNTH-B"
        result = compare_aggregate_rows(p, a)
        self.assertFalse(result["numeric_conservation_passed"])
        self.assertGreater(result["metrics"]["building_count"]["sauids_exceeding_tolerance"], 0)

    def test_invalid_null_negative_nan_and_boolean_fail_closed(self) -> None:
        for value in (None, float("nan"), float("inf"), -1, True, "100"):
            with self.subTest(value=str(value)):
                p, a = fake_source_rows()
                a[1]["E_AssetValue"] = value
                with self.assertRaises(NHSLReconcileError):
                    compare_aggregate_rows(p, a)
                p, a = fake_source_rows()
                p[0]["Et_AssetValue"] = value
                with self.assertRaises(NHSLReconcileError):
                    compare_aggregate_rows(p, a)

    def test_missing_or_nontext_sauid_rejected(self) -> None:
        for value in (None, "", 123, "x" * 71):
            with self.subTest(value=str(value)):
                p, a = fake_source_rows()
                a[0]["Sauid"] = value
                with self.assertRaises(NHSLReconcileError):
                    compare_aggregate_rows(p, a)

    def test_unbounded_or_empty_source_stops(self) -> None:
        p, a = fake_source_rows()
        with self.assertRaisesRegex(NHSLReconcileError, "empty"):
            compare_aggregate_rows([], a)
        with self.assertRaisesRegex(NHSLReconcileError, "empty"):
            compare_aggregate_rows(p, [])


if __name__ == "__main__":
    unittest.main()
