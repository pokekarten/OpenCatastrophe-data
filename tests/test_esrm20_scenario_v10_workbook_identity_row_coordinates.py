# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import unittest
import zipfile

from scripts import profile_esrm20_scenario_v10_workbook_identity as profile


def _workbook_with_row(row_open: str, cells: list[tuple[str, str]]) -> bytes:
    cell_xml = "".join(
        f'<c r="{ref}" t="inlineStr"><is><t>{value}</t></is></c>'
        for ref, value in cells
    )
    sheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData><row{row_open}>{cell_xml}</row></sheetData>'
        '</worksheet>'
    ).encode("utf-8")
    content_types = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        b'<Default Extension="xml" ContentType="application/xml"/>'
        b'</Types>'
    )
    workbook = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        b'<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>'
        b'</workbook>'
    )
    relationships = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rId1" '
        b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        b'Target="worksheets/sheet1.xml"/>'
        b'</Relationships>'
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", relationships)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()


class WorkbookRowCoordinateIntegrityTests(unittest.TestCase):
    def test_mixed_cell_row_coordinates_cannot_spoof_same_row_binding(self) -> None:
        payload = _workbook_with_row(
            ' r="1"',
            [
                ("A1", profile.TARGET_EVENT_ID),
                ("B2", "Athens 1999"),
            ],
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "mixed cell row coordinates",
        ):
            profile._scan_workbook(payload)

    def test_declared_row_must_match_cell_reference_coordinate(self) -> None:
        payload = _workbook_with_row(
            ' r="2"',
            [
                ("A1", profile.TARGET_EVENT_ID),
                ("B1", "Athens 1999"),
            ],
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "row reference disagrees with cell reference",
        ):
            profile._scan_workbook(payload)

    def test_invalid_declared_row_reference_fails_closed(self) -> None:
        payload = _workbook_with_row(
            ' r="0"',
            [("A1", profile.TARGET_EVENT_ID)],
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "row reference is invalid",
        ):
            profile._scan_workbook(payload)

    def test_absent_row_reference_allows_consistent_cell_coordinates(self) -> None:
        payload = _workbook_with_row(
            "",
            [
                ("A1", profile.TARGET_EVENT_ID),
                ("B1", "Athens 1999"),
            ],
        )
        result = profile._scan_workbook(payload)
        self.assertEqual(result["target_event_id_exact_cell_count"], 1)
        self.assertEqual(result["target_event_id_row_count"], 1)
        self.assertEqual(result["same_row_name_literal_binding"], "athens")
        self.assertEqual(result["target_same_row_name_literal_counts"]["athens"], 1)
        self.assertEqual(
            result["target_same_row_name_literal_counts"]["thessaloniki"], 0
        )


if __name__ == "__main__":
    unittest.main()
