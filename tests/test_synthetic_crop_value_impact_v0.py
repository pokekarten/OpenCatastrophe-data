# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Purely fictional crop-value arithmetic and uncertainty-bound tests."""
from __future__ import annotations

import unittest
from shapely.geometry import box, mapping

from research_runners.synthetic_crop_value_impact_v0 import (
    ImpactError, hypothetical_impact,
)


def fixture():
    parcels = {
        "schema": "synthetic-crop-parcels-v0", "crs": "EPSG:3035",
        "synthetic_only": True, "external_source_rows_used": 0,
        "parcels": [
            {"parcel_id": "SYNTH-CROP-001", "crop_class": "SYNTH-WHEAT",
             "geometry": mapping(box(0, 0, 100, 100))},
            {"parcel_id": "SYNTH-CROP-002", "crop_class": "SYNTH-MAIZE",
             "geometry": mapping(box(100, 0, 200, 100))},
        ],
    }
    hazard = {
        "schema": "synthetic-crop-hazard-v0", "crs": "EPSG:3035",
        "synthetic_only": True, "external_source_rows_used": 0,
        "event_id": "SYNTH-EVENT-001", "peril": "flood", "unit": "m",
        "zones": [
            {"zone_id": "SYNTH-ZONE-001", "intensity": 1, "nodata": False,
             "geometry": mapping(box(0, 0, 150, 100))},
            {"zone_id": "SYNTH-ZONE-002", "intensity": 2, "nodata": False,
             "geometry": mapping(box(50, 0, 100, 100))},
            {"zone_id": "SYNTH-ZONE-003", "intensity": None, "nodata": True,
             "geometry": mapping(box(150, 0, 200, 100))},
        ],
    }
    return parcels, hazard


class FictionalCropImpactTests(unittest.TestCase):
    def test_example_direct_impact_bounds_and_conservation(self):
        parcels, hazard = fixture()
        result = hypothetical_impact(parcels, hazard)
        self.assertEqual(result["fictional_total_asset_value_eur"], "24000.00")
        self.assertEqual(result["fictional_known_support_direct_impact_eur"], "4900.00")
        self.assertEqual(
            result["fictional_unobserved_support_impact_increment_max_eur"], "7000.00")
        self.assertEqual(result["fictional_total_direct_impact_lower_eur"], "4900.00")
        self.assertEqual(result["fictional_total_direct_impact_upper_eur"], "11900.00")
        self.assertEqual(result["per_fictional_parcel"][0][
            "known_support_direct_impact_eur"], "3500.00")
        self.assertEqual(result["per_fictional_parcel"][1][
            "known_support_direct_impact_eur"], "1400.00")
        self.assertEqual(result["per_fictional_parcel"][1][
            "unknown_support_increment_max_eur"], "7000.00")

    def test_unknown_outside_footprint_is_not_dry(self):
        parcels, hazard = fixture()
        hazard["zones"] = [{
            "zone_id": "SYNTH-ZONE-001", "intensity": 1, "nodata": False,
            "geometry": mapping(box(300, 0, 400, 100)),
        }]
        result = hypothetical_impact(parcels, hazard)
        self.assertEqual(result["fictional_known_support_direct_impact_eur"], "0.00")
        self.assertEqual(result["fictional_total_direct_impact_upper_eur"], "24000.00")

    def test_known_explicit_zero_is_not_unknown(self):
        parcels, hazard = fixture()
        hazard["zones"] = [{
            "zone_id": "SYNTH-ZONE-001", "intensity": 0, "nodata": False,
            "geometry": mapping(box(0, 0, 200, 100)),
        }]
        result = hypothetical_impact(parcels, hazard)
        self.assertEqual(result["fictional_total_direct_impact_lower_eur"], "0.00")
        self.assertEqual(result["fictional_total_direct_impact_upper_eur"], "0.00")

    def test_hail_millimetres_have_separate_ratios(self):
        parcels, hazard = fixture()
        hazard["peril"] = "hail"
        hazard["unit"] = "mm"
        hazard["zones"] = [
            {"zone_id": "SYNTH-ZONE-001", "intensity": 40, "nodata": False,
             "geometry": mapping(box(0, 0, 50, 100))},
            {"zone_id": "SYNTH-ZONE-002", "intensity": 20, "nodata": False,
             "geometry": mapping(box(50, 0, 100, 100))},
            {"zone_id": "SYNTH-ZONE-003", "intensity": 0, "nodata": False,
             "geometry": mapping(box(100, 0, 200, 100))},
        ]
        result = hypothetical_impact(parcels, hazard)
        self.assertEqual(result["peril"], "hail")
        self.assertEqual(result["fictional_total_direct_impact_lower_eur"], "2250.00")
        self.assertEqual(result["fictional_total_direct_impact_upper_eur"], "2250.00")

    def test_unsupported_intensity_requires_explicit_science(self):
        parcels, hazard = fixture()
        hazard["zones"][0]["intensity"] = 1.5
        with self.assertRaisesRegex(ImpactError, "toy ratio table"):
            hypothetical_impact(parcels, hazard)

    def test_non_synthetic_rows_cannot_be_relabelled(self):
        parcels, hazard = fixture()
        parcels["external_source_rows_used"] = 1
        with self.assertRaisesRegex(ImpactError, "synthetic support gate"):
            hypothetical_impact(parcels, hazard)

    def test_unknown_and_valid_hazard_overlap_block(self):
        parcels, hazard = fixture()
        hazard["zones"][2]["geometry"] = mapping(box(100, 0, 170, 100))
        with self.assertRaisesRegex(ImpactError, "nodata overlaps"):
            hypothetical_impact(parcels, hazard)

    def test_spatial_duplicate_field_rejected(self):
        parcels, hazard = fixture()
        parcels["parcels"][1]["geometry"] = mapping(box(50, 0, 150, 100))
        with self.assertRaisesRegex(ImpactError, "overlapping fields"):
            hypothetical_impact(parcels, hazard)

    def test_no_insured_or_cat_curve_claim(self):
        parcels, hazard = fixture()
        result = hypothetical_impact(parcels, hazard)
        for field in ("underwriting_or_insured_tiv", "insured_gross_or_net_loss_calculated",
                      "event_frequency_calibrated", "elt_or_aep_oep_calculated",
                      "admitted_cat_model_input"):
            self.assertIs(result[field], False)
        self.assertEqual(result["source_observed_crop_or_hazard_rows_used"], 0)
        self.assertTrue(result["unknown_hazard_support_not_assumed_dry"])


if __name__ == "__main__":
    unittest.main()
