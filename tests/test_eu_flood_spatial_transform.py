# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import math
import unittest
from decimal import Decimal

SPATIAL_DEPS_AVAILABLE = (
    importlib.util.find_spec("pyproj") is not None
    and importlib.util.find_spec("shapely") is not None
)

if SPATIAL_DEPS_AVAILABLE:
    from pyproj import Transformer
    from shapely.geometry import Polygon, box

    from scripts import eu_flood_spatial_transform as mod
    from scripts.eu_flood_exposure_semantic import aggregate_cells, canonical_json


@unittest.skipUnless(
    SPATIAL_DEPS_AVAILABLE,
    "requires requirements-eu-flood-spatial.txt",
)
class EuFloodSpatialTransformTests(unittest.TestCase):
    def source_box(self, min_lon, min_lat, max_lon, max_lat):
        return box(min_lon, min_lat, max_lon, max_lat)

    def target(self, geometry):
        return mod.transform_wgs84_geometry(geometry)

    def test_axis_order_matches_explicit_xy_reference(self) -> None:
        source = self.source_box(11.50, 48.10, 11.51, 48.11)
        projected = self.target(source)
        source_xy = tuple(source.exterior.coords)[0]
        projected_xy = tuple(projected.exterior.coords)[0]
        direct = Transformer.from_crs(
            mod.SOURCE_CRS,
            mod.TARGET_CRS,
            always_xy=True,
            allow_ballpark=False,
            only_best=True,
        )
        expected = direct.transform(*source_xy, errcheck=True)
        self.assertAlmostEqual(projected_xy[0], expected[0], places=6)
        self.assertAlmostEqual(projected_xy[1], expected[1], places=6)

    def test_full_overlap_reuses_a0_accounting(self) -> None:
        source = self.source_box(11.50, 48.10, 11.51, 48.11)
        census = self.target(source)
        cell = mod.build_spatial_census_cell(
            cell_id="A",
            population="100",
            census_geometry_epsg3035=census,
            aoi_geometry_epsg3035=census,
            supports=(mod.SpatialHazardSupport("wet", source, depth_m="2"),),
        )
        result = aggregate_cells([cell])
        row = result["cells"][0]
        self.assertEqual(row["source_population"], "100")
        self.assertEqual(row["excluded_by_aoi"], "0")
        self.assertLess(abs(Decimal(row["hazard_support_missing"])), Decimal("0.000001"))
        self.assertGreater(Decimal(row["depth_gt_1_le_3m"]), Decimal("99.999999"))

    def test_split_support_and_order_invariance(self) -> None:
        full = self.source_box(11.50, 48.10, 11.52, 48.12)
        left = self.source_box(11.50, 48.10, 11.51, 48.12)
        right = self.source_box(11.51, 48.10, 11.52, 48.12)
        census = self.target(full)
        supports = (
            mod.SpatialHazardSupport("left", left, depth_m="0.5"),
            mod.SpatialHazardSupport("right", right, depth_m="2"),
        )
        first = mod.build_spatial_census_cell(
            cell_id="A",
            population="200",
            census_geometry_epsg3035=census,
            aoi_geometry_epsg3035=census,
            supports=supports,
        )
        second = mod.build_spatial_census_cell(
            cell_id="A",
            population="200",
            census_geometry_epsg3035=census,
            aoi_geometry_epsg3035=census,
            supports=tuple(reversed(supports)),
        )
        self.assertEqual(first.supports, second.supports)
        self.assertEqual(
            canonical_json(aggregate_cells([first])),
            canonical_json(aggregate_cells([second])),
        )

    def test_aoi_clipping_precedes_population_allocation(self) -> None:
        source = self.source_box(11.50, 48.10, 11.52, 48.12)
        census = self.target(source)
        minx, miny, maxx, maxy = census.bounds
        aoi = box(minx, miny, (minx + maxx) / 2, maxy)
        cell = mod.build_spatial_census_cell(
            cell_id="A",
            population="100",
            census_geometry_epsg3035=census,
            aoi_geometry_epsg3035=aoi,
            supports=(mod.SpatialHazardSupport("wet", source, depth_m="2"),),
        )
        result = aggregate_cells([cell])
        row = result["cells"][0]
        considered = Decimal(row["aoi_population_considered"])
        excluded = Decimal(row["excluded_by_aoi"])
        wet = Decimal(row["depth_gt_1_le_3m"])
        missing = Decimal(row["hazard_support_missing"])
        self.assertGreater(considered, Decimal("0"))
        self.assertLess(considered, Decimal("100"))
        self.assertLess(abs(considered - wet), Decimal("0.000001"))
        self.assertLess(abs(missing), Decimal("0.000001"))
        self.assertLess(abs(considered + excluded - Decimal("100")), Decimal("0.000001"))

    def test_non_overlap_is_missing_support_not_dry(self) -> None:
        census_source = self.source_box(11.50, 48.10, 11.51, 48.11)
        outside = self.source_box(12.50, 49.10, 12.51, 49.11)
        census = self.target(census_source)
        cell = mod.build_spatial_census_cell(
            cell_id="A",
            population="10",
            census_geometry_epsg3035=census,
            aoi_geometry_epsg3035=census,
            supports=(mod.SpatialHazardSupport("outside", outside, depth_m="0"),),
        )
        row = aggregate_cells([cell])["cells"][0]
        self.assertEqual(row["dry_unexposed"], "0")
        self.assertEqual(row["hazard_support_missing"], "10")

    def test_boundary_touch_has_zero_allocated_area(self) -> None:
        census_source = self.source_box(11.50, 48.10, 11.51, 48.11)
        touching = self.source_box(11.51, 48.10, 11.52, 48.11)
        census = self.target(census_source)
        cell = mod.build_spatial_census_cell(
            cell_id="A",
            population="10",
            census_geometry_epsg3035=census,
            aoi_geometry_epsg3035=census,
            supports=(mod.SpatialHazardSupport("touch", touching, depth_m="2"),),
        )
        self.assertEqual(cell.supports, ())
        row = aggregate_cells([cell])["cells"][0]
        self.assertEqual(row["hazard_support_missing"], "10")

    def test_positive_area_overlap_fails_closed(self) -> None:
        full = self.source_box(11.50, 48.10, 11.52, 48.12)
        first = self.source_box(11.50, 48.10, 11.515, 48.12)
        second = self.source_box(11.505, 48.10, 11.52, 48.12)
        census = self.target(full)
        with self.assertRaisesRegex(mod.SpatialTransformError, "overlap"):
            mod.build_spatial_census_cell(
                cell_id="A",
                population="10",
                census_geometry_epsg3035=census,
                aoi_geometry_epsg3035=census,
                supports=(
                    mod.SpatialHazardSupport("first", first, depth_m="1"),
                    mod.SpatialHazardSupport("second", second, depth_m="2"),
                ),
            )

    def test_invalid_and_nonfinite_geometry_fail_closed(self) -> None:
        invalid = Polygon(
            [(11.50, 48.10), (11.52, 48.12), (11.52, 48.10), (11.50, 48.12)]
        )
        with self.assertRaises(mod.SpatialTransformError):
            mod.transform_wgs84_geometry(invalid)

        nonfinite = Polygon(
            [(11.50, 48.10), (math.nan, 48.11), (11.51, 48.11), (11.50, 48.10)]
        )
        with self.assertRaises(mod.SpatialTransformError):
            mod.transform_wgs84_geometry(nonfinite)

    def test_fraction_bounds_and_conservation_are_mechanical(self) -> None:
        source = self.source_box(11.50, 48.10, 11.51, 48.11)
        census = self.target(source)
        cell = mod.build_spatial_census_cell(
            cell_id="A",
            population="123.5",
            census_geometry_epsg3035=census,
            aoi_geometry_epsg3035=census,
            supports=(mod.SpatialHazardSupport("wet", source, depth_m="2"),),
        )
        self.assertGreaterEqual(Decimal(str(cell.aoi_fraction)), Decimal("0"))
        self.assertLessEqual(Decimal(str(cell.aoi_fraction)), Decimal("1"))
        for support in cell.supports:
            self.assertGreater(Decimal(str(support.fraction)), Decimal("0"))
            self.assertLessEqual(Decimal(str(support.fraction)), Decimal("1"))
        row = aggregate_cells([cell])["cells"][0]
        accounted = sum(
            Decimal(row[key])
            for key in (
                "dry_unexposed",
                "depth_gt_0_le_1m",
                "depth_gt_1_le_3m",
                "depth_gt_3_le_10m",
                "depth_gt_10m",
                "permanent_water_context",
                "spurious_depth_context",
                "nodata_unclassified",
                "hazard_support_missing",
                "excluded_by_aoi",
            )
        )
        self.assertLess(abs(accounted - Decimal("123.5")), Decimal("0.000001"))

    def test_transform_metadata_is_explicit_fixture_identity(self) -> None:
        metadata = mod.transform_metadata()
        self.assertEqual(metadata["config_id"], mod.TRANSFORM_CONFIG_ID)
        self.assertEqual(metadata["source_crs"], "EPSG:4326")
        self.assertEqual(metadata["target_crs"], "EPSG:3035")
        self.assertEqual(metadata["axis_order"], "xy_lon_lat_to_easting_northing")
        self.assertFalse(metadata["allow_ballpark"])
        self.assertTrue(metadata["only_best"])
        self.assertEqual(metadata["input_kind"], "fixture")
        self.assertEqual(metadata["scientific_role"], "test_fixture")


if __name__ == "__main__":
    unittest.main()
