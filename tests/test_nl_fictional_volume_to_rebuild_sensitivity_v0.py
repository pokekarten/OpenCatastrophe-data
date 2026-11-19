# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only completely fictional volume, unit-cost and index inputs are tested."""
from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from research_runners.nl_fictional_volume_to_rebuild_sensitivity_v0 import (
    FictionalRebuildError, calculate, main, read_fixture,
)


def fixture():
    return {
        "schema": "fictional-dutch-rebuild-cost-sensitivity-v0",
        "provenance": {
            "source_kind": "invented_fixture_only",
            "real_provider_rows": 0,
            "licensed_cost_baseline": False,
            "real_insurer_identity": False,
            "source_admitted": False,
            "model_input_approved": False,
        },
        "scenario": {
            "currency": "EUR",
            "rate_unit": "EUR_per_m3",
            "cost_rate_baseline_period": "2025-01",
            "target_period": "2026-01",
            "rate_was_already_indexed_to_target": False,
            "fictional_low_rate_eur_per_m3": "100.00",
            "fictional_high_rate_eur_per_m3": "200.00",
            "fictional_base_period_index": "100.0",
            "fictional_target_period_index": "110.0",
            "fictional_index_style": "independent_CBS_style_synthetic_numbers",
        },
        "buildings": [
            {"id": f"SYNTH-BLDG-{i:03d}",
             "usage_class": "synthetic_standard_residential",
             "volumes_m3": {"lod12": "110", "lod13": "100", "lod22": "90"}}
            for i in range(1, 6)
        ],
    }


class FictionalRebuildSensitivityTests(unittest.TestCase):
    def test_uses_volume_range_once_not_three_additive_lods(self):
        result = calculate(fixture())
        self.assertEqual(result["fictional_building_count"], 5)
        self.assertEqual(result["fictional_rebuild_lower_eur"], "49500.00")
        self.assertEqual(result["fictional_rebuild_mid_eur"], "82500.00")
        self.assertEqual(result["fictional_rebuild_upper_eur"], "121000.00")
        self.assertEqual(result["fictional_lod_volume_sums_m3"],
                         {"lod12": "550", "lod13": "500", "lod22": "450"})
        self.assertEqual(result["fictional_index_ratio_target_over_base"], "1.1")
        self.assertTrue(result["sensitivity_interval_not_confidence_band"])
        self.assertIsNone(result["actual_insured_tiv"])
        for key in ("cost_rate_rights_reviewed", "original_3dbag_release_pinned",
                    "3dbag_original_feature_bytes_used",
                    "real_buildings_or_insurer_inferred",
                    "premium_or_coverage_inferred",
                    "cat_model_input_approved",
                    "building_peril_or_treaty_model_calibrated",
                    "gross_net_oep_aep_ip_curves_computed"):
            self.assertFalse(result[key])

    def test_already_indexed_rate_must_not_be_escalated_again(self):
        d = fixture()
        d["scenario"]["rate_was_already_indexed_to_target"] = True
        with self.assertRaisesRegex(FictionalRebuildError, "double-escalation"):
            calculate(d)
        d = fixture()
        d["scenario"]["target_period"] = "2025-01"
        with self.assertRaisesRegex(FictionalRebuildError, "double-escalation"):
            calculate(d)

    def test_rejects_real_input_or_nonfictional_costs(self):
        for field, value in (
            ("source_kind", "3dbag_live"),
            ("real_provider_rows", 5),
            ("licensed_cost_baseline", True),
            ("real_insurer_identity", "R+V"),
            ("source_admitted", True),
            ("model_input_approved", True),
        ):
            with self.subTest(field=field):
                d = fixture()
                d["provenance"][field] = value
                with self.assertRaises(FictionalRebuildError):
                    calculate(d)

    def test_no_unvalidated_nonresidential_typologies(self):
        d = fixture()
        d["buildings"][0]["usage_class"] = "commercial"
        with self.assertRaisesRegex(FictionalRebuildError, "non-residential"):
            calculate(d)

    def test_rejects_volume_issues_and_duplicate_buildings(self):
        for v in ("0", "-1", "nan", True, "inf", "1000001"):
            with self.subTest(v=v):
                d = fixture()
                d["buildings"][0]["volumes_m3"]["lod22"] = v
                with self.assertRaises(FictionalRebuildError):
                    calculate(d)
        d = fixture()
        d["buildings"][1]["id"] = d["buildings"][0]["id"]
        with self.assertRaises(FictionalRebuildError):
            calculate(d)

    def test_costs_and_indices_must_be_fictional_and_bounded(self):
        for name, value in (
            ("fictional_low_rate_eur_per_m3", "0"),
            ("fictional_high_rate_eur_per_m3", "50.00"),
            ("fictional_base_period_index", "0"),
            ("fictional_target_period_index", "10000.1"),
            ("fictional_target_period_index", "999"),
        ):
            with self.subTest(field=name, value=value):
                d = fixture()
                d["scenario"][name] = value
                with self.assertRaises(FictionalRebuildError):
                    calculate(d)

    def test_rejects_address_fields_geography_and_treaty_data(self):
        d = fixture()
        d["buildings"][0]["latitude"] = 52.0
        with self.assertRaisesRegex(FictionalRebuildError, "wrong fields"):
            calculate(d)
        d = fixture()
        d["scenario"]["insurance_policy_id"] = "not-synthetic"
        with self.assertRaisesRegex(FictionalRebuildError, "wrong fields"):
            calculate(d)

    def test_rejects_backdated_cost_reference(self):
        d = fixture()
        d["scenario"]["cost_rate_baseline_period"] = "2026-11"
        d["scenario"]["target_period"] = "2025-01"
        with self.assertRaisesRegex(FictionalRebuildError, "back-date"):
            calculate(d)

    def test_cli_and_duplicate_toml_field_rejection(self):
        sample = (Path(__file__).resolve().parents[1] / "research" / "scenarios"
                  / "nl_fictional_volume_rebuild_math_v0.toml")
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "purely-invented.toml"
            file.write_bytes(sample.read_bytes())
            self.assertEqual(read_fixture(file), fixture())
            self.assertEqual(main(["--fixture", str(file)]), 0)
            file.write_text('schema = "x"\nschema = "y"\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                read_fixture(file)
            self.assertEqual(main(["--fixture", str(file)]), 2)


if __name__ == "__main__":
    unittest.main()
