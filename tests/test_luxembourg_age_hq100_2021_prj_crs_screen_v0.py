# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression: parsed provider PRJ ≠ field axis/epoch approval."""
from __future__ import annotations

import unittest

try:
    from pyproj import CRS
    HAS_PYPROJ = True
except ImportError:
    HAS_PYPROJ = False

from research_runners.luxembourg_age_hq100_2021_prj_crs_screen_v0 import (
    parse_wkt, HQ100CRSError,
)


@unittest.skipUnless(HAS_PYPROJ, "Requires pinned optional pyproj 3.7.2")
class AGEHQ100CRSScreenTests(unittest.TestCase):
    def test_realistic_2169_wkt_is_only_a_candidate_not_join_approval(self):
        wkt = CRS.from_epsg(2169).to_wkt().encode("utf-8")
        result = parse_wkt(wkt)
        self.assertEqual(result["crs_epsg_match_at_min90_confidence"], 2169)
        self.assertTrue(result["original_crs_is_projected"])
        self.assertFalse(result["source_hazard_polygon_axis_and_epoch_field_verified"])
        self.assertFalse(result["spatial_join_with_geobase_authorized"])
        self.assertFalse(result["model_input_admitted"])

    def test_wgs84_is_not_silently_2169(self):
        result = parse_wkt(CRS.from_epsg(4326).to_wkt().encode("utf-8"))
        self.assertEqual(result["crs_epsg_match_at_min90_confidence"], 4326)
        self.assertTrue(result["original_crs_is_geographic"])
        self.assertFalse(result["spatial_join_with_geobase_authorized"])

    def test_malformed_and_oversized_original_prj_fail(self):
        for value in (b"", b"not a WKT", b"X" * (64 * 1024 + 1)):
            with self.subTest(length=len(value)):
                with self.assertRaises(HQ100CRSError):
                    parse_wkt(value)


if __name__ == "__main__":
    unittest.main()
