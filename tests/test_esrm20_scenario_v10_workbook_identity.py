# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import io
import unittest
import warnings
import zipfile

from scripts import acquire_efehr_esrm20_scenario_tree_metadata as tree
from scripts import profile_esrm20_scenario_v10_workbook_identity as profile


class FakeResponse:
    def __init__(self, payload: bytes, url: str) -> None:
        self._payload = payload
        self._offset = 0
        self._url = url
        self.status = 200
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def geturl(self) -> str:
        return self._url

    def read(self, size: int = -1) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        end = len(self._payload) if size is None or size < 0 else min(
            len(self._payload), self._offset + size
        )
        chunk = self._payload[self._offset:end]
        self._offset = end
        return chunk


def _blob_sha(payload: bytes) -> str:
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def _sheet_xml(rows: list[list[str]], indexes: dict[str, int]) -> bytes:
    sheet_rows: list[bytes] = []
    for row_number, row in enumerate(rows, start=1):
        cells: list[bytes] = []
        for column_number, value in enumerate(row, start=1):
            column = chr(ord("A") + column_number - 1)
            index = indexes[value]
            cells.append(
                f'<c r="{column}{row_number}" t="s"><v>{index}</v></c>'.encode(
                    "ascii"
                )
            )
        sheet_rows.append(
            f'<row r="{row_number}">'.encode("ascii")
            + b"".join(cells)
            + b"</row>"
        )
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        b"<sheetData>"
        + b"".join(sheet_rows)
        + b"</sheetData></worksheet>"
    )


def _xlsx(
    rows: list[list[str]],
    *,
    extra_members: list[tuple[str, bytes]] | None = None,
    shared_xml_override: bytes | None = None,
    sheet_xml_override: bytes | None = None,
    relationship_target: str = "worksheets/sheet1.xml",
    relationship_target_mode: str | None = None,
    relationships_override: bytes | None = None,
) -> bytes:
    values: list[str] = []
    indexes: dict[str, int] = {}
    for row in rows:
        for value in row:
            if value not in indexes:
                indexes[value] = len(values)
                values.append(value)

    shared = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        + b"".join(
            b"<si><t>"
            + value.replace("&", "&amp;").replace("<", "&lt;").encode("utf-8")
            + b"</t></si>"
            for value in values
        )
        + b"</sst>"
    )
    if shared_xml_override is not None:
        shared = shared_xml_override

    sheet = sheet_xml_override or _sheet_xml(rows, indexes)
    content_types = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        b'<Default Extension="xml" ContentType="application/xml"/>'
        b"</Types>"
    )
    workbook = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        b'<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    mode = (
        b""
        if relationship_target_mode is None
        else f' TargetMode="{relationship_target_mode}"'.encode("ascii")
    )
    relationships = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rId1" '
        b'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        + f'Target="{relationship_target}"'.encode("utf-8")
        + mode
        + b"/></Relationships>"
    )
    if relationships_override is not None:
        relationships = relationships_override

    buffer = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types)
            archive.writestr("xl/workbook.xml", workbook)
            archive.writestr("xl/_rels/workbook.xml.rels", relationships)
            archive.writestr("xl/sharedStrings.xml", shared)
            archive.writestr("xl/worksheets/sheet1.xml", sheet)
            for name, content in extra_members or []:
                archive.writestr(name, content)
    return buffer.getvalue()


def _tree_receipt(payload: bytes, *, blob_id: str | None = None) -> dict:
    object_id = blob_id or _blob_sha(payload)
    entries = [
        {"path": "README.md", "type": "blob", "id": "1" * 40, "mode": "100644"},
        {
            "path": profile.WORKBOOK_PATH,
            "type": "blob",
            "id": object_id,
            "mode": "100644",
        },
        {"path": "ruptures", "type": "tree", "id": "2" * 40, "mode": "040000"},
    ]
    return {
        "schema_version": tree.SCHEMA_VERSION,
        "source_issue": 285,
        "project_id": 273,
        "project_path": "efehr/esrm20_scenario_tests",
        "release_tag": "v1.0",
        "resolved_commit_sha": profile.COMMIT_SHA,
        "tree_entry_count": len(entries),
        "entries": entries,
        "external_bytes_persisted": False,
        "publication_authorized": False,
        "model_use_authorized": False,
    }


class WorkbookIdentityProfileTests(unittest.TestCase):
    def _happy_rows(self) -> list[list[str]]:
        return [
            ["event_id", "event_name"],
            [profile.TARGET_EVENT_ID, "Athens 1999"],
            ["Greece_20-6-1978", "Thessaloniki 1978"],
        ]

    def test_happy_profile_binds_only_by_redacted_same_row_literal(self) -> None:
        payload = _xlsx(self._happy_rows())
        receipt = _tree_receipt(payload)
        calls: list[str] = []

        def opener(request, timeout):
            calls.append(request.full_url)
            self.assertEqual(request.full_url, profile._raw_url())
            return FakeResponse(payload, request.full_url)

        result = profile.acquire_and_profile_workbook_identity(
            tree_acquire=lambda: receipt,
            opener=opener,
            now=lambda: "2026-08-17T22:10:00Z",
            monotonic=lambda: 0.0,
        )

        self.assertEqual(calls, [profile._raw_url()])
        self.assertEqual(result["workbook_git_blob_sha1"], _blob_sha(payload))
        self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(result["target_event_id"], "Greece_07-9-1999")
        self.assertEqual(result["target_event_id_exact_cell_count"], 1)
        self.assertEqual(result["target_event_id_row_count"], 1)
        self.assertEqual(result["same_row_name_literal_binding"], "athens")
        self.assertEqual(result["target_same_row_name_literal_counts"]["athens"], 1)
        self.assertEqual(
            result["target_same_row_name_literal_counts"]["thessaloniki"], 0
        )
        self.assertFalse(result["raw_workbook_cells_returned"])
        self.assertFalse(result["raw_workbook_rows_returned"])
        self.assertTrue(result["provider_file_bytes_read"])
        self.assertFalse(result["external_bytes_persisted"])
        self.assertFalse(result["event_location_inference_authorized"])
        self.assertFalse(result["scenario_selection_authorized"])
        self.assertFalse(result["independent_validation_established"])
        self.assertFalse(result["holdout_status_established"])
        self.assertFalse(result["publication_authorized"])
        self.assertFalse(result["model_use_authorized"])

    def test_target_without_named_same_row_stays_unbound(self) -> None:
        payload = _xlsx(
            [["event_id", "event_name"], [profile.TARGET_EVENT_ID, "Greece event"]]
        )
        result = profile._scan_workbook(payload)
        self.assertEqual(result["target_event_id_row_count"], 1)
        self.assertIsNone(result["same_row_name_literal_binding"])

    def test_contradictory_target_name_rows_fail_closed(self) -> None:
        payload = _xlsx(
            [
                ["event_id", "event_name"],
                [profile.TARGET_EVENT_ID, "Athens 1999"],
                [profile.TARGET_EVENT_ID, "Thessaloniki 1978"],
            ]
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "contradictory same-row name literals",
        ):
            profile._scan_workbook(payload)

    def test_tree_blob_mismatch_and_tree_authority_drift_fail_closed(self) -> None:
        payload = _xlsx(self._happy_rows())
        wrong_blob = _tree_receipt(payload, blob_id="f" * 40)
        calls = 0

        def opener(request, timeout):
            nonlocal calls
            calls += 1
            return FakeResponse(payload, request.full_url)

        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "do not match immutable tree Git blob",
        ):
            profile.acquire_and_profile_workbook_identity(
                tree_acquire=lambda: wrong_blob,
                opener=opener,
                now=lambda: "2026-08-17T22:10:00Z",
                monotonic=lambda: 0.0,
            )
        self.assertEqual(calls, 1)

        drifted = _tree_receipt(payload)
        drifted["publication_authorized"] = True
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "publication_authorized",
        ):
            profile.acquire_and_profile_workbook_identity(
                tree_acquire=lambda: drifted,
                opener=lambda *_args, **_kwargs: self.fail("network must not be reached"),
                now=lambda: "2026-08-17T22:10:00Z",
                monotonic=lambda: 0.0,
            )

    def test_every_tree_entry_requires_canonical_path_object_and_type_mode_pair(self) -> None:
        payload = _xlsx(self._happy_rows())

        duplicate = _tree_receipt(payload)
        duplicate["entries"].append(dict(duplicate["entries"][1]))
        duplicate["tree_entry_count"] += 1
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError, "paths are duplicated"
        ):
            profile._workbook_blob_from_tree(duplicate)

        wrong_mode = _tree_receipt(payload)
        wrong_mode["entries"][0]["mode"] = "040000"
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError, "type/mode pair is invalid"
        ):
            profile._workbook_blob_from_tree(wrong_mode)

        bad_object = _tree_receipt(payload)
        bad_object["entries"][0]["id"] = "not-a-git-object"
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError, "object id is invalid"
        ):
            profile._workbook_blob_from_tree(bad_object)

        bad_path = _tree_receipt(payload)
        bad_path["entries"][0]["path"] = "dir\\README.md"
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError, "path is invalid"
        ):
            profile._workbook_blob_from_tree(bad_path)

        workbook_tree = _tree_receipt(payload)
        workbook_tree["entries"][1]["type"] = "tree"
        workbook_tree["entries"][1]["mode"] = "040000"
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "canonical regular blob",
        ):
            profile._workbook_blob_from_tree(workbook_tree)

    def test_zip_traversal_duplicate_and_xml_entity_fail_closed(self) -> None:
        traversal = _xlsx(
            self._happy_rows(), extra_members=[("../escape.xml", b"<x/>")]
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "member path is noncanonical",
        ):
            profile._scan_workbook(traversal)

        duplicate = _xlsx(
            self._happy_rows(),
            extra_members=[("xl/worksheets/sheet1.xml", b"<worksheet/>")],
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "duplicate member names",
        ):
            profile._scan_workbook(duplicate)

        entity = _xlsx(
            self._happy_rows(),
            shared_xml_override=(
                b'<!DOCTYPE x [<!ENTITY y "boom">]>'
                b"<sst><si><t>&y;</t></si></sst>"
            ),
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "DTD/entity declarations",
        ):
            profile._scan_workbook(entity)

    def test_utf16_entity_documents_fail_closed_before_xml_interpretation(self) -> None:
        utf16_shared = (
            '<?xml version="1.0" encoding="UTF-16"?>'
            '<!DOCTYPE sst [<!ENTITY ev "Greece_07-9-1999">'
            '<!ENTITY city "Athens 1999">]>'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<si><t>&ev;</t></si><si><t>&city;</t></si></sst>'
        ).encode("utf-16")
        payload = _xlsx(self._happy_rows(), shared_xml_override=utf16_shared)
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "XML encoding is outside policy",
        ):
            profile._scan_workbook(payload)

        utf16_sheet = (
            '<?xml version="1.0" encoding="UTF-16"?>'
            '<!DOCTYPE worksheet [<!ENTITY ev "Greece_07-9-1999">'
            '<!ENTITY city "Athens 1999">]>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData><row r="1">'
            '<c r="A1" t="inlineStr"><is><t>&ev;</t></is></c>'
            '<c r="B1" t="inlineStr"><is><t>&city;</t></is></c>'
            '</row></sheetData></worksheet>'
        ).encode("utf-16")
        payload = _xlsx(self._happy_rows(), sheet_xml_override=utf16_sheet)
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "XML encoding is outside policy",
        ):
            profile._scan_workbook(payload)

    def test_only_workbook_referenced_internal_worksheets_can_supply_identity(self) -> None:
        orphan = (
            b'<worksheet xmlns="http://schemas.openxmlformats.org/'
            b'spreadsheetml/2006/main"><sheetData/></worksheet>'
        )
        payload = _xlsx(
            self._happy_rows(),
            extra_members=[("xl/worksheets/orphan.xml", orphan)],
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "orphan or unreferenced worksheets",
        ):
            profile._scan_workbook(payload)

        external = _xlsx(
            self._happy_rows(),
            relationship_target="https://example.invalid/sheet.xml",
            relationship_target_mode="External",
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "external worksheet relationships are forbidden",
        ):
            profile._scan_workbook(external)

        traversal = _xlsx(
            self._happy_rows(), relationship_target="../worksheets/sheet1.xml"
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "relationship target is noncanonical",
        ):
            profile._scan_workbook(traversal)

    def test_foreign_namespace_rows_and_cells_cannot_spoof_identity(self) -> None:
        foreign_sheet = (
            b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            b'xmlns:x="urn:foreign"><sheetData><x:row r="1">'
            b'<x:c r="A1" t="inlineStr"><x:is><x:t>Greece_07-9-1999</x:t></x:is></x:c>'
            b'<x:c r="B1" t="inlineStr"><x:is><x:t>Athens 1999</x:t></x:is></x:c>'
            b"</x:row></sheetData></worksheet>"
        )
        payload = _xlsx(self._happy_rows(), sheet_xml_override=foreign_sheet)
        result = profile._scan_workbook(payload)
        self.assertEqual(result["scanned_row_count"], 0)
        self.assertEqual(result["scanned_cell_count"], 0)
        self.assertEqual(result["target_event_id_exact_cell_count"], 0)
        self.assertIsNone(result["same_row_name_literal_binding"])

    def test_duplicate_cell_reference_and_invalid_shared_index_fail_closed(self) -> None:
        duplicate_cell_sheet = (
            b'<worksheet xmlns="http://schemas.openxmlformats.org/'
            b'spreadsheetml/2006/main"><sheetData><row r="1">'
            b'<c r="A1" t="str"><v>x</v></c>'
            b'<c r="A1" t="str"><v>y</v></c>'
            b"</row></sheetData></worksheet>"
        )
        payload = _xlsx(
            self._happy_rows(), sheet_xml_override=duplicate_cell_sheet
        )
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "duplicate cell reference",
        ):
            profile._scan_workbook(payload)

        bad_index_sheet = (
            b'<worksheet xmlns="http://schemas.openxmlformats.org/'
            b'spreadsheetml/2006/main"><sheetData><row r="1">'
            b'<c r="A1" t="s"><v>999999</v></c>'
            b"</row></sheetData></worksheet>"
        )
        payload = _xlsx(self._happy_rows(), sheet_xml_override=bad_index_sheet)
        with self.assertRaisesRegex(
            profile.ScenarioWorkbookIdentityError,
            "shared-string cell index is out of range",
        ):
            profile._scan_workbook(payload)

    def test_fixed_url_contains_only_immutable_project_path_and_commit(self) -> None:
        url = profile._raw_url()
        self.assertIn(
            "/api/v4/projects/273/repository/files/testing_scenarios.xlsx/raw",
            url,
        )
        self.assertIn(profile.COMMIT_SHA, url)
        self.assertNotIn("v1.1", url)


if __name__ == "__main__":
    unittest.main()
