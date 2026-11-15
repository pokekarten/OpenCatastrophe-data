# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic-only interval consistency tests; no external data."""
import copy
import unittest

from research_runners.loing2016_synthetic_depth_interval_compare_v0 import (
    IntervalComparisonBlocked, compare_synthetic_intervals,
)


def row(identifier, label, predicted):
    return {
        "synthetic_cell_id": "SYN_" + identifier,
        "depth_class": label,
        "predicted_depth_m": predicted,
    }


def envelope(rows):
    return {
        "experiment": "SYNTHETIC_ONLY_NO_OBSERVED_PROVIDER_BYTES",
        "atlas_version": "DDT45_LOING_AVAL_AZI_2021",
        "event_id": "LOING_MAY_JUNE_2016",
        "synthetic_rows": rows,
    }


class SyntheticIntervalDiagnosticTests(unittest.TestCase):
    def test_all_four_2021_classes_and_open_top(self):
        r = compare_synthetic_intervals(envelope([
            row("A", "0-0.5", "0.125"),
            row("B", "0.5-1", "0.625"),
            row("C", "1-2", "1.375"),
            row("D", ">2", "8.000"),
        ]))
        self.assertEqual(r["synthetic_cells_checked"], 4)
        self.assertEqual(r["synthetic_cells_outside_intervals"], 0)
        self.assertIsNone(r["per_cell"][-1]["class_upper_boundary_m"])
        self.assertEqual(r["sum_distance_outside_intervals_m"], "0")

    def test_interval_distance_is_not_midpoint_error(self):
        r = compare_synthetic_intervals(envelope([
            row("A", "0.5-1", "0.200"),
            row("B", "1-2", "3.200"),
            row("C", ">2", "1.900"),
        ]))
        self.assertEqual(
            [x["interval_relation"] for x in r["per_cell"]],
            ["below_interval", "above_interval", "below_interval"],
        )
        self.assertEqual(
            [x["distance_outside_interval_m"] for x in r["per_cell"]],
            ["0.300", "1.200", "0.100"],
        )
        self.assertEqual(r["sum_distance_outside_intervals_m"], "1.600")
        self.assertEqual(r["max_distance_outside_intervals_m"], "1.200")

    def test_edges_are_uncertain_not_validated_inside(self):
        r = compare_synthetic_intervals(envelope([
            row("A", "0-0.5", "0.500"), row("B", "0.5-1", "0.500"),
            row("C", ">2", "2.000"),
        ]))
        self.assertEqual(
            {x["interval_relation"] for x in r["per_cell"]},
            {"on_boundary_inclusion_unresolved"},
        )

    def test_no_source_rights_loss_hazard_or_holdout_upgrade(self):
        r = compare_synthetic_intervals(envelope([row("A", "1-2", "1.250")]))
        for key in (
            "independent_observed_flood_holdout_verified",
            "original_atlas_geometry_or_depth_bytes_authenticated",
            "source_rights_and_calibration_lineage_established",
            "terrain_or_building_depth_inferred",
            "probabilistic_hazard_or_flood_return_period_validated",
            "insured_loss_or_gross_net_curve_permitted",
        ):
            self.assertFalse(r[key], key)
        self.assertFalse(r["per_cell"][0]["is_precise_observed_building_depth"])

    def test_no_real_address_or_geo_identifier_accepted(self):
        d = envelope([row("A", "1-2", "1.250")])
        d["synthetic_rows"][0]["synthetic_cell_id"] = "MONTARGIS_REAL_BUILDING"
        with self.assertRaises(IntervalComparisonBlocked):
            compare_synthetic_intervals(d)

    def test_fake_real_dataset_science_claim_rejected(self):
        for value in ("REAL_2016", "OBSERVED", "", None):
            d = envelope([row("A", "1-2", "1.250")])
            d["experiment"] = value
            with self.subTest(value=value), self.assertRaises(IntervalComparisonBlocked):
                compare_synthetic_intervals(d)

    def test_wrong_edition_event_or_extra_admission_rejected(self):
        for key, value in (
            ("atlas_version", "DRIEE_LOING_2017"),
            ("event_id", "LOING_1910"),
            ("approved_for_loss", True),
        ):
            d = envelope([row("A", "0-0.5", "0.250")])
            d[key] = value
            with self.subTest(key=key), self.assertRaises(IntervalComparisonBlocked):
                compare_synthetic_intervals(d)

    def test_float_boolean_negative_exp_and_nan_predictions_blocked(self):
        for value in (1.125, True, None, "-1", "1e3", "NaN", "Infinity",
                      "50.001", "0.1234", "000.001"):
            with self.subTest(value=value), self.assertRaises(IntervalComparisonBlocked):
                compare_synthetic_intervals(envelope([row("A", "1-2", value)]))

    def test_invalid_class_and_malformed_collections_rejected(self):
        for label in ("1-1.5", "2-3", 1, None, [], {"value": ">2"}):
            with self.subTest(label=label), self.assertRaises(IntervalComparisonBlocked):
                compare_synthetic_intervals(envelope([row("A", label, "1.5")]))

    def test_duplicate_cells_and_nonlist_rows_rejected(self):
        with self.assertRaises(IntervalComparisonBlocked):
            compare_synthetic_intervals(envelope([
                row("A", "0-0.5", "0.1"), row("A", ">2", "3.2")
            ]))
        with self.assertRaises(IntervalComparisonBlocked):
            compare_synthetic_intervals(envelope("not a list"))

    def test_bounded_cohort_enforced(self):
        for rs in ([], [row(str(i), "0-0.5", "0.1") for i in range(101)]):
            with self.assertRaises(IntervalComparisonBlocked):
                compare_synthetic_intervals(envelope(rs))

    def test_extra_source_provenance_approval_on_cell_rejected(self):
        d = envelope([row("A", "0.5-1", "0.7")])
        d["synthetic_rows"][0]["is_2016_validation"] = True
        with self.assertRaises(IntervalComparisonBlocked):
            compare_synthetic_intervals(d)

    def test_cell_type_and_nonpositive_id_rejected(self):
        for ident in ("SYN_", "SYN_A-B", 42, True, "", "SYN_abc"):
            d = envelope([row("A", "1-2", "1.0")])
            d["synthetic_rows"][0]["synthetic_cell_id"] = ident
            with self.subTest(ident=ident), self.assertRaises(IntervalComparisonBlocked):
                compare_synthetic_intervals(d)


if __name__ == "__main__":
    unittest.main()
