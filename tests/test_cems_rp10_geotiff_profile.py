# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

PROFILE_DEPS_AVAILABLE = (
    importlib.util.find_spec("rasterio") is not None
    and importlib.util.find_spec("numpy") is not None
)

if PROFILE_DEPS_AVAILABLE:
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    from scripts import profile_cems_europe_rp10_geotiff as mod


@unittest.skipUnless(
    PROFILE_DEPS_AVAILABLE,
    "requires requirements-cems-geotiff-profile.txt",
)
class CemsRp10GeoTiffProfileTests(unittest.TestCase):
    def _fixture(self, directory: str) -> tuple[Path, int, str]:
        path = Path(directory) / "synthetic-rp10.tif"
        data = np.array([[0.0, 1.5, -9999.0], [2.0, 3.0, 4.0]], dtype="float32")
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=3,
            height=2,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=from_origin(10.0, 50.0, 0.01, 0.01),
            nodata=-9999.0,
        ) as dataset:
            dataset.write(data, 1)
            dataset.update_tags(1, UNITTYPE="m", PIXEL_SAMPLE="must-not-escape")

        raw = path.read_bytes()
        return path, len(raw), hashlib.sha256(raw).hexdigest()

    def test_exact_synthetic_identity_profiles_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, byte_count, sha256 = self._fixture(directory)
            profile = mod._profile_bound_geotiff(
                path,
                expected_byte_count=byte_count,
                expected_sha256=sha256,
            )

        self.assertEqual(profile["schema_version"], "oc-cems-rp10-geotiff-profile-v1")
        self.assertTrue(profile["receipt_identity_verified"])
        self.assertEqual(profile["receipt_byte_count"], byte_count)
        self.assertEqual(profile["receipt_sha256"], sha256)
        self.assertEqual(profile["driver"], "GTiff")
        self.assertEqual(profile["band_count"], 1)
        self.assertEqual(profile["dtypes"], ["float32"])
        self.assertEqual(profile["width"], 3)
        self.assertEqual(profile["height"], 2)
        self.assertEqual(profile["crs"]["epsg"], 4326)
        self.assertEqual(profile["resolution"], [0.01, 0.01])
        self.assertEqual(profile["nodatavals"], [-9999.0])
        self.assertEqual(profile["band_unit_tags"], [{"UNITTYPE": "m"}])
        self.assertNotIn("PIXEL_SAMPLE", profile["band_unit_tags"][0])
        self.assertTrue(profile["unit_metadata_present"])
        self.assertEqual(profile["reader"]["name"], "rasterio")
        self.assertFalse(profile["raster_values_inspected"])
        self.assertNotIn("external_bytes_persisted", profile)
        self.assertTrue(profile["geotiff_metadata_verified"])
        self.assertFalse(profile["benchmark_use_authorized"])
        self.assertFalse(profile["publication_authorized"])
        self.assertFalse(profile["model_use_authorized"])
        for forbidden in ("values", "pixels", "data", "array", "statistics"):
            self.assertNotIn(forbidden, profile)

    def test_public_profile_is_frozen_to_trusted_main_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, _byte_count, _sha256 = self._fixture(directory)
            with self.assertRaisesRegex(
                mod.CemsRp10GeoTiffProfileError,
                "byte count.*accepted receipt",
            ):
                mod.profile_cems_rp10_geotiff(path)

    def test_identity_mismatch_fails_before_raster_reader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, byte_count, sha256 = self._fixture(directory)
            with mock.patch.object(mod.rasterio, "open") as reader:
                with self.assertRaisesRegex(
                    mod.CemsRp10GeoTiffProfileError,
                    "SHA-256.*accepted receipt",
                ):
                    mod._profile_bound_geotiff(
                        path,
                        expected_byte_count=byte_count,
                        expected_sha256="0" * 64 if sha256 != "0" * 64 else "1" * 64,
                    )
                reader.assert_not_called()

    def test_oversize_identity_fails_while_hashing_before_raster_reader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, byte_count, sha256 = self._fixture(directory)
            with mock.patch.object(mod.rasterio, "open") as reader:
                with self.assertRaisesRegex(
                    mod.CemsRp10GeoTiffProfileError,
                    "exceeds accepted receipt",
                ):
                    mod._profile_bound_geotiff(
                        path,
                        expected_byte_count=byte_count - 1,
                        expected_sha256=sha256,
                    )
                reader.assert_not_called()

    def test_band_count_is_bounded_before_per_band_metadata(self) -> None:
        class TooManyBands:
            driver = "GTiff"
            width = 1
            height = 1
            count = mod._MAX_BANDS + 1

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "identity.bin"
            path.write_bytes(b"identity")
            raw = path.read_bytes()
            with mock.patch.object(mod.rasterio, "open", return_value=TooManyBands()):
                with self.assertRaisesRegex(
                    mod.CemsRp10GeoTiffProfileError,
                    "band count.*bounded metadata contract",
                ):
                    mod._profile_bound_geotiff(
                        path,
                        expected_byte_count=len(raw),
                        expected_sha256=hashlib.sha256(raw).hexdigest(),
                    )

    def test_missing_unit_metadata_is_reported_not_inferred(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unitless.tif"
            with rasterio.open(
                path,
                "w",
                driver="GTiff",
                width=1,
                height=1,
                count=1,
                dtype="uint8",
                crs="EPSG:4326",
                transform=from_origin(0.0, 1.0, 1.0, 1.0),
            ) as dataset:
                dataset.write(np.array([[1]], dtype="uint8"), 1)
            raw = path.read_bytes()
            profile = mod._profile_bound_geotiff(
                path,
                expected_byte_count=len(raw),
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

        self.assertEqual(profile["band_units"], [None])
        self.assertEqual(profile["band_unit_tags"], [{}])
        self.assertFalse(profile["unit_metadata_present"])
        self.assertFalse(profile["model_use_authorized"])


if __name__ == "__main__":
    unittest.main()
