# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Wholly fictional in-memory original ID namespace QA and false-join barriers."""
from __future__ import annotations

import contextlib
import io
from pathlib import Path
import unittest

from research_runners.lu_caclr_geobase_original_id_namespace_v0 import (
    NamespaceEvidenceError, aggregate_ids, main, _id_counters,
)


class NamespaceTests(unittest.TestCase):
    def test_exact_shared_strings_are_only_candidates(self):
        r = aggregate_ids(["A","A","B","02",""],["x","x","B","2",""],["A","B","B","2"])
        self.assertEqual(r["address_caclr_building_id"]["rows"], 5)
        self.assertEqual(r["address_caclr_building_id"]["missing_or_blank"], 1)
        self.assertEqual(r["address_caclr_building_id"]["distinct_nonblank"], 3)
        self.assertEqual(r["address_caclr_building_id"]["duplicate_excess_rows"], 1)
        self.assertEqual(r["exact_text_overlap"]["caclr_to_geobase_distinct_shared_strings"],2)
        self.assertEqual(r["exact_text_overlap"]["caclr_address_rows_with_shared_string"],3)
        self.assertEqual(r["exact_text_overlap"]["geobase_rows_with_caclr_shared_string"],3)
        self.assertEqual(r["exact_text_overlap"]["geoportail_to_geobase_distinct_shared_strings"],2)
        self.assertFalse(r["id_namespace_equivalence_proven"])
        self.assertFalse(r["common_string_proves_same_physical_building"])
        self.assertFalse(r["scientific_model_input_admitted"])
        self.assertNotIn('"A"',str(r))
        self.assertNotIn('"B"',str(r))

    def test_no_overlap_is_not_construction_or_demolition(self):
        x = aggregate_ids(["CACLR-1","CACLR-2"],["GP-1","GP-2"],["BU-1","BU-2"])
        self.assertEqual(x["exact_text_overlap"]["caclr_to_geobase_distinct_shared_strings"],0)
        self.assertFalse(x["common_string_proves_same_physical_building"])

    def test_exact_text_preserves_leading_zeros_and_case(self):
        r = aggregate_ids(["0001","ABC"],["f"],["1","abc"])
        self.assertEqual(r["exact_text_overlap"]["caclr_to_geobase_distinct_shared_strings"],0)

    def test_duplicate_address_building_string_is_not_deduplicated_by_policy(self):
        x = aggregate_ids(["A","A","A","B"],["p","q","r","s"],["A","B"])
        self.assertEqual(x["address_caclr_building_id"]["duplicate_excess_rows"],2)
        self.assertEqual(x["address_caclr_building_id"]["max_rows_for_one_exact_id"],3)

    def test_missing_or_whitespace_ids_are_counted(self):
        x = aggregate_ids(["", " ", "  padded "],["","abc"," "],["",None,"padded"])
        self.assertEqual(x["address_caclr_building_id"]["missing_or_blank"],2)
        self.assertEqual(x["address_caclr_building_id"]["rows_with_surrounding_whitespace"],1)
        self.assertEqual(x["exact_text_overlap"]["caclr_to_geobase_distinct_shared_strings"],0)

    def test_identifier_population_mismatch_rejected(self):
        with self.assertRaisesRegex(NamespaceEvidenceError,"population mismatch"):
            aggregate_ids(["A"],[],["B"])

    def test_empty_original_candidate_sets_rejected(self):
        with self.assertRaises(NamespaceEvidenceError):
            aggregate_ids([],[],["B"])
        with self.assertRaises(NamespaceEvidenceError):
            aggregate_ids(["A"],["P"],[])

    def test_unsafe_original_id_type_or_control_character_rejected(self):
        for val in (True, 1.5, "\nunsafe", "\x00hidden", "q"*257):
            with self.subTest(val=str(val)[:8]), self.assertRaises(NamespaceEvidenceError):
                aggregate_ids([val],["good"],["B"])

    def test_valid_integer_geobase_source_is_literal_string_only(self):
        x = aggregate_ids(["123"],["foo"],[123])
        self.assertEqual(x["exact_text_overlap"]["caclr_to_geobase_distinct_shared_strings"],1)
        self.assertFalse(x["id_namespace_equivalence_proven"])

    def test_numeric_duplicates_do_not_leak_original_values(self):
        counts, summary = _id_counters(["token","token","other",""],budget=10,role="test")
        self.assertEqual(summary["distinct_nonblank"],2)
        self.assertEqual(summary["duplicate_excess_rows"],1)
        self.assertNotIn("token",str(summary))
        self.assertEqual(len(counts),2)

    def test_small_row_budget_fail_closed(self):
        with self.assertRaises(NamespaceEvidenceError):
            _id_counters(["a","b","c"],budget=2,role="test")

    def test_cli_never_discloses_original_filename(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code=main(["--address-csv","/tmp/real-home-address-secret.csv",
                       "--geobase-zip","/tmp/missing-building.zip"])
        self.assertEqual(code,2)
        self.assertNotIn("secret",err.getvalue())


if __name__=="__main__":
    unittest.main()
