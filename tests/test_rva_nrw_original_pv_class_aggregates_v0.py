# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only category, AGS and amount gates; no official source values."""
from decimal import Decimal
from xml.etree import ElementTree as ET
import unittest

from research_runners import rva_nrw_original_pv_class_aggregates_v0 as m


class RvNRWOriginalClassAggregatesTests(unittest.TestCase):
    def test_typed_1990_2025_header_family(self):
        headers = m.expected_headers("Bestand Leistung [kW]", True)
        self.assertEqual(len(headers), 254)
        self.assertEqual(headers[2], "AGS")
        self.assertEqual(headers[3], "Gemeinde")
        self.assertEqual(headers[4], "Bestand Leistung [kW] 1990 Wohngebäude")
        self.assertEqual(headers[255], "Bestand Leistung [kW] 2025 Insgesamt")

    def test_potential_seven_disjoint_named_six_classes_and_total(self):
        headers = m.expected_headers("Potenzial Ertrag [kWh]", False)
        self.assertEqual(len(headers), 9)
        self.assertEqual(headers[4], "Potenzial Ertrag [kWh] Wohngebäude")
        self.assertEqual(headers[10], "Potenzial Ertrag [kWh] Insgesamt")
        self.assertEqual(len(set(m.CLASSES[:6])), 6)

    def test_german_number_no_forged_comma_conversion(self):
        self.assertEqual(m.decimal_amount("1250.250"), Decimal("1250.250"))
        with self.assertRaisesRegex(ValueError, "NUMERIC_INVALID"):
            m.decimal_amount("1.250,50")

    def test_numeric_nan_and_inf_rejected(self):
        for val in ["NaN", "Infinity", "-Infinity", "1e999"]:
            with self.subTest(val=val):
                with self.assertRaises(ValueError):
                    m.decimal_amount(val)

    def test_negative_value_rejected(self):
        with self.assertRaisesRegex(ValueError, "NEGATIVE"):
            m.decimal_amount("-0.01")

    def test_empty_missing_and_excessive_number_rejected(self):
        for val in ["", "   ", "3"*100, None]:
            with self.subTest(val=val):
                with self.assertRaises(ValueError):
                    m.decimal_amount(val)

    def test_duplicate_ags_rejected_without_printing_ags(self):
        rows = [{2: "05162020", 3: "SYN_PLACE"}] * 396
        with self.assertRaisesRegex(ValueError, "DUPLICATE_AGS"):
            m.check_ags(rows)

    def test_wrong_ags_length_rejected(self):
        rows = [{2: f"05{i:06d}", 3: "SYN_PLACE"} for i in range(395)]
        with self.assertRaisesRegex(ValueError, "COUNT_CHANGED"):
            m.check_ags(rows)

    def test_exact_municipality_key_count_and_unique(self):
        rows = [{2: f"05{i:06d}", 3: "SYN_PLACE"} for i in range(396)]
        self.assertEqual(len(m.check_ags(rows)), 396)

    def test_ags_with_missing_geography_fails_closed(self):
        rows = [{2: f"05{i:06d}", 3: "SYN_PLACE"} for i in range(396)]
        rows[32] = {2: rows[32][2], 3: ""}
        with self.assertRaisesRegex(ValueError, "AGSCODE_OR_LABEL"):
            m.check_ags(rows)

    def test_duplicate_xml_reference_fails(self):
        root = ET.fromstring(
            '<row xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<c r="B2"><v>1</v></c><c r="B2"><v>2</v></c></row>'
        )
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CELL"):
            m.parse_row_cells(root, [])

    def test_source_full_byte_pin_required_even_for_synthetic(self):
        with self.assertRaisesRegex(ValueError, "BAD_SIZE"):
            m.verify_and_aggregate(b"not the exact source")

    def test_semantic_domain_no_company_insurance_by_definition(self):
        self.assertEqual(len(m.YEARS), 36)
        self.assertEqual(m.SHEETS[2][2], "kW")
        self.assertEqual(m.SHEETS[3][2], "kWh")
        self.assertNotIn("R+V", str(m.CLASSES))


if __name__ == "__main__":
    unittest.main()
