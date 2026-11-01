# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only tests: exact building ID matching must be fail-closed."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.building_id_enrichment_v0 import BuildingEnrichmentError, build_report

ROOT = Path(__file__).resolve().parents[1]
BASE_COLS = ["building_id", "construction_year", "roof_type", "floors_above_ground"]
SUP_COLS = [
    "source_record_id", "building_id", "record_kind", "observation_kind",
    "construction_year", "roof_type", "floors_above_ground",
]


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


class BuildingIdEnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name) / "base.csv"
        self.supp = Path(self.tmp.name) / "supp.csv"

    def report(self):
        return build_report(
            self.base, self.supp,
            base_source_id="synthetic.baseline",
            supplement_source_id="synthetic.registry",
        )

    def test_direct_measured_fill_and_existing_conflict_are_separate(self):
        write_csv(self.base, BASE_COLS, [
            ["B-1", "", "", "2"],
            ["B-2", "1970", "flat", "3"],
            ["B-3", "", "", ""],
        ])
        write_csv(self.supp, SUP_COLS, [
            ["R-1", "B-1", "building", "official_record", "1980", "gable", "2"],
            ["R-2", "B-2", "building", "measured", "1971", "FLAT", "4"],
            ["R-3", "B-4", "building", "official_record", "1965", "flat", "1"],
        ])
        result = self.report()
        counts = result["building_counts"]
        self.assertEqual(counts["exact_unique_matches"], 2)
        self.assertEqual(counts["unmatched_base"], 1)
        self.assertEqual(counts["source_building_records_without_base_match"], 1)
        self.assertEqual(result["attributes"]["construction_year"]["proposed_observed_fill"], 1)
        self.assertEqual(result["attributes"]["construction_year"]["conflict"], 1)
        self.assertEqual(result["attributes"]["roof_type"]["agreement"], 1)
        self.assertEqual(result["attributes"]["floors_above_ground"]["agreement"], 1)
        self.assertEqual(result["attributes"]["floors_above_ground"]["conflict"], 1)
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["rights_approved_for_model_input"])
        self.assertFalse(result["source_independence_established"])

    def test_address_dwelling_parcel_and_certificate_rows_are_never_building_matches(self):
        write_csv(self.base, BASE_COLS, [["B-1", "", "", ""]])
        write_csv(self.supp, SUP_COLS, [
            [f"S-{i}", "B-1", k, "official_record", "1980", "flat", "2"]
            for i, k in enumerate(("address", "dwelling", "parcel", "certificate"), 1)
        ])
        result = self.report()
        self.assertEqual(result["building_counts"]["nonbuilding_records_skipped"], 4)
        self.assertEqual(result["building_counts"]["exact_unique_matches"], 0)
        self.assertEqual(result["building_counts"]["unmatched_base"], 1)

    def test_ambiguous_one_to_many_is_not_greedy_joined(self):
        write_csv(self.base, BASE_COLS, [["B-1", "", "", ""]])
        write_csv(self.supp, SUP_COLS, [
            ["S-1", "B-1", "building", "official_record", "1981", "flat", "2"],
            ["S-2", "B-1", "building", "official_record", "1982", "gable", "3"],
        ])
        result = self.report()
        self.assertEqual(result["building_counts"]["ambiguous_base_buildings"], 1)
        self.assertEqual(result["building_counts"]["exact_unique_matches"], 0)
        self.assertEqual(sum(result["attributes"]["construction_year"].values()), 0)

    def test_modelled_and_statistical_estimate_not_counted_as_observed(self):
        write_csv(self.base, BASE_COLS, [
            ["B-1", "", "", ""], ["B-2", "", "", ""],
        ])
        write_csv(self.supp, SUP_COLS, [
            ["S-1", "B-1", "building", "modelled", "1980", "gable", "2"],
            ["S-2", "B-2", "building", "statistical_estimate", "1950", "flat", "1"],
        ])
        result = self.report()
        for field in ("construction_year", "roof_type", "floors_above_ground"):
            self.assertEqual(result["attributes"][field]["proposed_observed_fill"], 0)
            self.assertEqual(result["attributes"][field]["proposed_modelled_fill"], 1)
            self.assertEqual(result["attributes"][field]["blocked_aggregate_to_building_inference"], 1)

    def test_duplicate_base_identity_blocks_run(self):
        write_csv(self.base, BASE_COLS, [["B-1", "", "", ""], ["B-1", "1980", "flat", ""]])
        write_csv(self.supp, SUP_COLS, [])
        with self.assertRaisesRegex(BuildingEnrichmentError, "Duplicate base"):
            self.report()

    def test_duplicate_source_record_identity_blocks_run(self):
        write_csv(self.base, BASE_COLS, [["B-1", "", "", ""]])
        write_csv(self.supp, SUP_COLS, [
            ["S-1", "B-1", "building", "official_record", "", "", ""],
            ["S-1", "B-2", "building", "official_record", "", "", ""],
        ])
        with self.assertRaisesRegex(BuildingEnrichmentError, "Duplicate supplementary"):
            self.report()

    def test_invalid_future_or_missing_numeric_and_bad_kind_block(self):
        write_csv(self.base, BASE_COLS, [["B-1", "", "", ""]])
        write_csv(self.supp, SUP_COLS, [
            ["S-1", "B-1", "building", "official_record", "N/A", "flat", "2"],
        ])
        with self.assertRaisesRegex(BuildingEnrichmentError, "invalid numeric"):
            self.report()
        write_csv(self.supp, SUP_COLS, [
            ["S-1", "B-1", "building", "official_record", "1980", "flat", "0"],
        ])
        with self.assertRaisesRegex(BuildingEnrichmentError, "floor count"):
            self.report()
        write_csv(self.supp, SUP_COLS, [
            ["S-1", "B-1", "property", "official_record", "1980", "flat", "2"],
        ])
        with self.assertRaisesRegex(BuildingEnrichmentError, "record kind"):
            self.report()

    def test_malformed_csv_columns_block(self):
        write_csv(self.base, BASE_COLS[:-1], [["B-1", "", ""]])
        write_csv(self.supp, SUP_COLS, [])
        with self.assertRaisesRegex(BuildingEnrichmentError, "missing required"):
            self.report()

    def test_report_is_deterministic_and_contains_no_raw_values_or_ids(self):
        write_csv(self.base, BASE_COLS, [["PRIVATE-BASE-REF-123", "", "", ""]])
        write_csv(self.supp, SUP_COLS, [
            ["PRIVATE-SOURCE-REF-456", "PRIVATE-BASE-REF-123",
             "building", "official_record", "1952", "special roofing", "3"],
        ])
        first = self.report()
        self.assertEqual(first, self.report())
        s = json.dumps(first, sort_keys=True)
        for forbidden in ("PRIVATE-BASE-REF-123", "PRIVATE-SOURCE-REF-456", "special roofing"):
            self.assertNotIn(forbidden, s)
        self.assertEqual(len(first["base_sha256"]), 64)

    def test_cli_runs_offline_and_returns_diagnostics(self):
        write_csv(self.base, BASE_COLS, [["B-1", "", "", ""]])
        write_csv(self.supp, SUP_COLS, [
            ["R-1", "B-1", "building", "official_record", "1991", "gable", "2"],
        ])
        args = [
            sys.executable, "scripts/building_id_enrichment_v0.py",
            "--base", str(self.base), "--supplement", str(self.supp),
            "--base-source-id", "synthetic.base",
            "--supplement-source-id", "synthetic.verified",
        ]
        run = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=False, timeout=20)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["building_counts"]["exact_unique_matches"], 1)
        self.assertEqual(run.stdout, subprocess.run(
            args, cwd=ROOT, capture_output=True, text=True, check=True, timeout=20,
        ).stdout)


if __name__ == "__main__":
    unittest.main()
