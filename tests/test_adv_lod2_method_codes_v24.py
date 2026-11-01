# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline AdV PQS v2.4 candidate-only numerical membership tests."""
import unittest

from research_runners.adv_lod2_method_codes_v24 import (
    VERSION_DATE, HISTORIC_BERLIN_SOURCE_YEAR, CANDIDATES,
    candidate_membership_counts,
)


class CandidateMethodCodesTest(unittest.TestCase):
    def test_exact_official_2023_groups_are_not_2022_mapping(self):
        self.assertEqual(VERSION_DATE,"2023-03-23")
        self.assertEqual(HISTORIC_BERLIN_SOURCE_YEAR,2022)
        self.assertEqual({key:len(v) for key,v in CANDIDATES.items()},{
            "quelledachhoehe":7,"quellelage":3,"quellebodenhoehe":8,
        })
        self.assertIn("1100",CANDIDATES["quellebodenhoehe"])
        self.assertNotIn("1100",CANDIDATES["quelledachhoehe"])

    def test_only_four_ascii_digits_int_or_str_count(self):
        records=[
            {"quelledachhoehe":1000,"quellelage":" 1000 ","quellebodenhoehe":1100},
            {"quelledachhoehe":"7000","quellelage":"3000","quellebodenhoehe":"1400"},
            {"quelledachhoehe":"9999","quellelage":"0000","quellebodenhoehe":"9999"},
            {"quelledachhoehe":1000.0,"quellelage":True,"quellebodenhoehe":"١١٠٠"},
            {"unrelated":"ignored"},
        ]
        out=candidate_membership_counts(records)
        for field in CANDIDATES:
            self.assertEqual(out[field],{
                "ad_v24_candidate":2,"unlisted_or_malformed":2,"missing":1,
            })

    def test_source_values_cannot_leak_in_report(self):
        private="PRIVATE-1234-NEVER-EXPOSE@example.test"
        out=candidate_membership_counts([{
            "quelledachhoehe":private,"quellelage":"confidential address",
            "quellebodenhoehe":"1234",
        }])
        for secret in ("PRIVATE","example.test","confidential","1234"):
            self.assertNotIn(secret,str(out))
        self.assertEqual(out["quelledachhoehe"]["unlisted_or_malformed"],1)

    def test_bad_record_rejected_and_empty_is_empty(self):
        result=candidate_membership_counts([])
        self.assertTrue(all(sum(x.values())==0 for x in result.values()))
        with self.assertRaises(ValueError):
            candidate_membership_counts([{"quellelage":1000},False])


if __name__=="__main__":
    unittest.main()
