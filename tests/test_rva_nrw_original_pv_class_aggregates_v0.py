# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only category, AGS and amount gates; no official source values."""
from decimal import Decimal
import copy
import tomllib
from xml.etree import ElementTree as ET
import unittest

from research_runners import rva_nrw_original_pv_class_aggregates_v0 as m


def from_registered_source(d: dict) -> dict:
    keys = m.REGISTER_KEY
    return {
        "source_sha256": m.source.EXPECTED_SHA256,
        "verified_distinct_8digit_AGS_per_sheet": 396,
        "sheets": [{
            "sheet_title": sheet["sheet_name"],
            "units_exact_header": sheet["source_unit"],
            "selected_column_year": 2025 if sheet["is_2025_labeled_Bestand_column"] else None,
            "NRW_aggregate_by_building_type": {
                label: sheet["category_totals"][key]
                for label, key in zip(m.CLASSES, keys)
            }
        } for sheet in d["measures"]],
    }


class RvNRWOriginalClassAggregatesTests(unittest.TestCase):
    def test_original_state_observation_TOML_exact_format_and_units(self):
        d = tomllib.loads(m.REGISTER.read_text(encoding="utf-8"))
        self.assertEqual(d["verified_original_source_sha256"], m.source.EXPECTED_SHA256)
        self.assertEqual(d["source_rows_original_8digit_AGS_verified_and_unique_each_sheet"], 396)
        self.assertEqual(len(d["measures"]), 4)
        self.assertEqual(
            d["measures"][2]["category_totals"]["overall"], "84309002.198"
        )
        self.assertEqual(
            d["measures"][3]["category_totals"]["overall"], "67863744599.832"
        )
        self.assertFalse(d["model_input_admitted"])
        self.assertFalse(d["company_RV_actual_insured_roofs_or_pv_observed"])
        self.assertTrue(m.verify_recorded_state_observation(from_registered_source(d))[
            "recorded_396_municipality_state_aggregates_match_verified_original"
        ])

    def test_register_source_promoted_to_insurer_site_is_blocked(self):
        d = tomllib.loads(m.REGISTER.read_text(encoding="utf-8"))
        d["company_RV_actual_insured_roofs_or_pv_observed"] = True
        with self.assertRaisesRegex(ValueError, "INSURER_SCOPE_INVALID"):
            m.verify_recorded_state_observation(from_registered_source(d), register=d)

    def test_forged_PV_total_blocks_even_when_SHA_remains_same(self):
        d = tomllib.loads(m.REGISTER.read_text(encoding="utf-8"))
        observed = from_registered_source(d)
        observed["sheets"][2]["NRW_aggregate_by_building_type"]["Wohngebäude"] = "40000000.000"
        with self.assertRaisesRegex(ValueError, "VALUE_DRIFT"):
            m.verify_recorded_state_observation(observed, register=d)

    def test_missing_category_typed_source_receipt_blocks(self):
        d = tomllib.loads(m.REGISTER.read_text(encoding="utf-8"))
        observed = from_registered_source(d)
        del d["measures"][0]["category_totals"]["agriculture"]
        with self.assertRaisesRegex(ValueError, "TAXONOMY_DRIFT"):
            m.verify_recorded_state_observation(observed, register=d)

    def test_ROOF_potential_category_sum_vs_publisher_total_after_rounding(self):
        d = tomllib.loads(m.REGISTER.read_text(encoding="utf-8"))
        for sheet in d["measures"]:
            amounts = sheet["category_totals"]
            category_sum = sum((Decimal(amounts[k]) for k in m.REGISTER_KEY[:6]), Decimal(0))
            publisher_total = Decimal(amounts["overall"])
            self.assertLessEqual(abs(category_sum - publisher_total), Decimal("0.003"))

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

    def test_binary_float_serialisation_tail_is_not_an_adverse_category_error(self):
        self.assertEqual(
            m.validate_source_category_subtotal_residual(Decimal("4.732E-9"), "kW"),
            Decimal("0.00001"),
        )
        self.assertEqual(
            m.validate_source_category_subtotal_residual(Decimal("-0.0000036019"), "kWh"),
            Decimal("0.0001"),
        )

    def test_large_category_totals_disagreement_blocks(self):
        for val, units in [(Decimal("0.01"), "kW"), (Decimal("-0.1"), "kWh")]:
            with self.subTest(val=str(val), units=units):
                with self.assertRaisesRegex(ValueError, "OUTSIDE_LEXICAL_FLOAT_TOLERANCE"):
                    m.validate_source_category_subtotal_residual(val, units)

    def test_units_must_be_exact_source_header(self):
        with self.assertRaisesRegex(ValueError, "UNIT_NOT_RECOGNISED"):
            m.validate_source_category_subtotal_residual(Decimal(0), "kWp")

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
