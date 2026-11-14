# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tests: keep issued parent distinct from lapsed SG branch LEI."""
import json
import unittest

from scripts.mas_agcs_gleif_branch_proof_v0 import (
    BRANCH, PARENT, UEN, GLEIFBranchReceiptError, original_audit, MAX_BYTES,
)


def original_fixtures():
    branch = {
        "data": {"type": "lei-records", "id": BRANCH,
                 "attributes": {"entity": {
                     "category": "BRANCH",
                     "legalName": {"name": "ALLIANZ GLOBAL CORPORATE & SPECIALTY SE SINGAPORE BRANCH"},
                     "jurisdiction": "DE", "legalAddress": {"country": "SG"},
                     "registeredAt": {"id": "RA000523"}, "registeredAs": UEN,
                     "status": "ACTIVE"},
                     "registration": {"status": "LAPSED"}}}}
    parent = {
        "data": {"type": "lei-records", "id": PARENT,
                 "attributes": {"entity": {
                     "category": "GENERAL",
                     "legalName": {"name": "Allianz Global Corporate & Specialty SE"},
                     "jurisdiction": "DE", "legalAddress": {"country": "DE"},
                     "registeredAs": "HRB 208312", "status": "ACTIVE"},
                     "registration": {"status": "ISSUED"}}}}
    link = {
        "data": {"type": "relationship-records", "id": "synthetic-relationship",
                 "attributes": {"relationship": {
                     "type": "IS_INTERNATIONAL_BRANCH_OF",
                     "startNode": {"id": BRANCH, "type": "LEI"},
                     "endNode": {"id": PARENT, "type": "LEI"},
                     "status": "ACTIVE"},
                     "registration": {"status": "LAPSED"}}}}
    return {"branch": branch, "parent": parent, "relationship": link}


def encode(records):
    return {k: json.dumps(v, sort_keys=True).encode("utf-8")
            for k, v in records.items()}


class GLEIFBranchSourceReceiptTests(unittest.TestCase):
    def test_valid_original_source_preserves_three_separate_states(self):
        out = original_audit(encode(original_fixtures()))
        self.assertEqual(out["branch_lei"], BRANCH)
        self.assertEqual(out["parent_lei"], PARENT)
        self.assertEqual(out["branch_acra_registration"], UEN)
        self.assertEqual(out["gleif_relationship_type"], "IS_INTERNATIONAL_BRANCH_OF")
        self.assertEqual(out["gleif_relationship_status"], "ACTIVE")
        self.assertEqual(out["gleif_relationship_registration"], "LAPSED")
        self.assertEqual(out["branch_lei_registration"], "LAPSED")
        self.assertEqual(out["parent_lei_registration"], "ISSUED")
        for key in ("independently_verified_mas_licence_current",
                    "branch_parent_relationship_written_to_neon",
                    "cat_exposure_verified", "model_input_approved"):
            self.assertFalse(out[key])
        self.assertEqual(len(out["source_sha256"]), 3)
        self.assertTrue(all(len(v) == 64 for v in out["source_sha256"].values()))

    def test_wrong_branch_or_parent_lei_fails(self):
        for role in ("branch", "parent"):
            with self.subTest(role=role):
                j = original_fixtures()
                j[role]["data"]["id"] = "WRONG"
                with self.assertRaisesRegex(GLEIFBranchReceiptError, "wrong GLEIF LEI"):
                    original_audit(encode(j))

    def test_branch_leis_lapsed_must_not_be_autoupgraded(self):
        j = original_fixtures()
        j["branch"]["data"]["attributes"]["registration"]["status"] = "ISSUED"
        with self.assertRaisesRegex(GLEIFBranchReceiptError, "status changed"):
            original_audit(encode(j))

    def test_relationship_registration_lapsed_is_not_relationship_status(self):
        j = original_fixtures()
        j["relationship"]["data"]["attributes"]["registration"]["status"] = "ISSUED"
        with self.assertRaisesRegex(GLEIFBranchReceiptError, "registration status changed"):
            original_audit(encode(j))
        j = original_fixtures()
        j["relationship"]["data"]["attributes"]["relationship"]["status"] = "INACTIVE"
        with self.assertRaisesRegex(GLEIFBranchReceiptError, "relationship changed"):
            original_audit(encode(j))

    def test_reversed_international_branch_direction_rejected(self):
        j = original_fixtures()
        relationship = j["relationship"]["data"]["attributes"]["relationship"]
        relationship["startNode"], relationship["endNode"] = (
            relationship["endNode"], relationship["startNode"])
        with self.assertRaisesRegex(GLEIFBranchReceiptError, "relationship changed"):
            original_audit(encode(j))

    def test_wrong_uen_and_country_must_not_be_automatically_linked(self):
        for field, value in (("registeredAs", "T99FC9999Z"),
                             ("jurisdiction", "SG")):
            j = original_fixtures()
            j["branch"]["data"]["attributes"]["entity"][field] = value
            with self.subTest(field=field), self.assertRaises(GLEIFBranchReceiptError):
                original_audit(encode(j))

    def test_rejects_duplicate_key_and_malformed_source_json(self):
        originals = encode(original_fixtures())
        originals["branch"] = originals["branch"].replace(
            b'"type": "lei-records"', b'"type": "lei-records", "type": "lei-records"')
        with self.assertRaisesRegex(GLEIFBranchReceiptError, "duplicate JSON key"):
            original_audit(originals)
        for raw in (b"not-json", b"", b"x" * (MAX_BYTES + 1), b"\xff"):
            j = encode(original_fixtures())
            j["branch"] = raw
            with self.subTest(length=len(raw)), self.assertRaises(GLEIFBranchReceiptError):
                original_audit(j)

    def test_all_three_precisely_pinned_source_roles_required(self):
        j = encode(original_fixtures())
        j.pop("relationship")
        with self.assertRaisesRegex(GLEIFBranchReceiptError, "exactly three"):
            original_audit(j)


if __name__ == "__main__":
    unittest.main()
