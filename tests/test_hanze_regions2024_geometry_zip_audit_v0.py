# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic archive guards; never import or publish provider polygon bytes."""
from __future__ import annotations

import hashlib
import io
import struct
import unittest
from unittest.mock import patch
import zipfile

from research_runners import hanze_regions2024_geometry_zip_audit_v0 as audit


def shp_header(shape_type=5, length=100):
    data = bytearray(100)
    struct.pack_into(">I", data, 0, 9994)
    struct.pack_into(">I", data, 24, length // 2)
    struct.pack_into("<I", data, 28, 1000)
    struct.pack_into("<I", data, 32, shape_type)
    struct.pack_into("<4d", data, 36, -10.0, 35.0, 30.0, 71.0)
    return bytes(data)


def dbf_header():
    result = bytearray(65)
    result[0] = 3
    struct.pack_into("<IHH", result, 4, 0, 65, 6)
    result[32:36] = b"Code"
    result[43] = ord("C")
    result[48] = 5
    result[64] = 13
    return bytes(result)


def fake_archive(changes=None):
    files = {
        "Regions/Regions_2024.shp": shp_header(),
        "Regions/Regions_2024.shx": shp_header(),
        "Regions/Regions_2024.dbf": dbf_header(),
        "Regions/Regions_2024.prj": 'GEOGCS["WGS 84"]'.encode("ascii"),
    }
    files.update(changes or {})
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, value in files.items():
            if value is not None:
                zf.writestr(name, value)
    return out.getvalue()


def run(blob):
    with patch.object(audit, "PUBLISHER_BYTES", len(blob)), patch.object(
        audit, "PUBLISHER_MD5",
        hashlib.md5(blob, usedforsecurity=False).hexdigest()
    ):
        return audit.inspect_hanze_region_geometry_zip(
            blob, expected_sha256=hashlib.sha256(blob).hexdigest())


class HANZERegionGeometryZipTests(unittest.TestCase):
    def test_shape_dbf_projection_inventory_not_hazard_footprints(self):
        out = run(fake_archive())
        self.assertEqual(out["archive_member_count"], 4)
        self.assertEqual(out["member_extensions_counts"],
                         {".dbf": 1, ".prj": 1, ".shp": 1, ".shx": 1})
        self.assertEqual(len(out["shapefile_component_groups"]), 1)
        geo = out["shapefile_component_groups"][0]
        self.assertEqual(geo["shape_type_code"], 5)
        self.assertEqual(geo["shape_index_record_count"], 0)
        self.assertEqual(geo["dbf"]["field_names"], ["Code"])
        self.assertTrue(geo["has_projection_wkt"])
        self.assertFalse(out["model_input_admitted"])
        self.assertFalse(out["geometry_topology_or_projection_validated"])
        self.assertTrue(out["admin_polygons_are_not_flood_hazard_footprints"])
        self.assertNotIn("WGS 84", str(out))
        self.assertNotIn("Regions/Regions_2024.shp", str(out))

    def test_original_byte_size_md5_sha_fail_closed(self):
        blob = fake_archive()
        with self.assertRaisesRegex(audit.RegionArchiveError, "byte length"):
            audit.inspect_hanze_region_geometry_zip(blob)
        with patch.object(audit, "PUBLISHER_BYTES", len(blob)), patch.object(audit, "PUBLISHER_MD5", "0"*32):
            with self.assertRaisesRegex(audit.RegionArchiveError, "MD5"):
                audit.inspect_hanze_region_geometry_zip(blob)
        with patch.object(audit, "PUBLISHER_BYTES", len(blob)), patch.object(audit, "PUBLISHER_MD5", hashlib.md5(blob, usedforsecurity=False).hexdigest()):
            with self.assertRaisesRegex(audit.RegionArchiveError, "SHA256"):
                audit.inspect_hanze_region_geometry_zip(blob, expected_sha256="0"*64)

    def test_member_traversal_and_unreviewed_suffix_rejected(self):
        with self.assertRaisesRegex(audit.RegionArchiveError, "relative"):
            run(fake_archive({"../secrets.txt": b"secret"}))
        with self.assertRaisesRegex(audit.RegionArchiveError, "unreviewed"):
            run(fake_archive({"archive/command.py": b"print('bad')"}))

    def test_corrupted_shapefile_header_and_missing_trio_rejected(self):
        with self.assertRaisesRegex(audit.RegionArchiveError, "shapefile magic"):
            run(fake_archive({"Regions/Regions_2024.shp": b"\x00"*100}))
        with self.assertRaisesRegex(audit.RegionArchiveError, "trio incomplete"):
            run(fake_archive({"Regions/Regions_2024.dbf": None}))
        with self.assertRaisesRegex(audit.RegionArchiveError, "not a polygon"):
            run(fake_archive({"Regions/Regions_2024.shp": shp_header(1),
                              "Regions/Regions_2024.shx": shp_header(1)}))

    def test_dbf_declared_record_count_is_checked_against_shx(self):
        bad = bytearray(dbf_header())
        struct.pack_into("<I", bad, 4, 1)
        with self.assertRaisesRegex(audit.RegionArchiveError, "DBF length too short"):
            run(fake_archive({"Regions/Regions_2024.dbf": bytes(bad)}))


if __name__ == "__main__":
    unittest.main()
