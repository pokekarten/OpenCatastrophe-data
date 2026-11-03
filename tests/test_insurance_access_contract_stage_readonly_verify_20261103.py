# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source-only checks for the read-only, rights-preserving Neon stage receipt."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

PATH = (Path(__file__).resolve().parents[1]
        / "research_runners/sql/insurance_access_contract_stage_readonly_verify_20261103.sql")


class AccessContractStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PATH.read_text(encoding="utf-8")
        cls.sql = "\n".join(line for line in cls.source.splitlines()
                            if not line.lstrip().startswith("--")).strip()

    def test_fixed_isolated_branch_and_public_source_commit(self):
        self.assertIn("br-wild-wave-bazb2ck2", self.source)
        self.assertIn("5481c214d5e2c233d4d5cb95204f67d584f53599", self.sql)
        self.assertIn("ISOLATED_ACCESS_METADATA_STAGE_ONLY_NOT_PRODUCTION", self.sql)

    def test_cannot_write_or_mutate_production(self):
        self.assertEqual(self.sql.count(";"), 1)
        self.assertTrue(self.sql.startswith("WITH canonical AS ("))
        for verb in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
                     "CREATE", "COPY", "TRUNCATE", "MERGE", "GRANT"):
            with self.subTest(verb=verb):
                self.assertIsNone(re.search(r"\b" + verb + r"\b", self.sql,
                                            re.IGNORECASE))

    def test_rights_and_model_usage_are_never_promoted(self):
        for expected in (
            "altered_contract_rights_or_status",
            "unexpected_raw_admission", "mismatched_access_identity",
            "malformed_provenance", "FALSE AS restricted_source_probe_authorized",
            "FALSE AS provider_bytes_acquired",
            "FALSE AS insurance_cat_model_input_authorized",
            "FALSE AS automatic_production_promotion_authorized",
        ):
            self.assertIn(expected, self.sql)

    def test_two_drifted_historical_contracts_cannot_be_silently_overwritten(self):
        for name, old_blob in (
            ("esa.worldcover.2021.v200", "830fff1705d6b29d8c88dc423a27c7254608ca50"),
            ("noaa.coops.water-levels", "53aa5e6e9f23dc0ddd153fae1c57a4752f31b0aa"),
        ):
            with self.subTest(contract=name):
                self.assertIn("access/" + name + ".json", self.sql)
                self.assertIn(old_blob, self.sql)
        self.assertIn("esa_worldcover_prior_revision_preserved", self.sql)
        self.assertIn("noaa_coops_prior_revision_preserved", self.sql)

    def test_canonical_namespace_not_confused_with_noncanonical_research(self):
        self.assertIn("all_access_classified_rows", self.sql)
        self.assertIn("canonical_access_contracts", self.sql)
        self.assertIn("historical_canonical_contracts", self.sql)
        self.assertIn("newly_staged_contracts", self.sql)
        self.assertIn("distinct_git_paths", self.sql)


if __name__ == "__main__":
    unittest.main()
