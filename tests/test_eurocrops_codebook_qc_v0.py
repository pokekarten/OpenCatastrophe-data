# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline tests for source-pinned crop-code hierarchy joins."""
from __future__ import annotations

import unittest

from research_runners.eurocrops_codebook_qc_v0 import (
    Blocked, audit, git_blob_sha, sample_mapping_coverage, _read_rows,
    MAP_HEADER, HCAT_HEADER,
)


MAPPING = (
    "nuts,original_code,original_name,translated_name,hcat4_code,hcat4_name,usage_code,usage_name\n"
    "de4,0001,Grain,Grain,100,grain,0,Not specified\n"
    "de4,0002,Flower,Flower,999,flower,0,Not specified\n"
    "dea,0001,Grain,Grain,100,grain,0,Not specified\n"
).encode()
HCAT = (
    "hcat4_code,hcat4_name,seasonality_code,seasonality_name\n"
    "100,grain,0,NA\n"
).encode()


def run(mapping: bytes = MAPPING, hcat: bytes = HCAT,
        mapping_sha: str | None = None, hcat_sha: str | None = None) -> dict:
    return audit(mapping, mapping_sha or git_blob_sha(mapping),
                 hcat, hcat_sha or git_blob_sha(hcat))


class EuroCropsCodebookTests(unittest.TestCase):
    def test_original_mapping_crosswalk_reports_missing_taxonomy(self):
        result = run()
        self.assertEqual(result["mapping_rows"], 3)
        self.assertEqual(result["region_count"], 2)
        self.assertEqual(result["mapping_rows_by_region"], {"de4": 2, "dea": 1})
        self.assertEqual(result["unresolved_hcat4_reference_count"], 1)
        self.assertEqual(result["unresolved_hcat4_references"][0]["original_code"], "0002")
        self.assertFalse(result["safe_for_insured_value_or_cat_model"])

    def test_duplicate_region_and_original_code_blocked(self):
        duplicate = MAPPING + (
            b"de4,0001,Grain,Grain,100,grain,0,Not specified\n"
        )
        with self.assertRaisesRegex(Blocked, "duplicate NUTS"):
            run(mapping=duplicate)

    def test_original_git_blob_sha_mismatch_blocks(self):
        with self.assertRaisesRegex(Blocked, "SHA mismatch"):
            run(mapping_sha="0" * 40)

    def test_wrong_source_schema_blocks(self):
        bad = MAPPING.replace(b"original_code", b"fake_code", 1)
        with self.assertRaisesRegex(Blocked, "column names"):
            run(mapping=bad)

    def test_taxonomy_collision_blocks(self):
        bad = HCAT + b"100,other,0,NA\n"
        with self.assertRaisesRegex(Blocked, "duplicate HCAT4"):
            run(hcat=bad)

    def test_exact_publisher_unknown_sentinels_do_not_become_crop_codes(self):
        sentinels = (
            b"de4,,,,3390000000,not_known_and_other,0,No specified use\n"
            b"dea,,,,3390000000,not_known_and_other,0,No specified use\n"
        )
        mapping = MAPPING + sentinels
        hierarchy = HCAT + b"3390000000,not_known_and_other,0,NA\n"
        report = run(mapping=mapping, hcat=hierarchy)
        self.assertEqual(report["mapping_rows"], 5)
        self.assertEqual(report["joinable_original_code_rows"], 3)
        self.assertEqual(report["unknown_cultivation_sentinel_rows_not_joinable"], 2)
        self.assertEqual(report["unknown_cultivation_sentinel_regions"], ["de4", "dea"])
        self.assertEqual(report["unresolved_hcat4_reference_count"], 1)
        source_rows = _read_rows(mapping, git_blob_sha(mapping), MAP_HEADER)
        taxonomy_rows = _read_rows(hierarchy, git_blob_sha(hierarchy), HCAT_HEADER)
        coverage = sample_mapping_coverage(
            [{"original_code": "0001"}, {"original_code": ""},
             {"original_code": "0002"}], "de4", source_rows, taxonomy_rows,
        )
        self.assertEqual(coverage["resolved_to_hcat4_rows"], 1)
        self.assertEqual(coverage["blank_or_nonstring_original_code_rows"], 1)
        self.assertEqual(coverage["mapping_to_missing_hcat4_rows"], 1)
        self.assertEqual(sum(v for k, v in coverage.items() if k != "sampled_rows"), 3)

    def test_malformed_or_duplicate_unknown_sentinel_fails_closed(self):
        sentinel = b"de4,,,,3390000000,not_known_and_other,0,No specified use\n"
        taxonomy = HCAT + b"3390000000,not_known_and_other,0,NA\n"
        with self.assertRaisesRegex(Blocked, "malformed or duplicate"):
            run(mapping=MAPPING + sentinel + sentinel, hcat=taxonomy)
        with self.assertRaisesRegex(Blocked, "malformed or duplicate"):
            run(mapping=MAPPING + b"de4,,unknown,,3390000000,not_known_and_other,0,No specified use\n",
                hcat=taxonomy)
        with self.assertRaisesRegex(Blocked, "sentinel absent"):
            run(mapping=MAPPING + sentinel)

    def test_join_is_region_specific_and_preserves_leading_zero(self):
        mapping = [
            {"nuts": "de4", "original_code": "001", "hcat4_code": "100"},
            {"nuts": "de4", "original_code": "2", "hcat4_code": "999"},
            {"nuts": "dea", "original_code": "1", "hcat4_code": "100"},
        ]
        taxonomy = [{"hcat4_code": "100"}]
        rows = [
            {"original_code": "001"}, {"original_code": "1"},
            {"original_code": "2"}, {"original_code": "missing"},
            {"original_code": 1}, {"original_code": "001 "},
        ]
        report = sample_mapping_coverage(rows, "de4", mapping, taxonomy)
        self.assertEqual(report, {
            "sampled_rows": 6,
            "resolved_to_hcat4_rows": 1,
            "code_not_in_region_mapping_rows": 2,
            "mapping_to_missing_hcat4_rows": 1,
            "blank_or_nonstring_original_code_rows": 2,
        })
        self.assertNotIn("original_code", report)
        with self.assertRaisesRegex(Blocked, "region missing"):
            sample_mapping_coverage(rows, "nl", mapping, taxonomy)

    def test_duplicate_mapping_prevents_ambiguous_coverage(self):
        mapping = [
            {"nuts": "de4", "original_code": "1", "hcat4_code": "100"},
            {"nuts": "de4", "original_code": "1", "hcat4_code": "999"},
        ]
        with self.assertRaisesRegex(Blocked, "ambiguous"):
            sample_mapping_coverage([{"original_code": "1"}], "de4", mapping, [])


if __name__ == "__main__":
    unittest.main()
