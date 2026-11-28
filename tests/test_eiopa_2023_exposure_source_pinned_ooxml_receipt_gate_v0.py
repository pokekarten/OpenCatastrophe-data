# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original source metadata success must not grant rights or real insurer losses."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import eiopa_2023_exposure_source_pinned_ooxml_receipt_gate_v0 as gate


class SourcePinnedPrinterMetadataOnlyNoGoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = tomllib.loads(gate.RECEIPT.read_text(encoding="utf-8"))

    def test_exact_source_EIOPA_metadata_CRC_only_admitted(self):
        out = gate.validate_receipt(self.original)
        self.assertTrue(out["all_zip_CRC_verified"])
        self.assertEqual(out["original_zip_entries"], 31)
        self.assertEqual(out["sheet_count"], 1)
        self.assertTrue(out["printer_settings_blob_excluded_from_semantic_interpretation"])
        self.assertEqual(out["source_SHA_verified"], gate.EXPECTED["source_sha256"])
        self.assertFalse(out["worksheet_cells_or_insurer_amounts_interpreted"])
        self.assertFalse(out["R_V_insurer_GUL_IL_RI_OEP_AEP_admitted"])

    def test_source_binary_SHA_printer_metadata_size_and_proof_are_immutable(self):
        for k,v in (
            ("source_sha256","a"*64),
            ("original_source_bytes",28209),
            ("original_zip_members",30),
            ("original_zip_total_declared_expanded_bytes",100),
            ("source_pinned_original_workbook_sheet_count",2),
            ("original_printer_settings_blob_count",2),
            ("original_printer_settings_expanded_bytes",9999),
            ("original_printer_settings_compressed_bytes",7000),
            ("source_pinned_evidence_artifact_id",1),
        ):
            doc=deepcopy(self.original)
            doc[k]=v
            with self.subTest(field=k):
                with self.assertRaises(gate.EIOPAMetadataAdmissionBlocked):
                    gate.validate_receipt(doc)

    def test_false_workbook_licence_rights_insurer_claims_and_annual_ep_blocked(self):
        for k in gate.FALSE_FIELDS:
            with self.subTest(field=k):
                doc=deepcopy(self.original)
                doc[k]=True
                with self.assertRaises(gate.EIOPAMetadataAdmissionBlocked):
                    gate.validate_receipt(doc)

    def test_cannot_weaken_source_bound_printer_safety_facts(self):
        for k in gate.TRUE_FIELDS:
            with self.subTest(field=k):
                doc=deepcopy(self.original)
                doc[k]=False
                with self.assertRaises(gate.EIOPAMetadataAdmissionBlocked):
                    gate.validate_receipt(doc)
        doc=deepcopy(self.original)
        doc["source_pinned_metadata_quarantine_status"]="FULL_CLAIMS_MODEL_VALIDATED"
        with self.assertRaises(gate.EIOPAMetadataAdmissionBlocked):
            gate.validate_receipt(doc)

    def test_unreported_source_field_or_missing_provenance_not_admitted(self):
        doc=deepcopy(self.original)
        doc["actual_RV_insurer_policy_locations"]=10000
        with self.assertRaises(gate.EIOPAMetadataAdmissionBlocked):
            gate.validate_receipt(doc)
        doc=deepcopy(self.original)
        del doc["source_pinned_success_run_url"]
        with self.assertRaises(gate.EIOPAMetadataAdmissionBlocked):
            gate.validate_receipt(doc)


if __name__ == "__main__":
    unittest.main()
