# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network BT-150 percent *label*, contract identity, and safety tests."""
from __future__ import annotations

import unittest

from research_runners import ted_wbm_original_contract_identifier_labels_v0 as m


def build(
    ids=("Status Quo 50% Beteiligung", "40% Beteiligung Status Quo",
         "10% Beteiligung"),
    *,
    contract_tenders=("TEN-0001", "TEN-0002", "TEN-0003"),
    add_titles=True,
) -> bytes:
    pieces = []
    for i, (label, tender) in enumerate(zip(ids, contract_tenders), 1):
        pieces.append(f'''
<efac:SettledContract>
 <cbc:ID>CON-000{i}</cbc:ID>
 <efac:ContractReference><cbc:ID>{label}</cbc:ID></efac:ContractReference>
 {("<cbc:Title>Commercial insurance contract</cbc:Title>"
   if add_titles else "")}
 <efac:LotTender><cbc:ID>{tender}</cbc:ID></efac:LotTender>
</efac:SettledContract>''')
    return ('''
<ContractAwardNotice xmlns="urn:oasis:names:specification:ubl:schema:xsd:ContractAwardNotice-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
 xmlns:efac="http://data.europa.eu/p27/eforms-ubl-extension-aggregate-components/1"
 xmlns:efext="http://data.europa.eu/p27/eforms-ubl-extensions/1"
 xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">
<ext:UBLExtensions><ext:UBLExtension><ext:ExtensionContent><efext:EformsExtension>
<efac:NoticeResult>''' + "".join(pieces) +
'''</efac:NoticeResult></efext:EformsExtension>
</ext:ExtensionContent></ext:UBLExtension></ext:UBLExtensions>
</ContractAwardNotice>''').encode("utf-8")


class ContractIdentifierLabelTests(unittest.TestCase):
    expected = {"CON-0001": "TEN-0001", "CON-0002": "TEN-0002",
                "CON-0003": "TEN-0003"}

    def extract(self, data):
        return m.extract_contract_identifiers(
            data, expected_tender_contracts=self.expected)

    def test_exact_con_to_ten_with_three_distinct_percent_labels(self):
        rows = self.extract(build())
        self.assertEqual(list(sorted(rows)), list(m.EXPECTED_CONTRACTS))
        self.assertEqual(
            [rows[x]["percentage_string_in_business_identifier"]
             for x in m.EXPECTED_CONTRACTS], [50, 40, 10])
        self.assertEqual(
            [rows[x]["original_business_identifier_BT_150"]
             for x in m.EXPECTED_CONTRACTS],
            ["Status Quo 50% Beteiligung", "40% Beteiligung Status Quo",
             "10% Beteiligung"])
        for row in rows.values():
            self.assertFalse(row["actual_insurer_policy_share_proved"])
            self.assertFalse(row["insured_buildings_policy_schedule_or_tiv_proved"])

    def test_contract_title_optional_and_not_a_share_source(self):
        rows = self.extract(build(
            ids=("Contract A", "Contract B", "Contract C"), add_titles=False))
        self.assertEqual(
            [rows[c]["percentage_string_in_business_identifier"]
             for c in m.EXPECTED_CONTRACTS], [None, None, None])
        self.assertIsNone(rows["CON-0001"]["original_contract_title_BT_721_optional"])

    def test_cannot_confuse_unrelated_tender_with_awarded_tender(self):
        xml = build(contract_tenders=("TEN-9000", "TEN-0002", "TEN-0003"))
        with self.assertRaisesRegex(ValueError, "GRAPH_TENDER_MISMATCH"):
            self.extract(xml)

    def test_missing_bt150_business_identifier_fails_closed(self):
        xml = build().replace(
            b"<efac:ContractReference><cbc:ID>Status Quo 50% Beteiligung</cbc:ID></efac:ContractReference>",
            b"", 1)
        with self.assertRaisesRegex(ValueError, "MISSING_OR_REPEAT_BUSINESS_ID"):
            self.extract(xml)

    def test_duplicate_bt150_business_identifier_fails_closed(self):
        row = (b"<efac:ContractReference><cbc:ID>10% Beteiligung</cbc:ID>"
               b"</efac:ContractReference>")
        xml = build().replace(row, row + row)
        with self.assertRaisesRegex(ValueError, "MISSING_OR_REPEAT_BUSINESS_ID"):
            self.extract(xml)

    def test_business_identifiers_must_be_unique_in_source(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_BUSINESS_ID"):
            self.extract(build(ids=("Quota 50%", "Quota 40%", "Quota 40%")))

    def test_multi_percent_business_label_rejected_not_added(self):
        with self.assertRaisesRegex(ValueError, "MULTIPLE_PERCENT_LABELS"):
            self.extract(build(ids=("50% and 10%?", "40%", "10%")))

    def test_percent_101_refused(self):
        with self.assertRaisesRegex(ValueError, "OUT_OF_RANGE"):
            self.extract(build(ids=("101% participation", "40%", "10%")))

    def test_zero_percent_label_refused(self):
        with self.assertRaisesRegex(ValueError, "OUT_OF_RANGE"):
            self.extract(build(ids=("0% participation", "40%", "10%")))

    def test_missing_third_contract_not_a_proven_complete_mapping(self):
        xml = build().replace(
            b"<cbc:ID>CON-0003</cbc:ID>", b"<cbc:ID>CON-0002</cbc:ID>")
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CON_ID"):
            self.extract(xml)

    def test_wrong_root_notice_type_refused(self):
        xml = build().replace(b"<ContractAwardNotice", b"<ContractNotice", 1)
        xml = xml.replace(b"</ContractAwardNotice>", b"</ContractNotice>")
        with self.assertRaisesRegex(ValueError, "WRONG_NOTICE_ROOT"):
            self.extract(xml)

    def test_dtd_substitution_refused(self):
        xml = build().replace(
            b"<ContractAwardNotice", b'<!DOCTYPE ContractAwardNotice [<!ENTITY bad "ok">]>'
                                      b"<ContractAwardNotice", 1)
        with self.assertRaisesRegex(ValueError, "DTD_FORBIDDEN"):
            self.extract(xml)

    def test_no_unbounded_contract_label_text(self):
        xml = build(ids=("A" * 200, "40%", "10%"))
        with self.assertRaisesRegex(ValueError, "INVALID_TEXT"):
            self.extract(xml)

    def test_false_contract_number_within_text_not_parsed_as_number(self):
        rows = self.extract(build(ids=("50 times participation",
                                       "40 times participation",
                                       "10 times participation")))
        self.assertTrue(all(
            row["percentage_string_in_business_identifier"] is None
            for row in rows.values()))

    def test_legal_share_not_promoted_from_sum_of_100_labels(self):
        rows = self.extract(build())
        total = sum(x["percentage_string_in_business_identifier"]
                    for x in rows.values())
        self.assertEqual(total, 100)
        self.assertTrue(all(
            x["percentage_is_contract_identifier_label_only"]
            and not x["actual_insurer_policy_share_proved"]
            for x in rows.values()))

    def test_wrong_company_lot_graph_must_not_be_substituted(self):
        expected = dict(self.expected)
        expected["CON-0001"] = "TEN-0003"
        with self.assertRaisesRegex(ValueError, "GRAPH_TENDER_MISMATCH"):
            m.extract_contract_identifiers(
                build(), expected_tender_contracts=expected)


if __name__ == "__main__":
    unittest.main()
