# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""USGS S1M native GeoTIFF header science gate on synthetic source bytes only."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import tempfile
import unittest

from research_runners import usgs_s1m_original_tiff_profile_v0 as s


def nominal():
    return dict(driver="GTiff", bands=1, dtype="float32", horizontal_epsg=6350,
                horizontal_unit_factor=1, width=10000, height=10000,
                is_tiled=True, nodata=-999999, pixel_x=1, pixel_y=-1,
                rot_x=0, rot_y=0, origin_x=600000, origin_y=2200000)


class S1MOriginalHeaderTests(unittest.TestCase):
    def test_published_native_header_profile_never_admits_model_or_geoid(self):
        d = s.check_native_header(nominal())
        self.assertTrue(d["header_matches_published_horizontal_profile"])
        for k in ("vertical_epsg_5703_verified_from_header",
                  "geoid18_verified_from_original_lineage", "pixel_values_read",
                  "void_backfill_and_blending_verified", "companion_geopackage_verified",
                  "cog_layout_independently_verified", "model_input_approved"):
            self.assertIs(d[k], False)

    def test_invalid_metadata_fails_closed(self):
        candidates = [
            ("driver", "VRT"), ("bands", 2), ("bands", True), ("dtype", "uint16"),
            ("horizontal_epsg", 26917), ("horizontal_epsg", "6350"),
            ("horizontal_epsg", True), ("horizontal_unit_factor", 0.3048),
            ("width", 512), ("height", 9999999), ("is_tiled", False),
            ("is_tiled", 1), ("nodata", None), ("nodata", -9999),
            ("nodata", 0), ("nodata", 10 ** 1000), ("nodata", float("nan")), ("nodata", True),
            ("pixel_x", 0.5), ("pixel_y", 1), ("rot_x", 1e-6),
            ("rot_y", -1e-6), ("origin_x", float("inf")),
            ("origin_y", float("nan")), ("pixel_x", 10 ** 1000),
        ]
        for key, value in candidates:
            with self.subTest(field=key, value=str(value)):
                obj = nominal()
                obj[key] = value
                with self.assertRaises(s.Blocked):
                    s.check_native_header(obj)

    def test_missing_extra_and_non_mapping_blocked(self):
        bad = nominal()
        bad.pop("pixel_y")
        with self.assertRaises(s.Blocked):
            s.check_native_header(bad)
        bad = nominal()
        bad["source_verified"] = True
        with self.assertRaises(s.Blocked):
            s.check_native_header(bad)
        for value in (None, "header", [], 1):
            with self.subTest(value=value), self.assertRaises(s.Blocked):
                s.check_native_header(value)

    def test_full_hash_and_identity_are_required_before_parser(self):
        raw = b"II\x2a\x00" + b"not a real tiff"
        with tempfile.TemporaryDirectory() as tmp:
            exact = Path(tmp) / s.ORIGINAL_FILENAME
            wrong = Path(tmp) / "legacy_1m.tif"
            exact.write_bytes(raw)
            wrong.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            with self.assertRaises(s.Blocked):
                s.check_local_identity(exact, "0" * 64, len(raw))
            with self.assertRaises(s.Blocked):
                s.check_local_identity(exact, digest, len(raw) + 1)
            with self.assertRaises(s.Blocked):
                s.check_local_identity(wrong, digest, len(raw))
            with self.assertRaises(s.Blocked):
                s.check_local_identity(exact, digest.upper(), len(raw))
            self.assertEqual(s.check_local_identity(exact, digest, len(raw))["file_bytes"],len(raw))
            # A matching checksum on fabricated bytes is NOT a valid GeoTIFF.
            with self.assertRaises(s.Blocked):
                s.inspect_original_tiff(exact, digest, len(raw))
            link = Path(tmp) / "symlink-root"
            link.mkdir()
            forged = link / s.ORIGINAL_FILENAME
            try:
                forged.symlink_to(exact)
            except (OSError, NotImplementedError):
                pass
            else:
                with self.assertRaises(s.Blocked):
                    s.check_local_identity(forged, digest, len(raw))
            with self.assertRaises(s.Blocked):
                s.check_local_identity(exact, digest, s.MAX_ORIGINAL_BYTES + 1)

    def test_gdal_parses_synthetic_real_tiff_header_without_pixel_read(self):
        try:
            import numpy as np
            import rasterio
            from rasterio.transform import from_origin
            from rasterio.windows import Window
        except ImportError:
            self.skipTest("requires dedicated pinned GDAL job")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / s.ORIGINAL_FILENAME
            with rasterio.open(
                path, "w", driver="GTiff", width=10000, height=10000,
                count=1, dtype="float32", crs="EPSG:6350",
                transform=from_origin(600000, 2200000, 1, 1),
                nodata=-999999, tiled=True, blockxsize=256, blockysize=256,
                compress="deflate", SPARSE_OK="YES",
            ) as dst:
                dst.write(np.ones((256,256),dtype="float32"),1,window=Window(0,0,256,256))
            data = path.read_bytes()
            result = s.inspect_original_tiff(path, hashlib.sha256(data).hexdigest(), len(data))
            self.assertTrue(result["header_matches_published_horizontal_profile"])
            self.assertFalse(result["source_provider_original_verified"])
            self.assertFalse(result["model_input_approved"])
            self.assertFalse(result["pixel_values_read"])
            self.assertEqual(result["file_sha256"],hashlib.sha256(data).hexdigest())
            # A header-valid TIFF with an unverified source is NOT source attestation.
            self.assertIn("not_independent_provider_attestation",result["identity_status"])
            with self.assertRaises(s.Blocked):
                s.inspect_original_tiff(path, "0" * 64, len(data))


if __name__ == "__main__":
    unittest.main()
