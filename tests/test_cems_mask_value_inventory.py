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

    from scripts import profile_cems_europe_mask_values as mod


@unittest.skipUnless(
    PROFILE_DEPS_AVAILABLE,
    "requires requirements-cems-geotiff-profile.txt",
)
class CemsMaskValueInventoryTests(unittest.TestCase):
    def _fixture(
        self,
        directory: str,
        data,
        *,
        nodata: float = -9999.0,
        tiled: bool = False,
    ) -> tuple[Path, int, str]:
        path = Path(directory) / "synthetic-mask.tif"
        kwargs = {}
        if tiled:
            kwargs.update(tiled=True, blockxsize=16, blockysize=16)
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=int(data.shape[1]),
            height=int(data.shape[0]),
            count=1,
            dtype=str(data.dtype),
            crs="EPSG:4326",
            transform=from_origin(10.0, 50.0, 0.01, 0.01),
            nodata=nodata,
            **kwargs,
        ) as dataset:
            dataset.write(data, 1)
        raw = path.read_bytes()
        return path, len(raw), hashlib.sha256(raw).hexdigest()

    def _inventory(self, data, *, nodata: float = -9999.0) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path, _byte_count, _sha256 = self._fixture(
                directory,
                data,
                nodata=nodata,
            )
            with rasterio.open(path) as dataset:
                return mod.inventory_dataset(dataset)

    def test_single_finite_value_plus_nodata_has_only_candidate_support(self) -> None:
        result = self._inventory(
            np.array([[7.0, -9999.0], [7.0, 7.0]], dtype="float64")
        )

        self.assertEqual(result["total_cells"], 4)
        self.assertEqual(result["nodata_count"], 1)
        self.assertEqual(result["finite_count"], 3)
        self.assertEqual(result["finite_unique_value_count"], 1)
        self.assertEqual(result["finite_value_counts"], [{"value": 7, "count": 3}])
        self.assertEqual(
            result["encoding_observation"],
            "single_finite_value_candidate_support",
        )

    def test_zero_one_values_remain_mapping_unresolved(self) -> None:
        result = self._inventory(
            np.array([[0.0, 1.0], [1.0, 0.0]], dtype="float64")
        )

        self.assertEqual(result["zero_count"], 2)
        self.assertEqual(result["nonzero_count"], 2)
        self.assertEqual(result["finite_unique_value_count"], 2)
        self.assertEqual(
            result["finite_value_counts"],
            [{"value": 0, "count": 2}, {"value": 1, "count": 2}],
        )
        self.assertEqual(
            result["encoding_observation"],
            "multiple_finite_values_mapping_unresolved",
        )

    def test_nonfinite_values_are_counted_separately_from_nodata(self) -> None:
        result = self._inventory(
            np.array(
                [[-9999.0, np.nan], [np.inf, -np.inf], [2.0, 0.0]],
                dtype="float64",
            )
        )

        self.assertEqual(result["nodata_count"], 1)
        self.assertEqual(result["nan_non_nodata_count"], 1)
        self.assertEqual(result["positive_infinity_count"], 1)
        self.assertEqual(result["negative_infinity_count"], 1)
        self.assertEqual(result["finite_count"], 2)
        self.assertEqual(result["finite_min"], 0)
        self.assertEqual(result["finite_max"], 2)
        self.assertEqual(
            result["nodata_count"]
            + result["nan_non_nodata_count"]
            + result["positive_infinity_count"]
            + result["negative_infinity_count"]
            + result["finite_count"],
            result["total_cells"],
        )

    def test_cardinality_above_preregistered_cap_is_bounded(self) -> None:
        data = np.arange(33, dtype="float64").reshape(3, 11)
        result = self._inventory(data)

        self.assertTrue(result["cardinality_cap_exceeded"])
        self.assertIsNone(result["finite_unique_value_count"])
        self.assertIsNone(result["finite_value_counts"])
        self.assertEqual(result["encoding_observation"], "cardinality_cap_exceeded")

    def test_block_order_does_not_change_inventory_or_digest(self) -> None:
        data = np.zeros((32, 32), dtype="float64")
        data[:16, :16] = 1.0
        data[16:, 16:] = 2.0
        with tempfile.TemporaryDirectory() as directory:
            path, _byte_count, _sha256 = self._fixture(
                directory,
                data,
                tiled=True,
            )
            with rasterio.open(path) as dataset:
                windows = [window for _index, window in dataset.block_windows(1)]
                forward = mod._inventory_windows(
                    dataset,
                    windows,
                    cardinality_cap=mod.CARDINALITY_CAP,
                )
                reverse = mod._inventory_windows(
                    dataset,
                    reversed(windows),
                    cardinality_cap=mod.CARDINALITY_CAP,
                )

        self.assertGreater(len(windows), 1)
        self.assertEqual(forward, reverse)

    def test_partial_window_scan_fails_instead_of_silently_sampling(self) -> None:
        data = np.zeros((32, 32), dtype="float64")
        with tempfile.TemporaryDirectory() as directory:
            path, _byte_count, _sha256 = self._fixture(
                directory,
                data,
                tiled=True,
            )
            with rasterio.open(path) as dataset:
                windows = [window for _index, window in dataset.block_windows(1)]
                with self.assertRaisesRegex(
                    mod.CemsMaskValueProfileError,
                    "window scan covered",
                ):
                    mod._inventory_windows(
                        dataset,
                        windows[:-1],
                        cardinality_cap=mod.CARDINALITY_CAP,
                    )

    def test_public_inventory_does_not_accept_caller_selected_windows(self) -> None:
        data = np.zeros((16, 16), dtype="float64")
        with tempfile.TemporaryDirectory() as directory:
            path, _byte_count, _sha256 = self._fixture(directory, data, tiled=True)
            with rasterio.open(path) as dataset:
                windows = [window for _index, window in dataset.block_windows(1)]
                with self.assertRaises(TypeError):
                    mod.inventory_dataset(dataset, windows=windows)

    def test_public_inventory_does_not_accept_caller_selected_cardinality_cap(self) -> None:
        data = np.zeros((2, 2), dtype="float64")
        with tempfile.TemporaryDirectory() as directory:
            path, _byte_count, _sha256 = self._fixture(directory, data)
            with rasterio.open(path) as dataset:
                with self.assertRaises(TypeError):
                    mod.inventory_dataset(
                        dataset,
                        cardinality_cap=mod.CARDINALITY_CAP - 1,
                    )

    def test_private_aggregator_rejects_cap_above_preregistered_bound(self) -> None:
        data = np.zeros((2, 2), dtype="float64")
        with tempfile.TemporaryDirectory() as directory:
            path, _byte_count, _sha256 = self._fixture(directory, data)
            with rasterio.open(path) as dataset:
                windows = [window for _index, window in dataset.block_windows(1)]
                with self.assertRaisesRegex(
                    mod.CemsMaskValueProfileError,
                    "preregistered bound",
                ):
                    mod._inventory_windows(
                        dataset,
                        windows,
                        cardinality_cap=mod.CARDINALITY_CAP + 1,
                    )

    def test_exact_receipt_bound_profile_keeps_all_authority_false(self) -> None:
        data = np.array([[1.0, -9999.0], [1.0, 1.0]], dtype="float64")
        with tempfile.TemporaryDirectory() as directory:
            path, byte_count, sha256 = self._fixture(directory, data)
            receipt = {
                "filename": "Europe_permanent_water_bodies.tif",
                "byte_count": byte_count,
                "sha256": sha256,
            }
            with mock.patch.dict(
                mod._metadata.MASK_RECEIPTS,
                {"permanent_water": receipt},
                clear=False,
            ):
                result = mod.profile_cems_mask_value_inventory(
                    path,
                    mask_kind="permanent_water",
                )

        self.assertTrue(result["receipt_identity_verified"])
        self.assertTrue(result["mask_values_inspected"])
        self.assertFalse(result["mask_value_semantics_verified"])
        self.assertFalse(result["per_cell_scientific_correctness_verified"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertEqual(
            result["inventory"]["encoding_observation"],
            "single_finite_value_candidate_support",
        )

    def test_receipt_sha_drift_fails_before_value_scan(self) -> None:
        data = np.ones((2, 2), dtype="float64")
        with tempfile.TemporaryDirectory() as directory:
            path, byte_count, sha256 = self._fixture(directory, data)
            receipt = {
                "filename": "Europe_permanent_water_bodies.tif",
                "byte_count": byte_count,
                "sha256": "0" * 64 if sha256 != "0" * 64 else "1" * 64,
            }
            with mock.patch.dict(
                mod._metadata.MASK_RECEIPTS,
                {"permanent_water": receipt},
                clear=False,
            ):
                with self.assertRaisesRegex(
                    mod.CemsMaskValueProfileError,
                    "SHA-256",
                ):
                    mod.profile_cems_mask_value_inventory(
                        path,
                        mask_kind="permanent_water",
                    )

    def test_unknown_mask_kind_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            mod.CemsMaskValueProfileError,
            "frozen #809/#816 receipt set",
        ):
            mod.profile_cems_mask_value_inventory(
                "unused.tif",
                mask_kind="caller-selected",
            )

    def test_cross_raster_comparison_requires_exact_grid(self) -> None:
        with mock.patch.object(
            mod._metadata,
            "compare_mask_profile_to_rp10",
            return_value={"grid_metadata_equal": False},
        ):
            with self.assertRaisesRegex(
                mod.CemsMaskValueProfileError,
                "requires exact accepted grid metadata",
            ):
                mod.require_exact_grid_before_comparison({}, {})

        accepted = {"grid_metadata_equal": True, "container_metadata_equal": False}
        with mock.patch.object(
            mod._metadata,
            "compare_mask_profile_to_rp10",
            return_value=accepted,
        ):
            self.assertEqual(
                mod.require_exact_grid_before_comparison({}, {}),
                accepted,
            )


if __name__ == "__main__":
    unittest.main()
