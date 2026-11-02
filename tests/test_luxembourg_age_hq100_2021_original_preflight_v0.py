# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for Luxembourg AGE HQ100 original-source preflight."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from research_runners.luxembourg_age_hq100_2021_original_preflight_v0 import (
    inspect, HQ100OriginalError,
)


def shp_header(*, kind: int = 5, length: int = 100) -> bytes:
    b = bytearray(100)
    struct.pack_into(">i", b, 0, 9994)
    struct.pack_into(">i", b, 24, length // 2)
    struct.pack_into("<ii", b, 28, 1000, kind)
    return bytes(b)


def shp_record(*, kind: int = 5) -> bytes:
    n_parts, n_points = 1, 5
    content = bytearray(44 + 4 * n_parts + 16 * n_points)
    struct.pack_into("<I", content, 0, kind)
    struct.pack_into("<II", content, 36, n_parts, n_points)
    struct.pack_into("<I", content, 44, 0)
    size = 100 + 8 + len(content)
    return (shp_header(kind=kind, length=size)
            + struct.pack(">II", 1, len(content) // 2)
            + bytes(content))


def dbf_header() -> bytes:
    b = bytearray(65 + 4)
    b[0] = 3
    struct.pack_into("<IHH", b, 4, 1, 65, 4)
    b[32:37] = b"DEPTH"
    b[43] = ord("N")
    b[48] = 3
    b[49] = 1
    b[64] = 0x0D
    b[65:] = b" 123"
    return bytes(b)


def archive(path: Path, *, bad_member: str | None = None, bad_shape: bool = False):
    files = {
        "hq100/test.shp": shp_record(kind=8 if bad_shape else 5),
        "hq100/test.shx": shp_header(),
        "hq100/test.dbf": dbf_header(),
        "hq100/test.prj": b'PROJCS["LUREF",AUTHORITY["EPSG","2169"]]',
    }
    if bad_member is not None:
        files[bad_member] = b"test"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return hashlib.sha1(path.read_bytes()).hexdigest()


class HQ100OriginalPreflightTests(unittest.TestCase):
    def test_full_synthetic_headers_and_no_source_data_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.zip"
            checksum = archive(path)
            report = inspect(path, expected_sha1=checksum)
            self.assertTrue(report["original_zip_sha1_matches_publisher"])
            self.assertEqual(report["original_member_suffix_counts"][".shp"], 1)
            self.assertEqual(report["original_member_suffix_counts"][".dbf"], 1)
            dbf = next(x for x in report["format_header_inventory_only"]
                       if x["format"] == ".dbf")
            self.assertEqual(dbf["dbf_declared_records"], 1)
            self.assertTrue(report["shp_records_match_dbf_records"])
            shp = next(x for x in report["format_header_inventory_only"]
                       if x["format"] == ".shp")
            self.assertEqual(shp["shp_polygon_record_count"], 1)
            self.assertEqual(shp["shp_total_coordinate_pairs_skipped_without_decoding"], 5)
            self.assertEqual(dbf["dbf_field_schema"][0]["name"], "DEPTH")
            self.assertFalse(report["actual_hazard_geometry_read"])
            self.assertFalse(report["individual_depth_values_read"])
            self.assertFalse(report["model_input_admitted"])
            self.assertNotIn(" 123", json.dumps(report))

    def test_wrong_published_checksum_or_unsafe_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.zip"
            archive(path)
            with self.assertRaisesRegex(HQ100OriginalError, "SHA-1"):
                inspect(path)
            checksum = archive(path, bad_member="../do-not-extract.txt")
            with self.assertRaisesRegex(HQ100OriginalError, "Unsafe"):
                inspect(path, expected_sha1=checksum)

    def test_source_shp_invalid_record_length_or_kind_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.zip"
            checksum = archive(path, bad_shape=True)
            # Point-formatted data must NOT masquerade as polygonal flood support.
            with self.assertRaisesRegex(HQ100OriginalError, "structural scan blocked"):
                inspect(path, expected_sha1=checksum)

    def test_unexpected_symlink_and_corrupt_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / "test.zip"
            checksum = archive(original)
            symlink = Path(tmp) / "alias.zip"
            symlink.symlink_to(original)
            with self.assertRaisesRegex(HQ100OriginalError, "identity"):
                inspect(symlink, expected_sha1=checksum)
            original.write_bytes(b"falsified-zip")
            with self.assertRaisesRegex(HQ100OriginalError, "SHA-1"):
                inspect(original, expected_sha1=checksum)


if __name__ == "__main__":
    unittest.main()
