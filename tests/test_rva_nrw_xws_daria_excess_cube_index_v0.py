# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline independent source-fixture cubic wind-severity and negative tests."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
sys.path.insert(0, str(ROOT / "tests"))
import rva_nrw_xws_daria_excess_cube_index_v0 as idx
import rva_nrw_xws_daria_10k_original_gust_overlay_v0 as source
from test_rva_nrw_xws_daria_10k_original_gust_overlay_v0 import (
    fake_nrw_oed, fake_xws_source
)


class TestDariaSourceBoundSeverityIndex(unittest.TestCase):
    def setUp(self):
        fake = fake_xws_source()
        pins = {n: (len(content), hashlib.sha256(content).hexdigest())
                for n, content in fake.items()}
        self.patch_source = patch.object(source, "PINNED_SOURCE_FILES", pins)
        self.patch_index = patch.object(idx, "PINNED_SOURCE_FILES", pins)
        self.patch_source.start()
        self.patch_index.start()
        self.addCleanup(self.patch_source.stop)
        self.addCleanup(self.patch_index.stop)

    def study(self, path: Path):
        fake_nrw_oed(path)
        return source.overlay(
            fake_xws_source(), path,
            expected_sites=3, expected_counties=3, expected_tiv=600000
        )

    def calculate(self, study):
        return idx.compute_index(study, expected_sites=3,
                                 expected_counties=3, expected_tiv=600000)

    def test_three_uncertainty_views_same_physical_event_exact_cubed_oracle(self):
        with TemporaryDirectory() as d:
            result = self.calculate(self.study(Path(d) / "source.zip"))
            receipt = result["receipt"]
            self.assertTrue(receipt["original_grid_SSI_not_reproduced"])
            self.assertTrue(receipt["local_98th_percentile_not_estimated"])
            self.assertTrue(receipt["no_real_RV_insured_sites_or_money_losses"])
            self.assertTrue(receipt["no_GUL_IL_RI_OEP_AEP"])
            self.assertEqual(len(result["county_rows"]), 9)
            views = receipt["threshold_index_views"]
            self.assertEqual([v["original_wind_view_same_event"] for v in views],
                             ["lower95", "mean", "upper95"])
            self.assertEqual([v["candidate_sites_above_25_mps"] for v in views],
                             [1, 1, 2])
            self.assertEqual([Decimal(v["asset_sampled_excess_cubed_mps3"])
                              for v in views],
                             [Decimal(125), Decimal(1000), Decimal(3500)])
            self.assertEqual(
                [Decimal(v["fictional_TIV_weighted_excess_cubed_EUR_mps3"])
                 for v in views],
                [Decimal(37_500_000), Decimal(300_000_000),
                 Decimal(1_037_500_000)]
            )
            self.assertEqual(receipt["fictional_building_TIV_eur"], 600000)

    def test_strict_deterministic_output_and_refuse_existing_or_dangling(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            result = self.calculate(self.study(root / "source.zip"))
            a, b = root / "a.zip", root / "b.zip"
            ra = idx.write_zip(a, result)
            rb = idx.write_zip(b, result)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(ra, rb)
            with zipfile.ZipFile(a) as z:
                names = set(z.namelist())
                self.assertEqual(names, {
                    "one_storm_asset_sampled_excess_cubed_counties.csv",
                    "one_storm_severity_index_not_insurer_loss_receipt.json",
                })
                name = "one_storm_asset_sampled_excess_cubed_counties.csv"
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),
                                 ra["output_sha256"][name])
                self.assertTrue(json.loads(z.read(
                    "one_storm_severity_index_not_insurer_loss_receipt.json"
                ))["no_GUL_IL_RI_OEP_AEP"])
            with self.assertRaisesRegex(idx.WindIndexBlocked, "overwrite"):
                idx.write_zip(a, result)
            link = root / "link.zip"
            link.symlink_to(root / "nonexistent")
            with self.assertRaisesRegex(idx.WindIndexBlocked, "overwrite"):
                idx.write_zip(link, result)

    def test_same_source_permutation_preserves_canonical_output(self):
        with TemporaryDirectory() as d:
            study = self.study(Path(d) / "source.zip")
            original = self.calculate(study)
            study["site_rows"].reverse()
            study["county_rows"].reverse()
            self.assertEqual(original, self.calculate(study))

    def test_source_admission_flags_and_original_sha_cannot_be_promoted(self):
        with TemporaryDirectory() as d:
            good = self.study(Path(d) / "source.zip")
            changes = (
                ("storm_uncertainty_variants_are_same_physical_event", False),
                ("German_wind_vulnerability_by_material_roof_construction_validated", True),
                ("actual_1990_RV_insured_geographies_or_2025_RV_coverage_known", True),
                ("XWS_extreme_storm_selection_is_valid_annual_frequency_model", True),
                ("native_Oasis_or_NextGen_GUL_IL_RI_OEP_AEP_executed", True),
            )
            for name, value in changes:
                altered = deepcopy(good)
                altered["receipt"][name] = value
                with self.subTest(name=name):
                    with self.assertRaisesRegex(idx.WindIndexBlocked, "unverified"):
                        self.calculate(altered)
            altered = deepcopy(good)
            altered["receipt"]["provider_original_four_XWS_CSV_source_receipt"][
                "original_files"]["grid"]["full_sha256"] = "0" * 64
            with self.assertRaisesRegex(idx.WindIndexBlocked, "unverified"):
                self.calculate(altered)

    def test_site_schema_inverted_gust_fake_insured_and_duplicate_block(self):
        with TemporaryDirectory() as d:
            good = self.study(Path(d) / "source.zip")
            bad_cases = (
                lambda st: st["site_rows"][0].__setitem__(
                    "ActualRVInsuredSiteObserved", "true"),
                lambda st: st["site_rows"][0].__setitem__(
                    "Daria1990Lower95GustMps", "1000.0"),
                lambda st: st["site_rows"][1].__setitem__(
                    "FictionalSiteId", st["site_rows"][0]["FictionalSiteId"]),
                lambda st: st["site_rows"][0].__setitem__(
                    "Daria1990MeanGustMps", "-1"),
                lambda st: st["site_rows"][0].__setitem__("UnknownColumn", "x"),
            )
            for tamper in bad_cases:
                altered = deepcopy(good)
                tamper(altered)
                with self.assertRaises(idx.WindIndexBlocked):
                    self.calculate(altered)

    def test_county_and_national_conservation_cannot_be_waived(self):
        with TemporaryDirectory() as d:
            good = self.study(Path(d) / "source.zip")
            for change in (
                lambda st: st["county_rows"][0].__setitem__(
                    "FictionalBuildingTIVEUR", "9999999"),
                lambda st: st["county_rows"][0].__setitem__(
                    "FictionalBuildingsWithMeanGustGE25Mps", "7"),
                lambda st: st["site_rows"][0].__setitem__(
                    "Fictional2025BuildingTIVEUR", "1"),
                lambda st: st["site_rows"].pop(),
            ):
                modified = deepcopy(good)
                change(modified)
                with self.assertRaises(idx.WindIndexBlocked):
                    self.calculate(modified)

    def test_zero_at_threshold_and_intensity_units_not_eur_loss(self):
        self.assertEqual(idx.THRESHOLD_MPS, Decimal(25))
        self.assertEqual(idx.SCHEMA, "XWS_DARIA_1990_ASSET_SAMPLED_EXCESS_CUBED_INTENSITY_INDEX_V0")
        with TemporaryDirectory() as d:
            receipt = self.calculate(self.study(Path(d) / "source.zip"))["receipt"]
            self.assertEqual(receipt["unit_excess_cube"], "m^3/s^3 (m/s cubed)")
            self.assertEqual(receipt["unit_TIV_weighted_excess_cube"],
                             "fictional EUR * (m/s)^3")
            self.assertTrue(receipt["frequency_or_annual_probability_not_estimated"])


if __name__ == "__main__":
    unittest.main()
