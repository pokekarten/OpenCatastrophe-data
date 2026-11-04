# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Pure-synthetic offline original XLSX and GPKG archive structural tests."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.nhsl_v1_original_binary_preflight_v0 import (
    NHSLBinaryError, PINNED, _bytes, check_archive, check_sqlite_gpkg,
    inspect_assets, parse_original_dictionary,
)

SHEET_XML_PREFIX = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<sheetData><row r="1">'
)
SHEET_XML_SUFFIX = "</row></sheetData></worksheet>"


def fake_xlsx() -> bytes:
    wb = (
        '<?xml version="1.0"?><workbook '
        'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="polygons" sheetId="1" r:id="rId1"/>'
        '<sheet name="buildings" sheetId="2" r:id="rId2"/></sheets></workbook>'
    )
    rel = (
        '<?xml version="1.0"?><Relationships '
        'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Target="worksheets/sheet1.xml" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>'
        '<Relationship Id="rId2" Target="worksheets/sheet2.xml" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>'
        '</Relationships>'
    )
    polygon_fields = [
        "Sauid", "E_SauidLat", "E_SauidLon", "Et_BldgNum", "Et_BldgArea",
        "Et_BldgValue", "Et_StrValue", "Et_NStrValue", "Et_ContValue",
        "Et_AssetValue", "Et_ResHD", "fasuid",
    ]
    building_fields = [
        "Sauid", "BldgID", "BldgLat", "BldgLon", "E_BldgNum",
        "E_BldgValue", "E_StrValue", "E_NStrValue", "E_ContValue",
        "E_AssetValue", "E_BlgEpoch", "E_SSCZone", "fasuid",
    ]
    def sheet(fields: list[str]) -> str:
        return (
            SHEET_XML_PREFIX
            + "".join(
                f'<c r="{chr(65+i)}1" t="inlineStr"><is><t>{field}</t></is></c>'
                for i, field in enumerate(fields)
            )
            + SHEET_XML_SUFFIX
        )
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", rel)
        z.writestr("xl/worksheets/sheet1.xml", sheet(polygon_fields))
        z.writestr("xl/worksheets/sheet2.xml", sheet(building_fields))
    return stream.getvalue()


def synthetic_gpkg(role: str) -> bytes:
    spec = PINNED[role]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "synthetic.gpkg"
        con = sqlite3.connect(str(path))
        try:
            con.execute("CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY, data_type TEXT, srs_id INTEGER)")
            con.execute("CREATE TABLE gpkg_geometry_columns "
                        "(table_name TEXT, column_name TEXT, geometry_type_name TEXT, srs_id INTEGER)")
            con.execute("CREATE TABLE gpkg_spatial_ref_sys (srs_id INTEGER PRIMARY KEY, organization TEXT)")
            con.execute("INSERT INTO gpkg_spatial_ref_sys VALUES (4326, 'EPSG')")
            table = "fictional_poly" if role == "polygon" else "fictional_archetype"
            geometry = "MULTIPOLYGON" if role == "polygon" else "MULTIPOINT"
            fields = sorted(spec["required_columns"])
            columns = ", ".join(f'"{col}" TEXT' for col in fields)
            con.execute(f'CREATE TABLE "{table}" (feature_id INTEGER PRIMARY KEY, {columns}, geom BLOB)')
            con.execute("INSERT INTO gpkg_contents VALUES (?, 'features', 4326)", (table,))
            con.execute("INSERT INTO gpkg_geometry_columns VALUES (?, 'geom', ?, 4326)", (table, geometry))
            con.execute(
                f'INSERT INTO "{table}" ({",".join(chr(34)+f+chr(34) for f in fields)})'
                f' VALUES ({",".join("?" for _ in fields)})',
                ["invented" for _ in fields],
            )
            con.commit()
        finally:
            con.close()
        return path.read_bytes()


def synthetic_zip(gpkg: bytes, role: str) -> tuple[bytes, dict]:
    spec = copy.deepcopy(PINNED[role])
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(spec["member"], gpkg)
    raw = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info = z.infolist()[0]
        spec["gpkg_bytes"] = info.file_size
        spec["gpkg_crc32"] = f"{info.CRC:08x}"
    return raw, spec


class TestNHSLOfflineBinaryPreflight(unittest.TestCase):
    def test_synthetic_xlsx_fields_and_archetype_semantic_drift(self) -> None:
        result = parse_original_dictionary(fake_xlsx())
        self.assertEqual(result["source_sheets"], ["buildings", "polygons"])
        self.assertIn("fasuid != fsauid", result["literal_difference_to_live_service"]["polygon"])
        self.assertIn("E_BlgEpoch != E_BldgEpoch", result["literal_difference_to_live_service"]["archetype"])

    def test_missing_original_dictionary_field_fails(self) -> None:
        data = fake_xlsx().replace(b"xl/workbook.xml", b"xl/workbook.yy")
        with self.assertRaisesRegex(NHSLBinaryError, "XLSX"):
            parse_original_dictionary(data)
        with self.assertRaisesRegex(NHSLBinaryError, "ZIP"):
            parse_original_dictionary(b"not an xlsx")

    def test_synthetic_gpkg_validates_polygons_and_archetypes(self) -> None:
        for role in ("polygon", "archetype"):
            with self.subTest(role=role):
                data = synthetic_gpkg(role)
                output = check_sqlite_gpkg(data, role, PINNED[role])
                self.assertEqual(output["feature_count"], 1)
                self.assertEqual(output["sqlite_integrity_check"], "ok")
                raw, spec = synthetic_zip(data, role)
                result = check_archive(raw, role, spec)
                self.assertEqual(result["feature_count"], 1)
                self.assertFalse(result["original_rows_or_coordinates_emitted"])

    def test_wrong_geometry_family_rejected(self) -> None:
        gpkg = synthetic_gpkg("polygon")
        with self.assertRaisesRegex(NHSLBinaryError, "geometry"):
            check_sqlite_gpkg(gpkg, "archetype", PINNED["archetype"])

    def test_bad_member_size_crc_and_filename_rejected(self) -> None:
        gpkg = synthetic_gpkg("polygon")
        raw, spec = synthetic_zip(gpkg, "polygon")
        for mutation in ("crc", "size", "name"):
            with self.subTest(mutation=mutation):
                bad = copy.deepcopy(spec)
                if mutation == "crc":
                    bad["gpkg_crc32"] = "00000000"
                if mutation == "size":
                    bad["gpkg_bytes"] += 1
                if mutation == "name":
                    bad["member"] = "other.gpkg"
                with self.assertRaises(NHSLBinaryError):
                    check_archive(raw, "polygon", bad)

    def test_zip_path_traversal_and_extra_file_rejected(self) -> None:
        gpkg = synthetic_gpkg("polygon")
        for name in ("../outside.gpkg", "/tmp/evil.gpkg"):
            with self.subTest(name=name):
                mem = io.BytesIO()
                with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
                    z.writestr(name, gpkg)
                with self.assertRaises(NHSLBinaryError):
                    check_archive(mem.getvalue(), "polygon", PINNED["polygon"])
        raw, spec = synthetic_zip(gpkg, "polygon")
        buf = io.BytesIO(raw)
        with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED) as z:
            z.writestr("unexpected.txt", b"added")
        with self.assertRaisesRegex(NHSLBinaryError, "extra"):
            check_archive(buf.getvalue(), "polygon", spec)

    def test_invalid_sqlite_or_zip_is_blocked(self) -> None:
        with self.assertRaisesRegex(NHSLBinaryError, "SQLite"):
            check_sqlite_gpkg(b"garbage", "polygon", PINNED["polygon"])
        with self.assertRaises(NHSLBinaryError):
            check_archive(b"\x00\x01\x02", "polygon", PINNED["polygon"])

    def test_unpinned_or_missing_files_cannot_pass_main(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            dictionary = root / "synthetic.xlsx"
            polygon = root / "polygon.zip"
            archetype = root / "archetype.zip"
            dictionary.write_bytes(fake_xlsx())
            polygon.write_bytes(synthetic_zip(synthetic_gpkg("polygon"), "polygon")[0])
            archetype.write_bytes(synthetic_zip(synthetic_gpkg("archetype"), "archetype")[0])
            with self.assertRaisesRegex(NHSLBinaryError, "size drift"):
                inspect_assets(dictionary, polygon, archetype)
            with self.assertRaisesRegex(NHSLBinaryError, "missing"):
                _bytes(root / "missing", PINNED["dictionary"])


if __name__ == "__main__":
    unittest.main()
