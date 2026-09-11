# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import struct
from types import SimpleNamespace
import unittest

from scripts import diagnose_cems_spurious_falsifiers as mod


class CemsSpuriousFalsifierDiagnosticTests(unittest.TestCase):
    def _transform(self, *, west: float = 10.0, north: float = 50.0):
        return SimpleNamespace(
            a=0.01,
            b=0.0,
            c=west,
            d=0.0,
            e=-0.01,
            f=north,
        )

    def _distance(self, offset: float) -> float:
        return mod.DISTANCE_THRESHOLD_METRES + offset

    def test_order_invariance_and_exact_binary_digest(self) -> None:
        records = [
            (4, 2, self._distance(40.0)),
            (1, 7, self._distance(10.0)),
            (1, 3, self._distance(20.0)),
        ]
        result = mod.characterize_falsifiers(
            records,
            transform=self._transform(),
            raster_height=10,
            raster_width=10,
            max_row_offset=1,
            max_col_offset=1,
        )
        reversed_result = mod.characterize_falsifiers(
            list(reversed(records)),
            transform=self._transform(),
            raster_height=10,
            raster_width=10,
            max_row_offset=1,
            max_col_offset=1,
        )

        digest = hashlib.sha256()
        for row, column, distance in sorted(records):
            digest.update(struct.pack(">qqd", row, column, distance))

        self.assertEqual(result, reversed_result)
        self.assertEqual(result["falsifier_digest_sha256"], digest.hexdigest())
        self.assertEqual(
            result["falsifier_digest_encoding"],
            "big_endian_struct_>qqd_row_col_nearest_distance_metres",
        )
        self.assertEqual(
            [(item["row"], item["column"]) for item in result["first_16_falsifiers"]],
            [(1, 3), (1, 7), (4, 2)],
        )

    def test_translated_grid_changes_only_geographic_centres_not_digest(self) -> None:
        records = [
            (2, 2, self._distance(50.0)),
            (4, 5, self._distance(80.0)),
        ]
        original = mod.characterize_falsifiers(
            records,
            transform=self._transform(west=10.0, north=50.0),
            raster_height=10,
            raster_width=10,
            max_row_offset=1,
            max_col_offset=1,
        )
        translated = mod.characterize_falsifiers(
            records,
            transform=self._transform(west=20.0, north=40.0),
            raster_height=10,
            raster_width=10,
            max_row_offset=1,
            max_col_offset=1,
        )

        self.assertEqual(
            original["falsifier_digest_sha256"],
            translated["falsifier_digest_sha256"],
        )
        self.assertEqual(original["components_4_neighbour"], translated["components_4_neighbour"])
        self.assertAlmostEqual(
            translated["cell_centre_bounds"]["min_longitude"]
            - original["cell_centre_bounds"]["min_longitude"],
            10.0,
        )
        self.assertAlmostEqual(
            translated["cell_centre_bounds"]["min_latitude"]
            - original["cell_centre_bounds"]["min_latitude"],
            -10.0,
        )

    def test_four_and_eight_neighbour_components_remain_distinct(self) -> None:
        cells = [
            (1, 1, self._distance(10.0)),
            (1, 2, self._distance(20.0)),
            (5, 5, self._distance(30.0)),
            (6, 6, self._distance(40.0)),
        ]
        result = mod.characterize_falsifiers(
            cells,
            transform=self._transform(),
            raster_height=12,
            raster_width=12,
            max_row_offset=1,
            max_col_offset=1,
        )

        self.assertEqual(result["components_4_neighbour"]["component_count"], 3)
        self.assertEqual(result["components_4_neighbour"]["largest_10_sizes"], [2, 1, 1])
        self.assertEqual(result["components_4_neighbour"]["median_size"], 1.0)
        self.assertEqual(result["components_8_neighbour"]["component_count"], 2)
        self.assertEqual(result["components_8_neighbour"]["largest_10_sizes"], [2, 2])
        self.assertEqual(result["components_8_neighbour"]["median_size"], 2.0)

    def test_edge_envelope_is_descriptive_and_reconciles(self) -> None:
        records = [
            (0, 5, self._distance(10.0)),
            (5, 0, self._distance(20.0)),
            (8, 5, self._distance(30.0)),
            (5, 9, self._distance(40.0)),
            (5, 5, self._distance(50.0)),
        ]
        result = mod.characterize_falsifiers(
            records,
            transform=self._transform(),
            raster_height=10,
            raster_width=12,
            max_row_offset=2,
            max_col_offset=3,
        )

        self.assertEqual(result["edge_envelope_falsifier_cells"], 4)
        self.assertEqual(result["interior_falsifier_cells"], 1)
        self.assertEqual(
            result["edge_envelope_falsifier_cells"] + result["interior_falsifier_cells"],
            result["falsifier_count"],
        )
        self.assertEqual(
            result["raster_cell_bbox"],
            {"min_row": 0, "max_row": 8, "min_column": 0, "max_column": 9},
        )

    def test_nearest_rank_distance_summary_is_fixed_without_interpolation(self) -> None:
        distances = [2200.0, 2300.0, 2400.0, 2500.0, 2600.0]
        records = [(index + 1, 2, distance) for index, distance in enumerate(distances)]
        result = mod.characterize_falsifiers(
            records,
            transform=self._transform(),
            raster_height=10,
            raster_width=10,
            max_row_offset=1,
            max_col_offset=1,
        )
        summary = result["nearest_distance_summary_metres"]

        self.assertEqual(summary["minimum"], 2200.0)
        self.assertEqual(summary["q25_nearest_rank"], 2300.0)
        self.assertEqual(summary["median_nearest_rank"], 2400.0)
        self.assertEqual(summary["q75_nearest_rank"], 2500.0)
        self.assertEqual(summary["q95_nearest_rank"], 2600.0)
        self.assertEqual(summary["q99_nearest_rank"], 2600.0)
        self.assertEqual(summary["maximum"], 2600.0)

    def test_empty_and_one_cell_cases_are_bounded(self) -> None:
        empty = mod.characterize_falsifiers(
            [],
            transform=self._transform(),
            raster_height=10,
            raster_width=10,
            max_row_offset=1,
            max_col_offset=1,
            expected_falsifier_count=0,
        )
        self.assertEqual(empty["falsifier_count"], 0)
        self.assertEqual(
            empty["falsifier_digest_sha256"], hashlib.sha256(b"").hexdigest()
        )
        self.assertIsNone(empty["raster_cell_bbox"])
        self.assertIsNone(empty["cell_centre_bounds"])
        self.assertIsNone(empty["nearest_distance_summary_metres"])
        self.assertEqual(empty["first_16_falsifiers"], [])
        self.assertEqual(empty["components_4_neighbour"]["component_count"], 0)

        one = mod.characterize_falsifiers(
            [(4, 4, self._distance(1.0))],
            transform=self._transform(),
            raster_height=10,
            raster_width=10,
            max_row_offset=1,
            max_col_offset=1,
            expected_falsifier_count=1,
        )
        self.assertEqual(one["components_4_neighbour"]["component_count"], 1)
        self.assertEqual(one["components_8_neighbour"]["largest_10_sizes"], [1])
        self.assertEqual(one["first_16_falsifiers"][0]["row"], 4)
        self.assertEqual(one["first_16_falsifiers"][0]["column"], 4)

    def test_authority_ceiling_and_stage_d_disposition_are_immutable(self) -> None:
        result = mod.characterize_falsifiers(
            [(4, 4, self._distance(1.0))],
            transform=self._transform(),
            raster_height=10,
            raster_width=10,
            max_row_offset=1,
            max_col_offset=1,
        )

        self.assertEqual(result["stage_d_verdict"], mod.STAGE_D_VERDICT)
        self.assertEqual(result["stage_d_disposition"], mod.STAGE_D_DISPOSITION)
        self.assertTrue(result["diagnostic_only"])
        self.assertFalse(result["small_channel_filter_reconstructed"])
        self.assertFalse(result["mask_value_semantics_verified"])
        self.assertFalse(result["per_cell_scientific_correctness_verified"])
        self.assertFalse(result["benchmark_use_authorized"])
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["external_bytes_persisted"])

    def test_invalid_or_relabelled_falsifier_records_fail_closed(self) -> None:
        with self.assertRaisesRegex(mod.CemsSpuriousFalsifierDiagnosticError, "duplicate"):
            mod.characterize_falsifiers(
                [
                    (4, 4, self._distance(1.0)),
                    (4, 4, self._distance(2.0)),
                ],
                transform=self._transform(),
                raster_height=10,
                raster_width=10,
                max_row_offset=1,
                max_col_offset=1,
            )

        with self.assertRaisesRegex(mod.CemsSpuriousFalsifierDiagnosticError, "beyond"):
            mod.characterize_falsifiers(
                [(4, 4, mod.DISTANCE_THRESHOLD_METRES)],
                transform=self._transform(),
                raster_height=10,
                raster_width=10,
                max_row_offset=1,
                max_col_offset=1,
            )

        with self.assertRaisesRegex(mod.CemsSpuriousFalsifierDiagnosticError, "drifted"):
            mod.characterize_falsifiers(
                [(4, 4, self._distance(1.0))],
                transform=self._transform(),
                raster_height=10,
                raster_width=10,
                max_row_offset=1,
                max_col_offset=1,
                expected_falsifier_count=2,
            )


if __name__ == "__main__":
    unittest.main()
