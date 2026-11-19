# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, original-receipted synthetic R+V study matrix regression.

This is an OED/data-integrity smoke, NOT insured-site geocoding or CAT admission.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_runners"))
from export_rva_2025_oed_scenario_matrix_v0 import create_matrix


class TestOriginalSourceRvaOedScenarioMatrix(unittest.TestCase):
    def test_original_inputs_six_scenarios_and_no_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "matrix"
            manifest = create_matrix(root)
            self.assertEqual(manifest["schema"], "RVA_LIKE_400_KREIS_OED_6_SCENARIO_MATRIX_V0")
            self.assertEqual(manifest["scenario_count"], 6)
            for flag in ("model_input_approved", "geocoded",
                         "actual_insurer_buildings_verified",
                         "actual_insurer_tiv_observed",
                         "natural_peril_covers_observed",
                         "German_Oasis_GUL_IL_RI_run_verified"):
                self.assertIs(manifest[flag], False, flag)
            with (root / "scenario_comparison.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 6)
            self.assertEqual({r["valuation_pattern"] for r in rows},
                             {"flat", "age_archetype"})
            self.assertEqual(len({r["OED_directory"] for r in rows}), 6)
            original_hashes = manifest["original_source_sha256"]
            self.assertEqual(len(original_hashes), 3)
            self.assertTrue(all(len(v) == 64 for v in original_hashes.values()))
            self.assertEqual(manifest["observed_national_contracts_at_year_end"], 1_060_546)
            self.assertEqual(manifest["observed_national_building_gwp_eur_cents"], 99_771_000_000)
            for entry in rows:
                label = entry["OED_directory"]
                self.assertEqual(json.loads(entry["input_sha256"]), original_hashes)
                self.assertEqual(entry["sampled_contracts"], "10000")
                self.assertEqual(entry["geocodes_verified"], "False")
                self.assertEqual(entry["model_run_approved"], "False")
                folder = root / label
                with (folder / "location.csv").open(newline="", encoding="utf-8") as stream:
                    loc = list(csv.DictReader(stream))
                with (folder / "account.csv").open(newline="", encoding="utf-8") as stream:
                    acc = list(csv.DictReader(stream))
                with (folder / "cohort_receipt.csv").open(newline="", encoding="utf-8") as stream:
                    cohorts = list(csv.DictReader(stream))
                self.assertEqual((len(loc), len(acc), len(cohorts)), (10000, 10000, 4000))
                ids = {x["LocNumber"] for x in loc}
                self.assertEqual(len(ids), 10000)
                self.assertEqual(ids, {x["AccNumber"] for x in acc})
                self.assertEqual({x["Latitude"] for x in loc}, {""})
                self.assertEqual({x["Longitude"] for x in loc}, {""})
                tiv = sum(int(x["BuildingTIV"]) for x in loc)
                self.assertEqual(tiv, int(entry["sampled_fictional_tiv_eur"]))
                self.assertEqual(tiv, sum(int(x["FictionalExportedBuildingTIVEUR"])
                                          for x in cohorts))
                if entry["valuation_pattern"] == "flat":
                    self.assertEqual(tiv, 4_500_000_000)
            for filename, expected in manifest["artifact_manifest_sha256"].items():
                self.assertEqual(hashlib.sha256((root / filename).read_bytes()).hexdigest(),
                                 expected, filename)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "existing"
            root.mkdir()
            sentinel = root / "sentinel"
            sentinel.write_text("retain", encoding="utf-8")
            with self.assertRaises(ValueError):
                create_matrix(root)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "retain")


if __name__ == "__main__":
    unittest.main()
