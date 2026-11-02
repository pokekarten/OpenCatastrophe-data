# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic source SHP geometry/axis screen regression; never stores provider data."""
from __future__ import annotations

from io import BytesIO
import json
import math
import struct
import unittest

from research_runners.luxembourg_age_hq100_2021_ring_coordinate_quality_v0 import (
    check_shp, HQ100GeometryError, axis_envelope_screen,
)


def build_shape(rings, *, bad_first_offset: bool = False) -> bytes:
    vertices = [point for ring in rings for point in ring]
    x0, y0 = min(x for x, _ in vertices), min(y for _, y in vertices)
    x1, y1 = max(x for x, _ in vertices), max(y for _, y in vertices)
    bbox = (x0, y0, x1, y1)
    parts = []
    index = 0
    for ring in rings:
        parts.append(index)
        index += len(ring)
    if bad_first_offset:
        parts[0] = 1
    descriptor = (struct.pack("<i4dii", 5, *bbox, len(rings), len(vertices))
                  + b"".join(struct.pack("<I", i) for i in parts)
                  + b"".join(struct.pack("<dd", *v) for v in vertices))
    total = 100 + 8 + len(descriptor)
    header = bytearray(100)
    struct.pack_into(">i", header, 0, 9994)
    struct.pack_into(">i", header, 24, total // 2)
    struct.pack_into("<ii", header, 28, 1000, 5)
    struct.pack_into("<4d", header, 36, *bbox)
    return bytes(header) + struct.pack(">II", 1, len(descriptor) // 2) + descriptor


class HQ100RingCoordinateQualityTests(unittest.TestCase):
    def test_two_original_rings_opposite_winding_and_complete_bbox(self):
        ccw = [(0., 0.), (4., 0.), (4., 4.), (0., 4.), (0., 0.)]
        cw = [(1., 1.), (1., 2.), (2., 2.), (2., 1.), (1., 1.)]
        report = check_shp(BytesIO(build_shape([ccw, cw])))
        self.assertEqual(report["original_coordinate_pairs_read_and_aggregated"], 10)
        self.assertEqual(report["closed_ring_parts"], 2)
        self.assertEqual(report["positive_signed_orientation_ring_parts"], 1)
        self.assertEqual(report["negative_signed_orientation_ring_parts"], 1)
        self.assertEqual(report["aggregate_original_projected_bbox_rounded_m"], [0, 0, 4, 4])
        self.assertTrue(report["file_bbox_matches_all_original_vertices"])
        self.assertTrue(report["record_bbox_matches_all_original_vertices"])
        self.assertFalse(report["source_ring_topological_validity_proven"])
        self.assertFalse(report["model_input_admitted"])
        self.assertNotIn("ring_vertex_coordinates", json.dumps(report))

    def test_open_ring_is_counted_not_silently_corrected(self):
        unclosed = [(0., 0.), (4., 0.), (4., 4.), (0., 4.), (0., 1.)]
        result = check_shp(BytesIO(build_shape([unclosed])))
        self.assertEqual(result["open_ring_parts"], 1)
        self.assertEqual(result["closed_ring_parts"], 0)

    def test_bad_offsets_truncated_coordinate_and_nonfinite_fail_closed(self):
        ring = [(0., 0.), (4., 0.), (4., 4.), (0., 4.), (0., 0.)]
        with self.assertRaises(HQ100GeometryError):
            check_shp(BytesIO(build_shape([ring], bad_first_offset=True)))
        with self.assertRaises(HQ100GeometryError):
            check_shp(BytesIO(build_shape([ring])[:-8]))
        malformed = bytearray(build_shape([ring]))
        # The first XY at SHP 100 + record 8 + descriptor 44 + parts 4.
        struct.pack_into("<d", malformed, 156, math.nan)
        with self.assertRaises(HQ100GeometryError):
            check_shp(BytesIO(malformed))

    def test_axis_screen_declares_only_envelope_plausibility(self):
        try:
            import pyproj  # noqa: F401
        except ImportError:
            self.skipTest("Pinned pyproj optional spatial profile")
        report = axis_envelope_screen([50000, 70000, 100000, 130000])
        self.assertIn(report["axis_envelope_screen"],
                      ("native_only_plausible", "both_plausible",
                       "swapped_only_plausible", "neither_plausible"))
        self.assertFalse(report["field_survey_axis_or_epoch_verified"])


if __name__ == "__main__":
    unittest.main()
