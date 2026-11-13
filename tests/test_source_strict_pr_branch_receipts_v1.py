# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic/static tests for proposed additive PR-branch provider receipt ledger.

No network, production DB, sample data or source provider bytes are used.
The public GitHub job URLs are external provenance requiring human review
before a production CREATE/INSERT; tests are not an independent re-fetch.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1] / "research_runners" / "sql"
SCHEMA = ROOT / "insurance_source_strict_pr_branch_receipt_v1_schema.sql"
SEED = ROOT / "insurance_source_strict_pr_branch_receipt_v1_seed.sql"
VERIFY = ROOT / "insurance_source_strict_pr_branch_receipt_v1_verify.sql"

EXPECTED = {
    "dwd.radklim.rw.v2017.002": (
        "43488656039", "132103695178",
        "741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867",
        "01ab7b83d1765fb6bbe590ad772880c65d5e43c9",
    ),
    "noaa.swpc.real-time-solar-wind": (
        "43489514680", "132106651956",
        "bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159",
        "4a579279e240c9429e6e66360194446c7c6e48b9",
    ),
    "gfz.geomagnetic-kp": (
        "43491158483", "132112397671",
        "f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a",
        "17da6a4a3250bc63e7c363a47f74213472196eeb",
    ),
}


class StrictBranchReceiptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = SCHEMA.read_text(encoding="utf-8")
        cls.seed = SEED.read_text(encoding="utf-8")
        cls.verify = VERIFY.read_text(encoding="utf-8")

    def test_schema_additive_with_independent_branch_trust_level(self):
        ddl = self.schema
        self.assertIn("CREATE TABLE IF NOT EXISTS research.source_strict_pr_branch_receipt_v1", ddl)
        self.assertIn("github_ref <> 'refs/heads/main'", ddl)
        self.assertIn("first_party_trusted_main_run = false", ddl)
        self.assertIn("verified_public_pr_branch_run = true", ddl)
        self.assertIn("github_event = 'push'", ddl)
        self.assertIn("github_ref ~ '^refs/heads/research/", ddl)
        self.assertIn("github_run_url =", ddl)
        self.assertIn("github_head_sha ~ '^[a-f0-9]{40}$'", ddl)
        self.assertIn("original_response_sha256 ~ '^[a-f0-9]{64}$'", ddl)
        self.assertIn("original_request_sha256 ~ '^[a-f0-9]{64}$'", ddl)
        self.assertIn("runner_code_sha256 ~ '^[a-f0-9]{64}$'", ddl)
        self.assertIn("access_contract_sha256 IS NOT NULL OR offline_validator_sha256 IS NOT NULL", ddl)
        for forbidden in (
            "DROP TABLE", "ALTER TABLE", "TRUNCATE", "DELETE FROM",
            "UPDATE research.", "source_api_smoke_receipt_v0 SET",
            "INSERT INTO research.source_sample_v0",
        ):
            self.assertNotIn(forbidden, ddl.upper() if forbidden == forbidden.upper() else ddl)
        self.assertNotIn("CREATE EXTENSION", ddl)

    def test_hard_limits_for_original_bytes_and_prohibitions(self):
        ddl = self.schema
        self.assertIn("original_response_bytes BETWEEN 1 AND 4194304", ddl)
        self.assertIn("original_response_bytes = 2048", ddl)
        self.assertIn("original_request_range = 'bytes=0-2047'", ddl)
        self.assertIn("original_content_range = 'bytes 0-2047/820143312'", ddl)
        self.assertIn("original_http_status = 200", ddl)
        self.assertIn("original_http_status = 206", ddl)
        for col in ("original_bytes_persisted", "full_source_sha256_verified",
                    "physical_science_validated", "insurer_model_input_approved"):
            self.assertIn(col + " = false", ddl)
        self.assertIn("source_strict_pr_branch_receipt_v1_run_unique", ddl)
        self.assertIn("source_strict_pr_branch_receipt_v1_source_scope_ck", ddl)
        self.assertIn("source_strict_pr_branch_receipt_v1_http_scope_ck", ddl)

    def test_seed_is_exactly_three_known_original_public_run_proofs(self):
        seed = self.seed
        self.assertEqual(seed.count("('dwd.radklim.rw.v2017.002'"), 1)
        self.assertEqual(seed.count("('noaa.swpc.real-time-solar-wind'"), 1)
        self.assertEqual(seed.count("('gfz.geomagnetic-kp'"), 1)
        self.assertEqual(seed.count("'push'"), 3)
        self.assertEqual(seed.count("\n  true,"), 3)
        self.assertEqual(seed.count("ON CONFLICT"), 1)
        self.assertIn("DO NOTHING", seed)
        for source_id, (run_id,job_id,digest,commit) in EXPECTED.items():
            with self.subTest(source=source_id):
                for item in (run_id,job_id,digest,commit):
                    self.assertIn(item,seed)
                self.assertEqual(len(digest),64)
                self.assertEqual(len(commit),40)
                self.assertIn(
                    "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/" + run_id,
                    seed,
                )
        # Frozen DWD byte-range differs from original NOAA/GFZ JSON body size.
        self.assertIn("2048",seed)
        self.assertIn("1719377",seed)
        self.assertIn("361",seed)
        self.assertIn("first_party_trusted_main_run",self.schema)

    def test_seed_has_no_source_raw_bytes_or_admission_drift(self):
        seed=self.seed
        for bad in ("\\x89HDF", "COPY ", "DROP TABLE", "UPDATE ",
                    "source_sample_v0", "source_api_smoke_receipt_v0",
                    "CREATE TABLE", "model_input_approved = true"):
            self.assertNotIn(bad,seed)
        self.assertNotIn("raw_provider_body",seed)

    def test_verifier_is_read_only_and_does_not_upgrade_main_trust(self):
        sql=self.verify
        self.assertRegex(sql,r"\bSELECT\b")
        self.assertIn("research.source_strict_pr_branch_receipt_v1",sql)
        self.assertIn("research.source_strict_original_probe_receipt_v1",sql)
        self.assertIn("research.source_strict_metadata_probe_receipt_v1",sql)
        self.assertIn("research.all_source_inventory_v0",sql)
        self.assertIn("grants_source_data_admission",sql)
        self.assertIn("b.first_party_trusted_main_run",sql)
        self.assertIn("private_samples_with_matching_original_sha",sql)
        for verb in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER ",
                     "TRUNCATE ", "GRANT ", "COPY "):
            self.assertNotIn(verb,sql.upper())
        for _, (run_id,*_) in EXPECTED.items():
            self.assertIn(run_id,sql)


if __name__ == "__main__":
    unittest.main()
