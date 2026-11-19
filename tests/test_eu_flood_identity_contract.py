# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail closed on typed Census and hazard-support identities before accounting."""

from __future__ import annotations

import importlib.util
import unittest

from scripts.eu_flood_exposure_semantic import (
    CensusCell, HazardSupport, SemanticError, aggregate_cells,
)

SPATIAL_DEPS_AVAILABLE = (
    importlib.util.find_spec("shapely") is not None
    and importlib.util.find_spec("pyproj") is not None
)
if SPATIAL_DEPS_AVAILABLE:
    from shapely.geometry import box
    from scripts.eu_flood_spatial_transform import (
        SpatialHazardSupport, SpatialTransformError, build_spatial_census_cell,
        transform_wgs84_geometry,
    )


class CensusIdentityTests(unittest.TestCase):
    def test_numeric_and_string_id_must_not_double_count_population(self):
        # Before this check, these indistinguishable source identities yielded
        # two rows and source_population=200 instead of 100.
        cases = (
            CensusCell(1, "100", "1", ()),
            CensusCell("1", "100", "1", ()),
        )
        with self.assertRaisesRegex(SemanticError, "cell_id.*trimmed string"):
            aggregate_cells(cases)

    def test_noncanonical_cell_id_fails_before_hashing(self):
        for value in (0, 1, 1.0, True, None, [], {}, "", " ", "A ", "\nA"):
            with self.subTest(value=value), self.assertRaisesRegex(
                SemanticError, "cell_id.*trimmed string"
            ):
                aggregate_cells((CensusCell(value, "10", "1", ()),))

    def test_noncanonical_support_id_fails_before_hashing(self):
        for value in (0, 1, 1.0, True, None, [], {}, "", " ", "s ", "\ns"):
            with self.subTest(value=value), self.assertRaisesRegex(
                SemanticError, "support_id.*trimmed string"
            ):
                aggregate_cells((CensusCell("A", "10", "1", (
                    HazardSupport(value, "1", "2"),
                )),))

    def test_canonical_ids_reconcile_and_duplicates_still_fail(self):
        cell = CensusCell("01-A", "10", "1", (HazardSupport("src-a", "1", "2"),))
        result = aggregate_cells((cell,))
        self.assertEqual(result["cells"][0]["cell_id"], "01-A")
        self.assertEqual(result["totals"]["source_population"], "10")
        with self.assertRaisesRegex(SemanticError, "duplicate census cell id"):
            aggregate_cells((cell, cell))


@unittest.skipUnless(SPATIAL_DEPS_AVAILABLE, "requires flood spatial dependencies")
class SpatialIdentityTests(unittest.TestCase):
    def test_mixed_support_id_types_fail_with_domain_error_before_sort(self):
        source = box(11.50, 48.10, 11.51, 48.11)
        projected = transform_wgs84_geometry(source)
        for ids in ((1, "s"), ("s", 1), ([], "s")):
            supports = tuple(SpatialHazardSupport(identity, source, depth_m="2") for identity in ids)
            with self.subTest(ids=ids), self.assertRaisesRegex(
                SpatialTransformError, "support_id.*trimmed string"
            ):
                build_spatial_census_cell(
                    cell_id="A", population="10",
                    census_geometry_epsg3035=projected,
                    aoi_geometry_epsg3035=projected,
                    supports=supports,
                )

    def test_invalid_spatial_cell_identity_fails_early(self):
        source = box(11.50, 48.10, 11.51, 48.11)
        projected = transform_wgs84_geometry(source)
        for value in (1, None, [], " A ", ""):
            with self.subTest(cell_id=value), self.assertRaisesRegex(
                SpatialTransformError, "cell_id.*trimmed string"
            ):
                build_spatial_census_cell(
                    cell_id=value, population="10",
                    census_geometry_epsg3035=projected,
                    aoi_geometry_epsg3035=projected,
                    supports=(),
                )


if __name__ == "__main__":
    unittest.main()
