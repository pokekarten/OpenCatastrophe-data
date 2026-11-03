# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic GTSM original CI-size, return year and station-prefix QA."""
from __future__ import annotations

import math
import unittest

from scripts.gtsm_era5_e_return_band_severity_v0 import (
    OriginalBandSeverityBlocked,
    audit_return_band_severity_by_family_and_year,
    bootstrap_percentiles_from_nominal_alpha,
    BUCKETS,
)


def good_matrix(n):
    center = [[float(j) for j in range(8)] for _ in range(n)]
    low = [[x - 0.5 for x in row] for row in center]
    high = [[x + 0.5 for x in row] for row in center]
    return center, low, high


def catalogue(ids, families):
    return {key: (0, 0, family) for key, family in zip(ids, families)}


class HistoricalGtsmBootstrapAndBandSeverityTests(unittest.TestCase):
    def test_historical_source_alpha_95_is_2p5_to_97p5_and_not_5_to_95(self):
        self.assertAlmostEqual(bootstrap_percentiles_from_nominal_alpha(0.95)[0], 2.5)
        self.assertAlmostEqual(bootstrap_percentiles_from_nominal_alpha(0.95)[1], 97.5)
        self.assertAlmostEqual(bootstrap_percentiles_from_nominal_alpha(0.90)[0], 5.0)
        self.assertAlmostEqual(bootstrap_percentiles_from_nominal_alpha(0.90)[1], 95.0)
        self.assertNotEqual(bootstrap_percentiles_from_nominal_alpha(0.95), (5.0, 95.0))

    def test_illegal_nominal_alpha_rejected(self):
        for x in (-1, 0, 1, 2, None, True, math.nan, math.inf, "0.95"):
            with self.subTest(x=str(x)), self.assertRaises(OriginalBandSeverityBlocked):
                bootstrap_percentiles_from_nominal_alpha(x)

    def test_per_year_family_and_severity_exact_reconciliation(self):
        ids=[1,2,3]
        m=good_matrix(3)
        best,lower,upper=m
        upper[0][0]=best[0][0]-0.005
        upper[0][1]=best[0][1]-0.05
        upper[0][2]=best[0][2]-0.5
        upper[0][3]=best[0][3]-1.5
        lower[0][3]=best[0][3]-2.5  # valid interval, yet bestfit exceeds upper by 1.5m
        lower[1][4]=best[1][4]+0.05
        best[2][5]=math.nan
        report=audit_return_band_severity_by_family_and_year(
            ids,m,catalogue(ids,[
                "coast_name_prefix","regular_grid_name_prefix",
                "observation_name_prefix"]),expected_rows=3,
        )
        by=report["by_author_name_family_and_return_year"]
        severity=report["band_exceedance_size_categories_m"]
        self.assertEqual([x["above_reported_upper_cells"] for x in by["coast_name_prefix"]],
                         [1,1,1,1,0,0,0,0])
        self.assertEqual(by["regular_grid_name_prefix"][4]["below_reported_lower_cells"],1)
        self.assertEqual(by["observation_name_prefix"][5]["missing_or_nonfinite_triplets"],1)
        self.assertEqual(list(severity["coast_name_prefix"]["above_reported_upper"].values()),[1,1,1,1])
        self.assertEqual(severity["regular_grid_name_prefix"]["below_reported_lower"][BUCKETS[1]],1)
        self.assertTrue(report["historical_pyextremes_random_state_not_pinned_in_producer_script"])
        self.assertTrue(report["native_5perc_95perc_labels_not_reinterpreted"])
        self.assertFalse(report["individual_source_locations_or_levels_emitted"])
        self.assertFalse(report["cat_model_admitted"])

    def test_exact_upper_equality_and_tolerance_are_not_false_crossings(self):
        ids=[7]
        m=good_matrix(1)
        best,lo,hi=m
        hi[0][0]=best[0][0]
        hi[0][1]=best[0][1]-1e-10
        lo[0][2]=best[0][2]+1e-10
        result=audit_return_band_severity_by_family_and_year(
            ids,m,catalogue(ids,["coast_name_prefix"]),expected_rows=1
        )
        self.assertEqual(sum(x["above_reported_upper_cells"] for x in
                             result["by_author_name_family_and_return_year"]["coast_name_prefix"]),0)
        self.assertEqual(sum(x["below_reported_lower_cells"] for x in
                             result["by_author_name_family_and_return_year"]["coast_name_prefix"]),0)

    def test_missing_and_duplicate_source_ids_block(self):
        for ids, author in (
            ([1,1],catalogue([1],["coast_name_prefix"])),
            ([1,2],catalogue([2],["coast_name_prefix"])),
            ([True],catalogue([1],["coast_name_prefix"])),
        ):
            with self.subTest(ids=ids), self.assertRaises(OriginalBandSeverityBlocked):
                audit_return_band_severity_by_family_and_year(
                    ids,good_matrix(len(ids)),author,expected_rows=len(ids)
                )

    def test_inverted_published_interval_fails_closed(self):
        m=good_matrix(1)
        m[1][0][0]=3.0
        m[2][0][0]=1.0
        with self.assertRaises(OriginalBandSeverityBlocked):
            audit_return_band_severity_by_family_and_year(
                [1],m,catalogue([1],["coast_name_prefix"]),expected_rows=1
            )

    def test_invalid_matrices_fail_closed_without_source_value_echo(self):
        m=good_matrix(1)
        m[0][0][0]="bad"
        with self.assertRaises(OriginalBandSeverityBlocked):
            audit_return_band_severity_by_family_and_year(
                [1],m,catalogue([1],["coast_name_prefix"]),expected_rows=1
            )

    def test_no_crossing_no_missingness_is_zero_everywhere(self):
        ids=[1]
        report=audit_return_band_severity_by_family_and_year(
            ids,good_matrix(1),catalogue(ids,["other_name_prefix"]),expected_rows=1
        )
        for family, periods in report["by_author_name_family_and_return_year"].items():
            self.assertEqual(len(periods),8)
            self.assertEqual(sum(x["above_reported_upper_cells"]+
                                 x["below_reported_lower_cells"]+
                                 x["missing_or_nonfinite_triplets"] for x in periods),0)
            for direction in report["band_exceedance_size_categories_m"][family]:
                self.assertEqual(sum(report["band_exceedance_size_categories_m"][family][direction].values()),0)


if __name__=="__main__":
    unittest.main()
