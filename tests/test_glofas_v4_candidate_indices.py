# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
import unittest

from scripts.hydrology_grid_matching import (
    GLOFAS_V4_GRID_RESOLUTION_DEGREES,
    GLOFAS_V4_LATITUDE_COUNT,
    GLOFAS_V4_LONGITUDE_COUNT,
    GLOFAS_V4_MAX_LATITUDE_CENTER,
    GLOFAS_V4_MAX_LONGITUDE_CENTER,
    GLOFAS_V4_MIN_LATITUDE_CENTER,
    GLOFAS_V4_MIN_LONGITUDE_CENTER,
    GLOFAS_V4_UPSTREAM_AREA_FILENAME,
    GLOFAS_V4_UPSTREAM_AREA_UNIT,
    GLOFAS_V4_UPSTREAM_AREA_VARIABLE,
    MAX_ANGULAR_DISTANCE_DEGREES,
    GlofasGridPoint,
    GridMatchError,
    glofas_v4_candidate_grid_points,
    great_circle_angular_distance_degrees,
)


class GlofasV4CandidateIndexTests(unittest.TestCase):
    # Frozen by the pre-target PEGELONLINE metadata resolution on 2026-08-10.
    DRESDEN_LATITUDE = 51.054460
    DRESDEN_LONGITUDE = 13.738832

    @classmethod
    def setUpClass(cls) -> None:
        cls.points = glofas_v4_candidate_grid_points(
            station_latitude=cls.DRESDEN_LATITUDE,
            station_longitude=cls.DRESDEN_LONGITUDE,
        )

    def test_exact_v4_upstream_area_artifact_semantics_are_named(self) -> None:
        self.assertEqual(GLOFAS_V4_UPSTREAM_AREA_FILENAME, "uparea_glofas_v4_0.nc")
        self.assertEqual(GLOFAS_V4_UPSTREAM_AREA_VARIABLE, "uparea")
        self.assertEqual(GLOFAS_V4_UPSTREAM_AREA_UNIT, "m2")

    def test_official_v4_grid_geometry_closes_exactly(self) -> None:
        self.assertEqual(GLOFAS_V4_GRID_RESOLUTION_DEGREES, 0.05)
        self.assertEqual(GLOFAS_V4_LATITUDE_COUNT, 3000)
        self.assertEqual(GLOFAS_V4_LONGITUDE_COUNT, 7200)
        self.assertAlmostEqual(
            GLOFAS_V4_MAX_LATITUDE_CENTER
            - GLOFAS_V4_GRID_RESOLUTION_DEGREES * (GLOFAS_V4_LATITUDE_COUNT - 1),
            GLOFAS_V4_MIN_LATITUDE_CENTER,
            places=12,
        )
        self.assertAlmostEqual(
            GLOFAS_V4_MIN_LONGITUDE_CENTER
            + GLOFAS_V4_GRID_RESOLUTION_DEGREES * (GLOFAS_V4_LONGITUDE_COUNT - 1),
            GLOFAS_V4_MAX_LONGITUDE_CENTER,
            places=12,
        )

    def test_dresden_pre_target_neighborhood_has_exactly_46_grid_points(self) -> None:
        self.assertEqual(len(self.points), 46)
        self.assertEqual(
            self.points[0],
            GlofasGridPoint(776, 3872, 51.175, 13.625),
        )
        self.assertEqual(
            self.points[-1],
            GlofasGridPoint(781, 3876, 50.925, 13.825),
        )

    def test_exact_native_netcdf_row_spans_are_frozen(self) -> None:
        # This independently constrains the neighborhood shape, not merely its
        # total count. It catches a box-distance substitution or grid-origin
        # drift even if such a change accidentally returned 46 cells again.
        expected_longitude_indices_by_row = {
            776: tuple(range(3872, 3878)),
            777: tuple(range(3871, 3879)),
            778: tuple(range(3870, 3880)),
            779: tuple(range(3870, 3879)),
            780: tuple(range(3871, 3879)),
            781: tuple(range(3872, 3877)),
        }
        actual: dict[int, list[int]] = {}
        for point in self.points:
            actual.setdefault(point.latitude_index, []).append(point.longitude_index)
        self.assertEqual(
            {row: tuple(indices) for row, indices in actual.items()},
            expected_longitude_indices_by_row,
        )

    def test_every_point_matches_its_zero_based_netcdf_grid_indices(self) -> None:
        seen_indices: set[tuple[int, int]] = set()
        seen_coordinates: set[tuple[float, float]] = set()
        previous: tuple[int, int] | None = None
        for point in self.points:
            expected_latitude = round(
                GLOFAS_V4_MAX_LATITUDE_CENTER
                - GLOFAS_V4_GRID_RESOLUTION_DEGREES * point.latitude_index,
                12,
            )
            expected_longitude = round(
                GLOFAS_V4_MIN_LONGITUDE_CENTER
                + GLOFAS_V4_GRID_RESOLUTION_DEGREES * point.longitude_index,
                12,
            )
            self.assertEqual(point.latitude, expected_latitude)
            self.assertEqual(point.longitude, expected_longitude)
            self.assertGreaterEqual(point.latitude_index, 0)
            self.assertLess(point.latitude_index, GLOFAS_V4_LATITUDE_COUNT)
            self.assertGreaterEqual(point.longitude_index, 0)
            self.assertLess(point.longitude_index, GLOFAS_V4_LONGITUDE_COUNT)
            self.assertNotIn((point.latitude_index, point.longitude_index), seen_indices)
            self.assertNotIn((point.latitude, point.longitude), seen_coordinates)
            seen_indices.add((point.latitude_index, point.longitude_index))
            seen_coordinates.add((point.latitude, point.longitude))
            current = (point.latitude_index, point.longitude_index)
            if previous is not None:
                self.assertLess(previous, current)
            previous = current

    def test_every_emitted_point_is_inside_exact_great_circle_radius(self) -> None:
        for point in self.points:
            distance = great_circle_angular_distance_degrees(
                self.DRESDEN_LATITUDE,
                self.DRESDEN_LONGITUDE,
                point.latitude,
                point.longitude,
            )
            self.assertLessEqual(distance, MAX_ANGULAR_DISTANCE_DEGREES)

    def test_nearest_v4_grid_point_is_stable(self) -> None:
        nearest = min(
            self.points,
            key=lambda point: great_circle_angular_distance_degrees(
                self.DRESDEN_LATITUDE,
                self.DRESDEN_LONGITUDE,
                point.latitude,
                point.longitude,
            ),
        )
        self.assertEqual(nearest, GlofasGridPoint(778, 3874, 51.075, 13.725))
        self.assertAlmostEqual(
            great_circle_angular_distance_degrees(
                self.DRESDEN_LATITUDE,
                self.DRESDEN_LONGITUDE,
                nearest.latitude,
                nearest.longitude,
            ),
            0.022303655782505986,
            places=12,
        )

    def test_no_upstream_area_or_target_value_can_enter_candidate_generation(self) -> None:
        for point in self.points:
            self.assertEqual(point._fields, ("latitude_index", "longitude_index", "latitude", "longitude"))

    def test_candidate_generation_rejects_invalid_station_coordinates(self) -> None:
        cases = (
            (True, self.DRESDEN_LONGITUDE),
            (math.nan, self.DRESDEN_LONGITUDE),
            (91.0, self.DRESDEN_LONGITUDE),
            (self.DRESDEN_LATITUDE, 180.0),
        )
        for latitude, longitude in cases:
            with self.subTest(latitude=latitude, longitude=longitude), self.assertRaises(GridMatchError):
                glofas_v4_candidate_grid_points(
                    station_latitude=latitude,
                    station_longitude=longitude,
                )


if __name__ == "__main__":
    unittest.main()
