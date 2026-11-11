# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline GDAL/Rasterio cross-checks, entirely synthetic pixel fixtures.

These tests do NOT claim to validate the remote original COG: only the
separately gated read-only workflow does so. No original pixels in Git.
"""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.probe_dlr_wsf_native_cog_tile_v0 import (
    HEADER_SHA256, NativeCOGBlocked,
)
from scripts.verify_dlr_wsf_native_rasterio_v0 import verify_with_rasterio


class NativeRasterioCrosscheckTests(unittest.TestCase):
    def test_strict_original_sha_before_gdal_file_open(self):
        with self.assertRaisesRegex(NativeCOGBlocked, "source response identity"):
            verify_with_rasterio(b"II\x2a\x00" * 8192, b"fake compressed tile")
        self.assertEqual(len(HEADER_SHA256), 64)

    def test_synthetic_native_lzw_tile_roundtrip_in_gdal(self):
        try:
            import numpy as np
            import rasterio
            from rasterio.transform import from_origin
            from rasterio.windows import Window, bounds
        except ImportError:
            self.skipTest("Rasterio dependency not installed; live workflow installs it")
        step = 0.00008983152841195215
        transform = from_origin(9.989984611636375, 50.010020350689466, step, step)
        with tempfile.TemporaryDirectory(prefix="oc-wsf-gdal-synthetic-") as directory:
            path = Path(directory) / "synthetic-fixture.tif"
            with rasterio.open(
                    path, "w", driver="GTiff", width=22487, height=22487,
                    count=1, dtype="uint8", crs="EPSG:4326", transform=transform,
                    tiled=True, blockxsize=512, blockysize=512,
                    compress="LZW", predictor=1, SPARSE_OK="YES") as dst:
                tile = np.zeros((512, 512), dtype="uint8")
                # 16 filled columns out of 32 => an exact synthetic 50/50 case.
                tile[464:496, 464:480] = 255
                dst.write(tile, 1, window=Window(33 * 512, 40 * 512, 512, 512))
            with rasterio.open(path, "r") as src:
                self.assertEqual(src.crs.to_epsg(), 4326)
                self.assertEqual(src.block_shapes, [(512, 512)])
                self.assertEqual(src.dtypes, ("uint8",))
                self.assertIsNone(src.nodata)
                window = Window(33 * 512 + 464, 40 * 512 + 464, 32, 32)
                data = src.read(1, window=window)
                self.assertEqual(data.shape, (32, 32))
                self.assertEqual(int(np.count_nonzero(data == 255)), 512)
                self.assertEqual(int(np.count_nonzero(data == 0)), 512)
                self.assertEqual(set(np.unique(data).tolist()), {0, 255})
                digest = hashlib.sha256("\n".join(
                    "".join("1" if value == 255 else "0" for value in line)
                    for line in data
                ).encode("utf-8")).hexdigest()
                self.assertEqual(digest, hashlib.sha256(
                    "\n".join("1" * 16 + "0" * 16 for _ in range(32)).encode()
                ).hexdigest())
                bbox = bounds(window, src.transform)
                self.assertTrue(11.5 < bbox[0] < bbox[2] < 11.6)
                self.assertTrue(48.1 < bbox[1] < bbox[3] < 48.2)


if __name__ == "__main__":
    unittest.main()
