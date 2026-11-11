# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure fictional 3x3x4 historic Daria gust/rebuild exposure negative tests."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import rva_nrw_daria_footprint_tiv_exposure_v0 as model


def synthetic_three():
    original = [
        ("SYN-NRW-05111-01-000001", "05111", 100_000, "100"),
        ("SYN-NRW-05111-01-000002", "05111", 200_000, "110"),
        ("SYN-NRW-05974-01-000001", "05974", 300_000, "120"),
    ]
    loc = [
        dict(LocNumber=ident, AccNumber=ident, LocGroup="KREIS-" + county,
             CountryCode="DE", OEDVersion="5.0.0", BuildingTIV=str(tiv))
        for ident, county, tiv, _ in original
    ]
    acc = [dict(AccNumber=ident) for ident, *_ in original]
    ev = [
        dict(LocNumber=ident, KreisAGS2022=county,
             SourceFootprintAreaM2=area, SourceGFK="31001_1010",
             SourcePhysicalCandidateNotInsuredSite="true")
        for ident, county, _, area in original
    ]
    wind = [
        dict(FictionalSiteId=ident, Original2022KreisAGS=county,
             NearestXWSGridPointKm="9.12",
             Daria1990Lower95GustMps=str(10 + i),
             Daria1990MeanGustMps=str((28,31,33)[i]),
             Daria1990Upper95GustMps=str((45,48,55)[i]),
             Fictional2025BuildingTIVEUR=str(tiv),
             ActualRVInsuredSiteObserved="false")
        for i, (ident, county, tiv, _) in enumerate(original)
    ]
    county = [
        dict(KreisAGS2022="05111", FictionalSiteCount="2",
             FictionalBuildingTIVEUR="300000",
             FictionalBuildingsWithMeanGustGE25Mps="2",
             FictionalTIVWithMeanGustGE25MpsEUR="300000"),
        dict(KreisAGS2022="05974", FictionalSiteCount="1",
             FictionalBuildingTIVEUR="300000",
             FictionalBuildingsWithMeanGustGE25Mps="1",
             FictionalTIVWithMeanGustGE25MpsEUR="300000"),
    ]
    return loc, acc, ev, wind, county


def combine(rows):
    return model.aggregate(*rows, expected_sites=3, expected_counties=2)


class DariaFootprintValuationTests(unittest.TestCase):
    def test_three_value_scenarios_preserve_one_event_and_counties(self):
        result = combine(synthetic_three())
        self.assertEqual(result["matched_original_derived_public_physical_candidates"], 3)
        self.assertEqual(result["verified_NRW_counties"], 2)
        self.assertEqual(result["original_fictional_tiv_eur"], 600000)
        self.assertTrue(result["wind_views_are_one_physical_1990_storm"])
        self.assertFalse(result["German_wind_vulnerability_or_native_Oasis_NextGen_loss_calibrated"])
        self.assertFalse(result["annual_event_frequency_or_AEP_OEP_admitted"])
        results = result["fictional_rebuilding_value_cases"]
        totals = {
            "low_single_storey_1800_eur_per_m2": 594000,
            "central_two_storeys_2200_eur_per_m2": 1452000,
            "high_three_storeys_3000_eur_per_m2": 2970000,
        }
        for case, expected in totals.items():
            with self.subTest(case=case):
                self.assertEqual(results[case]["fictional_total_tiv_eur"], expected)
                self.assertEqual(results[case]["one_event_historical_gust_thresholds_mps"]["mean"]["25"],
                                 {"public_candidate_site_count": 3, "fictional_tiv_eur": expected})
                self.assertEqual(results[case]["one_event_historical_gust_thresholds_mps"]["lower95"]["25"],
                                 {"public_candidate_site_count": 0, "fictional_tiv_eur": 0})
                self.assertEqual(results[case]["one_event_historical_gust_thresholds_mps"]["upper95"]["40"],
                                 {"public_candidate_site_count": 3, "fictional_tiv_eur": expected})
        self.assertEqual(results["central_two_storeys_2200_eur_per_m2"][
            "one_event_historical_gust_thresholds_mps"]["mean"]["30"],
            {"public_candidate_site_count": 2, "fictional_tiv_eur": 1012000})

    def test_duplicate_or_missing_account_site_or_wind_identity_rejected(self):
        for layer, key in ((0, "LocNumber"), (1, "AccNumber"),
                           (2, "LocNumber"), (3, "FictionalSiteId")):
            with self.subTest(layer=layer):
                arrays = list(deepcopy(synthetic_three()))
                arrays[layer][1][key] = arrays[layer][0][key]
                with self.assertRaisesRegex(model.ExposureBlocked, "duplicate|crosswalk"):
                    combine(arrays)

    def test_wrong_county_gfk_insurer_flag_or_tiv_rejected(self):
        cases = (
            (0, "LocGroup", "KREIS-99999"),
            (2, "SourceGFK", "31001_2463"),
            (2, "SourcePhysicalCandidateNotInsuredSite", "false"),
            (3, "ActualRVInsuredSiteObserved", "true"),
            (3, "Original2022KreisAGS", "05112"),
            (3, "Fictional2025BuildingTIVEUR", "12345"),
            (3, "Daria1990MeanGustMps", "nan"),
            (3, "NearestXWSGridPointKm", "100.0"),
            (2, "SourceFootprintAreaM2", "-1"),
            (2, "SourceFootprintAreaM2", "Infinity"),
        )
        for layer, key, replacement in cases:
            with self.subTest(key=key, replacement=replacement):
                rows = list(deepcopy(synthetic_three()))
                rows[layer][0][key] = replacement
                with self.assertRaises(model.ExposureBlocked):
                    combine(rows)

    def test_corrupt_original_county_receipt_or_uncertainty_order_rejected(self):
        rows = list(deepcopy(synthetic_three()))
        rows[4][0]["FictionalSiteCount"] = "3"
        with self.assertRaisesRegex(model.ExposureBlocked, "county wind/exposure"):
            combine(rows)
        rows = list(deepcopy(synthetic_three()))
        rows[3][0]["Daria1990Upper95GustMps"] = "20"
        with self.assertRaisesRegex(model.ExposureBlocked, "uncertainty ordering"):
            combine(rows)

    def test_unpinned_or_symlinked_archive_cannot_claim_original_hazard(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            fake = directory / "fake.zip"
            with zipfile.ZipFile(fake, "w") as archive:
                archive.writestr("location.csv", "LocNumber\nFAKE\n")
                archive.writestr("account.csv", "AccNumber\nFAKE\n")
                archive.writestr("physical_candidate_evidence.csv", "LocNumber\nFAKE\n")
                archive.writestr("manifest.json", "{}")
            with self.assertRaisesRegex(model.ExposureBlocked, "CSV pin mismatch"):
                model._archive(fake, model.OED_PINS)
            link = directory / "link.zip"
            link.symlink_to(fake)
            with self.assertRaisesRegex(model.ExposureBlocked, "bounded regular"):
                model._archive(link, model.OED_PINS)


if __name__ == "__main__":
    unittest.main()
