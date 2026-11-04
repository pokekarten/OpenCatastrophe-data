# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic workbook schema tests. No insurer, town, or original raw source data."""
import io
import json
import unittest
import zipfile

from research_runners import rva_nrw_original_pv_schema_observation_v0 as audit


def fixture(*, duplicate=False, missing_sheet=False, bad_shared=False, bad_ref=False, macro=False):
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    content = (
        f'<workbook xmlns="{ns}"><sheets>'
        f'<sheet name="Technisches Potenzial" sheetId="1"/>'
        + ('<sheet name="Missing" sheetId="2"/>' if missing_sheet else '')
        + '</sheets></workbook>'
    )
    strings = ["Gemeindeschlüssel", "PV Potenzial kWp", "Gebäudetyp", "PRIVATE_FAKE_MUNICIPALITY", "Wohngebäude"]
    shared = f'<sst xmlns="{ns}">' + "".join(f"<si><t>{s}</t></si>" for s in strings) + '</sst>'
    cell_a = "A1" if not bad_ref else "BAD-CELL"
    row1 = (
        f'<row r="1"><c r="{cell_a}" t="s"><v>0</v></c>'
        f'<c r="B1" t="s"><v>{999 if bad_shared else 1}</v></c>'
        f'<c r="C1" t="s"><v>2</v></c>'
        + ('<c r="A1" t="s"><v>0</v></c>' if duplicate else '')
        + '</row>'
    )
    rows = (
        row1
        + '<row r="2"><c r="A2" t="s"><v>3</v></c>'
          '<c r="B2"><v>11.25</v></c><c r="C2" t="s"><v>4</v></c></row>'
        + '<row r="3"><c r="A3" t="inlineStr"><is><t>05162020</t></is></c>'
          '<c r="B3"><v>14.5</v></c><c r="C3" t="s"><v>4</v></c></row>'
    )
    sheet = f'<worksheet xmlns="{ns}"><sheetData>{rows}</sheetData></worksheet>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", content)
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
        if macro:
            archive.writestr("xl/vbaProject.bin", b"never-run")
        archive.comment = b"X" * 1200
    return buf.getvalue()


class RvaNrwPvSchemaTests(unittest.TestCase):
    def test_header_labels_and_no_record_leak(self):
        got = audit.describe(fixture(), pinned=False)
        out = json.dumps(got)
        self.assertNotIn("PRIVATE_FAKE_MUNICIPALITY", out)
        self.assertNotIn("05162020", out)
        sheet = got["spreadsheet_sheets"][0]
        self.assertEqual(sheet["rows_with_xml_elements"], 3)
        self.assertEqual(sheet["body_row_elements"], 2)
        self.assertEqual(sheet["first_header_labels_only"][1]["header"], "PV Potenzial kWp")
        self.assertIn("PV Potenzial kWp", [x["header"] for x in sheet["domain_header_hints_only"]])
        self.assertEqual(sheet["body_cell_types"]["numeric"], 2)
        self.assertEqual(sheet["candidate_key_format_counts_unassigned_columns"]["eight_digits_first_4_cols"], 1)

    def test_source_sha_mandatory_real_runner(self):
        with self.assertRaisesRegex(ValueError, "SHA256_MISMATCH"):
            audit.describe(fixture(), pinned=True)

    def test_no_observed_insurer_addresses_or_actual_pv(self):
        got = audit.describe(fixture(), pinned=False)
        self.assertIs(got["actual_pv_installations_verified"], False)
        self.assertIs(got["actual_rv_sites_or_insured_values_verified"], False)
        self.assertIs(got["building_category_semantics_validated"], False)
        self.assertIs(got["rva_model_input_admitted"], False)

    def test_duplicate_header_coordinates_blocked(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_HEADER"):
            audit.describe(fixture(duplicate=True), pinned=False)

    def test_malformed_coordinate_blocked(self):
        with self.assertRaisesRegex(ValueError, "CELL_REF_MALFORMED"):
            audit.describe(fixture(bad_ref=True), pinned=False)

    def test_bad_shared_index_blocked(self):
        with self.assertRaisesRegex(ValueError, "SHARED_STRING_OOB"):
            audit.describe(fixture(bad_shared=True), pinned=False)

    def test_sheet_name_xml_count_mismatch_blocked(self):
        with self.assertRaisesRegex(ValueError, "NONCANONICAL_SHEET_RELATION"):
            audit.describe(fixture(missing_sheet=True), pinned=False)

    def test_macro_blocked_by_parent_byte_integrity_gate(self):
        with self.assertRaisesRegex(ValueError, "UNSAFE_ZIP_ENTRY"):
            audit.describe(fixture(macro=True), pinned=False)

    def test_header_sanitization_printable_only(self):
        self.assertEqual(audit._safe_label("  Bad\r\n Label  "), "Bad Label")
        self.assertEqual(len(audit._safe_label("A"*150)), audit.MAX_HEADER_LENGTH)

    def test_not_all_8digit_fields_are_proven_municipal_codes(self):
        got = audit.describe(fixture(), pinned=False)
        key = got["spreadsheet_sheets"][0]["candidate_key_format_counts_unassigned_columns"]
        self.assertEqual(key["eight_digits_first_4_cols"], 1)
        self.assertNotIn("ags_verified", json.dumps(got))


if __name__ == "__main__":
    unittest.main()
