# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

DEPS_AVAILABLE = all(
    importlib.util.find_spec(name) is not None
    for name in ("numpy", "pyproj", "rasterio")
)

if DEPS_AVAILABLE:
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    from scripts import challenge_cems_spurious_depth_support as mod


@unittest.skipUnless(
    DEPS_AVAILABLE,
    "requires requirements-cems-mask-support-challenge.txt",
)
class CemsSpuriousDepthSupportTests(unittest.TestCase):
    def _write_raster(
        self,
        path: Path,
        data,
        *,
        transform=None,
        crs: str = "EPSG:4326",
    ) -> None:
        transform = transform or from_origin(10.0, 50.0, 0.01, 0.01)
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=data.shape[1],
            height=data.shape[0],
            count=1,
            dtype="float32",
            crs=crs,
            transform=transform,
            nodata=-9999.0,
        ) as dataset:
            dataset.write(data.astype("float32"), 1)

    def _run(self, mask, rp10, *, mask_transform=None, rp10_transform=None):
        with tempfile.TemporaryDirectory() as directory:
            mask_path = Path(directory) / "mask.tif"
            rp10_path = Path(directory) / "rp10.tif"
            self._write_raster(mask_path, mask, transform=mask_transform)
            self._write_raster(rp10_path, rp10, transform=rp10_transform)
            with rasterio.open(mask_path) as mask_dataset, rasterio.open(rp10_path) as rp10_dataset:
                return mod.challenge_spurious_support(mask_dataset, rp10_dataset)

    def _blank(self):
        return np.full((8, 8), np.nan, dtype="float32")

    def test_same_cell_seed_is_not_falsified_and_keeps_authority_closed(self) -> None:
        mask = self._blank()
        rp10 = self._blank()
        mask[3, 3] = 1.0
        rp10[3, 3] = 10.1

        result = self._run(mask, rp10)

        self.assertEqual(
            result["verdict"],
            "NOT_FALSIFIED_BY_CURRENT_RP10_NECESSARY_CONDITION",
        )
        self.assertEqual(result["candidate_support_cells"], 1)
        self.assertEqual(result["rp10_seed_cells"], 1)
        self.assertEqual(result["same_cell_candidate_seed_overlap_cells"], 1)
        self.assertEqual(result["candidate_with_seed_within_threshold_cells"], 1)
        self.assertEqual(result["candidate_farther_than_threshold_cells"], 0)
        self.assertEqual(result["distance_model"], "WGS84_GEOD")
        self.assertGreater(result["distance_threshold_metres"], 2_000.0)
        self.assertFalse(result["small_channel_filter_reconstructed"])
        self.assertFalse(result["mask_value_semantics_verified"])
        self.assertFalse(result["per_cell_scientific_correctness_verified"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["external_bytes_persisted"])

    def test_nearby_seed_is_covered_by_exact_geodesic_distance(self) -> None:
        mask = self._blank()
        rp10 = self._blank()
        mask[3, 3] = 1.0
        rp10[3, 5] = 12.0

        result = self._run(mask, rp10)

        self.assertEqual(
            result["verdict"],
            "NOT_FALSIFIED_BY_CURRENT_RP10_NECESSARY_CONDITION",
        )
        self.assertEqual(result["same_cell_candidate_seed_overlap_cells"], 0)
        self.assertEqual(result["candidate_with_seed_within_threshold_cells"], 1)
        self.assertEqual(result["candidate_farther_than_threshold_cells"], 0)

    def test_farther_candidate_fails_necessary_condition(self) -> None:
        mask = self._blank()
        rp10 = self._blank()
        mask[3, 0] = 1.0
        rp10[3, 7] = 12.0

        result = self._run(mask, rp10)

        self.assertEqual(result["verdict"], "CURRENT_RP10_NECESSARY_CONDITION_FAIL")
        self.assertEqual(result["candidate_support_cells"], 1)
        self.assertEqual(result["rp10_seed_cells"], 1)
        self.assertEqual(result["candidate_with_seed_within_threshold_cells"], 0)
        self.assertEqual(result["candidate_farther_than_threshold_cells"], 1)

    def test_rp10_threshold_is_strictly_greater_than_ten_metres(self) -> None:
        mask = self._blank()
        rp10 = self._blank()
        mask[3, 3] = 1.0
        rp10[3, 3] = 10.0

        result = self._run(mask, rp10)

        self.assertEqual(result["rp10_seed_cells"], 0)
        self.assertEqual(result["verdict"], "CURRENT_RP10_NECESSARY_CONDITION_FAIL")
        self.assertEqual(result["candidate_farther_than_threshold_cells"], 1)

    def test_empty_candidate_support_fails_closed(self) -> None:
        mask = self._blank()
        rp10 = self._blank()
        rp10[3, 3] = 12.0

        with self.assertRaisesRegex(
            mod.CemsSpuriousSupportChallengeError,
            "candidate support is empty",
        ):
            self._run(mask, rp10)

    def test_candidate_finite_class_drift_fails_closed(self) -> None:
        mask = self._blank()
        rp10 = self._blank()
        mask[3, 3] = 0.0
        rp10[3, 3] = 12.0

        with self.assertRaisesRegex(
            mod.CemsSpuriousSupportChallengeError,
            "finite class drifted",
        ):
            self._run(mask, rp10)

    def test_infinity_contamination_fails_closed(self) -> None:
        mask = self._blank()
        rp10 = self._blank()
        mask[3, 3] = np.inf
        rp10[3, 3] = 12.0

        with self.assertRaisesRegex(
            mod.CemsSpuriousSupportChallengeError,
            "contains infinity",
        ):
            self._run(mask, rp10)

    def test_grid_mismatch_fails_before_distance_result(self) -> None:
        mask = self._blank()
        rp10 = self._blank()
        mask[3, 3] = 1.0
        rp10[3, 3] = 12.0
        shifted = from_origin(10.1, 50.0, 0.01, 0.01)

        with self.assertRaisesRegex(
            mod.CemsSpuriousSupportChallengeError,
            "affine transforms differ",
        ):
            self._run(mask, rp10, rp10_transform=shifted)


if __name__ == "__main__":
    unittest.main()
