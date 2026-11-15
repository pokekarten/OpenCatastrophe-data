# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No external data or network: validate the public original-page receipt shape."""
import json
from pathlib import Path
import re
import unittest

PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/research/insurer-directory-original-page-receipt-20261101.json"
)
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ProviderOriginalPageReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(PATH.read_text(encoding="utf-8"))

    def test_exact_source_page_count_and_contiguous_original_page_ids(self):
        obj = self.obj
        pages = obj["source_pages"]
        self.assertEqual(obj["page_count"], 46)
        self.assertEqual([p["page"] for p in pages], list(range(1, 47)))
        self.assertEqual(sum(p["rows"] for p in pages), 18180)
        self.assertEqual([p["rows"] for p in pages[:-1]], [400] * 45)
        self.assertEqual(pages[-1]["rows"], 180)
        self.assertEqual(obj["unique_source_slugs"], 18180)
        self.assertEqual(obj["row_count"], 18180)

    def test_each_page_receipt_has_exact_identity_and_hash(self):
        obj = self.obj
        pages = obj["source_pages"]
        self.assertEqual(
            obj["original_page_bytes_total"],
            sum(p["original_bytes"] for p in pages),
        )
        for page in pages:
            self.assertEqual(
                page["source_url"],
                f"https://insurers.global/api/v1/insurers/names/pages/{page['page']}.json",
            )
            self.assertGreater(page["original_bytes"], 0)
            self.assertLessEqual(page["original_bytes"], 300000)
            self.assertIsNotNone(HEX64.fullmatch(page["sha256"]))
        self.assertEqual(len({p["sha256"] for p in pages}), 46)

    def test_five_field_parity_remains_separate_from_original_bytes(self):
        obj = self.obj
        neon = obj["neon_readonly_verification"]
        self.assertIsNotNone(HEX64.fullmatch(obj["canonical_field_digest_sha256"]))
        self.assertEqual(neon["row_count"], obj["row_count"])
        self.assertEqual(neon["unique_source_slugs"], obj["unique_source_slugs"])
        self.assertEqual(neon["missing_fields"], 0)
        self.assertEqual(neon["reserved_delimiters"], 0)
        self.assertEqual(neon["model_approvals"], 0)
        self.assertTrue(neon["same_five_field_digest"])
        self.assertIsNone(obj["source_original_aggregate_file_sha256"])
        self.assertIsNone(obj["historical_import_raw_original_sha256"])
        self.assertFalse(obj["model_input_approved"])
        self.assertFalse(obj["independent_regulator_status_verified"])
        self.assertFalse(obj["insured_exposure_observed"])
        self.assertFalse(obj["raw_provider_rows_committed"])

    def test_source_identity_licence_and_action_proof(self):
        obj = self.obj
        self.assertEqual(obj["source_dataset_version"], "2026-09-08+97f331e66662")
        self.assertEqual(obj["source_index_url"],
                         "https://insurers.global/api/v1/insurers/names.json")
        self.assertEqual(obj["provider_data_license"], "CC-BY-4.0")
        self.assertTrue(obj["github_actions_proof"].startswith(
            "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/"
        ))


if __name__ == "__main__":
    unittest.main()
