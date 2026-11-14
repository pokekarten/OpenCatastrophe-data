# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only negative and conservation tests for insurer premium marginals."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
from synthetic_insurer_premium_marginals_v0 import MarginalFitError, fit_synthetic_marginals


def fixture() -> dict:
    # Arbitrary fictional labels and numbers; not any insurer's real premiums.
    return {
        "schema_version": "0.1.0",
        "scenario_kind": "fully_synthetic_test_only",
        "premium_basis": "direct_gross_written_premium",
        "geography_basis": "underlying_risk_location",
        "currency": "EUR",
        "as_of": "2025-12-31",
        "region_totals": [{"region": "FICT_A", "premium": 80},
                          {"region": "FICT_B", "premium": 120}],
        "line_totals": [{"line": "FICT_PROPERTY", "premium": 100},
                        {"line": "FICT_MOTOR", "premium": 60},
                        {"line": "FICT_LIABILITY", "premium": 40}],
        "prior_weights": [
            {"region": r, "line": l, "weight": (3 if r == "FICT_A" else 1) if l == "FICT_PROPERTY" else 1}
            for r in ("FICT_A", "FICT_B")
            for l in ("FICT_PROPERTY", "FICT_MOTOR", "FICT_LIABILITY")
        ],
        "structural_zeros": [],
    }


class SyntheticMarginalTests(unittest.TestCase):
    def test_conservation_all_dimensions(self):
        scenario = fixture()
        result = fit_synthetic_marginals(scenario)
        for row in scenario["region_totals"]:
            self.assertAlmostEqual(
                sum(x["synthetic_premium"] for x in result["cells"] if x["region"] == row["region"]),
                row["premium"], places=7)
        for col in scenario["line_totals"]:
            self.assertAlmostEqual(
                sum(x["synthetic_premium"] for x in result["cells"] if x["line"] == col["line"]),
                col["premium"], places=7)
        self.assertFalse(result["observed_insurer_portfolio"])
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["has_insured_tiv"])
        self.assertFalse(result["has_cat_peril_allocation"])

    def test_deterministic_for_same_scenario(self):
        self.assertEqual(fit_synthetic_marginals(fixture()), fit_synthetic_marginals(fixture()))

    def test_joint_not_identified_by_identical_marginals(self):
        one = fixture()
        one["region_totals"] = [{"region": "FICT_A", "premium": 50},
                                {"region": "FICT_B", "premium": 50}]
        one["line_totals"] = [{"line": "FICT_PROPERTY", "premium": 50},
                              {"line": "FICT_MOTOR", "premium": 50}]
        one["prior_weights"] = [
            {"region": r, "line": l,
             "weight": 9 if (r == "FICT_A") == (l == "FICT_PROPERTY") else 1}
            for r in ("FICT_A", "FICT_B") for l in ("FICT_PROPERTY", "FICT_MOTOR")]
        two = deepcopy(one)
        for cell in two["prior_weights"]:
            cell["weight"] = 1 if cell["weight"] == 9 else 9
        first = fit_synthetic_marginals(one)
        second = fit_synthetic_marginals(two)
        def extract(o):
            return next(c["synthetic_premium"] for c in o["cells"]
                        if c["region"] == "FICT_A" and c["line"] == "FICT_PROPERTY")
        self.assertGreater(extract(first), 40)
        self.assertLess(extract(second), 10)
        self.assertEqual(first["scenario_kind"], "fully_synthetic_test_only")

    def test_explicit_structural_zero_is_preserved(self):
        scenario = fixture()
        scenario["structural_zeros"] = [{"region": "FICT_A", "line": "FICT_MOTOR"}]
        scenario["prior_weights"] = [p for p in scenario["prior_weights"]
                                     if (p["region"], p["line"]) != ("FICT_A", "FICT_MOTOR")]
        out = fit_synthetic_marginals(scenario)
        z = next(c for c in out["cells"] if c["region"] == "FICT_A" and c["line"] == "FICT_MOTOR")
        self.assertTrue(z["structural_zero"])
        self.assertEqual(z["synthetic_premium"], 0.0)

    def test_mismatched_region_and_lob_totals_rejected(self):
        scenario = fixture()
        scenario["line_totals"][0]["premium"] += 5
        with self.assertRaisesRegex(MarginalFitError, "totals disagree"):
            fit_synthetic_marginals(scenario)

    def test_missing_allowed_cell_cannot_be_assumed_zero(self):
        scenario = fixture()
        scenario["prior_weights"].pop()
        with self.assertRaisesRegex(MarginalFitError, "every allowed cell"):
            fit_synthetic_marginals(scenario)

    def test_no_implicit_risk_location_from_cedent_domicile(self):
        scenario = fixture()
        scenario["geography_basis"] = "cedent_domicile"
        with self.assertRaisesRegex(MarginalFitError, "risk situs"):
            fit_synthetic_marginals(scenario)

    def test_no_reinsurance_margins_treated_as_direct_gwp(self):
        scenario = fixture()
        scenario["premium_basis"] = "assumed_reinsurance_premium"
        with self.assertRaisesRegex(MarginalFitError, "direct GWP"):
            fit_synthetic_marginals(scenario)

    def test_unreviewed_real_data_cannot_use_synthetic_prototype(self):
        scenario = fixture()
        scenario["scenario_kind"] = "public_source_observation"
        with self.assertRaisesRegex(MarginalFitError, "synthetic"):
            fit_synthetic_marginals(scenario)

    def test_invalid_numbers_not_silently_zeroed(self):
        for invalid in [-1, float("nan"), float("inf"), True, None, "missing"]:
            with self.subTest(invalid=str(invalid)):
                scenario = fixture()
                scenario["region_totals"][0]["premium"] = invalid
                with self.assertRaises(MarginalFitError):
                    fit_synthetic_marginals(scenario)

    def test_duplicate_keys_rejected(self):
        scenario = fixture()
        scenario["region_totals"][1]["region"] = "FICT_A"
        with self.assertRaisesRegex(MarginalFitError, "duplicate"):
            fit_synthetic_marginals(scenario)

    def test_infeasible_structural_zeros_fail_closed(self):
        scenario = fixture()
        scenario["structural_zeros"] = [{"region": "FICT_A", "line": "FICT_PROPERTY"},
                                        {"region": "FICT_A", "line": "FICT_MOTOR"}]
        scenario["prior_weights"] = [p for p in scenario["prior_weights"]
                                     if not (p["region"] == "FICT_A"
                                             and p["line"] in ("FICT_PROPERTY", "FICT_MOTOR"))]
        with self.assertRaises(MarginalFitError):
            fit_synthetic_marginals(scenario)

    def test_no_unrecognised_fields_or_bad_date(self):
        scenario = fixture()
        scenario["location_count"] = 200
        with self.assertRaisesRegex(MarginalFitError, "keys"):
            fit_synthetic_marginals(scenario)
        scenario = fixture()
        scenario["as_of"] = "2025-02-30"
        with self.assertRaisesRegex(MarginalFitError, "valid"):
            fit_synthetic_marginals(scenario)


if __name__ == "__main__":
    unittest.main()
