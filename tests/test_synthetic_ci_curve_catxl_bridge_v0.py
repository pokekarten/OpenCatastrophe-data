# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only hazard -> vulnerability -> gross EUR -> CAT-XL regression tests."""

import copy
import json
import unittest

from research_runners.synthetic_ci_curve_catxl_bridge_v0 import (
    SyntheticCurveBridgeError,
    fictional_event_loss_cells,
    synthetic_hazard_to_catxl,
)


class SyntheticCurveToCatXLTests(unittest.TestCase):
    def setUp(self):
        self.positions = {"SYNTH-01": 500_000, "SYNTH-02": 300_000}
        self.curve = [(0, 0.0), (100, 0.5), (200, 1.0)]
        self.treaty = {
            "currency": "EUR", "year": 2026, "portfolio_as_of": "2026-11-01",
            "attachment_eur": 200_000, "occurrence_limit_eur": 500_000,
            "reinstatements": 1, "covered_perils": ["flood", "windstorm"],
            "reinstatement_pricing": "assumed_free_for_math_only", "synthetic_only": True,
        }
        self.events = [
            {"event_id": "FICTIONAL-FLOOD-001", "date": "2026-11-02",
             "peril": "flood", "intensity_unit": "mm", "intensities": {"SYNTH-01": 100}},
            {"event_id": "FICTIONAL-FLOOD-002", "date": "2026-11-03",
             "peril": "flood", "intensity_unit": "mm",
             "intensities": {"SYNTH-01": 200, "SYNTH-02": 100}},
        ]

    def run_bridge(self):
        return synthetic_hazard_to_catxl(
            positions_eur=self.positions, hazard_events=self.events,
            toy_treaty=self.treaty, curve_points=self.curve,
            source_curve_id="SYNTH-TEST-FLOOD-RATIO",
            asset_class="SYNTH-HOMOGENEOUS-BUILDING",
            curve_unit="mm", output_metric="fractional_damage_ratio",
        )

    def cells(self, **overrides):
        args = dict(
            positions_eur=self.positions, intensities={"SYNTH-01": 50},
            curve_points=self.curve, source_curve_id="SYNTH-TEST-FLOOD-RATIO",
            asset_class="SYNTH-HOMOGENEOUS-BUILDING", curve_unit="mm",
            event_unit="mm", output_metric="fractional_damage_ratio",
        )
        args.update(overrides)
        return fictional_event_loss_cells(**args)

    def test_full_arithmetic_chain_and_loss_conservation(self):
        r = self.run_bridge()
        self.assertEqual([e["gross_eur"] for e in r["events"]], [250_000, 650_000])
        self.assertEqual([e["ceded_eur"] for e in r["events"]], [50_000, 450_000])
        self.assertEqual((r["gross_eur"], r["ceded_eur"], r["net_eur"]),
                         (900_000, 500_000, 400_000))
        self.assertEqual(r["gross_eur"], r["ceded_eur"] + r["net_eur"])
        self.assertFalse(r["model_input_approved"])
        self.assertFalse(r["hazard_input_real"])
        self.assertFalse(r["commercial_use_cleared"])

    def test_linear_interpolation_midpoint(self):
        self.assertEqual(self.cells(), {"SYNTH-01": 125_000})

    def test_round_half_up_to_whole_eur(self):
        self.assertEqual(
            self.cells(positions_eur={"SYNTH-01": 1},
                       intensities={"SYNTH-01": 100}),
            {"SYNTH-01": 1},
        )

    def test_reject_out_of_support_instead_of_extrapolating(self):
        for intensity in (-1, 201):
            with self.subTest(intensity=intensity), self.assertRaises(SyntheticCurveBridgeError):
                self.cells(intensities={"SYNTH-01": intensity})

    def test_reject_unit_ambiguity(self):
        with self.assertRaisesRegex(SyntheticCurveBridgeError, "unit conversion"):
            self.cells(event_unit="m")

    def test_repair_rate_and_pipes_per_km_cannot_become_eur(self):
        for metric in ("repair_rate", "pipe_repairs_per_km"):
            with self.subTest(metric=metric), self.assertRaises(SyntheticCurveBridgeError):
                self.cells(output_metric=metric)

    def test_external_identifiers_and_asset_mismatch_rejected(self):
        for key, val in (
            ("source_curve_id", "NIRANDJAN-REAL-001"),
            ("asset_class", "Real substations"),
            ("intensities", {"EXTERNAL-01": 100}),
        ):
            with self.subTest(key=key), self.assertRaises(SyntheticCurveBridgeError):
                self.cells(**{key: val})

    def test_nonfinite_bool_and_invalid_exposure_rejected(self):
        for x in (True, float("inf"), float("nan"), "100"):
            with self.subTest(x=repr(x)), self.assertRaises(SyntheticCurveBridgeError):
                self.cells(intensities={"SYNTH-01": x})
        for x in (True, -1, 0, 10**13, 0.5):
            with self.subTest(tiv=repr(x)), self.assertRaises(SyntheticCurveBridgeError):
                self.cells(positions_eur={"SYNTH-01": x})

    def test_events_without_identity_and_extra_loss_injection_rejected(self):
        self.events[0]["real_loss_eur"] = 100
        with self.assertRaises(SyntheticCurveBridgeError):
            self.run_bridge()

    def test_same_day_and_unsupported_treaty_fails_downstream(self):
        from research_runners.synthetic_catxl_loss_math_v0 import SyntheticLossInputError
        self.events[1]["date"] = self.events[0]["date"]
        with self.assertRaises(SyntheticLossInputError):
            self.run_bridge()
        self.events[1]["date"] = "2026-11-03"
        self.treaty["synthetic_only"] = False
        with self.assertRaises(SyntheticLossInputError):
            self.run_bridge()

    def test_deterministic_and_input_immutable(self):
        before = copy.deepcopy((self.positions, self.events, self.treaty, self.curve))
        a = self.run_bridge()
        b = self.run_bridge()
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertEqual(before, (self.positions, self.events, self.treaty, self.curve))


if __name__ == "__main__":
    unittest.main()
