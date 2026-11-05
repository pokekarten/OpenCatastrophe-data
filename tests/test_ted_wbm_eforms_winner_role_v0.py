# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only eForms role chain and source-pinned XML admission tests."""
from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from research_runners import ted_wbm_eforms_winner_role_v0 as m
from research_runners import ted_berlin_insurance_original_xml_preflight_v0 as original


def xml_fixture() -> bytes:
    return """<?xml version="1.0" encoding="UTF-8"?>
<ContractAwardNotice xmlns="urn:oasis:names:specification:ubl:schema:xsd:ContractAwardNotice-2"
 xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:efext="http://data.europa.eu/p27/eforms-ubl-extensions/1"
 xmlns:efac="http://data.europa.eu/p27/eforms-ubl-extension-aggregate-components/1">
<ext:UBLExtensions><ext:UBLExtension><ext:ExtensionContent><efext:EformsExtension>
<efac:NoticeResult>
  <efac:LotResult><cbc:ID>RES-0001</cbc:ID>
    <cbc:TenderResultCode listName="winner-selection-status">selec-w</cbc:TenderResultCode>
    <efac:LotTender><cbc:ID>TEN-0001</cbc:ID></efac:LotTender>
    <efac:LotTender><cbc:ID>TEN-0003</cbc:ID></efac:LotTender>
    <efac:SettledContract><cbc:ID>CON-0001</cbc:ID></efac:SettledContract>
    <efac:TenderLot><cbc:ID>LOT-0001</cbc:ID></efac:TenderLot>
  </efac:LotResult>
  <efac:LotResult><cbc:ID>RES-0002</cbc:ID>
    <cbc:TenderResultCode listName="winner-selection-status">all-rej</cbc:TenderResultCode>
    <efac:LotTender><cbc:ID>TEN-0002</cbc:ID></efac:LotTender>
    <efac:TenderLot><cbc:ID>LOT-0002</cbc:ID></efac:TenderLot>
  </efac:LotResult>
  <efac:LotTender><cbc:ID>TEN-0001</cbc:ID>
    <efac:TenderingParty><cbc:ID>TPA-0001</cbc:ID></efac:TenderingParty>
    <efac:TenderLot><cbc:ID>LOT-0001</cbc:ID></efac:TenderLot>
  </efac:LotTender>
  <efac:LotTender><cbc:ID>TEN-0002</cbc:ID>
    <efac:TenderingParty><cbc:ID>TPA-0002</cbc:ID></efac:TenderingParty>
    <efac:TenderLot><cbc:ID>LOT-0002</cbc:ID></efac:TenderLot>
  </efac:LotTender>
  <efac:LotTender><cbc:ID>TEN-0003</cbc:ID>
    <efac:TenderingParty><cbc:ID>TPA-0002</cbc:ID></efac:TenderingParty>
    <efac:TenderLot><cbc:ID>LOT-0001</cbc:ID></efac:TenderLot>
  </efac:LotTender>
  <efac:TenderingParty><cbc:ID>TPA-0001</cbc:ID>
    <efac:Tenderer><cbc:ID>ORG-0002</cbc:ID></efac:Tenderer>
    <efac:Tenderer><cbc:ID>ORG-0003</cbc:ID></efac:Tenderer>
    <efac:Tenderer><cbc:ID>ORG-0004</cbc:ID></efac:Tenderer>
  </efac:TenderingParty>
  <efac:TenderingParty><cbc:ID>TPA-0002</cbc:ID>
    <efac:Tenderer><cbc:ID>ORG-0005</cbc:ID></efac:Tenderer>
  </efac:TenderingParty>
  <efac:SettledContract><cbc:ID>CON-0001</cbc:ID>
    <cbc:AwardDate>2026-09-21</cbc:AwardDate>
    <cac:SignatoryParty><cac:PartyIdentification>
      <cbc:ID>ORG-0001</cbc:ID>
    </cac:PartyIdentification></cac:SignatoryParty>
    <cac:SignatoryParty><cac:PartyIdentification>
      <cbc:ID>ORG-0005</cbc:ID>
    </cac:PartyIdentification></cac:SignatoryParty>
    <efac:LotTender><cbc:ID>TEN-0001</cbc:ID></efac:LotTender>
  </efac:SettledContract>
</efac:NoticeResult>
<efac:Organizations>
<efac:Organization><efac:Company>
 <cac:PartyIdentification><cbc:ID>ORG-0001</cbc:ID></cac:PartyIdentification>
 <cac:PartyName><cbc:Name>WBM Wohnungsbaugesellschaft Berlin-Mitte mbH</cbc:Name></cac:PartyName>
</efac:Company></efac:Organization>
<efac:Organization><efac:Company>
 <cac:PartyIdentification><cbc:ID>ORG-0002</cbc:ID></cac:PartyIdentification>
 <cac:PartyName><cbc:Name>HDI Global SE</cbc:Name></cac:PartyName>
</efac:Company></efac:Organization>
<efac:Organization><efac:Company>
 <cac:PartyIdentification><cbc:ID>ORG-0003</cbc:ID></cac:PartyIdentification>
 <cac:PartyName><cbc:Name>Helvetia Schweizerische Versicherungsgesellschaft AG</cbc:Name></cac:PartyName>
</efac:Company></efac:Organization>
<efac:Organization><efac:Company>
 <cac:PartyIdentification><cbc:ID>ORG-0004</cbc:ID></cac:PartyIdentification>
 <cac:PartyName><cbc:Name>R+V Allgemeine Versicherung AG</cbc:Name></cac:PartyName>
</efac:Company></efac:Organization>
<efac:Organization><efac:Company>
 <cac:PartyIdentification><cbc:ID>ORG-0005</cbc:ID></cac:PartyIdentification>
 <cac:PartyName><cbc:Name>NOT THE WINNER Versicherung AG</cbc:Name></cac:PartyName>
</efac:Company></efac:Organization>
</efac:Organizations>
</efext:EformsExtension></ext:ExtensionContent></ext:UBLExtension></ext:UBLExtensions>
<cbc:ID schemeName="notice-id">668506-2026</cbc:ID>
<cac:ContractingParty><cac:Party><cac:PartyIdentification>
<cbc:ID>ORG-0001</cbc:ID></cac:PartyIdentification></cac:Party></cac:ContractingParty>
<cac:ProcurementProject><cbc:Name>Industrielle Sachversicherung für neun reine Gewerbeobjekte</cbc:Name></cac:ProcurementProject>
</ContractAwardNotice>""".encode("utf-8")


class EformsWinnerRoleContractTests(unittest.TestCase):
    def setUp(self):
        self.raw = xml_fixture()
        source = dict(original.SOURCES[m.NOTICE])
        source["original_xml_sha256_pinned"] = hashlib.sha256(self.raw).hexdigest()
        source["original_xml_bytes_pinned"] = len(self.raw)
        p = patch.dict(original.SOURCES, {m.NOTICE: source})
        p.start()
        self.addCleanup(p.stop)

    def test_original_source_has_real_fixed_production_pin(self):
        raw = original.SOURCES[m.NOTICE]
        self.assertEqual(len(raw["original_xml_sha256_pinned"]), 64)
        self.assertEqual(raw["original_xml_bytes_pinned"], len(self.raw))

    def test_explicit_result_party_org_award_path(self):
        r = m.parse_award_roles(self.raw)
        self.assertEqual(r["winner_lot_result_count"], 1)
        self.assertTrue(r["exact_original_xml_sha256_and_bytes_pin_matched_this_execution"])
        self.assertTrue(r["source_winner_names_exactly_match_secondary_mirror_names"])
        win = r["award_role_paths"][0]
        self.assertEqual((win["lot_result_id"], win["lot_id"],
                          win["winning_tender_id"], win["winning_party_id"]),
                         ("RES-0001", "LOT-0001", "TEN-0001", "TPA-0001"))
        self.assertEqual(len(win["winning_party_member_organizations"]), 3)
        self.assertEqual(win["settled_contract_id"], "CON-0001")
        self.assertEqual(r["settled_contracts_linked_to_winning_results"], 1)
        self.assertEqual(r["winning_result_contract_tender_links"], 1)
        self.assertTrue(r["won_tenders_selected_by_settled_contract_not_received_tender_list"])
        self.assertFalse(win["contract_signatories_are_automatically_winning_underwriters"])

    def test_nonwinning_bidder_occurrence_excluded(self):
        r = m.parse_award_roles(self.raw)
        self.assertFalse(any("NOT THE WINNER" in name for name in
                             r["source_organization_names_in_winning_tendering_parties"]))
        self.assertFalse(r["claimed_carrier_insured_buildings"])
        self.assertFalse(r["known_insurance_contract_coin_shares"])
        self.assertFalse(r["actual_carrier_by_location_CAT_exposures_admitted"])

    def test_tampered_original_bytes_rejected_before_roles(self):
        changed = self.raw.replace(b"HDI Global SE", b"HDI GLOBAL SE")
        with self.assertRaisesRegex(ValueError, "PINNED_ORIGINAL_SHA256_MISMATCH"):
            m.parse_award_roles(changed)

    def test_unpinned_original_bytes_rejected(self):
        sample = dict(original.SOURCES[m.NOTICE], original_xml_sha256_pinned=None,
                      original_xml_bytes_pinned=None)
        with patch.dict(original.SOURCES, {m.NOTICE: sample}):
            with self.assertRaisesRegex(ValueError, "ORIGINAL_BYTES_NOT_RECHECKED"):
                m.parse_award_roles(self.raw)

    def test_tender_notice_not_permitted_as_award(self):
        with self.assertRaisesRegex(ValueError, "AWARD_NOTICE_NOT_ALLOWLISTED"):
            m.parse_award_roles(self.raw, notice="558592-2024")

    def test_false_winner_status_never_promoted(self):
        altered = self.raw.replace(b"selec-w", b"all-rej")
        with self.assertRaisesRegex(ValueError, "NO_EXPLICIT_WINNER_RESULT"):
            self.parse_modified(altered)

    def test_no_settled_contract_reference_rejected(self):
        altered = self.raw.replace(
            b'<efac:SettledContract><cbc:ID>CON-0001</cbc:ID></efac:SettledContract>',
            b'')
        with self.assertRaisesRegex(ValueError, "SELECTED_RESULT_WITHOUT_SETTLED_CONTRACT"):
            self.parse_modified(altered)

    def test_dangling_received_tender_reference_rejected(self):
        altered = self.raw.replace(
            b'<efac:LotTender><cbc:ID>TEN-0001</cbc:ID></efac:LotTender>',
            b'<efac:LotTender><cbc:ID>TEN-9999</cbc:ID></efac:LotTender>', 1)
        with self.assertRaisesRegex(ValueError, "RECEIVED_TENDER_ID_NOT_FOUND"):
            self.parse_modified(altered)

    def test_lot_mismatch_rejected(self):
        altered = self.raw.replace(
            b'<efac:TenderLot><cbc:ID>LOT-0001</cbc:ID></efac:TenderLot>',
            b'<efac:TenderLot><cbc:ID>LOT-0003</cbc:ID></efac:TenderLot>',
            1)
        with self.assertRaisesRegex(ValueError, "RECEIVED_TENDER_WRONG_LOT"):
            self.parse_modified(altered)

    def test_winner_party_reference_missing_rejected(self):
        altered = self.raw.replace(
            b'<efac:TenderingParty><cbc:ID>TPA-0001</cbc:ID></efac:TenderingParty>',
            b'<efac:TenderingParty><cbc:ID>TPA-9999</cbc:ID></efac:TenderingParty>',
            1)
        with self.assertRaisesRegex(ValueError, "WINNING_TENDERING_PARTY_NOT_FOUND"):
            self.parse_modified(altered)

    def test_unknown_winner_company_rejected(self):
        altered = self.raw.replace(
            b'<efac:Tenderer><cbc:ID>ORG-0004</cbc:ID></efac:Tenderer>',
            b'<efac:Tenderer><cbc:ID>ORG-9999</cbc:ID></efac:Tenderer>')
        with self.assertRaisesRegex(ValueError, "WINNER_ORGANIZATION_ID_NOT_FOUND"):
            self.parse_modified(altered)

    def test_wrong_buyer_role_rejected(self):
        altered = self.raw.replace(
            b'<cbc:ID>ORG-0001</cbc:ID></cac:PartyIdentification></cac:Party></cac:ContractingParty>',
            b'<cbc:ID>ORG-0002</cbc:ID></cac:PartyIdentification></cac:Party></cac:ContractingParty>')
        with self.assertRaisesRegex(ValueError, "AWARD_BUYER_ROLE_NOT_WBM"):
            self.parse_modified(altered)

    def test_buyer_in_tenderer_group_rejected(self):
        altered = self.raw.replace(
            b'<efac:Tenderer><cbc:ID>ORG-0004</cbc:ID></efac:Tenderer>',
            b'<efac:Tenderer><cbc:ID>ORG-0001</cbc:ID></efac:Tenderer>')
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_BUYER_IN_WINNER_GROUP"):
            self.parse_modified(altered)

    def test_duplicate_tender_party_node_rejected(self):
        needle = (b'<efac:TenderingParty><cbc:ID>TPA-0002</cbc:ID>'
                  b'\n    <efac:Tenderer><cbc:ID>ORG-0005</cbc:ID></efac:Tenderer>'
                  b'\n  </efac:TenderingParty>')
        self.assertIn(needle, self.raw)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_TENDERING_PARTY_ID"):
            self.parse_modified(self.raw.replace(needle, needle + needle))

    def test_organization_mentioned_in_document_not_awarded(self):
        extra = self.raw.replace(b"NOT THE WINNER Versicherung AG",
                                 b"Allianz Versicherung AG")
        r = self.parse_modified(extra)
        self.assertNotIn("Allianz Versicherung AG",
                         r["source_organization_names_in_winning_tendering_parties"])

    def test_renamed_awarded_group_does_not_auto_match_mirror(self):
        altered = self.raw.replace(b"HDI Global SE", b"HDI GLOBAL INSURANCE")
        r = self.parse_modified(altered)
        self.assertFalse(r["source_winner_names_exactly_match_secondary_mirror_names"])
        self.assertIn("HDI GLOBAL INSURANCE",
                      r["source_organization_names_in_winning_tendering_parties"])

    def test_no_second_organization_with_same_xml_id(self):
        needle = (b'<cac:PartyIdentification><cbc:ID>ORG-0005</cbc:ID>'
                  b'</cac:PartyIdentification>')
        self.assertIn(needle, self.raw)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_INVALID_COMPANY"):
            self.parse_modified(self.raw.replace(needle,
                                b'<cac:PartyIdentification><cbc:ID>ORG-0004</cbc:ID>'
                                b'</cac:PartyIdentification>'))

    def test_received_losing_tender_for_same_lot_is_not_a_winner(self):
        self.assertIn(
            b'<efac:LotTender><cbc:ID>TEN-0003</cbc:ID></efac:LotTender>',
            self.raw,
        )
        result = self.parse_modified(self.raw)
        self.assertEqual(result["winning_result_contract_tender_links"], 1)
        self.assertEqual(result["award_role_paths"][0]["winning_tender_id"], "TEN-0001")
        self.assertNotIn(
            "NOT THE WINNER Versicherung AG",
            result["source_organization_names_in_winning_tendering_parties"],
        )

    def test_selected_result_unknown_contract_reference_blocked(self):
        raw = self.raw.replace(
            b'<efac:SettledContract><cbc:ID>CON-0001</cbc:ID></efac:SettledContract>',
            b'<efac:SettledContract><cbc:ID>CON-9999</cbc:ID></efac:SettledContract>',
        )
        with self.assertRaisesRegex(ValueError, "SETTLED_CONTRACT_NOT_FOUND"):
            self.parse_modified(raw)

    def test_contract_without_tender_references_blocked(self):
        token = b'<efac:LotTender><cbc:ID>TEN-0001</cbc:ID></efac:LotTender>\n  </efac:SettledContract>'
        self.assertIn(token, self.raw)
        raw = self.raw.replace(token, b'</efac:SettledContract>')
        with self.assertRaisesRegex(ValueError, "SETTLED_CONTRACT_WITHOUT_TENDER_REFERENCES"):
            self.parse_modified(raw)

    def test_contract_links_received_other_company_without_name_fallback(self):
        token = b'<efac:LotTender><cbc:ID>TEN-0001</cbc:ID></efac:LotTender>\n  </efac:SettledContract>'
        self.assertIn(token, self.raw)
        raw = self.raw.replace(
            token,
            b'<efac:LotTender><cbc:ID>TEN-0003</cbc:ID></efac:LotTender>\n  </efac:SettledContract>',
        )
        result = self.parse_modified(raw)
        self.assertEqual(result["winning_result_contract_tender_links"], 1)
        self.assertEqual(
            result["source_organization_names_in_winning_tendering_parties"],
            ["NOT THE WINNER Versicherung AG"],
        )
        self.assertFalse(result["source_winner_names_exactly_match_secondary_mirror_names"])

    def test_contract_referencing_only_other_lot_cannot_win_this_lot(self):
        token = b'<efac:LotTender><cbc:ID>TEN-0001</cbc:ID></efac:LotTender>\n  </efac:SettledContract>'
        self.assertIn(token, self.raw)
        raw = self.raw.replace(
            token,
            b'<efac:LotTender><cbc:ID>TEN-0002</cbc:ID></efac:LotTender>\n  </efac:SettledContract>',
        )
        with self.assertRaisesRegex(ValueError, "CONTRACT_HAS_NO_TENDER_FOR_SELECTED_LOT"):
            self.parse_modified(raw)

    def test_duplicate_selected_result_contract_reference_blocked(self):
        token = b'<efac:SettledContract><cbc:ID>CON-0001</cbc:ID></efac:SettledContract>'
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CONTRACT_REFERENCE_IN_RESULT"):
            self.parse_modified(self.raw.replace(token, token + token))

    def test_signatory_mention_does_not_make_a_winner(self):
        result = self.parse_modified(self.raw)
        signs = {
            x["source_company_name"]
            for x in result["award_role_paths"][0][
                "contract_signatories_separate_from_winning_tenderers"]
        }
        self.assertIn("NOT THE WINNER Versicherung AG", signs)
        self.assertIn("WBM Wohnungsbaugesellschaft Berlin-Mitte mbH", signs)
        self.assertFalse(result["award_role_paths"][0][
            "contract_signatories_are_automatically_winning_underwriters"])
        self.assertNotIn("NOT THE WINNER Versicherung AG",
                         result["source_organization_names_in_winning_tendering_parties"])

    def test_unknown_contract_signatory_id_blocks(self):
        token = b'<cbc:ID>ORG-0005</cbc:ID>\n    </cac:PartyIdentification></cac:SignatoryParty>'
        self.assertIn(token, self.raw)
        raw = self.raw.replace(
            token,
            b'<cbc:ID>ORG-9999</cbc:ID>\n    </cac:PartyIdentification></cac:SignatoryParty>',
        )
        with self.assertRaisesRegex(ValueError, "CONTRACT_SIGNATORY_NOT_REGISTERED"):
            self.parse_modified(raw)

    def parse_modified(self, raw):
        local = dict(original.SOURCES[m.NOTICE],
                     original_xml_sha256_pinned=hashlib.sha256(raw).hexdigest(),
                     original_xml_bytes_pinned=len(raw))
        with patch.dict(original.SOURCES, {m.NOTICE: local}):
            return m.parse_award_roles(raw)


if __name__ == "__main__":
    unittest.main()
