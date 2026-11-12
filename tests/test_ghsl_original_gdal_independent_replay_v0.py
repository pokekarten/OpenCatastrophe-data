# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only independent libtiff/GDAL research regression; no provider GET."""
from __future__ import annotations

import hashlib
import importlib.util
import struct
import unittest
from unittest.mock import patch
import zlib

from scripts import ghsl_original_gdal_independent_replay_v0 as g


HAS_GDAL = (importlib.util.find_spec("rasterio") is not None
            and importlib.util.find_spec("numpy") is not None)


class GHSLIndependentGDALTests(unittest.TestCase):
    def test_unreviewed_source_compressed_length_and_hash_fail_closed(self):
        with self.assertRaises(g.IndependentGHSLBlocked):
            g.validate_original_gdal_result(b"", "surface")
        with self.assertRaisesRegex(g.IndependentGHSLBlocked, "SHA-256"):
            g.validate_original_gdal_result(b"x" * g.PRODUCTS["surface"]["native_block_bytes"], "surface")
        with self.assertRaises(g.IndependentGHSLBlocked):
            g.validate_original_gdal_result(b"x", "unknown")
        for bad in (b"", b"x" * (g.MAX_ORIGINAL_REQUEST_BYTES + 1), "not bytes"):
            with self.assertRaises(g.IndependentGHSLBlocked):
                g.make_ram_only_one_tile_tiff(bad)

    def test_no_live_request_without_explicit_flag(self):
        with self.assertRaises(SystemExit) as cm:
            g.main(["--product", "surface"])
        self.assertNotEqual(cm.exception.code, 0)

    def test_original_byte_header_rejected_before_block_fetch(self):
        with patch.object(g, "_fetch_range", return_value=b"x" * g.PREFIX_BYTES) as fetch:
            with self.assertRaises(g.IndependentGHSLBlocked):
                g.run_original_replay("surface")
            fetch.assert_called_once_with("surface", 0, g.PREFIX_BYTES)

    @unittest.skipUnless(HAS_GDAL, "optional independent GDAL/rasterio installed in source workflow")
    def test_lib_tiff_synthetic_unsigned_32_bit_window_and_uint64_sum(self):
        import numpy as np
        cells = np.zeros((g.TILE_SIDE, g.TILE_SIDE), dtype="<u4")
        view = cells[g.WINDOW_LOCAL_Y:g.WINDOW_LOCAL_Y+g.WINDOW_SIDE,
                     g.WINDOW_LOCAL_X:g.WINDOW_LOCAL_X+g.WINDOW_SIDE]
        view[:, :] = 4_000_000_000  # sum must NOT overflow uint32
        view[:, 0:8] = 0
        view[:, 8] = g.UINT32_NODATA_CANDIDATE
        blob = zlib.compress(cells.tobytes(order="C"), level=1)
        out = g.decode_gdal_aggregate(blob)
        self.assertEqual(out["positive"], 32*23)
        self.assertEqual(out["zero"], 32*8)
        self.assertEqual(out["potential_nodata"], 32)
        self.assertEqual(out["sum_positive"], 32*23*4_000_000_000)
        self.assertEqual(out["min_positive"], 4_000_000_000)
        self.assertEqual(out["max_positive"], 4_000_000_000)
        self.assertEqual(out["decoded_sha256"], hashlib.sha256(cells.tobytes()).hexdigest())
        self.assertEqual(out["window_sha256"], hashlib.sha256(view.tobytes()).hexdigest())
        self.assertFalse(out["nodata_semantics_validated"])
        self.assertFalse(out["insurance_CAT_model_input_approved"])
        self.assertFalse(out["original_pixels_or_reconstructed_tiff_saved"])

    @unittest.skipUnless(HAS_GDAL, "optional independent GDAL/rasterio installed in source workflow")
    def test_gdal_synthetic_does_not_trust_fake_original_receipt(self):
        import numpy as np
        arr = np.zeros((g.TILE_SIDE,g.TILE_SIDE),dtype="<u4")
        arr[291:323,445:477] = 5
        blob = zlib.compress(arr.tobytes())
        one = g.decode_gdal_aggregate(blob)
        self.assertEqual(one["positive"], 1024)
        with self.assertRaisesRegex(g.IndependentGHSLBlocked, "original source block length"):
            g.validate_original_gdal_result(blob, "surface")

    @unittest.skipUnless(HAS_GDAL, "optional independent GDAL/rasterio installed in source workflow")
    def test_unsupported_and_corrupted_deflate_rejected(self):
        for blob in (b"x" * 100, zlib.compress(b"small"), zlib.compress(b"too big" * 500_000)):
            with self.subTest(size=len(blob)), self.assertRaises(g.IndependentGHSLBlocked):
                g.decode_gdal_aggregate(blob)


if __name__ == "__main__":
    unittest.main()
