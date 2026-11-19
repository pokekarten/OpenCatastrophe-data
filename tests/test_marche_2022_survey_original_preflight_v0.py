# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic XLSX/ZIP fixtures only; no real property or survey microdata in Git."""

from __future__ import annotations

import io
import json
import unittest
import zipfile

from research_runners.marche_2022_survey_original_preflight_v0 import (
    SourceStructureError, _form_a_parent_count, audit_archive,
    PREFIX, EXPECTED,
)

N = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _xlsx(*, ids: tuple[str, ...] = ("fake1", "fake2"), dictionary: int = 1,
          headers_ok: bool = True, styled_blank: bool = False,
          populated_no_id: bool = False) -> bytes:
    names = [f'<sheet name="{i}" sheetId="{i}" />' for i in range(1, dictionary + 1)]
    book = f'<workbook xmlns="{N}"><sheets>{"".join(names)}</sheets></workbook>'
    def inline(cell: str, value: str) -> str:
        return f'<c r="{cell}" t="inlineStr"><is><t>{value}</t></is></c>'
    hdr = (f'<row r="3">{inline("A3", "ID" if headers_ok else "Wrong")}'
           f'{inline("E3", "Latitude")}{inline("F3", "Longitude")}</row>')
    rows = []
    for i, identifier in enumerate(ids, 4):
        # The synthetic identifier is deliberately not a real site or address.
        rows.append(f'<row r="{i}">{inline(f"A{i}", identifier)}'
                    f'{inline(f"B{i}", "dummy-non-geographic")}</row>')
    if styled_blank:
        rows.append(f'<row r="{len(ids)+4}"><c r="A{len(ids)+4}" s="1"/></row>')
    if populated_no_id:
        k = len(ids) + 4 + int(styled_blank)
        rows.append(f'<row r="{k}">{inline(f"B{k}", "orphan-synthetic")}</row>')
    xml = f'<worksheet xmlns="{N}"><sheetData>{hdr}{"".join(rows)}</sheetData></worksheet>'
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("xl/workbook.xml", book)
        archive.writestr("xl/worksheets/sheet1.xml", xml)
    return result.getvalue()


def _archive(sector: str = "industrial", *, ids=("fake1", "fake2"),
             styled_blank: bool = False, populated_no_id: bool = False,
             duplicate_ids: bool = False, missing_form: bool = False,
             bad_header: bool = False, traversal: bool = False,
             bad_dictionary: bool = False) -> bytes:
    prefix = PREFIX[sector]
    dictionary_path = (prefix + "Data_dictionary.xlsx" if sector == "industrial"
                       else prefix + "Data dictionary.xlsx")
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        expected_sheets = EXPECTED[sector]["dictionary_sheets"]
        archive.writestr(dictionary_path, _xlsx(dictionary=expected_sheets - int(bad_dictionary)))
        for form in "ABCDE":
            if form == "C" and missing_form:
                continue
            contents = (_xlsx(ids=ids if not duplicate_ids else ("fake1", "fake1"),
                              styled_blank=styled_blank,
                              populated_no_id=populated_no_id,
                              headers_ok=not bad_header)
                        if form == "A" else _xlsx())
            archive.writestr(prefix + f"Form_{form}.xlsx", contents)
        if traversal:
            archive.writestr("../privacy-unsafe.txt", "synthetic")
    return raw.getvalue()


class MarcheOriginalPreflightTests(unittest.TestCase):
    def test_business_parent_count_and_privacy(self) -> None:
        out = audit_archive(_archive(), "industrial", count_override=2,
                            verify_release_hash=False)
        self.assertEqual(out["form_a_unique_parent_survey_count"], 2)
        self.assertEqual(out["data_dictionary_sheet_count"], 7)
        self.assertFalse(out["model_admitted"])
        self.assertFalse(out["contains_original_row_level_data_in_output"])
        self.assertNotIn("fake1", json.dumps(out))

    def test_residential_parent_count(self) -> None:
        out = audit_archive(_archive("residential", ids=("fake3",)), "residential",
                            count_override=1, verify_release_hash=False)
        self.assertEqual(out["form_a_unique_parent_survey_count"], 1)
        self.assertEqual(out["data_dictionary_sheet_count"], 9)

    def test_styled_blank_row_is_not_a_survey(self) -> None:
        out = audit_archive(_archive(styled_blank=True), "industrial",
                            count_override=2, verify_release_hash=False)
        self.assertEqual(out["form_a_unique_parent_survey_count"], 2)

    def test_populated_no_id_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "parent identifier"):
            audit_archive(_archive(populated_no_id=True), "industrial",
                          count_override=2, verify_release_hash=False)

    def test_duplicate_parent_id_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "duplicate"):
            audit_archive(_archive(duplicate_ids=True), "industrial",
                          count_override=2, verify_release_hash=False)

    def test_header_three_not_silent_assumption(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "header"):
            audit_archive(_archive(bad_header=True), "industrial",
                          count_override=2, verify_release_hash=False)

    def test_missing_form_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "missing"):
            audit_archive(_archive(missing_form=True), "industrial",
                          count_override=2, verify_release_hash=False)

    def test_traversal_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "path"):
            audit_archive(_archive(traversal=True), "industrial",
                          count_override=2, verify_release_hash=False)

    def test_dictionary_sheet_structure_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "dictionary"):
            audit_archive(_archive(bad_dictionary=True), "industrial",
                          count_override=2, verify_release_hash=False)

    def test_wrong_original_zip_hash_fails_closed(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "MD5/SHA"):
            audit_archive(_archive(), "industrial", verify_release_hash=True)

    def test_corrupt_form_a_fails_closed(self) -> None:
        with self.assertRaises(SourceStructureError):
            _form_a_parent_count(b"not-a-zip", expected_count=1)


if __name__ == "__main__":
    unittest.main()
