# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fictional original-data lineage classification, no network or source rows."""
import unittest
from pathlib import Path

from research_runners.lu_geobase_source_origin_two_site_v0 import (
    PUBLISHER_CODES, SourceLineageError, main, run, study_rect,
    summarize_source_codes,
)


class BuildingSourceLineageTests(unittest.TestCase):
    def test_official_codes_partition_entire_bounded_sample(self):
        values=list(PUBLISHER_CODES)+["Bati3DACT","Ortho"]
        out=summarize_source_codes(values,expected=len(values))
        self.assertEqual(out["Bati3DACT"],2)
        self.assertEqual(out["Ortho"],2)
        self.assertEqual(sum(out.values()),len(values))

    def test_missing_and_unreviewed_are_never_independent_claims(self):
        out=summarize_source_codes([None,"","unknown:private-feature"],expected=3)
        self.assertEqual(out["missing_label"],2)
        self.assertEqual(out["other_unreviewed"],1)
        self.assertNotIn("unknown:private-feature",str(out))

    def test_nonstring_source_rejected(self):
        with self.assertRaises(SourceLineageError):
            summarize_source_codes([37],expected=1)

    def test_invalid_true_count_rejected(self):
        for expected in (True,0,401,1.5):
            with self.subTest(expected=expected):
                with self.assertRaises(SourceLineageError):
                    summarize_source_codes(["PCN"],expected=expected)

    def test_no_silent_population_change(self):
        with self.assertRaises(SourceLineageError):
            summarize_source_codes(["PCN"],expected=2)

    def test_oversized_provider_source_value_rejected_without_print(self):
        with self.assertRaises(SourceLineageError):
            summarize_source_codes(["x"*129],expected=1)

    def test_source_labels_not_lowercased_to_invent_equivalence(self):
        out=summarize_source_codes(["pcn","PCN"],expected=2)
        self.assertEqual(out["other_unreviewed"],1)
        self.assertEqual(out["PCN"],1)

    def test_unapproved_site_fails_without_optional_pyproj(self):
        with self.assertRaisesRegex(SourceLineageError,"Unapproved geographic study site"):
            study_rect("synthetic:unknown-site")

    def test_missing_file_blocks_without_original_source(self):
        with self.assertRaises(SourceLineageError):
            run(Path("synthetic-original-does-not-exist.zip"))

    def test_cli_never_prints_source_record_on_failure(self):
        self.assertEqual(main(["--geobase-zip","synthetic-original-does-not-exist.zip"]),2)


if __name__=="__main__":
    unittest.main()
