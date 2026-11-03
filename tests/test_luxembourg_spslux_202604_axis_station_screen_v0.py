# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Frame-aware official non-personal GNSS station axis-screen regressions."""
from __future__ import annotations

import copy
import json
import unittest

try:
    import pyproj
    HAS_PYPROJ = True
except ImportError:
    HAS_PYPROJ = False

from research_runners.luxembourg_spslux_202604_axis_station_screen_v0 import (
    screen, STATIONS, StationScreenError, FRAME_TRANSITION_DATE,
)


@unittest.skipUnless(HAS_PYPROJ, "Requires pinned pyproj==3.7.2 spatial runner")
class SPSLuxPublishedStationScreenTests(unittest.TestCase):
    def test_published_april2026_station_screen_is_frame_and_epoch_aware(self):
        summary = screen()
        self.assertEqual(summary["station_control_points"], 7)
        self.assertEqual(summary["station_native_xy_max_residual_m_rounded_1dp"], 0.9)
        self.assertGreater(summary["station_swapped_xy_min_residual_m_rounded_1dp"], 1000)
        self.assertEqual(summary["luref2025_effective_date"], "2026-10-31")
        self.assertEqual(FRAME_TRANSITION_DATE, "2026-10-31")
        self.assertTrue(summary["swapped_xy_rejected_for_published_stations"])
        self.assertFalse(summary["individual_geobase_geometry_axis_ground_control_verified"])
        self.assertFalse(summary["CAT_model_input_admitted"])
        self.assertFalse(summary["official_direct_wgs84_to_lures_transform_exists"])
        for code, *_ in STATIONS:
            self.assertNotIn(code, json.dumps(summary))
        self.assertNotIn("63444.851", json.dumps(summary))

    def test_swapped_published_coordinates_are_blocked(self):
        data = list(STATIONS)
        name, lon, lat, e, n = data[0]
        data[0] = (name, lon, lat, n, e)
        with self.assertRaisesRegex(StationScreenError, "do not support"):
            screen(tuple(data))

    def test_changed_reference_position_fails_closed(self):
        data = list(STATIONS)
        name, lon, lat, e, n = data[1]
        data[1] = (name, lon + 0.1, lat, e, n)
        with self.assertRaises(StationScreenError):
            screen(tuple(data))

    def test_duplicates_nonfinite_wrong_shapes_and_missing_controls_rejected(self):
        choices = [
            (STATIONS[0], STATIONS[0], STATIONS[1]),
            STATIONS[:2],
            STATIONS + (STATIONS[0],),
            tuple((name, float("nan"), lat, east, north) if i == 0
                  else (name, lon, lat, east, north)
                  for i, (name, lon, lat, east, north) in enumerate(STATIONS)),
            tuple((name, lon, lat, -100, north) if i == 1
                  else (name, lon, lat, east, north)
                  for i, (name, lon, lat, east, north) in enumerate(STATIONS)),
        ]
        for value in choices:
            with self.subTest(kind=str(value)[:60]):
                with self.assertRaises(StationScreenError):
                    screen(value)


if __name__ == "__main__":
    unittest.main()
