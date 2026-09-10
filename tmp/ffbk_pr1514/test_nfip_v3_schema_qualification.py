from __future__ import annotations
import importlib.util, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts"/"validate_nfip_v3_schema_qualification.py"
spec=importlib.util.spec_from_file_location("nfipq",P); m=importlib.util.module_from_spec(spec); sys.modules["nfipq"]=m; spec.loader.exec_module(m)
R=ROOT/"research"/"capital-modeling"/"nfip-v3-registry-qualification-receipt-v1.json"
V0=ROOT/"research"/"capital-modeling"/"nfip-v3-registry-qualification-receipt-v0.json"
class T(unittest.TestCase):
    def base(self): return json.loads(R.read_text())
    def test_current_receipt_confirms_authoritative_fields_vintage_only(self):
        self.assertEqual(m.validate(self.base()),"FIELD_SEMANTICS_CONFIRMED_VINTAGE_ONLY")
    def test_no_claim_rows_accessed(self):
        x=self.base(); x["claim_rows_accessed"]=True
        with self.assertRaisesRegex(m.QualificationError,"claim_rows_accessed"): m.validate(x)
    def test_registry_identity_is_pinned(self):
        x=self.base(); x["fema_registry"]["dataset"]["hash"]="drift"
        with self.assertRaisesRegex(m.QualificationError,"registry mismatch"): m.validate(x)
    def test_metadata_response_is_pinned(self):
        x=self.base(); x["field_semantics"]["metadata_response_sha256"]="drift"
        with self.assertRaisesRegex(m.QualificationError,"response hash"): m.validate(x)
    def test_core_field_identity_is_pinned(self):
        x=self.base(); by={r["name"]:r for r in x["field_semantics"]["qualified_field_records"]}; by["buildingDamageAmount"]["hash"]="drift"
        with self.assertRaisesRegex(m.QualificationError,"field identity mismatch"): m.validate(x)
    def test_v3_coverage_and_damage_fields_are_required(self):
        x=self.base(); x["field_semantics"]["authoritative_fields_qualified"].remove("totalBuildingInsuranceCoverage")
        with self.assertRaisesRegex(m.QualificationError,"qualification incomplete"): m.validate(x)
    def test_no_naive_v2_v3_stitch(self):
        x=self.base(); x["decision"]["v2_v3_naive_vintage_stitching"]="ALLOWED"
        with self.assertRaisesRegex(m.QualificationError,"stitching"): m.validate(x)
    def test_future_target_remains_forbidden(self):
        x=self.base(); x["decision"]["future_target_access"]="ALLOWED"
        with self.assertRaisesRegex(m.QualificationError,"future target"): m.validate(x)
    def test_damage_field_cannot_be_promoted_to_prospective_target(self):
        x=self.base(); x["field_semantics"]["economic_classification"]["damage_candidate"]["buildingDamageAmount"]="PROSPECTIVE_TARGET"
        with self.assertRaisesRegex(m.QualificationError,"damage candidate"): m.validate(x)
    def test_claim_finality_remains_unproven(self):
        x=self.base(); x["field_semantics"]["economic_classification"]["identity_and_vintage"]["finality"]="FINAL"
        with self.assertRaisesRegex(m.QualificationError,"finality"): m.validate(x)
    def test_model_promotion_remains_forbidden(self):
        x=self.base(); x["field_semantics"]["promotion_status"]="PROMOTED"
        with self.assertRaisesRegex(m.QualificationError,"model promotion"): m.validate(x)
    def test_v0_historical_receipt_stays_blocked(self):
        self.assertEqual(m.validate(json.loads(V0.read_text())),"REGISTRY_CONFIRMED_FIELD_SEMANTICS_BLOCKED")
if __name__=="__main__": unittest.main()
