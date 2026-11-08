# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic source shapes; no original Italian survey values or identifiers."""

from __future__ import annotations

import io
import json
import unittest
import zipfile
from xml.sax.saxutils import escape

from research_runners.marche_2022_survey_original_preflight_v0 import SourceStructureError
from research_runners.marche_2022_water_surface_elevation_probe_v0 import (
    TARGET_COLUMN, DEPTH_COLUMN, classify_storage, profile_form_a,
    check_dictionary_for_depth,
)

N = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def make_form(
    sector: str = "industrial", values: tuple[str, ...] = ("1.8", "unknown", ""),
    *, bad_header: bool = False, duplicate: bool = False, styled_empty: bool = False,
) -> bytes:
    target = TARGET_COLUMN[sector]
    depth = DEPTH_COLUMN[sector]
    def cell(addr: str, value: str) -> str:
        return f'<c r="{addr}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    header = ('<row r="3">' + cell("A3", "ID") +
              cell(f"{target}3", "Other measurement" if bad_header else "Water surface elevation") +
              cell(f"{depth}3", "hw") +
              '</row>')
    records = []
    for i, value in enumerate(values, 4):
        id_value = "fake-parent-1" if duplicate and i == 5 else f"fake-parent-{i-3}"
        body = cell(f"A{i}", id_value)
        if value:
            body += cell(f"{target}{i}", value)
            body += cell(f"{depth}{i}", value)
        records.append(f'<row r="{i}">{body}</row>')
    if styled_empty:
        i = len(values) + 4
        records.append(f'<row r="{i}"><c r="A{i}" s="1"/></row>')
    xml = f'<worksheet xmlns="{N}"><sheetData>{header}{"".join(records)}</sheetData></worksheet>'
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as file:
        file.writestr("xl/worksheets/sheet1.xml", xml)
    return out.getvalue()



def make_dictionary(sector: str = "industrial", *, wrong_unit: bool = False) -> bytes:
    label = "Measurement in feet" if wrong_unit else "Measurement in meters"
    missing = "7" if sector == "industrial" else "2"
    def c(pos: str, txt: str) -> str:
        return f'<c r="{pos}" t="inlineStr"><is><t>{escape(txt)}</t></is></c>'
    sheet = (
        f'<worksheet xmlns="{N}"><sheetData>'
        f'<row r="5">{c("C5","hw")}{c("D5","float")}{c("E5",label)}{c("G5",missing)}</row>'
        f'<row r="6">{c("C6","Water surface elevation")}{c("D6","float")}'
        f'{c("E6","Water surface elevation is computed as the sum of terrain elevation, hw, and ∆Q.")}</row>'
        f'</sheetData></worksheet>'
    )
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return out.getvalue()


class MarcheAmbiguousWaterSurfaceTests(unittest.TestCase):
    def test_storage_types_are_only_counts(self) -> None:
        result = profile_form_a(make_form(), sector="industrial", expected_parents=3)
        self.assertEqual(result["storage_type_counts"], {
            "numeric": 1, "non_numeric": 1, "blank": 1,
        })
        self.assertEqual(result["outside_water_depth_storage_counts"], {
            "numeric": 1, "non_numeric": 1, "blank": 1,
        })
        self.assertEqual(result["outside_water_depth_field"], "hw")
        self.assertFalse(result["water_depth_above_floor_verified"])
        self.assertFalse(result["can_fit_depth_damage_function"])
        self.assertFalse(result["individual_source_values_exported"])
        text = json.dumps(result)
        self.assertNotIn("fake-parent", text)
        self.assertNotIn("unknown", text)

    def test_residential_uses_distinct_source_column(self) -> None:
        result = profile_form_a(make_form("residential", ("2.1",)), sector="residential", expected_parents=1)
        self.assertEqual(result["storage_type_counts"]["numeric"], 1)

    def test_styled_blank_row_not_a_parent(self) -> None:
        result = profile_form_a(make_form(styled_empty=True), sector="industrial", expected_parents=3)
        self.assertEqual(result["parent_count"], 3)

    def test_duplicate_parent_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "Duplicate"):
            profile_form_a(make_form(duplicate=True), sector="industrial", expected_parents=3)

    def test_header_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "label"):
            profile_form_a(make_form(bad_header=True), sector="industrial", expected_parents=3)

    def test_parent_population_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "parent population"):
            profile_form_a(make_form(), sector="industrial", expected_parents=133)

    def test_unknown_sector_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "Unknown"):
            profile_form_a(make_form(), sector="other", expected_parents=3)

    def test_missing_distinct_from_zero(self) -> None:
        self.assertEqual(classify_storage(""), "blank")
        self.assertEqual(classify_storage("0"), "numeric")
        self.assertEqual(classify_storage("0.0"), "numeric")
        self.assertEqual(classify_storage("NA"), "non_numeric")
        self.assertEqual(classify_storage("2,5"), "non_numeric")

    def test_nonfinite_measurement_rejected(self) -> None:
        for candidate in ("NaN", "Infinity", "-Inf"):
            with self.subTest(candidate=candidate), self.assertRaisesRegex(
                SourceStructureError, "Nonfinite"
            ):
                classify_storage(candidate)

    def test_original_dictionary_semantics_verified(self) -> None:
        self.assertTrue(check_dictionary_for_depth(make_dictionary(), "industrial"))
        self.assertTrue(check_dictionary_for_depth(make_dictionary("residential"), "residential"))

    def test_wrong_hazard_unit_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "dictionary"):
            check_dictionary_for_depth(make_dictionary(wrong_unit=True), "industrial")

    def test_broken_workbook_rejected(self) -> None:
        with self.assertRaises(SourceStructureError):
            profile_form_a(b"not a ZIP", sector="industrial", expected_parents=3)


if __name__ == "__main__":
    unittest.main()
