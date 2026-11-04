# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fictional ID populations: fail-closed cross-release address namespace proof."""
from __future__ import annotations

import contextlib
import io
from pathlib import Path
import unittest

from research_runners.lu_apr_nov_address_id_overlap_v0 import (
    CrossReleaseAddressError, compare, main,
)


class AprNovAddressIDTests(unittest.TestCase):
    def test_both_raw_id_columns_and_ordered_pairs_are_measured(self):
        apr=[("gp1","ca1"),("gp2","ca2"),("gp3","ca2"),("gp5","ca5")]
        nov=[("gp1","ca1"),("gp2","ca2"),("gp7","ca2"),("gp4","ca4")]
        r=compare(apr,nov)
        self.assertEqual(r["source_populations"]["april_geo_base_address_rows"],4)
        self.assertEqual(r["exact_string_id_evidence"]
                         ["april_AD_AddressID_vs_november_id_geoportail"]
                         ["distinct_exact_shared_strings"],2)
        self.assertEqual(r["exact_string_id_evidence"]
                         ["april_AlternativeIdentifier_vs_november_id_caclr_bat"]
                         ["distinct_exact_shared_strings"],2)
        self.assertEqual(r["exact_pair_evidence"]["distinct_exact_ordered_pairs_shared"],2)
        self.assertEqual(r["exact_pair_evidence"]["april_rows_with_shared_ordered_pair"],2)
        self.assertFalse(r["literal_match_proves_same_real_address"])
        self.assertFalse(r["address_to_geobase_building_crosswalk_proven"])
        self.assertFalse(r["scientific_cat_model_admitted"])
        self.assertNotIn("gp1",str(r))
        self.assertNotIn("ca2",str(r))

    def test_repeated_alternate_id_never_collapses_multiple_addresses(self):
        a=[("x","k"),("y","k"),("z","k")]
        b=[("x","k"),("y","k"),("w","k")]
        r=compare(a,b)
        q=r["exact_string_id_evidence"]["april_AlternativeIdentifier_vs_november_id_caclr_bat"]
        self.assertEqual(q["distinct_exact_shared_strings"],1)
        self.assertEqual(q["left_rows_with_shared_string"],3)
        self.assertEqual(q["right_rows_with_shared_string"],3)
        self.assertEqual(q["shared_strings_multirow_either_side"],1)
        self.assertEqual(r["exact_pair_evidence"]["distinct_exact_ordered_pairs_shared"],2)

    def test_identical_primary_id_but_different_secondary_pair_is_not_exact_pair(self):
        r=compare([("addr1","old")],[("addr1","new")])
        self.assertEqual(r["exact_string_id_evidence"]
                         ["april_AD_AddressID_vs_november_id_geoportail"]
                         ["distinct_exact_shared_strings"],1)
        self.assertEqual(r["exact_pair_evidence"]["distinct_exact_ordered_pairs_shared"],0)

    def test_zeros_are_not_inferred_building_demolition(self):
        r=compare([("april","a")],[("nov","b")])
        self.assertEqual(r["exact_pair_evidence"]["distinct_exact_ordered_pairs_shared"],0)
        self.assertFalse(r["cross_vintage_unchanged_identity_proven"])
        self.assertFalse(r["insurer_exposure_or_tiv_proven"])

    def test_preserve_leading_zeros_and_case(self):
        r=compare([("001","ABC")],[("1","abc")])
        self.assertEqual(r["exact_pair_evidence"]["distinct_exact_ordered_pairs_shared"],0)

    def test_blank_fields_do_not_create_matches(self):
        r=compare([(None,""),("x","ok")],[("","ok"),("x",None)])
        self.assertEqual(r["exact_pair_evidence"]["distinct_exact_ordered_pairs_shared"],0)
        self.assertEqual(r["april_ad_addressid"]["blank_rows"],1)
        self.assertEqual(r["november_id_caclr_bat"]["blank_rows"],1)

    def test_reject_row_width_or_population_shape(self):
        for a,b in [([("a",)], [("b","c")]), ([("a","b")], []),
                    ([("a","b")], [("x","y","z")])]:
            with self.subTest(a=a,b=b), self.assertRaises(CrossReleaseAddressError):
                compare(a,b)

    def test_reject_controls_invalid_types_and_oversized_key(self):
        for bad in (True,3.5,"in\nvalid","z"*257):
            with self.subTest(value=str(bad)[:7]),self.assertRaises(CrossReleaseAddressError):
                compare([("a",bad)],[("a","b")])

    def test_integer_keys_do_not_autofix_zeros(self):
        r=compare([(1,"001")],[("1","1")])
        self.assertEqual(r["exact_string_id_evidence"]
                         ["april_AD_AddressID_vs_november_id_geoportail"]
                         ["distinct_exact_shared_strings"],1)
        self.assertEqual(r["exact_pair_evidence"]["distinct_exact_ordered_pairs_shared"],0)

    def test_cli_does_not_disclose_source_path(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            result=main(["--geobase-addresses-zip","/tmp/private-address-data.zip",
                         "--bd-adresses-csv","/tmp/missing-original.csv"])
        self.assertEqual(result,2)
        self.assertNotIn("private-address",err.getvalue())


if __name__=="__main__":
    unittest.main()
