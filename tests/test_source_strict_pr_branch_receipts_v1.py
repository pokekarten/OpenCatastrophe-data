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
        self.assertIn("original_request_range IS NOT NULL", ddl)
        self.assertIn("original_content_range IS NOT NULL", ddl)
        self.assertIn("original_request_range = 'bytes=0-2047'", ddl)
        self.assertIn("original_content_range = 'bytes 0-2047/820143312'", ddl)
        self.assertIn("source_strict_pr_branch_receipt_v1_exact_endpoint_ck", ddl)
        for path in (
            "https://services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json",
            "https://kp.gfz.de/app/json/?start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&index=Kp&status=def",
            "https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/reproc/2017_002/netCDF/supplement/RW2017.002_2021_netcdf_supplement.tar.gz",
        ):
            self.assertIn(path, ddl)
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

    def test_live_fallback_overlay_is_readonly_and_matches_frozen_three_proofs(self):
        """Existing Neon metadata-only proof samples work without new DDL."""
        sql=(ROOT / "insurance_source_pr_branch_live_metadata_readonly_v1.sql").read_text()
        self.assertIn("WITH fixed_expected(", sql)
        self.assertIn("research.source_sample_v0", sql)
        self.assertIn("research.source_usage_rights_v0", sql)
        self.assertIn("research.all_source_inventory_v0", sql)
        self.assertIn("research.source_strict_original_probe_receipt_v1", sql)
        self.assertIn("research.source_strict_metadata_probe_receipt_v1", sql)
        self.assertIn("canonical_sample_sha_valid", sql)
        self.assertIn("metadata_only_no_admission", sql)
        self.assertIn("internal_metadata_licence_scoped", sql)
        self.assertIn("grants_cat_scientific_admission", sql)
        self.assertIn("false AS grants_cat_scientific_admission", sql)
        self.assertIn("NOT c.model_input_approved", sql)
        self.assertIn("NOT c.source_byte_persistence_authorized", sql)
        for forbidden in ("CREATE ", "INSERT ", "UPDATE ", "DELETE ", "DROP ",
                          "ALTER ", "TRUNCATE ", "COPY "):
            # Ignore descriptive SQL comments; test only the SELECT body.
            body="\n".join(line for line in sql.splitlines()
                           if not line.lstrip().startswith("--"))
            self.assertNotIn(forbidden,body.upper())
        for source_id,(run_id,job_id,digest,commit) in EXPECTED.items():
            with self.subTest(source=source_id):
                self.assertIn(source_id, sql)
                self.assertIn(run_id, sql)
                self.assertIn(digest, sql)
                self.assertIn(source_id, self.seed)
                self.assertIn(digest, self.seed)
        # No evidence from main is implied by evidence from a PR branch.
        self.assertIn("separately_trusted_main_range_exists", sql)
        self.assertIn("separately_trusted_main_metadata_exists", sql)

    def test_full_707_source_queue_overlay_is_readonly_and_non_promoting(self):
        """Queue keeps historical P1 but uses scoped original response proof."""
        sql = (ROOT / "insurance_707_source_original_pr_branch_priority_overlay_v1.sql").read_text()
        for required in (
            "WITH original_prioritized AS (", "sample_evidence AS (",
            "FROM research.all_source_inventory_v0 i",
            "source_strict_pr_branch_receipt_v1",  # Separate proposed table is not needed here!
        ):
            if required == "source_strict_pr_branch_receipt_v1":
                self.assertNotIn(required, sql)
            else:
                self.assertIn(required, sql)
        for expected in (
            "original_branch_evidence AS (",
            "research.source_usage_rights_v0 rights",
            "rights.product_scope=e.exact_product_rights_scope",
            "s.sample_sha256 =",
            "s.provider_response_sha256",
            "e.exact_source_url=s.source_url",
            "s.sample_json->>'github_head_sha'=e.github_head_sha",
            "s.sample_json->>'github_job_id'=e.github_job_id::text",
            "s.sample_json->>'request_sha256'=e.request_sha256",
            "s.sample_json->>'runner_code_sha256'",
            "s.sample_json->>'probe_code_sha256'",
            "source_id IN ('",  # This is absent: review explicit positive markers below instead
        ):
            if expected == "source_id IN ('":
                self.assertNotIn(expected, sql)
            else:
                self.assertIn(expected, sql)
        self.assertIn("historical_queue_priority", sql)
        self.assertIn("evidence_adjusted_next_action_priority", sql)
        self.assertIn("older_intermediary_inconclusive_superseded_for_one_original_proof", sql)
        self.assertIn("'P2_review_product_rights_and_science_after_original_probe'", sql)
        self.assertIn("q.registry_commercial_verdict IN ('prohibited','restricted')", sql)
        self.assertIn("q.record_type='admitted_manifest'", sql)
        self.assertIn("false AS newly_grants_trusted_main_status", sql)
        self.assertIn("false AS newly_grants_model_input_approval", sql)
        self.assertIn("COALESCE(q.last_api_shape_status='inconclusive',false)", sql)
        self.assertIn("EXISTS (", sql)
        self.assertNotIn("JOIN research.source_usage_rights_v0 rights", sql)
        body = "\n".join(line for line in sql.splitlines()
                         if not line.lstrip().startswith("--")).upper()
        for word in ("INSERT INTO ", "CREATE TABLE ", "UPDATE RESEARCH.", "DROP TABLE ",
                     "DELETE FROM ", "ALTER TABLE ", "TRUNCATE ", "COPY "):
            self.assertNotIn(word, body)
        for source_id,(run_id,job_id,digest,commit) in EXPECTED.items():
            with self.subTest(source=source_id):
                for item in (source_id,run_id,job_id,digest,commit):
                    self.assertIn(item, sql)

    def test_queue_overlay_only_changes_historical_inconclusive_case(self):
        sql = (ROOT / "insurance_707_source_original_pr_branch_priority_overlay_v1.sql").read_text()
        self.assertIn("WHEN q.last_api_shape_status='inconclusive' AND v.source_id IS NOT NULL", sql)
        self.assertIn("THEN q.next_action_priority", sql)
        self.assertIn("ELSE q.next_action_priority", sql)
        self.assertIn("q.next_action_priority AS historical_queue_priority", sql)
        # Source-specific format and rights are checked before any ranking adjustment.
        self.assertIn("e.exact_product_rights_scope", sql)
        self.assertIn("rights.rights_result='allowed'", sql)
        self.assertIn("rights.scientific_model_admission=false", sql)
        self.assertIn("rights.original_asset_admitted=false", sql)
        self.assertIn("NOT s.model_input_approved", sql)
        self.assertIn("NOT s.source_byte_persistence_authorized", sql)

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
