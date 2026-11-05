# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline tests for source-pinned crop-code hierarchy joins."""
from __future__ import annotations

import unittest

from research_runners.eurocrops_codebook_qc_v0 import (
    Blocked, audit, git_blob_sha,
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


if __name__ == "__main__":
    unittest.main()
