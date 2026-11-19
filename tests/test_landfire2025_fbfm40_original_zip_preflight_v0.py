# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""LANDFIRE original-archive security, native-header and source non-admission tests.

All inputs are authored synthetic bytes: no provider acquisition, credentials,
remote API request, external assets or writes to public source registries.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

from research_runners import landfire2025_fbfm40_original_zip_preflight_v0 as s


def header():
    return {
        "driver": "GTiff", "bands": 1, "dtype": "int16", "crs_epsg": 5070,
        "crs_unit_metres": 1.0, "width": 512, "height": 512,
        "nodata": -9999, "a": 30, "b": 0, "c": -1020000,
        "d": 0, "e": -30, "f": 2190000,
    }


def create_zip(root: Path, tif: bytes, extra: list[tuple[str, bytes]] | None = None):
    path = root / s.ARCHIVE_NAME
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("LF2025_FBFM40_CONUS/LF2025_FBFM40_CONUS.tif", tif)
        for name, data in extra or []:
            z.writestr(name, data)
    return path


def pins(path: Path):
    raw = path.read_bytes()
    return {"publisher_md5": hashlib.md5(raw, usedforsecurity=False).hexdigest(),
            "expected_sha256": hashlib.sha256(raw).hexdigest(),
            "expected_archive_bytes": len(raw)}


class LANDFIRENativeArchiveTests(unittest.TestCase):
    def test_header_profile_only_claims_raster_structure(self):
        p = s.screen_native_raster_profile(header())
        self.assertTrue(p["native_header_profile_matches_expected_albers_30m"])
        for field in ("class_values_and_statistics_verified",
                      "geographic_extent_within_conus_verified",
                      "native_raster_pixel_values_read",
                      "raster_suitable_for_individual_buildings"):
            self.assertFalse(p[field])

    def test_bad_crs_spacing_nodata_bands_and_ambiguous_headers_block(self):
        mutations = [
            ("driver", "VRT"), ("bands", 2), ("bands", True),
            ("dtype", "float32"), ("dtype", "uint16"),
            ("crs_epsg", 4326), ("crs_epsg", "5070"), ("crs_epsg", True),
            ("crs_unit_metres", 0.3048), ("crs_unit_metres", float("nan")),
            ("width", 0), ("height", 150000), ("width", True),
            ("nodata", None), ("nodata", 0), ("nodata", -9998),
            ("a", 29.999), ("e", 30), ("b", 1), ("d", -1),
            ("c", float("nan")), ("f", 60000000),
        ]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                profile = header()
                profile[key] = value
                with self.assertRaises(s.LandfireArchiveError):
                    s.screen_native_raster_profile(profile)
        for invalid in (None, "profile", [], 25):
            with self.assertRaises(s.LandfireArchiveError):
                s.screen_native_raster_profile(invalid)
        p = header(); p.pop("nodata")
        with self.assertRaises(s.LandfireArchiveError):
            s.screen_native_raster_profile(p)
        p = header(); p["pass"] = True
        with self.assertRaises(s.LandfireArchiveError):
            s.screen_native_raster_profile(p)

    def test_zip_member_identity_safety_and_fuel_tiff_uniqueness(self):
        cases = [
            [("../evil.txt", b"x")],
            [("/absolute.txt", b"x")],
            [("dir\\bad.txt", b"x")],
            [("more/../bad.txt", b"x")],
            [("extra_FBFM40.tif", b"IIxxxx")],
            [("LF2025_FBFM40_CONUS/LF2025_FBFM40_CONUS.tif", b"dup")],
        ]
        with tempfile.TemporaryDirectory() as d:
            for more in cases:
                path = create_zip(Path(d), b"IIsynthetic", more)
                with self.subTest(more=more), zipfile.ZipFile(path) as zf:
                    with self.assertRaises(s.LandfireArchiveError):
                        s._safe_member_names(zf)
            path = Path(d) / s.ARCHIVE_NAME
            with zipfile.ZipFile(path, "w") as zf:
                info = zipfile.ZipInfo("LF2025_FBFM40_CONUS.tif")
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                zf.writestr(info, b"relative")
            with zipfile.ZipFile(path) as zf:
                with self.assertRaises(s.LandfireArchiveError):
                    s._safe_member_names(zf)

    def test_real_synthetic_geotiff_in_zip_hash_header_and_non_admission(self):
        try:
            import numpy as np
            import rasterio
            from rasterio.transform import from_origin
        except ImportError:
            self.skipTest("native GDAL optional in generic Python jobs")
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            tif_path = root / "synthetic-fuel.tif"
            with rasterio.open(tif_path, "w", driver="GTiff", count=1,
                               width=32, height=32, dtype="int16", crs="EPSG:5070",
                               transform=from_origin(-1020000,2190000,30,30),
                               nodata=-9999,compress="deflate") as dst:
                dst.write(np.full((32,32), 101, dtype="int16"),1)
            raw_tif = tif_path.read_bytes()
            original_zip = create_zip(root, raw_tif)
            kwargs = pins(original_zip)
            result = s.inspect_local_original_zip(original_zip, **kwargs)
            self.assertTrue(result["native_header_profile_matches_expected_albers_30m"])
            self.assertEqual(result["tiff_uncompressed_sha256"], hashlib.sha256(raw_tif).hexdigest())
            self.assertEqual(result["original_zip_sha256"], kwargs["expected_sha256"])
            self.assertEqual(result["original_zip_md5"], kwargs["publisher_md5"])
            self.assertFalse(result["provider_pins_independently_authenticated_by_tool"])
            self.assertFalse(result["native_raster_qualified_for_cat_model"])
            self.assertFalse(result["native_raster_pixel_values_read"])
            self.assertFalse(result["archive_source_commercial_rights_verified"])
            self.assertFalse(result["neon_database_written"])
            for change in (
                {"publisher_md5":"0"*32},
                {"expected_sha256":"0"*64},
                {"expected_archive_bytes":len(original_zip.read_bytes())+1},
                {"publisher_md5":"not-hex"},
            ):
                with self.subTest(change=change):
                    with self.assertRaises(s.LandfireArchiveError):
                        s.inspect_local_original_zip(original_zip, **{**kwargs, **change})
            alias = root / "alias" / s.ARCHIVE_NAME
            alias.parent.mkdir()
            alias.symlink_to(original_zip)
            with self.assertRaises(s.LandfireArchiveError):
                s.inspect_local_original_zip(alias, **kwargs)
            renamed = root / "LF2024_FBFM40_CONUS.zip"
            renamed.write_bytes(original_zip.read_bytes())
            with self.assertRaises(s.LandfireArchiveError):
                s.inspect_local_original_zip(renamed, **kwargs)
            # Confirm a fully valid, pinned ZIP still fails science if native
            # raster has inappropriate grid spacing.
            bad_tif = root / "bad-fuel.tif"
            with rasterio.open(bad_tif, "w", driver="GTiff", count=1,
                               width=32, height=32, dtype="int16", crs="EPSG:5070",
                               transform=from_origin(-1020000,2190000,60,60),
                               nodata=-9999) as dst:
                dst.write(np.full((32,32), 91, dtype="int16"),1)
            original_zip = create_zip(root, bad_tif.read_bytes())
            with self.assertRaises(s.LandfireArchiveError):
                s.inspect_local_original_zip(original_zip, **pins(original_zip))


if __name__ == "__main__":
    unittest.main()
