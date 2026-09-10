from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_nfip_v3_schema_qualification.py"
spec = importlib.util.spec_from_file_location("nfipq", SCRIPT)
m = importlib.util.module_from_spec(spec)
sys.modules["nfipq"] = m
assert spec.loader is not None
spec.loader.exec_module(m)

R2 = ROOT / "research" / "capital-modeling" / "nfip-v3-registry-qualification-receipt-v2.json"
R1 = ROOT / "research" / "capital-modeling" / "nfip-v3-registry-qualification-receipt-v1.json"
R0 = ROOT / "research" / "capital-modeling" / "nfip-v3-registry-qualification-receipt-v0.json"


class T(unittest.TestCase):
    def base(self):
        return json.loads(R2.read_text())

    def test_current_receipt_uses_stable_semantic_fingerprint(self):
        self.assertEqual(
            m.validate(self.base()),
            "FIELD_SEMANTICS_CONFIRMED_VINTAGE_ONLY_STABLE_FINGERPRINT",
        )

    def test_v1_historical_capture_receipt_remains_valid(self):
        self.assertEqual(
            m.validate(json.loads(R1.read_text())),
            "FIELD_SEMANTICS_CONFIRMED_VINTAGE_ONLY",
        )

    def test_v0_historical_receipt_stays_blocked(self):
        self.assertEqual(
            m.validate(json.loads(R0.read_text())),
            "REGISTRY_CONFIRMED_FIELD_SEMANTICS_BLOCKED",
        )

    def test_no_claim_rows_accessed(self):
        x = self.base()
        x["claim_rows_accessed"] = True
        with self.assertRaisesRegex(m.QualificationError, "claim_rows_accessed"):
            m.validate(x)

    def test_registry_identity_is_pinned(self):
        x = self.base()
        x["fema_registry"]["dataset"]["hash"] = "drift"
        with self.assertRaisesRegex(m.QualificationError, "registry mismatch"):
            m.validate(x)

    def test_semantic_metadata_hash_is_pinned(self):
        x = self.base()
        x["field_semantics"]["metadata_semantic_sha256"] = "drift"
        with self.assertRaisesRegex(m.QualificationError, "semantic hash"):
            m.validate(x)

    def test_canonicalization_field_set_is_pinned(self):
        x = self.base()
        x["field_semantics"]["canonicalization"]["included_record_keys"].remove(
            "description"
        )
        with self.assertRaisesRegex(m.QualificationError, "canonicalization field set"):
            m.validate(x)

    def test_core_field_identity_is_pinned(self):
        x = self.base()
        x["field_semantics"]["core_field_identities"]["buildingDamageAmount"][
            "hash"
        ] = "drift"
        with self.assertRaisesRegex(m.QualificationError, "field identity mismatch"):
            m.validate(x)

    def test_v3_coverage_and_damage_fields_are_required(self):
        x = self.base()
        x["field_semantics"]["authoritative_fields_qualified"].remove(
            "totalBuildingInsuranceCoverage"
        )
        with self.assertRaisesRegex(m.QualificationError, "qualification incomplete"):
            m.validate(x)

    def test_no_naive_v2_v3_stitch(self):
        x = self.base()
        x["decision"]["v2_v3_naive_vintage_stitching"] = "ALLOWED"
        with self.assertRaisesRegex(m.QualificationError, "stitching"):
            m.validate(x)

    def test_future_target_remains_forbidden(self):
        x = self.base()
        x["decision"]["future_target_access"] = "ALLOWED"
        with self.assertRaisesRegex(m.QualificationError, "future target"):
            m.validate(x)

    def test_damage_field_cannot_be_promoted_to_prospective_target(self):
        x = self.base()
        x["field_semantics"]["economic_classification"]["damage_candidate"][
            "buildingDamageAmount"
        ] = "PROSPECTIVE_TARGET"
        with self.assertRaisesRegex(m.QualificationError, "damage candidate"):
            m.validate(x)

    def test_claim_finality_remains_unproven(self):
        x = self.base()
        x["field_semantics"]["economic_classification"]["identity_and_vintage"][
            "finality"
        ] = "FINAL"
        with self.assertRaisesRegex(m.QualificationError, "finality"):
            m.validate(x)

    def test_model_promotion_remains_forbidden(self):
        x = self.base()
        x["field_semantics"]["promotion_status"] = "PROMOTED"
        with self.assertRaisesRegex(m.QualificationError, "model promotion"):
            m.validate(x)

    def test_semantic_fingerprint_ignores_query_time_metadata_and_last_refresh_only(self):
        records = []
        for index in range(m.EXPECTED_METADATA_RECORD_COUNT):
            record = {key: None for key in m.SEMANTIC_RECORD_KEYS}
            record.update(
                {
                    "datasetId": "dataset",
                    "openFemaDataSet": "NfipClaims",
                    "datasetVersion": 3,
                    "name": f"field{index:02d}",
                    "title": f"Field {index:02d}",
                    "description": f"description {index:02d}",
                    "type": "text",
                    "sortOrder": index,
                    "isSearchable": True,
                    "isNestedObject": False,
                    "isNullable": True,
                    "primaryKey": index == 0,
                    "id": f"id-{index:02d}",
                    "hash": f"hash-{index:02d}",
                    "srid": None,
                    "lastRefresh": "2026-09-10T00:00:00Z",
                }
            )
            records.append(record)

        first = {
            "OpenFemaDataSetFields": records,
            "metadata": {"rundate": "2026-09-10T19:00:00Z"},
        }
        second = json.loads(json.dumps(first))
        second["metadata"]["rundate"] = "2026-09-10T19:05:00Z"
        for record in second["OpenFemaDataSetFields"]:
            record["lastRefresh"] = "2026-09-11T00:00:00Z"

        self.assertEqual(
            m.semantic_metadata_sha256(first),
            m.semantic_metadata_sha256(second),
        )

        second["OpenFemaDataSetFields"][0]["description"] = "semantic drift"
        self.assertNotEqual(
            m.semantic_metadata_sha256(first),
            m.semantic_metadata_sha256(second),
        )


if __name__ == "__main__":
    unittest.main()
