# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline independent rasterio/GDAL checks, no original licensed raster fixture."""
from __future__ import annotations

import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window

from scripts.verify_dlr_wsf_native_gdal_v0 import (
    NativeCOGBlocked, WINDOW_SIZE, SAMPLE_IDS, mask_receipt,
    verify_bounded_gdal,
)


def synthetic_tiff_tiles(source: Path) -> tuple[np.ndarray, bytes, tuple[int, int]]:
    """Produce a tiny synthetic independent GDAL fixture with a TIFF tile table."""
    arr = np.zeros((1024, 1024), dtype=np.uint8)
    rows, columns = np.indices((256, 256))
    arr[768:, 768:] = np.where((rows + columns) % 3 == 0, 255, 0).astype("uint8")
    with rasterio.open(
        source, "w", driver="GTiff", height=1024, width=1024,
        count=1, dtype="uint8", tiled=True, blockxsize=256, blockysize=256,
        compress="LZW", crs="EPSG:4326",
        transform=from_origin(11.0, 49.0, 0.0001, 0.0001),
    ) as dst:
        dst.write(arr, 1)
    original = source.read_bytes()
    if original[:4] != b"II\x2a\x00":
        raise AssertionError("CI GDAL changed synthetic TIFF container")
    ifd = struct.unpack_from("<I", original, 4)[0]
    count = struct.unpack_from("<H", original, ifd)[0]
    tags = {}
    for i in range(count):
        tag, typ, n, value = struct.unpack_from("<HHII", original, ifd + 2 + 12 * i)
        tags[tag] = (typ, n, value)
    offsets = struct.unpack_from("<" + "I" * tags[324][1], original, tags[324][2])
    sizes = struct.unpack_from("<" + "I" * tags[325][1], original, tags[325][2])
    return arr, original, (offsets[15], sizes[15])


class NativeGDALCrosscheckTests(unittest.TestCase):
    def test_mask_receipt_correct_classes_and_stable_hash(self):
        a = np.zeros((32, 32), dtype=np.uint8)
        a[0, 0] = 255
        a[8:10, 8:10] = 255
        result = mask_receipt(a)
        self.assertEqual(result["255"], 5)
        self.assertEqual(result["0"], 1019)
        rows = ["".join("1" if x == 255 else "0" for x in line) for line in a]
        self.assertEqual(result["mask_rows_sha256"],
                         hashlib.sha256("\n".join(rows).encode("ascii")).hexdigest())

    def test_reject_wrong_dtype_shape_and_classes(self):
        for a in (
            np.zeros((32, 31), dtype=np.uint8),
            np.zeros((32, 32), dtype=np.uint16),
            np.full((32, 32), 127, dtype=np.uint8),
            [[0] * 32 for _ in range(32)],
        ):
            with self.subTest(type=type(a).__name__):
                with self.assertRaises(NativeCOGBlocked):
                    mask_receipt(a)

    def test_original_source_hash_is_required_before_gdal(self):
        with self.assertRaises(NativeCOGBlocked):
            verify_bounded_gdal(b"\x00" * 32768, b"\x00" * 24659, 18_000_000)
        with self.assertRaises(NativeCOGBlocked):
            verify_bounded_gdal(b"", b"", 18_000_000)

    def test_sparse_tiff_keeps_exact_one_original_block(self):
        """Independent GDAL must read identical values from one copied tile."""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d) / "synthetic.tif"
            original_pixels, blob, (start, size) = synthetic_tiff_tiles(base)
            self.assertGreater(start, 1024)
            self.assertGreater(size, 100)
            sparse = Path(d) / "sparse.tif"
            with sparse.open("w+b") as f:
                f.truncate(len(blob))
                f.seek(0)
                f.write(blob[:1024])  # only classic TIFF metadata directory
                f.seek(start)
                f.write(blob[start:start + size])  # one target tile
            with rasterio.open(sparse) as src:
                got = src.read(1, window=Window(768, 768, 32, 32))
            expected = original_pixels[768:800, 768:800]
            self.assertTrue(np.array_equal(got, expected))
            self.assertEqual(mask_receipt(got), mask_receipt(expected))

    def test_only_two_neon_windows_no_admission(self):
        self.assertEqual(SAMPLE_IDS, {"nonsettlement": 28, "mixed": 29})
        self.assertEqual(WINDOW_SIZE, 32)


if __name__ == "__main__":
    unittest.main()
