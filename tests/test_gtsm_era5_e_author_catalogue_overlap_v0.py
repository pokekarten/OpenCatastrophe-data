# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic GTSM original-to-author-catalogue join tests."""
from __future__ import annotations

import unittest

from scripts.gtsm_era5_e_author_catalogue_overlap_v0 import (
    AuthorCatalogueAuditBlocked,
    compare_original_to_author_catalogue,
    parse_author_catalogue,
)


def sample(rows: list[tuple[int, str, str, str]]) -> str:
    return "station_id\tstation_name\tlon\tlat\n" + "".join(
        f"{id_}\t{name}\t{lon}\t{lat}\n" for id_, name, lon, lat in rows
    )


class GtsmAuthorCatalogueOverlapTests(unittest.TestCase):
    def test_parse_author_catalogue_source_schema_and_coordinate_quantization(self):
        cat = parse_author_catalogue(sample([
            (0, "id_coast_glob_0001", "10.001", "52.000"),
            (2, "id_reg_grid_glob_0002", "-4.125", "51.003"),
        ]))
        self.assertEqual(cat[0], (10001, 52000, "coast_name_prefix"))
        self.assertEqual(cat[2], (-4125, 51003, "regular_grid_name_prefix"))

    def test_reconciled_exact_overlap(self):
        cat = parse_author_catalogue(sample([
            (0, "id_coast_glob_0001", "10.001", "52.000"),
            (2, "id_reg_grid_glob_0002", "-4.125", "51.003"),
            (3, "id_obs_xxx", "0.003", "0.001"),
        ]))
        report = compare_original_to_author_catalogue(
            [0, 2], [10001, -4125], [52000, 51003], cat, expected_rows=2
        )
        self.assertEqual(report["original_zenodo_statistical_rows"], 2)
        self.assertEqual(report["matching_native_station_ids"], 2)
        self.assertEqual(report["matching_ids_with_exact_quantized_coordinates"], 2)
        self.assertEqual(report["author_catalogue_ids_not_in_original_statistics"], 1)
        self.assertEqual(report["source_station_family_by_author_prefix"]["coast_name_prefix"], 1)
        self.assertEqual(report["author_catalogue_not_in_statistics_by_prefix"]["observation_name_prefix"], 1)
        self.assertEqual(report["author_catalogue_not_in_statistics_outside_occupied_original_id_span"], 1)
        self.assertEqual(report["integer_id_labels_absent_in_both_files_inside_original_span"], 1)
        self.assertEqual(sum(report["author_catalogue_name_family_by_prefix"].values()), 3)
        self.assertTrue(report["source_source_parent_catalogue_join_for_all_rows_proven"])
        self.assertFalse(report["commercial_rights_approved"])

    def test_rounding_tolerance_and_coordinate_conflict_are_not_conflated(self):
        cat = parse_author_catalogue(sample([
            (1, "id_coast_bay", "1.000", "2.000"),
            (2, "id_reg_grid_a", "1.000", "2.000"),
            (3, "id_coast_glob_x", "1.000", "2.000"),
        ]))
        report = compare_original_to_author_catalogue(
            [1, 2, 3], [1000, 1001, 1003], [2000, 2000, 2000], cat,
            expected_rows=3,
        )
        self.assertEqual(report["matching_ids_with_exact_quantized_coordinates"], 1)
        self.assertEqual(report["matching_ids_within_one_0p001_degree_packed_unit"], 1)
        self.assertEqual(report["matching_ids_with_coordinate_conflict_larger_than_0p001_degree"], 1)
        self.assertFalse(report["source_source_parent_catalogue_join_for_all_rows_proven"])

    def test_source_native_id_missing_in_author_file_counted(self):
        cat = parse_author_catalogue(sample([(9, "id_obs_a", "0.0", "0.0")]))
        report = compare_original_to_author_catalogue(
            [7, 9], [0, 0], [0, 0], cat, expected_rows=2,
        )
        self.assertEqual(report["original_native_station_ids_absent_in_author_catalogue"], 1)
        self.assertEqual(report["matching_native_station_ids"], 1)
        self.assertEqual(report["author_catalogue_ids_not_in_original_statistics"], 0)
        self.assertFalse(report["source_source_parent_catalogue_join_for_all_rows_proven"])

    def test_author_only_inside_and_outside_original_span_reconcile(self):
        cat = parse_author_catalogue(sample([
            (0, "id_coast_first", "0", "0"),
            (1, "id_reg_grid_extra", "1", "1"),
            (2, "id_obs_last", "2", "2"),
            (3, "id_coast_beyond", "3", "3"),
        ]))
        summary = compare_original_to_author_catalogue(
            [0, 2], [0, 2000], [0, 2000], cat, expected_rows=2,
        )
        self.assertEqual(
            summary["author_catalogue_not_in_statistics_inside_occupied_original_id_span"], 1
        )
        self.assertEqual(
            summary["author_catalogue_not_in_statistics_outside_occupied_original_id_span"], 1
        )
        self.assertEqual(summary["author_catalogue_not_in_statistics_by_prefix"]["coast_name_prefix"], 1)
        self.assertEqual(summary["author_catalogue_not_in_statistics_by_prefix"]["regular_grid_name_prefix"], 1)
        self.assertEqual(sum(summary["author_catalogue_not_in_statistics_by_prefix"].values()), 2)
        self.assertEqual(summary["integer_id_labels_absent_in_both_files_inside_original_span"], 0)

    def test_neither_original_nor_author_occupies_some_native_id_labels(self):
        cat = parse_author_catalogue(sample([
            (0, "id_coast_a", "0", "0"),
            (4, "id_reg_grid_b", "4", "4"),
        ]))
        result = compare_original_to_author_catalogue(
            [0, 4], [0, 4000], [0, 4000], cat, expected_rows=2,
        )
        self.assertEqual(result["original_native_id_span_width"], 5)
        self.assertEqual(
            result["integer_id_labels_absent_in_both_files_inside_original_span"], 3
        )
        self.assertFalse(result["parent_paper_44734_model_positions_same_catalogue_release_proven"])

    def test_header_and_duplicate_ids_rejected(self):
        bad_header = "station\tname\tx\ty\n1\tid_coast\t1.1\t2.2\n"
        with self.assertRaises(AuthorCatalogueAuditBlocked):
            parse_author_catalogue(bad_header)
        with self.assertRaises(AuthorCatalogueAuditBlocked):
            parse_author_catalogue(sample([
                (1, "id_coast_a", "1", "1"),
                (1, "id_coast_b", "2", "2"),
            ]))

    def test_non_numeric_or_outside_earth_coordinates_rejected(self):
        for lon, lat in (("nan", "2"), ("nanometre", "1"),
                         ("181", "0"), ("1", "91"), ("", "0")):
            with self.subTest(lon=lon, lat=lat), self.assertRaises(AuthorCatalogueAuditBlocked):
                parse_author_catalogue(sample([(2, "id_coast_a", lon, lat)]))

    def test_non_uint16_ids_and_oversized_names_rejected(self):
        for row in ("-1", "65536", "a", ""):
            with self.subTest(row=row), self.assertRaises(AuthorCatalogueAuditBlocked):
                parse_author_catalogue(
                    "station_id\tstation_name\tlon\tlat\n"
                    + f"{row}\tid_coast_a\t1\t2\n"
                )
        with self.assertRaises(AuthorCatalogueAuditBlocked):
            parse_author_catalogue(sample([(1, "x" * 257, "1", "2")]))

    def test_row_budget_bounded_and_empty_blocked(self):
        with self.assertRaises(AuthorCatalogueAuditBlocked):
            parse_author_catalogue(sample([(0, "id_coast_a", "0", "0"),
                                           (1, "id_coast_b", "0", "0")]), limit=1)
        with self.assertRaises(AuthorCatalogueAuditBlocked):
            parse_author_catalogue("station_id\tstation_name\tlon\tlat\n")

    def test_statistical_row_length_and_duplicate_rejected(self):
        cat = parse_author_catalogue(sample([(0, "id_coast", "0", "0")]))
        with self.assertRaises(AuthorCatalogueAuditBlocked):
            compare_original_to_author_catalogue(
                [0], [0], [], cat, expected_rows=1
            )
        with self.assertRaises(AuthorCatalogueAuditBlocked):
            compare_original_to_author_catalogue(
                [0, 0], [0, 0], [0, 0], cat, expected_rows=2
            )

    def test_no_raw_ids_or_positions_in_report(self):
        cat = parse_author_catalogue(sample([(3, "id_obs_a", "10", "30")]))
        result = compare_original_to_author_catalogue(
            [3], [10000], [30000], cat, expected_rows=1
        )
        self.assertFalse(result["source_original_rows_or_provider_coordinates_emitted"])
        self.assertFalse(result["source_original_data_persisted"])
        self.assertFalse(result["cat_model_admitted"])
        self.assertFalse(result["vertical_datum_alignment_proven"])
        self.assertNotIn("station_ids", result)
        self.assertNotIn("locations", result)

    def test_boolean_station_id_and_coordinate_blocked(self):
        cat = parse_author_catalogue(sample([(0, "id_coast", "0", "0")]))
        for ids, lons, lats in (([True], [0], [0]), ([0], [True], [0]), ([0], [0], [True])):
            with self.assertRaises(AuthorCatalogueAuditBlocked):
                compare_original_to_author_catalogue(
                    ids, lons, lats, cat, expected_rows=1
                )


if __name__ == "__main__":
    unittest.main()
