# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only TED eForms BT-04 procedure UUID / BT-701 notice UUID gates."""
from __future__ import annotations

import unittest

from research_runners import ted_wbm_2026_procedure_lineage_v0 as m


EARLY_NOTICE = "2fbf4f2f-b3e4-44cb-9e5b-39c23b34de11"
AWARD_NOTICE = "3b69089c-2645-40ab-99a7-12a9a3d9e149"
PROCEDURE_1 = "1e86a664-ae3c-41eb-8529-0242ac130003"
PROCEDURE_2 = "ad45f0c6-5762-4380-8806-18f2315ef8fa"


def fixture(
    *, role="competition", procedure=PROCEDURE_1,
    notice=None, internal="WBM-INS-2026",
    previous=(), previous_scheme="ojs-notice-id",
):
    r = "ContractNotice" if role == "competition" else "ContractAwardNotice"
    n = notice or (EARLY_NOTICE if role == "competition" else AWARD_NOTICE)
    refs = "".join(
        f'<cac:NoticeDocumentReference>'
        f'<cbc:ID schemeName="{previous_scheme}">{ref}</cbc:ID>'
        f'</cac:NoticeDocumentReference>'
        for ref in previous
    )
    internal_el = (
        f'<cac:ProcurementProject><cbc:ID schemeName="InternalID">'
        f'{internal}</cbc:ID></cac:ProcurementProject>'
        if internal is not None else ''
    )
    return (f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<{r} xmlns="urn:oasis:names:specification:ubl:schema:xsd:{r}-2"'
            f' xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"'
            f' xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">'
            f'<cbc:ID schemeName="notice-id">{n}</cbc:ID>'
            f'<cbc:ContractFolderID>{procedure}</cbc:ContractFolderID>'
            f'{internal_el}{refs}'
            f'<cbc:VersionID>01</cbc:VersionID></{r}>').encode("utf-8")


class ProcedureLineageTests(unittest.TestCase):
    def meta(self, **kw):
        role = kw.get("role", "competition")
        return m.extract_metadata(fixture(**kw), role=role)

    def test_identical_procedure_uuid_confirmed_despite_distinct_notice_uuid(self):
        a = self.meta()
        b = self.meta(role="award")
        r = m.compare(a, b)
        self.assertTrue(r["procedure_ids_identical"])
        self.assertEqual(r["classification"], "SAME_PROCEDURE_CONFIRMED_BY_BT04")
        self.assertFalse(r["insured_buildings_or_current_coinsurance_shares_proved"])
        self.assertNotEqual(a["root_notice_id_BT701"], b["root_notice_id_BT701"])

    def test_different_bt04_with_same_internal_id_not_same_proc(self):
        a = self.meta()
        b = self.meta(role="award", procedure=PROCEDURE_2)
        r = m.compare(a, b)
        self.assertFalse(r["procedure_ids_identical"])
        self.assertTrue(r["buyer_internal_procedure_ids_identical"])
        self.assertFalse(r["same_title_or_internal_id_alone_establishes_same_procedure"])
        self.assertEqual(r["classification"], "DIFFERENT_BT04_NO_DIRECT_SAME_PROCEDURE_PROOF")

    def test_different_bt04_with_explicit_previous_publication_stays_distinct(self):
        a = self.meta()
        b = self.meta(role="award", procedure=PROCEDURE_2, previous=("286307-2026",))
        r = m.compare(a, b)
        self.assertFalse(r["procedure_ids_identical"])
        self.assertTrue(r["award_explicitly_references_competition_publication"])
        self.assertEqual(r["classification"],
                         "DIFFERENT_BT04_BUT_EXPLICIT_EARLIER_PUBLICATION_REFERENCE_REVIEW")

    def test_same_notice_bt701_with_different_bt04_refused(self):
        a = self.meta()
        b = self.meta(role="award", notice=EARLY_NOTICE, procedure=PROCEDURE_2)
        with self.assertRaisesRegex(ValueError, "SAME_BT701_NOTICE"):
            m.compare(a, b)

    def test_invalid_uuid_procedure_refused(self):
        with self.assertRaisesRegex(ValueError, "PROCEDURE_NOT_UUID"):
            self.meta(procedure="not-a-uuid")

    def test_uuid_v1_procedure_refused(self):
        with self.assertRaisesRegex(ValueError, "PROCEDURE_NOT_UUID4"):
            self.meta(procedure="f47ac10b-58cc-11cf-a447-001122334455")

    def test_invalid_notice_uuid_refused(self):
        with self.assertRaisesRegex(ValueError, "NOTICE_NOT_UUID"):
            self.meta(notice="publication-286307-2026")

    def test_missing_procedure_id_refused(self):
        raw = fixture().replace(
            f'<cbc:ContractFolderID>{PROCEDURE_1}</cbc:ContractFolderID>'.encode(),
            b'')
        with self.assertRaisesRegex(ValueError, "INVALID_PROCEDURE_CARDINALITY"):
            m.extract_metadata(raw, role="competition")

    def test_duplicate_procedure_id_refused(self):
        needle = f'<cbc:ContractFolderID>{PROCEDURE_1}</cbc:ContractFolderID>'.encode()
        with self.assertRaisesRegex(ValueError, "INVALID_PROCEDURE_CARDINALITY"):
            m.extract_metadata(fixture().replace(needle, needle + needle),
                               role="competition")

    def test_root_notice_id_requires_notice_scheme(self):
        raw = fixture().replace(b'schemeName="notice-id"', b'schemeName="InternalID"')
        with self.assertRaisesRegex(ValueError, "MISSING_EXACT_NOTICE_ID_SCHEME"):
            m.extract_metadata(raw, role="competition")

    def test_internal_buyer_procedure_id_is_not_global_uuid(self):
        a = self.meta(internal="WBM-123-X")
        self.assertEqual(a["buyer_defined_internal_procedure_id_BT22"], "WBM-123-X")
        self.assertNotEqual(a["root_procedure_id_BT04"], "WBM-123-X")

    def test_no_internal_id_still_allows_same_bt04_procedure(self):
        a = self.meta(internal=None)
        b = self.meta(role="award", internal=None)
        self.assertEqual(m.compare(a,b)["classification"], "SAME_PROCEDURE_CONFIRMED_BY_BT04")

    def test_previous_notice_ref_ignores_unknown_scheme(self):
        a = self.meta(role="award", previous=("286307-2026",),
                      previous_scheme="notice-id-ref")
        self.assertEqual(a["previous_published_notice_ids_OPP090"], [])

    def test_duplicate_previous_publication_ref_refused(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_TOO_MANY_PREVIOUS_REFS"):
            self.meta(previous=("286307-2026", "286307-2026"))

    def test_malformed_previous_publication_ref_refused(self):
        with self.assertRaisesRegex(ValueError, "INVALID_PREVIOUS_OJS_NUMBER"):
            self.meta(previous=("not-a-publication",))

    def test_award_xml_cannot_be_parsed_as_competition(self):
        with self.assertRaisesRegex(ValueError, "WRONG_UBL_NOTICE_ROOT"):
            m.extract_metadata(fixture(role="award"), role="competition")

    def test_dtd_and_entity_forbidden(self):
        raw = fixture()
        raw = raw.replace(b"<ContractNotice ", b'<!DOCTYPE ContractNotice [<!ENTITY hi "there">]><ContractNotice ', 1)
        with self.assertRaisesRegex(ValueError, "XML_DTD_FORBIDDEN"):
            m.extract_metadata(raw, role="competition")

    def test_unapproved_role_refused(self):
        with self.assertRaisesRegex(ValueError, "ROLE_NOT_ALLOWLISTED"):
            m.extract_metadata(fixture(), role="planning")

    def test_tampered_metadata_claim_true_is_refused(self):
        a = self.meta()
        b = self.meta(role="award")
        b["metadata_extraction_alone_authenticates_official_source"] = True
        with self.assertRaisesRegex(ValueError, "SOURCE_AUTHENTICITY_CLAIM_FORBIDDEN"):
            m.compare(a,b)

    def test_full_source_verify_rejects_synthetic_even_if_ids_match(self):
        with self.assertRaises(ValueError):
            m.verify(competition_raw=fixture(), award_raw=fixture(role="award"))

    def test_different_pub_previous_unknown_does_not_prove_lineage(self):
        a = self.meta()
        b = self.meta(role="award",procedure=PROCEDURE_2,
                      previous=("123456-2024",))
        r = m.compare(a,b)
        self.assertFalse(r["award_explicitly_references_competition_publication"])
        self.assertEqual(r["classification"], "DIFFERENT_BT04_NO_DIRECT_SAME_PROCEDURE_PROOF")


if __name__ == "__main__":
    unittest.main()
