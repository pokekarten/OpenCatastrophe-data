# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Source proxy's full loss XLSX SHA must not imply EIOPA science admission."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import eiopa_2023_original_xlsx_binary_receipt_gate_v0 as gate


class OriginalBinarySourceReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = tomllib.loads(gate.RECEIPT.read_text(encoding="utf-8"))

    def test_real_loss_source_SHA_and_partial_exposure_are_distinct(self):
        v = gate.verify_source_receipt(self.original)
        self.assertEqual(v["publisher_link_full_hash"],
                         "201bef4a15dccf4cb56edfe80fd2327b9bcd51ce3d815befb0730ffec5394fd6")
        self.assertEqual(v["publisher_link_complete_bytes"], 28209)
        self.assertEqual(v["publisher_link_complete_binary_count"], 1)
        for key in (
            "other_publisher_xlsx_has_full_binary",
            "insurer_claim_cells_analyzed",
            "original_XLSX_bytes_committed",
            "workbook_specific_rights_clearance",
            "actual_Daria1990_or_German_RV_loss_calibration",
            "annual_gross_net_OEP_AEP",
        ):
            self.assertIs(v[key], False)

    def test_original_xlsx_hash_wrong_or_exposure_fake_full_digest_blocked(self):
        for family, field, value in (
            (0, "whole_binary_sha256", "a"*64),
            (0, "whole_binary_size_bytes", 27550),
            (0, "zip_central_directory_members", 28),
            (0, "zip_central_directory_worksheets", 2),
            (0, "sha256_repeat_independent_implementation_agreed", False),
            (1, "whole_binary_sha256", "b"*64),
            (1, "retrieval_status", "COMPLETE_BYTES_RETURNED_BY_SOURCE_PROXY"),
            (1, "zip_central_directory_worksheets", 3),
        ):
            d=deepcopy(self.original)
            d["originals"][family][field]=value
            with self.subTest(family=family, field=field):
                with self.assertRaises(gate.EIOPASourceIntegrityBlocked):
                    gate.verify_source_receipt(d)

    def test_false_insurer_model_calibration_and_rights_attestation_blocked(self):
        for key in gate.FALSE_FLAGS:
            d=deepcopy(self.original)
            d[key]=True
            with self.subTest(key=key):
                with self.assertRaises(gate.EIOPASourceIntegrityBlocked):
                    gate.verify_source_receipt(d)
        for family in (0,1):
            for key in ("full_zip_CRC_tested", "workbook_sheet_names_or_observed_losses_inspected",
                        "licensed_claims_model_use_approved"):
                d=deepcopy(self.original)
                d["originals"][family][key]=True
                with self.subTest(family=family,key=key):
                    with self.assertRaises(gate.EIOPASourceIntegrityBlocked):
                        gate.verify_source_receipt(d)

    def test_genuine_EIOPA_URLs_and_source_provenance_are_required(self):
        for family in (0,1):
            d=deepcopy(self.original)
            d["originals"][family]["publisher_url"] = "https://some-other-origin.example/eiopa.xlsx"
            with self.subTest(family=family):
                with self.assertRaises(gate.EIOPASourceIntegrityBlocked):
                    gate.verify_source_receipt(d)
        for key, value in (
            ("publisher_legal_notice", "https://other.example/copyright"),
            ("proxy_transport_not_independent_origin_TLSPIN", False),
            ("website_reproduction_attribution_reviewed", False),
        ):
            d=deepcopy(self.original)
            d[key]=value
            with self.subTest(key=key):
                with self.assertRaises(gate.EIOPASourceIntegrityBlocked):
                    gate.verify_source_receipt(d)

    def test_receipt_population_not_reorder_duplicate_or_add_licenses(self):
        for fn in (
            lambda d:d["originals"].pop(),
            lambda d:d["originals"].append(deepcopy(d["originals"][0])),
            lambda d:d["originals"][1].__setitem__("id","HISTORICAL_INSURED_LOSSES"),
            lambda d:d.__setitem__("claims_1990_Daria_EUR",19000000),
            lambda d:d["originals"][0].__setitem__("claims_EUR",1000),
        ):
            d=deepcopy(self.original)
            fn(d)
            with self.assertRaises(gate.EIOPASourceIntegrityBlocked):
                gate.verify_source_receipt(d)


if __name__ == "__main__":
    unittest.main()
