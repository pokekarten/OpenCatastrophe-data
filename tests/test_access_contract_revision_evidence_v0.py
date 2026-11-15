# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fail-closed source guards for the isolated access-revision evidence ledger."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DDL = ROOT / "research_runners/sql/access_contract_revision_evidence_v0_ddl.sql"
RECEIPT = ROOT / "research_runners/sql/access_contract_revision_evidence_v0_verify_readonly.sql"


class AccessRevisionEvidenceBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ddl = DDL.read_text(encoding="utf-8")
        cls.receipt = "\n".join(
            l for l in RECEIPT.read_text(encoding="utf-8").splitlines()
            if not l.lstrip().startswith("--")
        ).strip()

    def test_explicit_isolated_branch_and_separate_research_table(self):
        self.assertIn("br-steep-lab-baeo8bmc", self.ddl)
        self.assertIn("CREATE TABLE research.access_contract_revision_evidence_v0", self.ddl)
        self.assertNotIn("CREATE TABLE registry.source_record", self.ddl)
        self.assertNotIn("ALTER TABLE registry.source_record", self.ddl)
        self.assertNotIn("UPDATE registry.source_record", self.ddl)
        self.assertNotIn("DELETE FROM registry.source_record", self.ddl)

    def test_revision_identity_is_exact_git_blob_and_access_id(self):
        self.assertIn("PRIMARY KEY (access_id, git_blob_sha)", self.ddl)
        self.assertIn("git_path = 'access/' || access_id || '.json'", self.ddl)
        self.assertIn("evidence_role IN ('historical_observed','proposed_unapproved')", self.ddl)
        self.assertIn("contract_metadata->>'access_id' = access_id", self.ddl)

    def test_ledger_is_fail_closed_and_blocks_mutation(self):
        self.assertIn("CHECK (authorized_for_production = false", self.ddl)
        self.assertIn("provider_bytes_admitted = false", self.ddl)
        self.assertIn("model_input_approved = false", self.ddl)
        self.assertIn("BEFORE UPDATE OR DELETE", self.ddl)
        self.assertIn("RAISE EXCEPTION", self.ddl)
        self.assertIn("FOR EACH ROW EXECUTE FUNCTION", self.ddl)

    def test_original_contract_status_and_rights_labels_are_preserved(self):
        for expected in (
            "contract_metadata->>'status' = review_status",
            "contract_metadata->'rights_and_policy'->>'dataset_rights_status'",
            "contract_metadata->'probe_contract'->>'mode' = probe_mode",
        ):
            self.assertIn(expected, self.ddl)

    def test_readonly_verifier_never_grants_api_or_model_access(self):
        self.assertTrue(self.receipt.startswith("WITH evidence AS ("))
        self.assertEqual(self.receipt.count(";"), 1)
        for verb in ("INSERT", "UPDATE", "DELETE", "CREATE", "DROP",
                     "ALTER", "TRUNCATE", "GRANT", "COPY"):
            with self.subTest(verb=verb):
                self.assertIsNone(re.search(r"\b" + verb + r"\b",
                                            self.receipt, flags=re.IGNORECASE))
        for phrase in (
            "authorization_violations",
            "mutated_historical_contracts",
            "historical_revisions",
            "proposed_unapproved_revisions",
            "FALSE AS production_migration_approved",
            "FALSE AS commercial_provider_download_approved",
            "FALSE AS science_or_cat_loss_admitted",
        ):
            self.assertIn(phrase, self.receipt)


if __name__ == "__main__":
    unittest.main()
