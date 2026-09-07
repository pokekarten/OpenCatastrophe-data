# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
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

    from scripts import profile_cems_europe_mask_geotiffs as mod
    from scripts import profile_cems_europe_rp10_geotiff as rp10


@unittest.skipUnless(
    PROFILE_DEPS_AVAILABLE,
    "requires requirements-cems-geotiff-profile.txt",
)
class CemsMaskGeoTiffProfileTests(unittest.TestCase):
    def _fixture(
        self,
        directory: str,
        *,
        dtype: str = "uint8",
        nodata: int = 255,
    ) -> tuple[Path, int, str]:
        path = Path(directory) / "synthetic-mask.tif"
        data = np.array([[0, 1, nodata], [1, 0, 1]], dtype=dtype)
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=3,
            height=2,
            count=1,
            dtype=dtype,
            crs="EPSG:4326",
            transform=from_origin(10.0, 50.0, 0.01, 0.01),
            nodata=nodata,
        ) as dataset:
            dataset.write(data, 1)
        raw = path.read_bytes()
        return path, len(raw), hashlib.sha256(raw).hexdigest()

    def _profile_dict(self, *, mask: bool = True) -> dict:
        mask_receipt = mod.MASK_RECEIPTS["permanent_water"]
        profile = {
            "schema_version": (
                mod.PROFILE_SCHEMA_VERSION
                if mask
                else mod.RP10_PROFILE_SCHEMA_VERSION
            ),
            "dataset_id": mod.DATASET_ID,
            "source_issue": mod.SOURCE_ISSUE if mask else rp10.SOURCE_ISSUE,
            "profile_issue": mod.PROFILE_ISSUE if mask else rp10.PROFILE_ISSUE,
            "release": mod.RELEASE,
            "filename": mask_receipt["filename"] if mask else rp10.FILENAME,
            "source_url": (
                mod.BASE_URL + mask_receipt["filename"]
                if mask
                else rp10.SOURCE_URL
            ),
            "receipt_byte_count": (
                mask_receipt["byte_count"] if mask else rp10.ACCEPTED_BYTE_COUNT
            ),
            "receipt_sha256": (
                mask_receipt["sha256"] if mask else rp10.ACCEPTED_SHA256
            ),
            "receipt_identity_verified": True,
            "driver": "GTiff",
            "band_count": 1,
            "dtypes": ["float32"],
            "width": 110162,
            "height": 51992,
            "crs": {"string": "EPSG:4326", "epsg": 4326, "wkt": "WGS84"},
            "transform_gdal": [
                -24.54208333,
                0.0008333333333333334,
                0.0,
                71.13375,
                0.0,
                -0.0008333333333333334,
            ],
            "resolution": [0.0008333333333333334, 0.0008333333333333334],
            "bounds": [
                -24.54208333,
                27.80708333333334,
                67.25958333666668,
                71.13375,
            ],
            "nodatavals": [-9999.0],
            "scales": [1.0],
            "offsets": [0.0],
            "descriptions": [None],
            "band_units": [None],
            "band_unit_tags": [{}],
            "unit_metadata_present": False,
            "reader": {
                "name": "rasterio",
                "version": "test",
                "gdal_version": "test",
                "proj_version": "test",
            },
            "raster_values_inspected": False,
            "geotiff_metadata_verified": True,
            "benchmark_use_authorized": False,
            "publication_authorized": False,
            "model_use_authorized": False,
        }
        if mask:
            profile["mask_kind"] = "permanent_water"
            profile["mask_values_inspected"] = False
        return profile

    def test_frozen_receipts_match_trusted_main_issue_809(self) -> None:
        self.assertEqual(
            mod.MASK_RECEIPTS,
            {
                "permanent_water": {
                    "filename": "Europe_permanent_water_bodies.tif",
                    "byte_count": 112_287_284,
                    "sha256": "5e14f13fb202263a8407026aa60e7c455db7976284217e5da09ea49c13112eee",
                },
                "spurious_depth": {
                    "filename": "Europe_spurious_depth_areas.tif",
                    "byte_count": 74_730_820,
                    "sha256": "6b609153e28b7e634159525cf7cc9089242a8e17de2578f162d51a0e80d2e7c8",
                },
            },
        )

    def test_exact_synthetic_mask_identity_reuses_metadata_only_profiler(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, byte_count, sha256 = self._fixture(directory)
            synthetic_receipt = {
                "filename": "Europe_permanent_water_bodies.tif",
                "byte_count": byte_count,
                "sha256": sha256,
            }
            with mock.patch.dict(
                mod.MASK_RECEIPTS,
                {"permanent_water": synthetic_receipt},
                clear=False,
            ):
                profile = mod.profile_cems_mask_geotiff(
                    path,
                    mask_kind="permanent_water",
                )

        self.assertEqual(profile["schema_version"], mod.PROFILE_SCHEMA_VERSION)
        self.assertEqual(profile["source_issue"], 809)
        self.assertEqual(profile["profile_issue"], 816)
        self.assertEqual(profile["mask_kind"], "permanent_water")
        self.assertEqual(profile["filename"], "Europe_permanent_water_bodies.tif")
        self.assertEqual(profile["receipt_byte_count"], byte_count)
        self.assertEqual(profile["receipt_sha256"], sha256)
        self.assertTrue(profile["receipt_identity_verified"])
        self.assertTrue(profile["geotiff_metadata_verified"])
        self.assertEqual(profile["crs"]["epsg"], 4326)
        self.assertFalse(profile["raster_values_inspected"])
        self.assertFalse(profile["mask_values_inspected"])
        self.assertFalse(profile["benchmark_use_authorized"])
        self.assertFalse(profile["publication_authorized"])
        self.assertFalse(profile["model_use_authorized"])

    def test_unknown_mask_kind_fails_before_profiler(self) -> None:
        with mock.patch.object(rp10, "_profile_bound_geotiff") as profiler:
            with self.assertRaisesRegex(
                mod.CemsMaskGeoTiffProfileError,
                "outside the frozen #809 receipt set",
            ):
                mod.profile_cems_mask_geotiff(
                    "unused.tif",
                    mask_kind="caller-selected",
                )
        profiler.assert_not_called()

    def test_receipt_sha_drift_fails_before_raster_reader(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, byte_count, sha256 = self._fixture(directory)
            bad = {
                "filename": "Europe_permanent_water_bodies.tif",
                "byte_count": byte_count,
                "sha256": "0" * 64 if sha256 != "0" * 64 else "1" * 64,
            }
            with (
                mock.patch.dict(
                    mod.MASK_RECEIPTS,
                    {"permanent_water": bad},
                    clear=False,
                ),
                mock.patch.object(rp10.MemoryFile, "open", autospec=True) as reader,
                self.assertRaisesRegex(mod.CemsMaskGeoTiffProfileError, "SHA-256"),
            ):
                mod.profile_cems_mask_geotiff(
                    path,
                    mask_kind="permanent_water",
                )
            reader.assert_not_called()

    def test_grid_match_is_separate_from_container_differences(self) -> None:
        mask = self._profile_dict(mask=True)
        reference = self._profile_dict(mask=False)
        mask["dtypes"] = ["uint8"]
        mask["nodatavals"] = [255.0]

        comparison = mod.compare_mask_profile_to_rp10(mask, reference)

        self.assertTrue(comparison["grid_metadata_equal"])
        self.assertFalse(comparison["container_metadata_equal"])
        self.assertTrue(all(comparison["grid_field_equal"].values()))
        self.assertFalse(comparison["container_field_equal"]["dtypes"])
        self.assertFalse(comparison["container_field_equal"]["nodatavals"])
        self.assertFalse(comparison["mask_values_inspected"])
        self.assertFalse(comparison["mask_value_semantics_verified"])
        self.assertFalse(comparison["benchmark_use_authorized"])
        self.assertFalse(comparison["publication_authorized"])
        self.assertFalse(comparison["model_use_authorized"])

    def test_grid_drift_is_reported_field_by_field(self) -> None:
        mask = self._profile_dict(mask=True)
        reference = self._profile_dict(mask=False)
        mask["width"] += 1
        mask["crs"] = {
            "string": "EPSG:3857",
            "epsg": 3857,
            "wkt": "WebMercator",
        }
        mask["transform_gdal"] = list(mask["transform_gdal"])
        mask["transform_gdal"][0] += 1.0

        comparison = mod.compare_mask_profile_to_rp10(mask, reference)

        self.assertFalse(comparison["grid_metadata_equal"])
        self.assertFalse(comparison["grid_field_equal"]["width"])
        self.assertFalse(comparison["grid_field_equal"]["crs"])
        self.assertFalse(comparison["grid_field_equal"]["transform_gdal"])
        self.assertTrue(comparison["grid_field_equal"]["height"])
        self.assertTrue(comparison["grid_field_equal"]["resolution"])

    def test_comparison_rejects_mask_receipt_or_authority_drift(self) -> None:
        reference = self._profile_dict(mask=False)
        for field, value in (
            ("receipt_sha256", "0" * 64),
            ("receipt_byte_count", 1),
            ("source_url", "https://example.invalid/drift.tif"),
            ("mask_values_inspected", True),
            ("model_use_authorized", True),
        ):
            with self.subTest(field=field):
                mask = copy.deepcopy(self._profile_dict(mask=True))
                mask[field] = value
                with self.assertRaises(mod.CemsMaskGeoTiffProfileError):
                    mod.compare_mask_profile_to_rp10(mask, reference)

    def test_comparison_requires_exact_accepted_rp10_identity(self) -> None:
        mask = self._profile_dict(mask=True)
        for field, value in (
            ("receipt_sha256", "0" * 64),
            ("receipt_byte_count", 1),
            ("source_issue", 999),
            ("profile_issue", 999),
            ("filename", "other.tif"),
            ("source_url", "https://example.invalid/other.tif"),
        ):
            with self.subTest(field=field):
                reference = copy.deepcopy(self._profile_dict(mask=False))
                reference[field] = value
                with self.assertRaisesRegex(
                    mod.CemsMaskGeoTiffProfileError,
                    "accepted #793/#802 identity",
                ):
                    mod.compare_mask_profile_to_rp10(mask, reference)

    def test_existing_rp10_public_profile_contract_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, _byte_count, _sha256 = self._fixture(directory)
            with self.assertRaisesRegex(
                rp10.CemsRp10GeoTiffProfileError,
                "byte count.*accepted receipt",
            ):
                rp10.profile_cems_rp10_geotiff(path)


if __name__ == "__main__":
    unittest.main()
