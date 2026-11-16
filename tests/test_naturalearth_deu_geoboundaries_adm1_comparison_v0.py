# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only two-provider Germany boundary comparison adversarial tests."""
from __future__ import annotations

import copy
import json
import unittest

from shapely.affinity import translate
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from research_runners.naturalearth_deu_geoboundaries_adm1_comparison_v0 import (
    ANALYSIS_CRS, IndependentBorderBlocked, compare_geometries,
    compare_original_bytes,
)


def synthetic_states():
    # Sixteen *invented* rectangular German-extent ADM1 features.
    return [
        box(6 + (i % 4) * 0.65, 48 + (i // 4) * 0.65,
            6.50 + (i % 4) * 0.65, 48.50 + (i // 4) * 0.65)
        for i in range(16)
    ]


class NaturalEarthVsIndependentAdmin1Tests(unittest.TestCase):

    def test_identical_synthetic_country_and_16_states(self):
        states = synthetic_states()
        country = unary_union(states)
        r = compare_geometries(country, states)
        self.assertEqual(r["compared_admin1_geometries"], 16)
        self.assertEqual(r["comparison_crs"], ANALYSIS_CRS)
        self.assertEqual(r["intersect_over_union"], 1.0)
        self.assertEqual(r["natural_earth_only_area_km2"], 0.0)
        self.assertEqual(r["geoboundaries_only_area_km2"], 0.0)
        self.assertFalse(r["independent_reference_confirms_legal_border"])
        self.assertFalse(r["model_input_approved"])
        self.assertFalse(r["source_or_model_geometries_exported"])
        serialized = json.dumps(r)
        self.assertNotIn("POLYGON", serialized)
        self.assertNotIn("shapeID", serialized)

    def test_synthetic_shift_is_detected_not_silently_repaired(self):
        states = synthetic_states()
        country = translate(unary_union(states), xoff=0.11)
        r = compare_geometries(country, states)
        self.assertLess(r["intersect_over_union"], 1.0)
        self.assertGreater(r["natural_earth_only_area_km2"], 0.0)
        self.assertGreater(r["geoboundaries_only_area_km2"], 0.0)
        self.assertFalse(r["automatic_geometries_repaired_or_snapped"])

    def test_missing_admin1_feature_fails_closed(self):
        states = synthetic_states()[:-1]
        with self.assertRaisesRegex(IndependentBorderBlocked, "expected 16"):
            compare_geometries(unary_union(states), states)

    def test_adm1_overlap_is_not_hidden_by_union(self):
        states = synthetic_states()
        states[-1] = copy.deepcopy(states[0])
        with self.assertRaisesRegex(IndependentBorderBlocked, "material overlap"):
            compare_geometries(unary_union(states), states)

    def test_bowtie_country_and_invalid_admin1_fail(self):
        states = synthetic_states()
        bowtie = Polygon([(6,48),(7,49),(6,49),(7,48),(6,48)])
        with self.assertRaisesRegex(IndependentBorderBlocked, "natural-de"):
            compare_geometries(bowtie, states)
        states[1] = bowtie
        with self.assertRaisesRegex(IndependentBorderBlocked, "invalid original admin1"):
            compare_geometries(unary_union(synthetic_states()), states)

    def test_out_of_country_or_unverified_source_is_rejected(self):
        states = synthetic_states()
        country = box(50,20,51,21)
        with self.assertRaisesRegex(IndependentBorderBlocked, "coverage outside"):
            compare_geometries(country, states)
        for raw in (None,b"",b"version https://git-lfs.github.com/spec/v1\n"):
            with self.subTest(raw=raw), self.assertRaises(IndependentBorderBlocked):
                compare_original_bytes(raw,b"other")
        with self.assertRaisesRegex(IndependentBorderBlocked, "geoBoundaries original source"):
            compare_original_bytes(b"x"*838726,b"not-an-original")

    def test_reverse_sources_and_untrusted_bytes_never_accepted(self):
        with self.assertRaises(IndependentBorderBlocked):
            compare_original_bytes(b"fake-geoBoundaries-source",b"fake-natural-earth-source")


if __name__ == "__main__":
    unittest.main()
