# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only proof of exact NOAA positive-alpha polygon raster algebra."""

from __future__ import annotations

import unittest
import zlib

from research_runners.noaa_fema_exact_alpha_mask_v0 import (
    ExactAlphaMaskError, alpha_mask_from_deflate, polygonize_exact_positive_pixels,
    dilate_alpha_mask, _area2, MAX_VERTICES,
)

SIZE = 512


def synth_deflate(predicate) -> bytes:
    source = bytearray(SIZE * SIZE * 4)
    for y in range(SIZE):
        for x in range(SIZE):
            source[(y * SIZE + x) * 4 + 3] = 255 if predicate(x, y) else 0
    # TIFF horizontal predictor 2 acts on each pixel-interleaved sample;
    # reverse x loop so each sample subtracts the original previous sample.
    for y in range(SIZE):
        for x in range(SIZE - 1, 0, -1):
            at=(y*SIZE+x)*4+3
            source[at]=(source[at]-source[at-4])&255
    return zlib.compress(source)


class ExactAlphaRasterGeometryTests(unittest.TestCase):
    def test_single_pixel_produces_clockwise_outer_rectangle(self):
        rings, n = polygonize_exact_positive_pixels(
            [b"\x00\x00", b"\x00\x01"]
        )
        self.assertEqual(n, 1)
        self.assertEqual(rings, [[(1,1),(2,1),(2,2),(1,2),(1,1)]])
        self.assertEqual(sum(_area2(r) for r in rings), 2)

    def test_donut_has_one_outer_and_one_hole(self):
        rows = [bytes([1]*5) for _ in range(5)]
        rows[2] = bytes([1,1,0,1,1])
        rings, n = polygonize_exact_positive_pixels(rows)
        self.assertEqual(n,24)
        self.assertEqual(len(rings),2)
        self.assertEqual(sorted(_area2(r) for r in rings),[-2,50])
        self.assertEqual(sum(_area2(r) for r in rings),48)

    def test_diagonal_touch_does_not_merge_two_disjoint_pixels(self):
        rings,n=polygonize_exact_positive_pixels([
            bytes([1,0]), bytes([0,1])
        ])
        self.assertEqual(n,2)
        self.assertEqual(len(rings),2)
        self.assertEqual(sorted(_area2(r) for r in rings),[2,2])

    def test_concave_l_shape_is_single_polygon_and_area_matches(self):
        rings,n=polygonize_exact_positive_pixels([
            bytes([1,1,0,0]),bytes([1,0,0,0]),
            bytes([1,1,1,1]),bytes([0,0,0,0]),
        ])
        self.assertEqual(n,7)
        self.assertEqual(len(rings),1)
        self.assertEqual(_area2(rings[0]),14)
        self.assertEqual(len(rings[0]),9)

    def test_empty_mask_no_positive_polygon(self):
        self.assertEqual(polygonize_exact_positive_pixels([b"\x00\x00"]),([],0))
        with self.assertRaises(ExactAlphaMaskError):
            polygonize_exact_positive_pixels([b""])
        for bad in ([[1,0]], [b"\x02"], [b"\x01",b"\x00\x01"], [], None):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(ExactAlphaMaskError):
                    polygonize_exact_positive_pixels(bad)

    def test_two_pixel_sensitivity_expands_without_leaving_512_grid(self):
        m=[b"\x00"*5 for _ in range(5)]
        m[0]=b"\x01\x00\x00\x00\x00"
        m[4]=b"\x00\x00\x00\x00\x01"
        padded=dilate_alpha_mask(m)
        self.assertEqual(sum(sum(row) for row in padded),17)
        self.assertEqual(padded[0],b"\x01\x01\x01\x00\x00")
        self.assertEqual(padded[4],b"\x00\x00\x01\x01\x01")
        rings,n=polygonize_exact_positive_pixels(padded)
        self.assertEqual(n,17)
        self.assertEqual(sum(_area2(r) for r in rings),34)
        with self.assertRaises(ExactAlphaMaskError):
            dilate_alpha_mask(m,radius=1)

    def test_dilation_respects_valid_image_edge_rows(self):
        c=synth_deflate(lambda x,y:y==123 and x==0)
        mask=alpha_mask_from_deflate(c,height=124)
        padded=dilate_alpha_mask(mask)
        self.assertEqual(len(padded),124)
        self.assertEqual(sum(sum(row) for row in padded),9)
        self.assertEqual(sum(padded[-1]),3)

    def test_tiff_predictor2_real_uncompressed_shape_and_census(self):
        compressed=synth_deflate(lambda x,y:(x<9 and y<11) or (x==20 and y==20))
        mask=alpha_mask_from_deflate(compressed)
        self.assertEqual(len(mask),SIZE)
        self.assertEqual(len(mask[0]),SIZE)
        rings,n=polygonize_exact_positive_pixels(mask)
        self.assertEqual(n,100)
        self.assertEqual(len(rings),2)
        self.assertEqual(sum(_area2(r) for r in rings),200)
        self.assertEqual(mask[0][0],1)
        self.assertEqual(mask[20][20],1)
        self.assertEqual(mask[100][100],0)

    def test_clip_to_source_raster_height(self):
        c=synth_deflate(lambda x,y:y>123)
        mask=alpha_mask_from_deflate(c, height=124)
        self.assertEqual(len(mask),124)
        self.assertEqual(polygonize_exact_positive_pixels(mask),([],0))

    def test_decode_fail_closed_corrupt_adler_and_oversized(self):
        c=synth_deflate(lambda x,y:False)
        for bad in (c[:-2],c+b"extra",c[:-4]+b"\x00"*4):
            with self.subTest(kind=len(bad)):
                with self.assertRaises(ExactAlphaMaskError):
                    alpha_mask_from_deflate(bad)
        with self.assertRaises(ExactAlphaMaskError):
            alpha_mask_from_deflate(b"\x78\x9c"+b"A"*1_000_001)
        for bad in (True,1.5,0,513,None):
            with self.assertRaises(ExactAlphaMaskError):
                alpha_mask_from_deflate(c,width=bad)


if __name__ == "__main__":
    unittest.main()
