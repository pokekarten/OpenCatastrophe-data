# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only first 64 native Shapefile records + GEOS ring QA tests."""
from __future__ import annotations

import hashlib
import struct
import unittest

from tests.test_by_hausumringe_oberbayern_shp_first_original_v0 import fake_first_shp
from research_runners import by_hausumringe_oberbayern_first64_geos_v0 as geos


def synthetic_first64(*, bowtie: bool = False) -> bytes:
    out=bytearray(fake_first_shp())
    assert len(out)==236
    first_rec=bytes(out[108:236])
    for i in range(2,65):
        out.extend(struct.pack(">II",i,64))
        out.extend(first_rec)
    if bowtie:
        # First source fixture Polygon becomes a self-crossing bowtie whose
        # bounding box is unchanged. No real source coordinates are used.
        coords=((650000.,5350000.),(650020.,5350010.),
                (650020.,5350000.),(650000.,5350010.),(650000.,5350000.))
        for i,(x,y) in enumerate(coords):
            struct.pack_into("<dd",out,156+i*16,x,y)
    return bytes(out)


class First64IndependentGEOS(unittest.TestCase):
    def test_all_64_synthetic_polygons_independently_geos_valid(self):
        receipt=geos.inspect_first64_decoded(synthetic_first64())
        self.assertEqual(receipt["native_source_records_structurally_decoded"],64)
        self.assertEqual(receipt["native_source_polygon_records"],64)
        self.assertEqual(receipt["native_source_rings_checked_with_geos"],64)
        self.assertEqual(receipt["native_source_vertices_transiently_checked"],320)
        self.assertEqual(receipt["geos_invalid_rings"],0)
        self.assertEqual(receipt["geos_invalid_single_part_polygon_interpretations"],0)
        self.assertFalse(receipt["original_first_record_source_SHA_identity_matched"])
        self.assertFalse(receipt["insurance_CAT_model_input_approved"])
        self.assertNotIn("650000",str(receipt))
        self.assertNotIn("5350000",str(receipt))

    def test_geos_detects_real_topological_crossing_but_does_not_export_it(self):
        receipt=geos.inspect_first64_decoded(synthetic_first64(bowtie=True))
        self.assertEqual(receipt["geos_invalid_rings"],1)
        self.assertEqual(receipt["geos_invalid_single_part_polygon_interpretations"],1)
        self.assertFalse(receipt["scientifically_representative_buildings_sample"])

    def test_incomplete_64th_record_refused(self):
        with self.assertRaises(geos.BoundedGEOSBlocked):
            geos.inspect_first64_decoded(synthetic_first64()[:-60])

    def test_wrong_original_first_record_number_refused(self):
        altered=bytearray(synthetic_first64())
        struct.pack_into(">I",altered,236,9999)
        with self.assertRaises(geos.BoundedGEOSBlocked):
            geos.inspect_first64_decoded(bytes(altered))

    def test_original_source_hash_pin_before_parsing(self):
        with self.assertRaisesRegex(geos.BoundedGEOSBlocked,"SHA-256"):
            geos.inspect_live_original_source(synthetic_first64(),
                status=206,response_url=geos.URL,
                headers={})

    def test_missing_or_empty_cannot_be_claimed_as_source(self):
        for x in (b"",b"not a shapefile",b"x"*(geos.MAX_INFLATED_PREVIEW+1)):
            with self.subTest(size=len(x)),self.assertRaises(geos.BoundedGEOSBlocked):
                geos.inspect_first64_decoded(x)


if __name__=="__main__":
    unittest.main()
