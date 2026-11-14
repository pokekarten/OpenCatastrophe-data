# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, offline 2021 Loing AZI categorical hazard semantics."""
import unittest

from research_runners.loing2016_azi_depth_class_semantics_v0 import (
    AtlasClassBlocked, review_azi_class,
)


def synthetic(label):
    return {
        "atlas_version": "DDT45_LOING_AVAL_AZI_2021",
        "event_id": "LOING_MAY_JUNE_2016",
        "depth_class": label,
    }


class LoingDepthClassTests(unittest.TestCase):
    def test_every_published_class_is_an_interval(self):
        expected = [
            ("0-0.5", "0.00", "0.50"),
            ("0.5-1", "0.50", "1.00"),
            ("1-2", "1.00", "2.00"),
            (">2", "2.00", None),
        ]
        for label, lo, hi in expected:
            with self.subTest(label=label):
                r = review_azi_class(synthetic(label))
                self.assertEqual(r["lower_depth_class_boundary_m"], lo)
                self.assertEqual(r["upper_depth_class_boundary_m"], hi)
                self.assertIsNone(r["exact_observed_depth_m"])
                self.assertIsNone(r["exact_reconstructed_depth_m"])

    def test_top_class_has_no_invented_upper_bound(self):
        r = review_azi_class(synthetic(">2"))
        self.assertTrue(r["open_ended_upper_class"])
        self.assertIsNone(r["upper_depth_class_boundary_m"])

    def test_even_correct_class_never_gains_model_or_loss_approval(self):
        r = review_azi_class(synthetic("1-2"))
        self.assertEqual(r["source_polygon_min_area_m2"], 500)
        self.assertFalse(r["source_original_GIS_bytes_attested"])
        self.assertFalse(r["valid_independent_2016_holdout"])
        self.assertFalse(r["asset_footprint_covered_by_source_established"])
        self.assertFalse(r["insured_loss_estimate_permitted"])
        self.assertFalse(r["model_input_admitted"])

    def test_unmapped_does_not_mean_unflooded(self):
        r = review_azi_class(synthetic("0-0.5"))
        self.assertFalse(r["unmapped_location_proves_dry"])

    def test_2017_driee_edition_cannot_inherit_ddt_rules(self):
        d = synthetic("0-0.5")
        d["atlas_version"] = "DRIEE_LOING_2017"
        with self.assertRaises(AtlasClassBlocked):
            review_azi_class(d)

    def test_other_event_cannot_inherit_2016_classes(self):
        d = synthetic("0-0.5")
        d["event_id"] = "LOING_1910"
        with self.assertRaises(AtlasClassBlocked):
            review_azi_class(d)

    def test_midpoint_is_not_a_published_class(self):
        for value in ("1.5", "1.50", 1.5, 0, None):
            with self.subTest(value=value):
                with self.assertRaises(AtlasClassBlocked):
                    review_azi_class(synthetic(value))

    def test_artificial_extra_approval_field_blocked(self):
        d = synthetic("1-2")
        d["model_ready"] = True
        with self.assertRaises(AtlasClassBlocked):
            review_azi_class(d)

    def test_unknown_legend_or_inconsistent_metadata_fails(self):
        for value in ("0.0-1.0", "1-1.5", "2-2.5", ">=2.0", "NODATA"):
            with self.subTest(value=value):
                with self.assertRaises(AtlasClassBlocked):
                    review_azi_class(synthetic(value))

    def test_boolean_and_collection_class_rejected(self):
        for value in (True, [], {"name": "1-2"}):
            with self.subTest(value=value):
                with self.assertRaises(AtlasClassBlocked):
                    review_azi_class(synthetic(value))

    def test_boundary_inclusion_unknown_not_made_exact(self):
        r = review_azi_class(synthetic("0.5-1"))
        self.assertFalse(r["class_edge_inclusion_from_legend_verified"])

    def test_no_model_approval_even_2021_license_claim(self):
        d = synthetic(">2")
        d["source_licensed"] = True
        with self.assertRaises(AtlasClassBlocked):
            review_azi_class(d)


if __name__ == "__main__":
    unittest.main()
