# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic OOXML only; never source provider bytes or buildings."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners.eubucco_lu_original_metadata_xlsx_v0 import (
    SourceMetadataError, inspect,
)

ROOT = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"></workbook>"""
SHARED = """<?xml version="1.0" encoding="UTF-8"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<si><t>country</t></si><si><t>source</t></si>
<si><t>Luxembourg</t></si><si><t>Dataset ACT</t></si>
<si><t>France</t></si><si><t>Other</t></si>
</sst>"""
SHEET = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData>
<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>
<row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2" t="s"><v>3</v></c></row>
<row r="3"><c r="A3" t="s"><v>4</v></c><c r="B3" t="s"><v>5</v></c></row>
</sheetData></worksheet>"""


def make_xlsx(path: Path, *, sheet=SHEET, shared=SHARED, extra=None):
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("xl/workbook.xml", ROOT)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        z.writestr("xl/sharedStrings.xml", shared)
        if extra:
            z.writestr(*extra)
    return path


class SourceMetadataTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "provider.xlsx"
        make_xlsx(self.path)

    def test_luxembourg_only_with_exact_source_receipt(self):
        checksum = hashlib.sha256(self.path.read_bytes()).hexdigest()
        result = inspect(self.path, expected_sha256=checksum)
        self.assertEqual(result["luxembourg_source_metadata_row_count"], 1)
        self.assertEqual(result["luxembourg_source_metadata_rows"][0]["row"], 2)
        self.assertEqual(result["luxembourg_source_metadata_rows"][0]["metadata_cells"]["B"], "Dataset ACT")
        self.assertTrue(result["independent_prior_sha256_verified"])
        self.assertFalse(result["source_lineage_independence_verified"])
        self.assertFalse(result["licence_and_model_input_admitted"])
        self.assertTrue(result["no_building_geometries_read"])

    def test_unpinned_reports_without_claiming_verification(self):
        self.assertFalse(inspect(self.path)["independent_prior_sha256_verified"])
        with self.assertRaisesRegex(SourceMetadataError, "SHA-256 mismatch"):
            inspect(self.path, expected_sha256="0" * 64)

    def test_lu_exact_and_inline_string(self):
        xml=SHEET.replace('<c r="A2" t="s"><v>2</v></c>',
                          '<c r="A2" t="inlineStr"><is><t>LU</t></is></c>')
        make_xlsx(self.path, sheet=xml)
        self.assertEqual(inspect(self.path)["luxembourg_source_metadata_row_count"], 1)

    def test_never_match_unrelated_substring(self):
        xml=SHEET.replace('<v>2</v>', '<v>4</v>').replace('<v>3</v>', '<v>5</v>')
        make_xlsx(self.path, sheet=xml)
        self.assertEqual(inspect(self.path)["luxembourg_source_metadata_row_count"], 0)

    def test_traversal_and_external_links_blocked(self):
        make_xlsx(self.path, extra=("../evil", b"bad"))
        with self.assertRaisesRegex(SourceMetadataError, "unsafe"):
            inspect(self.path)
        make_xlsx(self.path, extra=("xl/externalLinks/externalLink1.xml", b"bad"))
        with self.assertRaisesRegex(SourceMetadataError, "unsafe"):
            inspect(self.path)

    def test_corrupted_shared_index_blocked(self):
        xml=SHEET.replace('<v>2</v>', '<v>999</v>')
        make_xlsx(self.path, sheet=xml)
        with self.assertRaisesRegex(SourceMetadataError, "shared string"):
            inspect(self.path)

    def test_reject_symlink_and_wrong_file_type(self):
        alias = self.path.parent / "alias.xlsx"
        try:
            alias.symlink_to(self.path)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(SourceMetadataError, "regular"):
            inspect(alias)
        self.path.write_text("not a zip")
        with self.assertRaisesRegex(SourceMetadataError, "cannot safely inspect"):
            inspect(self.path)

    def test_output_is_deterministic_and_contains_no_individual_buildings(self):
        first = inspect(self.path)
        second = inspect(self.path)
        self.assertEqual(first, second)
        raw = json.dumps(first)
        self.assertNotIn("geometry", raw)
        self.assertNotIn("insured_value", raw)


if __name__ == "__main__":
    unittest.main()
