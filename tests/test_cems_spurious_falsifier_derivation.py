# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import math
import unittest

DEPS_AVAILABLE = all(
    importlib.util.find_spec(name) is not None
    for name in ("numpy", "pyproj", "rasterio")
)

if DEPS_AVAILABLE:
    import numpy as np
    from pyproj import Geod
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin

    from scripts import challenge_cems_spurious_depth_support as stage_d
    from scripts import derive_cems_spurious_falsifiers as mod


@unittest.skipUnless(
    DEPS_AVAILABLE,
    "requires requirements-cems-mask-support-challenge.txt",
)
class CemsSpuriousFalsifierDerivationTests(unittest.TestCase):
    def _geotiff(self, data, *, dtype: str, transform=None) -> MemoryFile:
        if transform is None:
            transform = from_origin(10.0, 50.0, 0.01, 0.01)
        memory = MemoryFile()
        with memory.open(
            driver="GTiff",
            width=data.shape[1],
            height=data.shape[0],
            count=1,
            dtype=dtype,
            crs="EPSG:4326",
            transform=transform,
            nodata=-9999.0,
        ) as dataset:
            dataset.write(data.astype(dtype), 1)
        return memory

    def _blank(self, shape=(64, 64)):
        return np.full(shape, np.nan, dtype="float64")

    def _exhaustive_distance(
        self,
        candidate_row: int,
        candidate_column: int,
        seed_rows: dict[int, np.ndarray],
        transform,
    ) -> float:
        geod = Geod(ellps="WGS84")
        candidate_longitude, candidate_latitude = stage_d._cell_centre(
            transform, candidate_row, candidate_column
        )
        best = math.inf
        for seed_row, seed_columns in seed_rows.items():
            for seed_column in seed_columns:
                seed_longitude, seed_latitude = stage_d._cell_centre(
                    transform, seed_row, int(seed_column)
                )
                _az1, _az2, distance = geod.inv(
                    candidate_longitude,
                    candidate_latitude,
                    seed_longitude,
                    seed_latitude,
                )
                best = min(best, float(distance))
        return best

    def test_global_nearest_matches_exhaustive_pairwise_reference(self) -> None:
        rng = np.random.default_rng(835)
        transform = from_origin(-5.0, 55.0, 0.01, 0.01)
        seed_rows: dict[int, np.ndarray] = {}
        for row in (1, 3, 9, 17, 31, 46, 58):
            seed_rows[row] = np.array(
                sorted(rng.choice(64, size=5, replace=False).tolist()),
                dtype=np.int64,
            )
        seed_row_numbers = tuple(seed_rows)
        geod = Geod(ellps="WGS84")

        for candidate_row, candidate_column in (
            (0, 0),
            (2, 63),
            (8, 17),
            (16, 32),
            (30, 4),
            (45, 61),
            (63, 28),
        ):
            with self.subTest(row=candidate_row, column=candidate_column):
                observed = mod._global_nearest_seed_distance(
                    candidate_row,
                    candidate_column,
                    seed_rows,
                    seed_row_numbers,
                    transform=transform,
                    geod=geod,
                )
                expected = self._exhaustive_distance(
                    candidate_row,
                    candidate_column,
                    seed_rows,
                    transform,
                )
                self.assertAlmostEqual(observed, expected, places=9)

    def test_global_nearest_can_lie_outside_stage_d_row_envelope(self) -> None:
        transform = from_origin(-24.54208333, 71.13375, 1.0 / 1200.0, 1.0 / 1200.0)
        candidate_row = 5
        candidate_column = 20
        seed_row = candidate_row + 30
        seed_rows = {seed_row: np.array([candidate_column], dtype=np.int64)}
        geod = Geod(ellps="WGS84")

        observed = mod._global_nearest_seed_distance(
            candidate_row,
            candidate_column,
            seed_rows,
            tuple(seed_rows),
            transform=transform,
            geod=geod,
        )
        expected = self._exhaustive_distance(
            candidate_row,
            candidate_column,
            seed_rows,
            transform,
        )

        self.assertGreater(30, 23)
        self.assertGreater(observed, 2123.5739672579953)
        self.assertAlmostEqual(observed, expected, places=9)

    def test_safe_latitude_pruning_does_not_use_longitude_assumptions(self) -> None:
        transform = from_origin(-20.0, 60.0, 0.02, 0.02)
        seed_rows = {
            9: np.array([0, 63], dtype=np.int64),
            10: np.array([1, 62], dtype=np.int64),
            11: np.array([32], dtype=np.int64),
            55: np.array([31], dtype=np.int64),
        }
        geod = Geod(ellps="WGS84")
        observed = mod._global_nearest_seed_distance(
            10,
            32,
            seed_rows,
            tuple(seed_rows),
            transform=transform,
            geod=geod,
        )
        expected = self._exhaustive_distance(10, 32, seed_rows, transform)
        self.assertAlmostEqual(observed, expected, places=9)

    def test_derive_reuses_stage_d_falsifier_decision_then_bounds_output(self) -> None:
        mask = self._blank((16, 16))
        rp10 = self._blank((16, 16)).astype("float32")
        mask[5, 5] = 1.0
        mask[5, 15] = 1.0
        rp10[5, 5] = 12.0
        transform = from_origin(10.0, 50.0, 0.01, 0.01)

        with self._geotiff(mask, dtype="float64", transform=transform) as mask_memory, self._geotiff(
            rp10, dtype="float32", transform=transform
        ) as rp10_memory:
            with mask_memory.open() as mask_dataset, rp10_memory.open() as rp10_dataset:
                stage_d_result = stage_d.challenge_spurious_support(
                    mask_dataset, rp10_dataset
                )
                result = mod.derive_and_characterize_falsifiers(
                    mask_dataset,
                    rp10_dataset,
                    expected_candidate_support_cells=2,
                    expected_rp10_seed_cells=1,
                    expected_falsifier_cells=1,
                )

        self.assertEqual(stage_d_result["candidate_support_cells"], 2)
        self.assertEqual(
            stage_d_result["candidate_farther_than_threshold_cells"],
            result["candidate_farther_than_threshold_cells"],
        )
        self.assertEqual(result["candidate_farther_than_threshold_cells"], 1)
        self.assertEqual(result["diagnostic"]["falsifier_count"], 1)
        self.assertGreater(
            result["diagnostic"]["first_16_falsifiers"][0]["nearest_distance_metres"],
            result["distance_threshold_metres"],
        )
        self.assertTrue(result["diagnostic_only"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["publication_authorized"])

    def test_derive_finds_global_nearest_beyond_stage_d_decision_envelope(self) -> None:
        mask = self._blank((64, 64))
        rp10 = self._blank((64, 64)).astype("float32")
        mask[5, 20] = 1.0
        rp10[35, 20] = 12.0
        transform = from_origin(-24.54208333, 71.13375, 1.0 / 1200.0, 1.0 / 1200.0)

        with self._geotiff(mask, dtype="float64", transform=transform) as mask_memory, self._geotiff(
            rp10, dtype="float32", transform=transform
        ) as rp10_memory:
            with mask_memory.open() as mask_dataset, rp10_memory.open() as rp10_dataset:
                result = mod.derive_and_characterize_falsifiers(
                    mask_dataset,
                    rp10_dataset,
                    expected_candidate_support_cells=1,
                    expected_rp10_seed_cells=1,
                    expected_falsifier_cells=1,
                )

        self.assertLess(result["max_row_offset"], 30)
        nearest = result["diagnostic"]["first_16_falsifiers"][0][
            "nearest_distance_metres"
        ]
        self.assertGreater(nearest, result["distance_threshold_metres"])
        expected = self._exhaustive_distance(
            5,
            20,
            {35: np.array([20], dtype=np.int64)},
            transform,
        )
        self.assertAlmostEqual(nearest, expected, places=9)

    def test_preregistered_count_drift_fails_closed(self) -> None:
        mask = self._blank((16, 16))
        rp10 = self._blank((16, 16)).astype("float32")
        mask[5, 15] = 1.0
        rp10[5, 0] = 12.0

        with self._geotiff(mask, dtype="float64") as mask_memory, self._geotiff(
            rp10, dtype="float32"
        ) as rp10_memory:
            with mask_memory.open() as mask_dataset, rp10_memory.open() as rp10_dataset:
                with self.assertRaisesRegex(
                    mod.CemsSpuriousFalsifierDerivationError,
                    "candidate support count drifted",
                ):
                    mod.derive_and_characterize_falsifiers(
                        mask_dataset,
                        rp10_dataset,
                        expected_candidate_support_cells=2,
                        expected_rp10_seed_cells=1,
                        expected_falsifier_cells=1,
                    )

    def test_empty_seed_support_fails_closed(self) -> None:
        mask = self._blank((8, 8))
        rp10 = self._blank((8, 8)).astype("float32")
        mask[3, 3] = 1.0

        with self._geotiff(mask, dtype="float64") as mask_memory, self._geotiff(
            rp10, dtype="float32"
        ) as rp10_memory:
            with mask_memory.open() as mask_dataset, rp10_memory.open() as rp10_dataset:
                with self.assertRaisesRegex(
                    mod.CemsSpuriousFalsifierDerivationError,
                    "no current >10 m seed",
                ):
                    mod.derive_and_characterize_falsifiers(mask_dataset, rp10_dataset)


if __name__ == "__main__":
    unittest.main()
