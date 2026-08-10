# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.hydrology_grid_matching import (
    DRESDEN_DRAINAGE_AREA_KM2,
    GlofasGridCell,
    select_dresden_glofas_grid_cell,
)


class ExactAreaTieRegressionTests(unittest.TestCase):
    def test_distance_is_decisive_when_upstream_area_is_exactly_identical(self) -> None:
        station_latitude = 51.05
        station_longitude = 13.74
        identical_model_area = DRESDEN_DRAINAGE_AREA_KM2 * 1.01
        farther = GlofasGridCell(
            station_latitude + 0.10,
            station_longitude,
            identical_model_area,
        )
        closer = GlofasGridCell(
            station_latitude + 0.05,
            station_longitude,
            identical_model_area,
        )

        result = select_dresden_glofas_grid_cell(
            station_latitude=station_latitude,
            station_longitude=station_longitude,
            candidates=[farther, closer],
        )

        self.assertEqual(
            abs(farther.upstream_area_km2 - DRESDEN_DRAINAGE_AREA_KM2),
            abs(closer.upstream_area_km2 - DRESDEN_DRAINAGE_AREA_KM2),
        )
        self.assertEqual(result.cell, closer)
        self.assertLess(
            result.angular_distance_degrees,
            0.10,
        )


if __name__ == "__main__":
    unittest.main()
