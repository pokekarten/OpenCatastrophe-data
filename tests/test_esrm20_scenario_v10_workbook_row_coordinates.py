# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import unittest
import zipfile

from scripts import profile_esrm20_scenario_v10_workbook_identity as profile


_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>
"""
_WORKBOOK = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>
</workbook>
"""
_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
</Relationships>
"""


def _workbook_with_row(row_xml: str) -> bytes:
    worksheet = f"""<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>{row_xml}</sheetData>
</worksheet>
"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
        archive.writestr("xl/workbook.xml", _WORKBOOK)
        archive.writestr("xl/_rels/workbook.xml.rels", _RELS)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)
    return buffer.getvalue()


def _cell(ref: str, value: str) -> str:
    return f'<c r="{ref}" t="str"><v>{value}</v></c>'


class WorkbookRowCoordinateIntegrityTests(unittest.TestCase):
    def test_mixed_cell_row_coordinates_fail_closed_before_same_row_binding(self) -> None:
        payload = _workbook_with_row(
            '<row r="1">'
            + _cell("A1", profile.TARGET_EVENT_ID)
            + _cell("B2", "Athens")
            + "</row>"
        )

        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "mixed cell row coordinates",
        ):
            profile._scan_workbook(payload)

    def test_declared_row_coordinate_must_match_cell_reference(self) -> None:
        payload = _workbook_with_row(
            '<row r="2">' + _cell("A1", profile.TARGET_EVENT_ID) + "</row>"
        )

        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "row coordinate disagrees with cell reference",
        ):
            profile._scan_workbook(payload)

    def test_invalid_declared_row_coordinate_fails_closed(self) -> None:
        payload = _workbook_with_row(
            '<row r="0">' + _cell("A1", profile.TARGET_EVENT_ID) + "</row>"
        )

        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "row coordinate is invalid",
        ):
            profile._scan_workbook(payload)

    def test_consistent_cell_coordinates_preserve_same_row_binding(self) -> None:
        payload = _workbook_with_row(
            '<row r="1">'
            + _cell("A1", profile.TARGET_EVENT_ID)
            + _cell("B1", "Athens")
            + "</row>"
        )

        result = profile._scan_workbook(payload)

        self.assertEqual(result["target_event_id_row_count"], 1)
        self.assertEqual(result["target_same_row_name_literal_counts"]["athens"], 1)
        self.assertEqual(result["same_row_name_literal_binding"], "athens")


if __name__ == "__main__":
    unittest.main()
