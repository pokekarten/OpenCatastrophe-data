# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source, rotated XWS geometry and insurer nonadmission guards."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from xws_kyrill_2022_nrw_10k_source_gust_handoff_v0 import (
    nearest_rotated_position,original_fictional_oed,SourceBlocked,
    EXPECTED_OED_ZIP_SHA,EXPECTED_HU_ORIGINAL_SHA,EXPECTED_MANIFEST_SHA,
    EXPECTED_SYNTH_TIV,SITE_COUNT,COUNTIES
)


class FakeToRotated:
    def transform(self, lon, lat):
        return (6.001457192940548,-1.2998242188691274)


class NoOverlap:
    def transform(self, lon, lat):
        return (-35.0,23.0)


class XWSNRWSourceHandoffTests(unittest.TestCase):
    def test_exact_source_and_sample_receipts(self):
        self.assertEqual(EXPECTED_OED_ZIP_SHA,
          "5b0055ce71314f7d7baf4f67008cd4abba3df28a4bce0690bbe9521a3cc35757")
        self.assertEqual(EXPECTED_HU_ORIGINAL_SHA,
          "10e5b9fd1d299ef0efa883bfadce7c4c3fd2ed7b42076557cbdff887a0d277da")
        self.assertEqual(EXPECTED_MANIFEST_SHA,
          "b4713a9a09a55193d39b64550bc1408ba588303d8a4e658f05536b3dbe14b416")
        self.assertEqual((SITE_COUNT,COUNTIES,EXPECTED_SYNTH_TIV),
                         (10000,53,4826029500))

    def test_original_derived_artifact_not_accepted_on_wrong_sha(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"invalid.zip"
            with zipfile.ZipFile(p,"w") as z:
                z.writestr("untrusted.csv","hello")
            with self.assertRaisesRegex(SourceBlocked,"SHA"):
                original_fictional_oed(p)

    def test_synthetic_rotated_coordinate_nearest_source_cell(self):
        try:import numpy as np
        except ImportError:self.skipTest("numpy optional in generic CI")
        x=np.array([365.78145719294,366.00145719294,366.22145719294])
        y=np.array([-1.519824218869,-1.299824218869,-1.079824218869])
        self.assertEqual(nearest_rotated_position(
            FakeToRotated(),x,y,7.020381,50.804382),(1,1))

    def test_rotated_longitude_and_mismatched_spatial_support_block(self):
        try:import numpy as np
        except ImportError:self.skipTest("numpy optional in generic CI")
        x=np.array([365.78,366.00,366.22])
        y=np.array([-1.52,-1.30,-1.08])
        with self.assertRaises(SourceBlocked):
            nearest_rotated_position(NoOverlap(),x,y,7.020381,50.804382)
        with self.assertRaises(SourceBlocked):
            nearest_rotated_position(FakeToRotated(),x,y,3.0,50.804382)

    def test_no_toy_sample_becomes_real_insurer_or_annual_cat(self):
        src=(ROOT/"research_runners/xws_kyrill_2022_nrw_10k_source_gust_handoff_v0.py"
             ).read_text(encoding="utf-8")
        for term in (
            '"actual_RV_insured_site_identity_or_tiv_observed":False',
            '"native_Oasis_GUL_IL_RI_ran_for_Kyrill":False',
            '"annual_Gross_Net_OEP_AEP_authorized":False',
            '"historical_catalogue_selected_extremes_no_unbiased_year_frequency":True',
            '"historical_physical_storm_count":1',
            '"external_original_NetCDF_bytes_redistributed":False'
        ):
            with self.subTest(term=term):self.assertIn(term,src)


if __name__=="__main__":
    unittest.main()
