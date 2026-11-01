# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only adversarial TIFF headers: no original provider pixels."""
from __future__ import annotations

import struct
import unittest

from research_runners.berlin_srhk_tiff_grid_affine_v0 import (
    BerlinTiffGridError, inspect_berlin_tiff_header_grid,
)


def header(*, x=391600.0, y=5820200.0, sx=1.0, sy=1.0,
           width=500, height=500, epsg=25833, model=1, raster=1,
           orientation=1, tie_i=0.0, tie_j=0.0, skip=(), big_endian=False,
           multi_tie=False):
    order = ">" if big_endian else "<"
    start = b"MM\x00*" if big_endian else b"II*\x00"
    keys = [1, 1, 0, 3, 1024, 0, 1, model, 1025, 0, 1, raster,
            3072, 0, 1, epsg]
    data = {
        256: (4, 1, width), 257: (4, 1, height),
        274: (3, 1, orientation),
        33550: (12, 3, struct.pack(order+"3d", sx, sy, 0.0)),
        33922: (12, 12 if multi_tie else 6, struct.pack(order+"6d", tie_i,tie_j,0.0,x,y,0.0)),
        34735: (3, len(keys), struct.pack(order+str(len(keys))+"H", *keys)),
    }
    for tag in skip:
        data.pop(tag, None)
    rows = sorted(data.items())
    first_ifd = 8
    tail = first_ifd + 2 + len(rows)*12 + 4
    buf = bytearray(start + struct.pack(order+"I", first_ifd))
    buf += struct.pack(order+"H", len(rows))
    payloads = bytearray()
    for tag, (typ, count, payload) in rows:
        if isinstance(payload, int):
            if typ == 3:
                # Classic TIFF SHORT inline is the first two bytes of the value field.
                raw = struct.pack(order+"H", payload) + b"\0\0"
                val_field = struct.unpack(order+"I", raw)[0]
            else:
                val_field = payload
        else:
            val_field = tail + len(payloads)
            payloads += payload
        buf += struct.pack(order+"HHII", tag, typ, count, val_field)
    buf += struct.pack(order+"I", 0)
    buf += payloads
    return bytes(buf)


class BerlinFloodTiffGridTests(unittest.TestCase):
    def test_projected_header_and_full_frozen_pilot_extent(self):
        result = inspect_berlin_tiff_header_grid(header())
        self.assertTrue(result["header_only_georeferencing_verified"])
        self.assertEqual(result["header_declared_crs_epsg"], 25833)
        self.assertEqual(result["header_projected_bbox_epsg25833_m"],
                         [391600.0, 5819700.0, 392100.0, 5820200.0])
        self.assertTrue(result["pilot_bbox_intersects_header_raster_extent"])
        self.assertTrue(result["header_covers_entire_pilot_bbox"])
        self.assertFalse(result["original_tiff_pixels_sampled"])
        self.assertFalse(result["actual_flood_exposure_admitted"])

    def test_big_endian_header(self):
        result = inspect_berlin_tiff_header_grid(header(big_endian=True))
        self.assertTrue(result["header_only_georeferencing_verified"])

    def test_outside_and_partial_pilot_not_claimed_as_full_coverage(self):
        out = inspect_berlin_tiff_header_grid(header(x=395000, y=5820200))
        self.assertFalse(out["pilot_bbox_intersects_header_raster_extent"])
        self.assertFalse(out["header_covers_entire_pilot_bbox"])
        p = inspect_berlin_tiff_header_grid(header(x=391800, y=5820200))
        self.assertTrue(p["pilot_bbox_intersects_header_raster_extent"])
        self.assertFalse(p["header_covers_entire_pilot_bbox"])

    def test_missing_tag_or_unavailable_ifd_returns_unknown_not_dry(self):
        for missing in (256, 257, 33550, 33922, 34735):
            with self.subTest(missing=missing):
                res = inspect_berlin_tiff_header_grid(header(skip=(missing,)))
                self.assertFalse(res["header_only_georeferencing_verified"])
                self.assertIsNone(res["pilot_bbox_intersects_header_raster_extent"])
        unavailable = b"II*\x00" + struct.pack("<I", 400000)
        res = inspect_berlin_tiff_header_grid(unavailable)
        self.assertFalse(res["header_only_georeferencing_verified"])
        self.assertIsNone(res["header_covers_entire_pilot_bbox"])

    def test_unreviewed_crs_model_pixelispoint_transformation_fail_closed(self):
        for kwargs in ({"epsg":25832}, {"model":2}, {"raster":2}, {"orientation":3},
                       {"sx":0}, {"sy":float("nan")}, {"width":300000}, {"multi_tie":True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(BerlinTiffGridError):
                inspect_berlin_tiff_header_grid(header(**kwargs))

    def test_malformed_tag_type_duplicate_and_bad_geokey_detected(self):
        raw = bytearray(header())
        # Corrupt scale entry's type, count or offset.
        for pos, replacement in ((8+2+3*12+2,4),):
            with self.subTest(pos=pos):
                tmp = bytearray(raw)
                struct.pack_into("<H", tmp, pos, replacement)
                with self.assertRaises(BerlinTiffGridError):
                    inspect_berlin_tiff_header_grid(bytes(tmp))
        duplicate = bytearray(header())
        # Alias ImageLength as ImageWidth in its own IFD entry.
        struct.pack_into("<H", duplicate, 8+2+12, 256)
        with self.assertRaisesRegex(BerlinTiffGridError, "duplicate"):
            inspect_berlin_tiff_header_grid(bytes(duplicate))
        with self.assertRaises(BerlinTiffGridError):
            inspect_berlin_tiff_header_grid(b"BAD HEADER")

    def test_nonzero_raster_tiepoint_indices_preserve_extent(self):
        r = inspect_berlin_tiff_header_grid(header(tie_i=20, tie_j=30,
                                                  x=391620, y=5820170))
        self.assertEqual(r["header_projected_bbox_epsg25833_m"],
                         [391600.0, 5819700.0, 392100.0, 5820200.0])

    def test_missing_critical_geokey_cannot_establish_spatial_coverage(self):
        raw = bytearray(header())
        # Replace GTRasterTypeGeoKey key ID with unknown key.
        geo_offset = struct.unpack_from("<I", raw, 8+2+5*12+8)[0]
        struct.pack_into("<H", raw, geo_offset+16, 8000)
        r = inspect_berlin_tiff_header_grid(bytes(raw))
        self.assertFalse(r["header_only_georeferencing_verified"])
        self.assertIsNone(r["pilot_bbox_intersects_header_raster_extent"])


if __name__ == "__main__":
    unittest.main()
