# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Official historical HU composite GFK: no four-digit-only false positives."""
from __future__ import annotations
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_nrw_hu_gfk_residential_candidate_v0 import (
    classify_gfk,audit_gfk_counts,RESIDENTIAL_CANDIDATES
)


class TestHistoricalHUFunction(unittest.TestCase):
    def test_only_official_building_type_plus_residential_function(self):
        for suffix in ("1000","1010","1100","1110","1120","1121","1122","1123","1130","1131","1220","1221","1222","1223"):
            self.assertEqual(classify_gfk("31001_"+suffix)[0],
                             "residential_function_candidate_only")
            self.assertIn(suffix,RESIDENTIAL_CANDIDATES)
        self.assertEqual(classify_gfk(" 31001_1010 ")[0],"residential_function_candidate_only")

    def test_other_object_type_or_unverified_function_is_quarantined(self):
        for value in ("31002_1010","31003_1100","32001_1000"):
            self.assertEqual(classify_gfk(value)[0],"non_building_object_quarantine")
        for value in ("31001_9999","31001_3100","31001_1312"):
            self.assertEqual(classify_gfk(value)[0],"unmapped_quarantine")
        for value in ("31001_1020","31001_1022","31001_1024"):
            self.assertEqual(classify_gfk(value)[0],"special_occupancy_quarantine")
        for value in ("31001_2460","31001_2462","31001_2463","31001_2723","31001_1313","31001_2000","31001_2720"):
            self.assertEqual(classify_gfk(value)[0],"known_nonresidential_example")
        for value in ("1010","31001","31001_10","31001_10100","garbage",
                      "31001_1010/../etc",""):
            self.assertEqual(classify_gfk(value)[0],"malformed")
        self.assertEqual(classify_gfk(None)[0],"malformed")

    def test_audit_nontext_source_keys_fail_closed(self):
        # Original GFK distributions use text identifiers. Mixed Python
        # key types must not crash in sorted() or be mistaken for source data.
        for invalid in ({1010: 1},
                        {"31001_1010": 2, None: 1},
                        {("31001", "1010"): 1},
                        {True: 1}):
            with self.subTest(keys=list(invalid)), self.assertRaisesRegex(
                    ValueError, "GFK code must be a string"):
                audit_gfk_counts(invalid)

    def test_count_receipt_no_invented_residential_classification(self):
        source={"31001_1010":8,"31001_1100":2,"31001_2460":5,
                "31002_1010":1,"31001_3100":10,"":2}
        a=audit_gfk_counts(source)
        self.assertEqual(sum(a["source_gfk_categories"].values()),28)
        self.assertEqual(a["source_gfk_categories"]["residential_function_candidate_only"],10)
        self.assertEqual(a["source_gfk_categories"]["unmapped_quarantine"],10)
        self.assertTrue(a["source_gfk_requires_AX_Gebaeude_31001_prefix"])
        self.assertIs(a["actual_RV_insurer_building_identity_known"],False)
        for bad in ({"31001_1010":-1},{"31001_1010":True},None):
            with self.assertRaises(ValueError):
                audit_gfk_counts(bad)


if __name__=="__main__":
    unittest.main()
