# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only GDW source ZIP structural tests, zero original data."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from research_runners import gdw_v1_shapefile_archive_preflight_v0 as m

COUNTS = {"GDW_barriers_v1_0": (1, 1), "GDW_reservoirs_v1_0": (5, 1)}


def shp_header(shape_type: int, byte_length: int) -> bytes:
    value = bytearray(100)
    struct.pack_into(">I", value, 0, 9994)
    struct.pack_into(">I", value, 24, byte_length // 2)
    struct.pack_into("<I", value, 28, 1000)
    struct.pack_into("<I", value, 32, shape_type)
    return bytes(value)


def files(**flags):
    items = {}
    for name, (shape_type, _) in COUNTS.items():
        typ = 0 if flags.get("null_geom") and shape_type == 5 else shape_type
        if shape_type == 1:
            body = struct.pack("<Idd", typ, 13.4, 52.2)
        else:
            ring = ((13.0, 52.0), (13.1, 52.0), (13.1, 52.1),
                    (13.0, 52.1), (13.0, 52.0))
            if flags.get("open_ring"):
                ring = (*ring[:-1], (13.05, 52.0))
            if flags.get("bad_coordinate"):
                ring = (*ring[:-1], (999.0, 52.0))
            body = struct.pack("<IddddII", typ, 13.0, 52.0, 13.1, 52.1, 1, len(ring))
            body += struct.pack("<I", 0)
            body += b"".join(struct.pack("<dd", x, y) for x, y in ring)
        record = struct.pack(">II", 1, len(body) // 2) + body
        shp = shp_header(shape_type, 100 + len(record)) + record
        index_offset = 52 if flags.get("bad_offset") and shape_type == 5 else 50
        shx = shp_header(shape_type, 108) + struct.pack(">II", index_offset, len(body) // 2)
        if flags.get("missing_shx") and shape_type == 5:
            shx = None
        dbf = bytearray(32)
        dbf[0] = 3
        struct.pack_into("<I", dbf, 4, 2 if flags.get("dbf_rows") and shape_type == 5 else 1)
        struct.pack_into("<H", dbf, 8, 65)
        struct.pack_into("<H", dbf, 10, 7)
        field = bytearray(32)
        field[:6] = b"GDW_ID"
        field[11] = ord("N")
        field[16] = 6
        if flags.get("wrong_gdw_id") and shape_type == 5:
            ident = b"     2"
        elif flags.get("invalid_gdw_id") and shape_type == 5:
            ident = b"   -99"
        else:
            ident = b"     1"
        deletion = b"*" if flags.get("deleted_row") and shape_type == 5 else b" "
        dbf = bytes(dbf) + bytes(field) + b"\r" + deletion + ident
        prefix = "GDW_v1_0_shp/"
        items[prefix + name + ".shp"] = shp
        if shx is not None:
            items[prefix + name + ".shx"] = shx
        items[prefix + name + ".dbf"] = dbf
        items[prefix + name + ".prj"] = (
            b'PROJCS["Not a geographic CRS"]' if flags.get("wrong_prj") and shape_type == 5
            else b'GEOGCS["GCS_WGS_1984"]'
        )
    items["GDW_v1_0_shp/GDW_TechDoc_v1_0.pdf"] = b"synthetic documentation"
    if flags.get("unsafe_path"):
        items["../escape.txt"] = b"bad"
    return items


def build_zip(**flags) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, content in files(**flags).items():
            z.writestr(name, content)
        if flags.get("casefold_duplicate"):
            z.writestr("GDW_v1_0_shp/GDW_BARRIERS_v1_0.shp", b"duplicate")
        if flags.get("symlink"):
            inf = zipfile.ZipInfo("GDW_v1_0_shp/source-link")
            inf.create_system = 3
            inf.external_attr = 0o120777 << 16
            z.writestr(inf, b"/private/etc/passwd")
    return out.getvalue()


class GDWShapefilePreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "original.zip"

    def inspect(self, b, *, sha=True):
        self.path.write_bytes(b)
        return m.inspect(self.path, original_size=len(b),
                         publisher_md5=hashlib.md5(b, usedforsecurity=False).hexdigest(),
                         expected_sha256=hashlib.sha256(b).hexdigest() if sha else None,
                         counts=COUNTS)

    def test_synthetic_valid_identity_count_crc_and_nonadmission(self):
        result = self.inspect(build_zip())
        self.assertEqual(result["layer_record_counts"], {x: 1 for x in COUNTS})
        self.assertTrue(result["provider_declared_md5_matches"])
        self.assertTrue(result["caller_supplied_sha256_matches"])
        self.assertTrue(result["shp_shx_dbf_row_counts_agree"])
        self.assertTrue(result["zip_streams_crc_checked"])
        self.assertTrue(result["coordinate_bounds_and_polygon_ring_closure_checked"])
        self.assertTrue(result["dbf_gdw_id_subset_verified"])
        self.assertEqual(result["dbf_point_only_id_count"], 0)
        for key in ("point_polygon_spatial_join_verified", "record_coordinates_or_ids_exported",
                    "topology_validated", "missing_value_sentinels_applied",
                    "model_input_admitted", "provider_bytes_committed"):
            self.assertFalse(result[key])
        self.assertNotIn("synthetic documentation", str(result))

    def test_unpinned_digest_is_not_an_independent_identity(self):
        self.assertFalse(self.inspect(build_zip(), sha=False)["caller_supplied_sha256_matches"])

    def test_provider_md5_or_byte_size_drift_blocks(self):
        b = build_zip()
        self.path.write_bytes(b)
        with self.assertRaisesRegex(m.GDWArchiveError, "MD5 mismatch"):
            m.inspect(self.path, original_size=len(b), publisher_md5="0" * 32, counts=COUNTS)
        with self.assertRaisesRegex(m.GDWArchiveError, "size or"):
            m.inspect(self.path, original_size=len(b) + 1,
                      publisher_md5=hashlib.md5(b, usedforsecurity=False).hexdigest(), counts=COUNTS)
        with self.assertRaisesRegex(m.GDWArchiveError, "SHA256 mismatch"):
            m.inspect(self.path, original_size=len(b),
                      publisher_md5=hashlib.md5(b, usedforsecurity=False).hexdigest(),
                      expected_sha256="0" * 64, counts=COUNTS)

    def test_invalid_origins_and_shapefile_mismatch_block(self):
        for case in ("bad_offset", "missing_shx", "dbf_rows", "wrong_prj", "null_geom", "unsafe_path", "casefold_duplicate", "symlink", "open_ring", "bad_coordinate", "wrong_gdw_id", "invalid_gdw_id", "deleted_row"):
            with self.subTest(case=case), self.assertRaises(m.GDWArchiveError):
                self.inspect(build_zip(**{case: True}))

    def test_missing_shape_count_blocks(self):
        b = build_zip()
        self.path.write_bytes(b)
        with self.assertRaises(m.GDWArchiveError):
            m.inspect(self.path, original_size=len(b),
                      publisher_md5=hashlib.md5(b, usedforsecurity=False).hexdigest(),
                      counts={"GDW_barriers_v1_0": (1, 2), "GDW_reservoirs_v1_0": (5, 1)})

    def test_zip_crc_error_blocks(self):
        b = bytearray(build_zip())
        needle = b"synthetic documentation"
        # Generate a stored-member fixture so one changed byte invalidates the expected CRC.
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as z:
            for n, content in files().items():
                z.writestr(n, content)
        b = bytearray(out.getvalue())
        idx = b.index(needle)
        b[idx] ^= 0x01
        with self.assertRaises(m.GDWArchiveError):
            self.inspect(bytes(b))

    def test_symlink_local_input_blocks(self):
        other = Path(self.tmp.name) / "symlink.zip"
        self.path.write_bytes(build_zip())
        other.symlink_to(self.path)
        with self.assertRaises(m.GDWArchiveError):
            m.inspect(other)


if __name__ == "__main__":
    unittest.main()
