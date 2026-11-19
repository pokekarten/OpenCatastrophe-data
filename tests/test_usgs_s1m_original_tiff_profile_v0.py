# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""USGS S1M native GeoTIFF header science gate on synthetic source bytes only."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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

    def test_caller_chosen_full_hash_cannot_replace_original_provider_prefix(self):
        # Synthetic bytes stand in for the trusted prefix under a test-only
        # patch; the production constants remain frozen from the original job.
        prefix = b"X" * 65536
        original = prefix + b"synthetic tail"
        digest = hashlib.sha256(prefix).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / s.ORIGINAL_FILENAME
            path.write_bytes(original)
            with patch.object(s, "TRUSTED_ORIGINAL_TOTAL_BYTES", len(original)), \
                 patch.object(s, "TRUSTED_ORIGINAL_PREFIX_SHA256", digest):
                receipt = s.check_pinned_florida_original_prefix(path, len(original))
                self.assertTrue(receipt["pinned_original_prefix_matches_trusted_receipt"])
                self.assertFalse(receipt["complete_original_provider_file_attested"])
                self.assertFalse(receipt["model_input_approved"])
                with self.assertRaisesRegex(s.Blocked, "supplied S1M full-file size"):
                    s.check_pinned_florida_original_prefix(path, len(original) + 1)
                changed = b"Y" + original[1:]
                path.write_bytes(changed)
                # A matching caller-chosen full SHA remains a false provenance
                # witness if the first source-original 64 KiB were replaced.
                self.assertEqual(
                    s.check_local_identity(path, hashlib.sha256(changed).hexdigest(), len(changed))["file_bytes"],
                    len(changed),
                )
                with self.assertRaisesRegex(s.Blocked, "trusted provider SHA-256"):
                    s.check_pinned_florida_original_prefix(path, len(changed))
                with self.assertRaisesRegex(s.Blocked, "trusted provider SHA-256"):
                    s.inspect_original_tiff(path, hashlib.sha256(changed).hexdigest(), len(changed))
            # Even the same bytes must be rejected at the real frozen 447 MB size.
            with self.assertRaisesRegex(s.Blocked, "trusted original range receipt"):
                s.check_pinned_florida_original_prefix(path, len(changed))

    def test_valid_header_at_wrong_coordinates_is_not_frozen_florida_tile(self):
        # Published CRS/resolution/NoData alone are no geographic identity.
        profile = nominal()  # Origin is far from the selected Florida tile.
        self.assertTrue(s.check_native_header(profile)["header_matches_published_horizontal_profile"])
        try:
            import rasterio
        except ImportError:
            self.skipTest("requires pinned Rasterio/PROJ spatial test")
        with self.assertRaisesRegex(s.Blocked, "does not match pinned Florida"):
            s.check_frozen_florida_footprint(profile)

    def test_frozen_florida_spatial_screen_does_not_attest_original_pixels(self):
        try:
            import rasterio
            from rasterio.warp import transform
        except ImportError:
            self.skipTest("requires pinned Rasterio/PROJ spatial test")
        west, south, east, north = s.FROZEN_PRODUCT_BBOX_WGS84
        xs, ys = transform("EPSG:4326", "EPSG:6350",
                           [(west + east) / 2], [(south + north) / 2])
        profile = nominal()
        profile["origin_x"] = xs[0] - 5000
        profile["origin_y"] = ys[0] + 5000
        receipt = s.check_frozen_florida_footprint(profile)
        self.assertTrue(receipt["frozen_florida_catalogue_bbox_consistent"])
        self.assertFalse(receipt["native_raster_provider_origin_independently_attested"])
        self.assertFalse(receipt["native_raster_elevation_pixels_verified"])
        profile["origin_x"] += 50000
        with self.assertRaisesRegex(s.Blocked, "does not match pinned Florida"):
            s.check_frozen_florida_footprint(profile)

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
            from rasterio.warp import transform
            from rasterio.windows import Window
            west, south, east, north = s.FROZEN_PRODUCT_BBOX_WGS84
            xs, ys = transform("EPSG:4326", "EPSG:6350",
                               [(west + east) / 2], [(south + north) / 2])
            origin_x, origin_y = xs[0] - 5000, ys[0] + 5000
        except ImportError:
            self.skipTest("requires dedicated pinned GDAL job")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / s.ORIGINAL_FILENAME
            with rasterio.open(
                path, "w", driver="GTiff", width=10000, height=10000,
                count=1, dtype="float32", crs="EPSG:6350",
                transform=from_origin(origin_x, origin_y, 1, 1),
                nodata=-999999, tiled=True, blockxsize=256, blockysize=256,
                compress="deflate", SPARSE_OK="YES",
            ) as dst:
                dst.write(np.ones((256,256),dtype="float32"),1,window=Window(0,0,256,256))
            data = path.read_bytes()
            # The fixture is synthetic, never the public 447 MB provider file:
            # override both trusted original observations only inside this test.
            fixture_prefix_bytes = min(len(data), s.TRUSTED_PREFIX_BYTES)
            with patch.object(s, "TRUSTED_ORIGINAL_TOTAL_BYTES", len(data)), \
                 patch.object(s, "TRUSTED_PREFIX_BYTES", fixture_prefix_bytes), \
                 patch.object(s, "TRUSTED_ORIGINAL_PREFIX_SHA256",
                              hashlib.sha256(data[:fixture_prefix_bytes]).hexdigest()):
                result = s.inspect_original_tiff(path, hashlib.sha256(data).hexdigest(), len(data))
                with self.assertRaises(s.Blocked):
                    s.inspect_original_tiff(path, "0" * 64, len(data))
            self.assertTrue(result["header_matches_published_horizontal_profile"])
            self.assertTrue(result["frozen_florida_catalogue_bbox_consistent"])
            self.assertFalse(result["native_raster_provider_origin_independently_attested"])
            self.assertTrue(result["pinned_original_prefix_matches_trusted_receipt"])
            self.assertFalse(result["complete_original_provider_file_attested"])
            self.assertFalse(result["source_provider_original_verified"])
            self.assertFalse(result["model_input_approved"])
            self.assertFalse(result["pixel_values_read"])
            self.assertEqual(result["file_sha256"],hashlib.sha256(data).hexdigest())
            # A header-valid TIFF with an unverified source is NOT source attestation.
            self.assertIn("not_independent_provider_attestation",result["identity_status"])

if __name__ == "__main__":
    unittest.main()
