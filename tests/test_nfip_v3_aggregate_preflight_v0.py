# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests; no FEMA traffic, coordinates or provider records."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from research_runners.nfip_v3_aggregate_preflight_v0 import (
    SOURCE, SourceError, _read, summarize,
)

ROOT = Path(__file__).resolve().parents[1]

def claim(i, **extra):
    row = {"id": "CLAIM_" + str(i), "countyCode": "01001",
           "yearOfLoss": 2024, "amountPaidOnBuildingClaim": "100.25",
           "amountPaidOnContentsClaim": "5.75",
           "latitude": 32.5, "longitude": -86.5}
    row.update(extra)
    return row

def policy(i, **extra):
    row = {"id": "POLICY_" + str(i), "countyCode": "01001",
           "policyEffectiveDate": "2024-01-01",
           "policyTerminationDate": "2025-01-01",
           "totalBuildingInsuranceCoverage": "250000",
           "latitude": 32.5, "longitude": -86.5}
    row.update(extra)
    return row

class NFIPV3PreflightTests(unittest.TestCase):
    def test_only_county_aggregate_without_individual_identifiers(self):
        result = summarize([claim(i) for i in range(10)],
                           [policy(i) for i in range(10)], date(2024, 6, 1))
        self.assertEqual(result["claims_by_county_loss_year"][0]["recorded_paid_building_and_contents_usd"], "1060.00")
        self.assertEqual(result["policies_in_force_by_county"][0]["recorded_building_coverage_usd"], "2500000")
        self.assertFalse(result["model_input_admitted"])
        self.assertTrue(result["no_individual_join"])
        serialized = json.dumps(result)
        self.assertNotIn("CLAIM_", serialized)
        self.assertNotIn("POLICY_", serialized)
        self.assertNotIn("latitude", serialized)
        self.assertNotIn("longitude", serialized)
        self.assertNotIn("32.5", serialized)

    def test_small_groups_suppressed_even_if_user_asks_for_lower_threshold(self):
        result = summarize([claim(i) for i in range(9)],
                           [policy(i) for i in range(9)], date(2024, 6, 1))
        self.assertEqual(result["claims_by_county_loss_year"], [])
        self.assertEqual(result["policies_in_force_by_county"], [])
        self.assertEqual(result["suppressed_claim_groups"], 1)
        self.assertEqual(result["suppressed_policy_groups"], 1)
        with self.assertRaises(SourceError):
            summarize([], [], date(2024, 6, 1), minimum=1)

    def test_time_as_of_not_any_year_and_missing_not_zero(self):
        claims = [claim(i) for i in range(10)]
        policies = [policy(i) for i in range(10)]
        claims[0]["amountPaidOnBuildingClaim"] = None
        policies[0]["totalBuildingInsuranceCoverage"] = None
        result = summarize(claims, policies, date(2024, 6, 1))
        self.assertEqual(result["claims_by_county_loss_year"][0]["missing_payment_record_count"], 1)
        self.assertIsNone(result["claims_by_county_loss_year"][0]["recorded_paid_building_and_contents_usd"])
        self.assertIsNone(result["policies_in_force_by_county"][0]["recorded_building_coverage_usd"])
        later = summarize(claims, policies, date(2025, 6, 1))
        self.assertEqual(later["policies_in_force_by_county"], [])

    def test_negative_payments_preserved_as_recorded(self):
        rows = [claim(i, amountPaidOnBuildingClaim="-100") for i in range(10)]
        result = summarize(rows, [policy(i) for i in range(10)], date(2024, 6, 1))
        self.assertEqual(result["claims_by_county_loss_year"][0]["recorded_paid_building_and_contents_usd"], "-942.50")

    def test_bad_geography_and_types_block(self):
        for mutant in [claim(1, countyCode=1001), claim(1, countyCode="1001"),
                       claim(1, yearOfLoss=True), claim(1, amountPaidOnContentsClaim="NaN"),
                       claim(1, amountPaidOnBuildingClaim=float("inf"))]:
            with self.subTest(mutant=repr(mutant)):
                with self.assertRaises(SourceError):
                    summarize([mutant], [], date(2024, 6, 1))
        with self.assertRaises(SourceError):
            summarize([], [policy(1, policyTerminationDate="2024-01-01")], date(2024, 6, 1))

    def test_exact_sha_envelope_and_unique_provider_ids(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "claims.json"
            data = {"NfipClaims": [claim(1), claim(2)]}
            raw = json.dumps(data).encode()
            path.write_bytes(raw)
            expected = hashlib.sha256(raw).hexdigest()
            rows, size, digest = _read(path, expected, "NfipClaims")
            self.assertEqual(len(rows), 2)
            self.assertEqual(size, len(raw))
            self.assertEqual(digest, expected)
            with self.assertRaisesRegex(SourceError, "SHA-256 mismatch"):
                _read(path, "0" * 64, "NfipClaims")
            with self.assertRaisesRegex(SourceError, "wrong v3 provider envelope"):
                _read(path, expected, "FimaNfipClaims")
            path.write_text('{"NfipClaims":[],"NfipClaims":[]}')
            with self.assertRaises(SourceError):
                _read(path, hashlib.sha256(path.read_bytes()).hexdigest(), "NfipClaims")
            path.write_text(json.dumps({"NfipClaims": [claim(1), claim(1)]}))
            with self.assertRaisesRegex(SourceError, "duplicate provider row"):
                _read(path, hashlib.sha256(path.read_bytes()).hexdigest(), "NfipClaims")

    def test_cli_never_exports_original_rows(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "c.json"
            b = root / "p.json"
            a.write_text(json.dumps({"NfipClaims": [claim(i) for i in range(10)]}))
            b.write_text(json.dumps({"NfipPolicies": [policy(i) for i in range(10)]}))
            args = [sys.executable, "research_runners/nfip_v3_aggregate_preflight_v0.py",
                    "--claims-json", str(a), "--claims-sha256", hashlib.sha256(a.read_bytes()).hexdigest(),
                    "--policies-json", str(b), "--policies-sha256", hashlib.sha256(b.read_bytes()).hexdigest(),
                    "--as-of", "2024-06-01"]
            proc = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=30, check=True)
            output = json.loads(proc.stdout)
            self.assertEqual(output["inputs"]["claims"]["source_id"], SOURCE["claims"][1])
            self.assertEqual(output["inputs"]["policies"]["source_id"], SOURCE["policies"][1])
            self.assertEqual(output["inputs"]["claims"]["sample_rows"], 10)
            self.assertNotIn("CLAIM_", proc.stdout)
            self.assertNotIn("POLICY_", proc.stdout)
            self.assertNotIn("latitude", proc.stdout)

if __name__ == "__main__":
    unittest.main()
