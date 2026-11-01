# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent synthetic-only tests for seven external EIOPA -> GLEIF identities."""
import json
import unittest

from scripts.eiopa_gleif_seven_identity_receipt_v0 import (
    EI0PA_LEI_CASES, IdentityReceiptError, MAX_BYTES, audit, inspect_gleif_bytes,
)
from scripts.gleif_level1_insurer_identity_pilot import valid_lei


def fixture(lei, *, legal_name=None, country=None, status="ACTIVE",
            lei_status="ISSUED", aliases=None, registered_as=None):
    observed_country, observed_name, local_id = EI0PA_LEI_CASES[lei]
    return {
        "meta": {"goldenCopy": {"publishDate": "2026-11-01T12:00:00Z"}},
        "data": {
            "type": "lei-records", "id": lei,
            "attributes": {
                "lei": lei,
                "entity": {
                    "status": status,
                    "jurisdiction": country or observed_country,
                    "legalAddress": {"country": country or observed_country},
                    "legalName": {"name": legal_name if legal_name is not None else observed_name},
                    "registeredAs": registered_as if registered_as is not None else local_id,
                    "transliteratedOtherNames": aliases or [],
                },
                "registration": {"status": lei_status},
            },
        },
    }


def blob(doc):
    return json.dumps(doc, ensure_ascii=False).encode("utf-8")


class EIOPAGLEIFSevenIdentityTests(unittest.TestCase):
    def setUp(self):
        self.leis = sorted(EI0PA_LEI_CASES)
        self.assertEqual(len(self.leis), 7)

    def test_all_expected_lei_checksums(self):
        self.assertEqual(len(set(self.leis)), 7)
        for lei in self.leis:
            with self.subTest(lei=lei):
                self.assertTrue(valid_lei(lei))

    def test_exact_lei_jurisdiction_and_legality_not_an_exposure(self):
        lei = self.leis[0]
        out = inspect_gleif_bytes(blob(fixture(lei)), lei)
        self.assertEqual(out["eiopa_to_gleif_name_relation"], "exact")
        self.assertEqual(out["eiopa_to_gleif_local_registration_relation"], "exact")
        self.assertEqual(len(out["gleif_original_byte_sha256"]), 64)
        self.assertEqual(out["gleif_source_license"], "CC0-1.0")
        for key in ("neon_updated", "model_input_approved", "insured_exposure_observed",
                    "eiopa_registration_currently_verified", "eiopa_original_csv_verified"):
            self.assertFalse(out[key])

    def test_transliteration_accepted_only_as_evidence_class(self):
        lei = "95980020140005024486"
        obj = fixture(lei, legal_name="MUTUALITAT DELS ENGINYERS MUTUALITAT DE PREVISIÓ SOCIAL",
                      aliases=[{"name":EI0PA_LEI_CASES[lei][1]}],
                      registered_as="1000334867575")
        out = inspect_gleif_bytes(blob(obj), lei)
        self.assertEqual(out["eiopa_to_gleif_name_relation"], "gleif_ascii_transliteration_exact")
        self.assertEqual(out["eiopa_to_gleif_local_registration_relation"], "manual_local_register_id_review")

    def test_different_legal_name_keeps_manual_review(self):
        lei = "529900SURJXJXSY5O039"
        obj = fixture(lei, legal_name='Akcinė bendrovė "Lietuvos draudimas"')
        out = inspect_gleif_bytes(blob(obj), lei)
        self.assertEqual(out["eiopa_to_gleif_name_relation"], "manual_legal_name_variant")
        self.assertEqual(out["eiopa_to_gleif_local_registration_relation"], "exact")

    def test_all_seven_deterministic_offline_receipts(self):
        expected = {lei:blob(fixture(lei)) for lei in self.leis}
        out = audit(expected.__getitem__)
        self.assertEqual(out["source_lei_count"], 7)
        self.assertEqual(out["status_active_issued_count"], 7)
        self.assertEqual(out["name_exact_count"], 7)
        self.assertEqual(out["name_manual_review_count"], 0)
        self.assertEqual(out["local_register_exact_count"], 7)
        self.assertFalse(out["neon_updated"])
        self.assertFalse(out["model_input_approved"])

    def test_wrong_lei_and_wrong_jurisdiction_fail_closed(self):
        a, b = self.leis[:2]
        wrong = fixture(a)
        wrong["data"]["id"] = b
        with self.assertRaisesRegex(IdentityReceiptError, "LEI"):
            inspect_gleif_bytes(blob(wrong), a)
        for bad in ("US", "Germany", ""):
            with self.subTest(country=bad):
                obj = fixture(a)
                obj["data"]["attributes"]["entity"]["jurisdiction"] = bad
                with self.assertRaisesRegex(IdentityReceiptError, "jurisdiction"):
                    inspect_gleif_bytes(blob(obj), a)

    def test_inactive_or_unissued_lei_fails_closed(self):
        lei = self.leis[0]
        for keyword in ({"status":"INACTIVE"}, {"lei_status":"LAPSED"}):
            with self.subTest(keyword=keyword):
                with self.assertRaisesRegex(IdentityReceiptError, "inactive|unissued"):
                    inspect_gleif_bytes(blob(fixture(lei, **keyword)), lei)

    def test_duplicate_keys_nonfinite_oversize_invalid_json_fail_closed(self):
        lei = self.leis[0]
        obj = blob(fixture(lei))
        duplicate = obj.replace(b'"type": "lei-records"', b'"type": "lei-records", "type": "lei-records"', 1)
        for invalid in (duplicate, b'NaN', b'broken', b'', b'x'*(MAX_BYTES+1), b'\xff'):
            with self.subTest(size=len(invalid)),self.assertRaises(IdentityReceiptError):
                inspect_gleif_bytes(invalid,lei)

    def test_missing_record_and_incomplete_batch_fail(self):
        lei = self.leis[0]
        obj = fixture(lei)
        del obj["data"]["attributes"]["registration"]
        with self.assertRaisesRegex(IdentityReceiptError, "missing"):
            inspect_gleif_bytes(blob(obj), lei)
        d = {item:blob(fixture(item)) for item in self.leis[:-1]}
        with self.assertRaises(KeyError):
            audit(d.__getitem__)

    def test_unexpected_lei_is_rejected_before_json(self):
        with self.assertRaisesRegex(IdentityReceiptError, "unexpected"):
            inspect_gleif_bytes(b'{}', "BAD")


if __name__ == "__main__":
    unittest.main()
