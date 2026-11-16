# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic GeoTIFF inputs only; no original DLR TIFF or HTTP requests."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_runners import dlr_wsf3d_v02_native_height_tiff_v0 as s

HAS_READER = (
    importlib.util.find_spec("rasterio") is not None
    and importlib.util.find_spec("numpy") is not None
)


@unittest.skipUnless(HAS_READER, "optional rasterio/numpy research reader not installed")
class DLRWSF3DNativeHeightTests(unittest.TestCase):
    @staticmethod
    def synthetic_tiff(*, bounds=(21, -25, 22, -24), crs="EPSG:4326",
                       compression="LZW", count=1, dtype="uint8",
                       values=None, nodata=0, size=1200) -> bytes:
        import numpy as np
        from rasterio.io import MemoryFile
        from rasterio.transform import from_bounds

        if values is None:
            values = np.zeros((size, size), dtype=dtype)
            values[100:200, 100:200] = 12
        p = {
            "driver": "GTiff", "width": size, "height": size,
            "count": count, "dtype": dtype, "nodata": nodata,
            "crs": crs, "transform": from_bounds(*bounds, size, size),
            "compress": compression,
        }
        with MemoryFile() as mem:
            with mem.open(**p) as dest:
                for band in range(1, count + 1):
                    dest.write(values, band)
            return mem.read()

    def inspect(self, binary: bytes) -> dict:
        return s.inspect_native_bytes(
            binary, expected_sha256=hashlib.sha256(binary).hexdigest()
        )

    def test_bounded_native_geotiff_stats_research_only(self):
        b = self.synthetic_tiff()
        self.assertLess(len(b), s.MAX_SOURCE_BYTES)
        out = self.inspect(b)
        self.assertEqual(out["original_sha256"], hashlib.sha256(b).hexdigest())
        self.assertEqual(out["compression"], "lzw")
        self.assertEqual(out["raster_crs"], "EPSG:4326")
        self.assertEqual(out["total_pixels"], 1_440_000)
        self.assertEqual(out["mask_valid_pixels"], 10_000)
        self.assertEqual(out["masked_pixels"], 1_430_000)
        self.assertEqual(out["observed_min_height_raw"], 12.0)
        self.assertEqual(out["observed_max_height_raw"], 12.0)
        self.assertTrue(out["nodata_marker_present"])
        for flag in (
            "observed_pixel_values_scientifically_calibrated",
            "provider_nodata_semantics_independently_verified",
            "individual_building_heights_verified",
            "insured_building_replacement_values_verified",
            "independent_building_ground_truth_verified",
            "original_provider_retrieval_receipt_verified_by_this_function",
            "raw_raster_pixel_values_emitted",
            "provider_bytes_persisted_by_runner",
            "CAT_model_input_approved",
        ):
            self.assertFalse(out[flag], flag)
        self.assertNotIn("21.0", str(out))

    def test_sha_magic_and_source_size_fail_closed(self):
        good = self.synthetic_tiff()
        for case, binary, expected_hash in (
            ("bad digest", good, "0" * 64),
            ("bad digest syntax", good, "not-sha256"),
            ("not a TIFF", b"PNG image", hashlib.sha256(b"PNG image").hexdigest()),
            ("too big", b"x" * (s.MAX_SOURCE_BYTES + 1), "0" * 64),
            ("empty", b"", hashlib.sha256(b"").hexdigest()),
        ):
            with self.subTest(case=case), self.assertRaises(s.WSF3DScienceBlocked):
                s.inspect_native_bytes(binary, expected_sha256=expected_hash)

    def test_bad_crs_geography_band_or_compression_rejected(self):
        for case, changes in (
            ("wrong CRS", {"crs": "EPSG:3857"}),
            ("wrong tile", {"bounds": (22, -25, 23, -24)}),
            ("wrong height tile", {"bounds": (21, -24, 22, -23)}),
            ("three bands", {"count": 3}),
            ("not LZW", {"compression": "DEFLATE"}),
            ("coarse raster", {"size": 256}),
        ):
            binary = self.synthetic_tiff(**changes)
            with self.subTest(case=case), self.assertRaises(s.WSF3DScienceBlocked):
                self.inspect(binary)

    def test_negative_unmasked_height_is_not_treated_as_nodata(self):
        import numpy as np
        a = np.zeros((1200, 1200), dtype="int16")
        a[100:120, 100:120] = -1
        b = self.synthetic_tiff(dtype="int16", values=a, nodata=0)
        self.assertLess(len(b), s.MAX_SOURCE_BYTES)
        with self.assertRaises(s.WSF3DScienceBlocked):
            self.inspect(b)

    def test_missing_nodata_remains_uncertain_not_invented(self):
        b = self.synthetic_tiff(nodata=None)
        out = self.inspect(b)
        self.assertFalse(out["nodata_marker_present"])
        self.assertEqual(out["mask_valid_pixels"], 1_440_000)
        self.assertFalse(out["provider_nodata_semantics_independently_verified"])
        self.assertFalse(out["CAT_model_input_approved"])

    def test_original_filename_and_symlink_gate(self):
        b = self.synthetic_tiff()
        with tempfile.TemporaryDirectory() as tmp:
            wrong = Path(tmp) / "not-the-original.tif"
            wrong.write_bytes(b)
            with self.assertRaises(s.WSF3DScienceBlocked):
                s.audit_file(wrong, expected_sha256=hashlib.sha256(b).hexdigest())
            good = Path(tmp) / s.TILE_NAME
            good.write_bytes(b)
            out = s.audit_file(good, expected_sha256=hashlib.sha256(b).hexdigest())
            self.assertEqual(out["original_bytes"], len(b))
            wrong.unlink()
            wrong.symlink_to(good)
            with self.assertRaises(s.WSF3DScienceBlocked):
                s.audit_file(wrong, expected_sha256=hashlib.sha256(b).hexdigest())

    def test_cli_failure_does_not_leak_untrusted_source_errors(self):
        from contextlib import redirect_stderr
        from io import StringIO
        stderr = StringIO()
        with patch.object(s, "audit_file", side_effect=RuntimeError(
            "Untrusted source file /private/source.tif at [21, -25]")):
            with redirect_stderr(stderr):
                rc = s.main(["--original-tiff", "bad.tif",
                             "--original-sha256", "0" * 64])
        self.assertEqual(rc, 2)
        self.assertIn("BLOCKED:", stderr.getvalue())
        self.assertNotIn("/private/source", stderr.getvalue())
        self.assertNotIn("21", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
