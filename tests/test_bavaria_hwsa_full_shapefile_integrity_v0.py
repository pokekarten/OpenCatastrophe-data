# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely synthetic LfU-style ZIP fixtures; no external geometry in repository."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners import bavaria_hwsa_full_shapefile_integrity_v0 as m


ROOT = Path(__file__).resolve().parents[1]


def shapefile_header(size: int, bbox: tuple[float, float, float, float]) -> bytes:
    h = bytearray(100)
    struct.pack_into(">I", h, 0, 9994)
    struct.pack_into(">I", h, 24, size // 2)
    struct.pack_into("<II", h, 28, 1000, 3)
    struct.pack_into("<4d", h, 36, *bbox)
    return bytes(h)


def invented_shape(n: int, epsg: int, *, bad_offset: bool = False,
                   bad_vertex: bool = False):
    if epsg == 4258:
        a, b = 11.0, 48.0
        step = 0.001
    else:
        a, b = 550000.0, 5350000.0
        step = 1.0
    bbox = (a, b, a + step, b + step)
    shp = bytearray(shapefile_header(100 + n * 88, bbox))
    shx = bytearray(shapefile_header(100 + n * 8, bbox))
    for i in range(n):
        rec = bytearray(80)
        struct.pack_into("<I", rec, 0, 3)
        struct.pack_into("<4d", rec, 4, *bbox)
        struct.pack_into("<II", rec, 36, 1, 2)
        struct.pack_into("<I", rec, 44, 0)
        struct.pack_into("<4d", rec, 48,
                         a, b, a + (step * (9 if bad_vertex and i == 0 else 1)),
                         b + step)
        offset_words = (100 + i * 88) // 2
        if bad_offset and i == 0:
            offset_words += 4
        shx.extend(struct.pack(">II", offset_words, 40))
        shp.extend(struct.pack(">II", i + 1, 40))
        shp.extend(rec)
    return bytes(shp), bytes(shx)


def invented_dbf(n: int, *, bad_row_count: bool = False, deleted: bool = False) -> bytes:
    widths = (13, 30, 30, 50, 200)
    head_len, record_len = 193, 324
    dbf = bytearray(head_len + n * record_len + 1)
    dbf[0] = 3
    struct.pack_into("<IHH", dbf, 4, n + int(bad_row_count), head_len, record_len)
    for i, (name, width) in enumerate(zip(m.FIELD_NAMES, widths)):
        offset = 32 + i * 32
        rawname = name.encode("ascii")
        dbf[offset:offset + len(rawname)] = rawname
        dbf[offset + 11] = ord("C")
        dbf[offset + 16] = width
    dbf[192] = 13
    for i in range(n):
        dbf[head_len + i * record_len] = (ord("*") if deleted and i == 0 else ord(" "))
    dbf[-1] = 0x1A
    return bytes(dbf)


def fixture_zip(epsg: int, *, wrong_kind: str = "",
                bad_offset: bool = False, bad_vertex: bool = False,
                bad_row_count: bool = False, bad_crs: bool = False) -> bytes:
    with BytesIO() as buffer:
        with ZipFile(buffer, "w", ZIP_DEFLATED) as zout:
            for kind, n in m.EXPECTED_COUNTS.items():
                shp, shx = invented_shape(n, epsg,
                                         bad_offset=bad_offset and kind == "deich",
                                         bad_vertex=bad_vertex and kind == "deich")
                dbf = invented_dbf(n, bad_row_count=bad_row_count and kind == "deich")
                prj = ('GEOGCS["ETRS_1989"]' if epsg == 4258
                       else 'PROJCS["ETRS_1989_UTM_Zone_32N"]').encode()
                if bad_crs and kind == "deich":
                    prj = b'GEOGCS["WGS84"]'
                for ext, data in (("dbf", dbf), ("prj", prj),
                                  ("shp", shp), ("shx", shx)):
                    name = f"{kind}_epsg{epsg}.{ext}"
                    if wrong_kind and kind == wrong_kind and ext == "shp":
                        name = "unsafe/../../hijack.shp"
                    zout.writestr(name, data)
        return buffer.getvalue()


class BavariaFullShapefileIntegrityTests(unittest.TestCase):
    def test_actual_source_counts_and_format_contract(self):
        self.assertEqual(m.EXPECTED_COUNTS, {
            "deich": 2171, "hwschutzwand": 801, "hwschutzsystem": 891
        })
        self.assertEqual(sum(m.EXPECTED_COUNTS.values()), 3863)
        self.assertEqual(set(m.SOURCE_ARCHIVES), {4258, 25832})
        self.assertEqual(m.FIELD_NAMES,
                         ("WWO_KNZ", "GEW_KNZ", "OBJ_ART", "WWA", "LINK"))

    def test_all_three_polyline_layers_synthetic_original_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.zip"
            path.write_bytes(fixture_zip(4258))
            receipt = m.inspect_original_zip(path, 4258)
            self.assertEqual(receipt["total_source_records"], 3863)
            self.assertEqual(receipt["archive_member_count"], 12)
            self.assertTrue(receipt["full_original_zip_crc_and_spatial_geometry_checked"])
            for kind, n in m.EXPECTED_COUNTS.items():
                with self.subTest(kind=kind):
                    detail = receipt["classes"][kind]
                    self.assertEqual(detail["source_dbf"]["records_in_source_dbf"], n)
                    self.assertEqual(detail["source_line_geometry"]["source_polyline_records"], n)
                    self.assertEqual(detail["source_line_geometry"]["polyline_parts_checked"], n)
                    self.assertEqual(detail["source_line_geometry"]["polyline_points_checked"], 2*n)
                    self.assertEqual(detail["source_line_geometry"]["source_null_shape_records"], 0)
                    self.assertEqual(detail["source_dbf"]["deleted_row_flags"], 0)
                    self.assertFalse(detail["per_record_insured_protection_proven"])

    def test_both_projection_exports_are_not_doubled(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "4258.zip"
            second = Path(tmp) / "25832.zip"
            first.write_bytes(fixture_zip(4258))
            second.write_bytes(fixture_zip(25832))
            result = m.inspect_original_archives({4258: first, 25832: second})
            self.assertEqual(result["counted_unique_source_rows_not_both_projection_exports"], 3863)
            self.assertFalse(result["model_input_admitted"])
            self.assertFalse(result["WRI_hazard_defence_depth_correction_computed"])
            self.assertFalse(result["reprojecting_EPSG_to_WRI_4326_performed"])
            self.assertEqual(set(result["source_archives_proved"]), {4258, 25832})

    def test_mutated_geometry_index_and_outlier_vertices_block(self):
        for variant in ("bad_offset", "bad_vertex", "bad_row_count", "bad_crs"):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "fake-source.zip"
                path.write_bytes(fixture_zip(4258, **{variant: True}))
                with self.assertRaises(m.GeometryGateError):
                    m.inspect_original_zip(path, 4258)

    def test_zip_manifest_and_bad_content_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "source.zip"
            p.write_bytes(fixture_zip(4258, wrong_kind="deich"))
            with self.assertRaises(m.GeometryGateError):
                m.inspect_original_zip(p, 4258)
            p.write_bytes(b"not an original ZIP")
            with self.assertRaises(m.GeometryGateError):
                m.inspect_original_zip(p, 4258)
            p.write_bytes(b"x" * (m.MAX_ARCHIVE + 1))
            with self.assertRaises(m.GeometryGateError):
                m.inspect_original_zip(p, 4258)

    def test_missing_wrong_epsg_or_duplicate_inputs_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "source.zip"
            p.write_bytes(fixture_zip(4258))
            with self.assertRaises(m.GeometryGateError):
                m.inspect_original_zip(p, 25832)
            with self.assertRaises(m.GeometryGateError):
                m.inspect_original_archives({})
            with self.assertRaises(m.GeometryGateError):
                m.inspect_original_archives({4258: p, 25832: p})

    def test_deleted_rows_are_identified_not_silently_discarded(self):
        result = m._inspect_dbf(invented_dbf(6, deleted=True))
        self.assertEqual(result["records_in_source_dbf"], 6)
        self.assertEqual(result["deleted_row_flags"], 1)

    def test_cli_does_not_overwrite_original_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fake-source.zip"
            path.write_bytes(b"synthetic-only")
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/bavaria_hwsa_full_shapefile_integrity_v0.py"),
                "--epsg-4258", str(path),
                "--out", str(path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(path.read_bytes(), b"synthetic-only")


if __name__ == "__main__":
    unittest.main()
