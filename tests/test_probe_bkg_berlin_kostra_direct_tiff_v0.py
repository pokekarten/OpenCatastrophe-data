# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic tests for exactly one BKG direct-TIFF source and pilot window."""
from __future__ import annotations

from io import BytesIO
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest

from research_runners.probe_bkg_berlin_kostra_direct_tiff_v0 import (
    URL, MAX_SOURCE_BYTES, BkgTileBlocked, download_exact_source,
    pilot_projected_bounds, inspect_bkg_tile,
)

SPATIAL_AVAILABLE = all(
    importlib.util.find_spec(name) is not None
    for name in ("rasterio", "pyproj", "numpy")
)


class Fake(BytesIO):
    status = 200

    def __init__(self, raw: bytes, *, url=URL, status=200, mime="image/tiff",
                 declared_length=None, encoding="identity"):
        super().__init__(raw)
        self._url = url
        self.status = status
        self.headers = {
            "Content-Type": mime,
            "Content-Length": str(len(raw) if declared_length is None else declared_length),
            "Content-Encoding": encoding,
        }

    def geturl(self):
        return self._url


class DirectOriginalTiffAccessTests(unittest.TestCase):
    def test_fixed_source_and_full_object_hash_bound_without_real_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = b"II*\0" + b"\x01" * 4996
            path = Path(tmp) / "original.tif"
            r = download_exact_source(path, opener=lambda req: Fake(raw))
            from hashlib import sha256
            self.assertEqual(r["source_original_bytes"], len(raw))
            self.assertEqual(r["source_full_tiff_sha256_locally_calculated"],
                             sha256(raw).hexdigest())
            self.assertEqual(path.read_bytes(), raw)
            self.assertFalse(r["original_bytes_committed_or_retained"])

    def test_source_redirect_media_encoding_and_status_are_rejected(self):
        cases = [
            {"url": "https://evil.example.org/other.tif"},
            {"status": 206},
            {"mime": "text/html"},
            {"encoding": "gzip"},
            {"declared_length": MAX_SOURCE_BYTES + 1},
            {"declared_length": 4999},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(BkgTileBlocked):
                    download_exact_source(Path(tmp) / "source.tif",
                                          opener=lambda req: Fake(b"z"*5000, **kwargs))

    def test_source_missing_length_does_not_infer_complete_if_truncated(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(BkgTileBlocked):
                download_exact_source(Path(tmp) / "source.tif",
                                      opener=lambda req: Fake(b"x" * 100))

    @unittest.skipUnless(SPATIAL_AVAILABLE, "spatial dependencies tested in dedicated pinned CI")
    def test_pilot_perimeter_transformation_to_bkg_crs(self):
        bbox = pilot_projected_bounds()
        self.assertTrue(all(math.isfinite(x) for x in bbox))
        self.assertTrue(bbox[0] < bbox[2] and bbox[1] < bbox[3])
        # BKG 32790_5820 tile was selected from this coordinate conversion;
        # real TIFF bounds still must be independently checked.
        self.assertTrue(790000 < bbox[0] < bbox[2] < 800000)
        self.assertTrue(5820000 < bbox[1] < bbox[3] < 5830000)

    @unittest.skipUnless(SPATIAL_AVAILABLE, "spatial dependencies tested in dedicated pinned CI")
    def test_synthetic_geotiff_nodata_and_zero_remain_distinct(self):
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        l, b, r, t = pilot_projected_bounds()
        width = math.ceil(r-l) + 120
        height = math.ceil(t-b) + 120
        values = np.zeros((height, width), dtype=np.float32)
        values[65, 65] = -9999
        values[66, 66] = 3.5
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic-only.tif"
            with rasterio.open(path, "w", driver="GTiff", width=width, height=height,
                               count=1, dtype="float32", crs="EPSG:25832",
                               transform=from_origin(l-60, t+60, 1, 1),
                               nodata=-9999) as ds:
                ds.write(values, 1)
            receipt = inspect_bkg_tile(path)
            self.assertEqual(receipt["source_tiff_crs"], "EPSG:25832")
            self.assertGreater(receipt["original_masked_cells"], 0)
            self.assertGreater(receipt["original_unmasked_numeric_zeros"], 0)
            self.assertGreater(receipt["original_unmasked_positive_numbers"], 0)
            self.assertEqual(receipt["original_unmasked_negative_numbers"], 0)
            self.assertEqual(
                receipt["original_raw_cells_examined"],
                math.prod(receipt["source_window_shape_pixels"]),
            )
            self.assertFalse(receipt["raw_pixel_physical_depth_units_verified"])
            self.assertFalse(receipt["individual_building_hazard_join_verified"])
            self.assertFalse(receipt["insured_exposure_or_cat_model_admitted"])

    @unittest.skipUnless(SPATIAL_AVAILABLE, "spatial dependencies tested in dedicated pinned CI")
    def test_wrong_crs_does_not_silently_reproject_or_admit_pixels(self):
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        l, b, r, t = pilot_projected_bounds()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrong-crs.tif"
            with rasterio.open(path, "w", driver="GTiff", width=600, height=600,
                               count=1, dtype="float32", crs="EPSG:25833",
                               transform=from_origin(l-200, t+200, 1, 1),
                               nodata=-9999) as ds:
                ds.write(np.zeros((600, 600), dtype=np.float32), 1)
            with self.assertRaisesRegex(BkgTileBlocked, "EPSG:25832"):
                inspect_bkg_tile(path)

    @unittest.skipUnless(SPATIAL_AVAILABLE, "spatial dependencies tested in dedicated pinned CI")
    def test_no_source_pilot_coverage_is_blocked_not_zero(self):
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "outside.tif"
            with rasterio.open(path, "w", driver="GTiff", width=600, height=600,
                               count=1, dtype="float32", crs="EPSG:25832",
                               transform=from_origin(700000, 5900000, 1, 1)) as ds:
                ds.write(np.zeros((600, 600), dtype=np.float32), 1)
            with self.assertRaisesRegex(BkgTileBlocked, "does not fully cover"):
                inspect_bkg_tile(path)


if __name__ == "__main__":
    unittest.main()
