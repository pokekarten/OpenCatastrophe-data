# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
import unittest

from scripts.hydrology_grid_matching import (
    DRESDEN_DRAINAGE_AREA_KM2,
    MAX_ANGULAR_DISTANCE_DEGREES,
    MAX_RELATIVE_DRAINAGE_AREA_MISMATCH,
    GlofasGridCell,
    GridMatchError,
    great_circle_angular_distance_degrees,
    select_dresden_glofas_grid_cell,
)


class GreatCircleDistanceTests(unittest.TestCase):
    def test_identical_coordinates_have_zero_distance(self) -> None:
        self.assertEqual(great_circle_angular_distance_degrees(51.0, 13.0, 51.0, 13.0), 0.0)

    def test_one_degree_latitude_is_one_degree_central_angle(self) -> None:
        self.assertAlmostEqual(
            great_circle_angular_distance_degrees(50.0, 13.0, 51.0, 13.0),
            1.0,
        )

    def test_antimeridian_wrap_uses_short_great_circle_path(self) -> None:
        self.assertAlmostEqual(
            great_circle_angular_distance_degrees(0.0, 179.9, 0.0, -179.9),
            0.2,
            places=12,
        )

    def test_invalid_coordinates_and_type_confusion_fail_closed(self) -> None:
        cases = (
            (91.0, 13.0, 51.0, 13.0),
            (51.0, 180.0, 51.0, 13.0),
            (True, 13.0, 51.0, 13.0),
            (math.nan, 13.0, 51.0, 13.0),
        )
        for args in cases:
            with self.subTest(args=args), self.assertRaises(GridMatchError):
                great_circle_angular_distance_degrees(*args)


class DresdenGridSelectionTests(unittest.TestCase):
    STATION_LAT = 51.05
    STATION_LON = 13.74

    @staticmethod
    def cell(
        latitude: float,
        longitude: float,
        relative_area_offset: float,
    ) -> GlofasGridCell:
        return GlofasGridCell(
            latitude,
            longitude,
            DRESDEN_DRAINAGE_AREA_KM2 * (1.0 + relative_area_offset),
        )

    def test_smallest_area_mismatch_wins_before_distance(self) -> None:
        closer = self.cell(self.STATION_LAT + 0.01, self.STATION_LON, 0.02)
        better_area = self.cell(self.STATION_LAT + 0.10, self.STATION_LON, 0.01)
        result = select_dresden_glofas_grid_cell(
            station_latitude=self.STATION_LAT,
            station_longitude=self.STATION_LON,
            candidates=[closer, better_area],
        )
        self.assertEqual(result.cell, better_area)
        self.assertAlmostEqual(result.relative_drainage_area_mismatch, 0.01)

    def test_distance_breaks_exact_area_mismatch_tie(self) -> None:
        farther = self.cell(self.STATION_LAT + 0.10, self.STATION_LON, 0.01)
        closer = self.cell(self.STATION_LAT + 0.05, self.STATION_LON, -0.01)
        result = select_dresden_glofas_grid_cell(
            station_latitude=self.STATION_LAT,
            station_longitude=self.STATION_LON,
            candidates=[farther, closer],
        )
        self.assertEqual(result.cell, closer)

    def test_coordinates_break_remaining_exact_tie_independent_of_input_order(self) -> None:
        # Symmetric north/south candidates have equal area mismatch and angular distance.
        north = self.cell(self.STATION_LAT + 0.05, self.STATION_LON, 0.0)
        south = self.cell(self.STATION_LAT - 0.05, self.STATION_LON, 0.0)
        first = select_dresden_glofas_grid_cell(
            station_latitude=self.STATION_LAT,
            station_longitude=self.STATION_LON,
            candidates=[north, south],
        )
        second = select_dresden_glofas_grid_cell(
            station_latitude=self.STATION_LAT,
            station_longitude=self.STATION_LON,
            candidates=[south, north],
        )
        self.assertEqual(first.cell, south)
        self.assertEqual(second.cell, south)

    def test_candidate_outside_angular_radius_is_ineligible(self) -> None:
        inside = self.cell(self.STATION_LAT + 0.149, self.STATION_LON, 0.02)
        outside = self.cell(self.STATION_LAT + 0.151, self.STATION_LON, 0.0)
        result = select_dresden_glofas_grid_cell(
            station_latitude=self.STATION_LAT,
            station_longitude=self.STATION_LON,
            candidates=[outside, inside],
        )
        self.assertEqual(result.cell, inside)
        self.assertLess(result.angular_distance_degrees, MAX_ANGULAR_DISTANCE_DEGREES)

    def test_candidate_outside_10_percent_area_gate_is_ineligible(self) -> None:
        eligible = self.cell(self.STATION_LAT + 0.05, self.STATION_LON, 0.09)
        ineligible = self.cell(self.STATION_LAT + 0.01, self.STATION_LON, 0.1001)
        result = select_dresden_glofas_grid_cell(
            station_latitude=self.STATION_LAT,
            station_longitude=self.STATION_LON,
            candidates=[ineligible, eligible],
        )
        self.assertEqual(result.cell, eligible)
        self.assertLessEqual(
            result.relative_drainage_area_mismatch,
            MAX_RELATIVE_DRAINAGE_AREA_MISMATCH,
        )

    def test_no_eligible_cell_fails_closed_without_relaxing_rules(self) -> None:
        candidates = [
            self.cell(self.STATION_LAT + 0.151, self.STATION_LON, 0.0),
            self.cell(self.STATION_LAT + 0.01, self.STATION_LON, 0.11),
        ]
        with self.assertRaisesRegex(GridMatchError, "no GloFAS cell satisfies"):
            select_dresden_glofas_grid_cell(
                station_latitude=self.STATION_LAT,
                station_longitude=self.STATION_LON,
                candidates=candidates,
            )

    def test_duplicate_grid_coordinates_fail_closed(self) -> None:
        first = self.cell(self.STATION_LAT + 0.05, self.STATION_LON, 0.01)
        duplicate = GlofasGridCell(
            first.latitude,
            first.longitude,
            DRESDEN_DRAINAGE_AREA_KM2 * 1.02,
        )
        with self.assertRaisesRegex(GridMatchError, "duplicate candidate grid coordinate"):
            select_dresden_glofas_grid_cell(
                station_latitude=self.STATION_LAT,
                station_longitude=self.STATION_LON,
                candidates=[first, duplicate],
            )

    def test_malformed_candidate_metadata_fails_closed(self) -> None:
        with self.assertRaisesRegex(GridMatchError, "must be a GlofasGridCell"):
            select_dresden_glofas_grid_cell(
                station_latitude=self.STATION_LAT,
                station_longitude=self.STATION_LON,
                candidates=[(self.STATION_LAT, self.STATION_LON, DRESDEN_DRAINAGE_AREA_KM2)],  # type: ignore[list-item]
            )
        with self.assertRaisesRegex(GridMatchError, "must be positive"):
            select_dresden_glofas_grid_cell(
                station_latitude=self.STATION_LAT,
                station_longitude=self.STATION_LON,
                candidates=[GlofasGridCell(self.STATION_LAT, self.STATION_LON, 0.0)],
            )


if __name__ == "__main__":
    unittest.main()
