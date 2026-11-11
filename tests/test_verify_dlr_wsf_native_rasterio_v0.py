# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline GDAL/Rasterio cross-checks, entirely synthetic pixel fixtures.

These tests do NOT claim to validate the remote original COG: only the
separately gated read-only workflow does so. No original pixels in Git.
"""
from __future__ import annotations

import hashlib
import os
import struct
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



    def test_sparse_file_from_only_one_native_tile(self):
        """Real GDAL reads exactly one LZW tile from a partly present TIFF.

        Synthetic fixture: all provider bytes are local synthetic and the
        independent pixel check does not depend on our pure-Python decoder.
        """
        import struct
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        from rasterio.windows import Window

        with tempfile.TemporaryDirectory(prefix="oc-wsf-sparse-gdal-test-") as directory:
            original_path = Path(directory) / "synthetic-full.tif"
            sparse_path = Path(directory) / "synthetic-one-block.tif"
            native = np.zeros((1024, 1024), dtype="uint8")
            ys, xs = np.indices((256, 256))
            native[768:, 768:] = np.where((ys + xs) % 3 == 0, 255, 0).astype("uint8")

            with rasterio.open(
                original_path, "w", driver="GTiff", width=1024, height=1024,
                count=1, dtype="uint8", crs="EPSG:4326",
                transform=from_origin(11.0, 49.0, 0.0001, 0.0001),
                compress="LZW", tiled=True, blockxsize=256, blockysize=256,
            ) as dst:
                dst.write(native, 1)
            original = original_path.read_bytes()
            self.assertEqual(original[:4], b"II\x2a\x00")
            ifd = struct.unpack_from("<I", original, 4)[0]
            entries = struct.unpack_from("<H", original, ifd)[0]
            tags = {}
            for i in range(entries):
                tag, kind, number, address = struct.unpack_from(
                    "<HHII", original, ifd + 2 + 12 * i)
                tags[tag] = (kind, number, address)
            offsets = struct.unpack_from(
                "<" + "I" * tags[324][1], original, tags[324][2])
            lengths = struct.unpack_from(
                "<" + "I" * tags[325][1], original, tags[325][2])
            offset, length = offsets[15], lengths[15]
            self.assertGreater(offset, 1024)
            self.assertGreater(length, 100)

            with sparse_path.open("w+b") as out:
                out.truncate(len(original))
                out.seek(0)
                out.write(original[:1024])  # TIFF metadata, no full raster
                out.seek(offset)
                out.write(original[offset:offset + length])  # one original block
                out.flush()
            with rasterio.open(sparse_path) as src:
                pixels = src.read(1, window=Window(768, 768, 32, 32))
            self.assertTrue(np.array_equal(pixels, native[768:800, 768:800]))
            self.assertEqual(int(np.count_nonzero(pixels == 255)), 341)


    def test_relocated_sparse_single_tile_gdal_reads_original_lzw(self):
        """Synthetic tile at the actual DLR byte offset; no provider fixture."""
        try:
            import numpy as np
            import rasterio
            from rasterio.transform import from_origin
            from rasterio.windows import Window
        except ImportError:
            self.skipTest("rasterio wheel required by dedicated native check")
        with tempfile.TemporaryDirectory(prefix="oc-sparse-relocation-test-") as d:
            original = Path(d) / "synthetic_source.tif"
            relocated = Path(d) / "original_like_sparse_copy.tif"
            resolution = 0.00008983152841195215
            affine = from_origin(
                9.989984611636375, 50.010020350689466,
                resolution, resolution,
            )
            with rasterio.open(
                    original, "w", driver="GTiff", width=22487,
                    height=22487, count=1, dtype="uint8", crs="EPSG:4326",
                    transform=affine, tiled=True, blockxsize=512,
                    blockysize=512, compress="LZW", predictor=1,
                    SPARSE_OK="YES") as dst:
                # Entirely artificial. Not copied from the WSF provider.
                tile = np.zeros((512, 512), dtype="uint8")
                tile[464:496, 464:480] = 255
                dst.write(
                    tile, 1, window=Window(33 * 512, 40 * 512, 512, 512)
                )
            header = bytearray(original.read_bytes())
            self.assertEqual(header[:4], b"II\x2a\x00")
            ifd = struct.unpack_from("<I", header, 4)[0]
            count = struct.unpack_from("<H", header, ifd)[0]
            tags = {}
            for index in range(count):
                pos = ifd + 2 + 12 * index
                tag, typ, n, ptr = struct.unpack_from("<HHII", header, pos)
                tags[tag] = (typ, n, ptr)
            self.assertIn(324, tags)  # original TIFF tile-offset array
            self.assertIn(325, tags)  # compressed byte-count array
            idx = 40 * 44 + 33
            original_offset = struct.unpack_from(
                "<I", header, tags[324][2] + 4 * idx
            )[0]
            nbytes = struct.unpack_from(
                "<I", header, tags[325][2] + 4 * idx
            )[0]
            compressed = bytes(header[original_offset:original_offset + nbytes])
            self.assertTrue(0 < nbytes < 32768)
            original_dlr_offset = 12156322
            struct.pack_into(
                "<I", header, tags[324][2] + 4 * idx,
                original_dlr_offset,
            )
            # This mimics the live runner: only first 32 KiB and ONE
            # compressed tile at an otherwise sparse 12.1 MB offset.
            with relocated.open("wb") as dest:
                dest.write(bytes(header[:32768]).ljust(32768, b"\x00"))
                dest.seek(original_dlr_offset, os.SEEK_SET)
                dest.write(compressed)
            self.assertEqual(
                relocated.stat().st_size, original_dlr_offset + nbytes
            )
            with rasterio.open(relocated, "r") as src:
                native = src.read(
                    1, window=Window(
                        33 * 512 + 464, 40 * 512 + 464, 32, 32
                    )
                )
                self.assertEqual(src.crs.to_epsg(), 4326)
                self.assertEqual(src.block_shapes, [(512, 512)])
                self.assertEqual(int(np.count_nonzero(native == 255)), 512)
                self.assertEqual(int(np.count_nonzero(native == 0)), 512)


if __name__ == "__main__":
    unittest.main()
