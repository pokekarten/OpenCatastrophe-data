# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only negative/structural tests; every test raster is synthetic."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from research_runners import noaa_mrms_mesh_original_preflight_v0 as mrms

ROOT = Path(__file__).resolve().parents[1]


def section(number: int, size: int) -> bytearray:
    part = bytearray(size)
    part[:4] = size.to_bytes(4, "big")
    part[4] = number
    return part


def synthetic_grib(parameter: int = 28, extra_section: bool = False) -> bytes:
    """Structurally minimal illustrative GRIB2; NOT an encoded physical raster."""
    sec1 = section(1, 21)
    sec1[5:7] = (161).to_bytes(2, "big")  # NOAA OAR center
    sec1[7:9] = (0).to_bytes(2, "big")
    sec1[12:14] = (2020).to_bytes(2, "big")
    sec1[14:19] = bytes([10, 14, 0, 0, 25])
    sec3 = section(3, 14)
    sec3[6:10] = (100).to_bytes(4, "big")
    sec3[12:14] = (0).to_bytes(2, "big")
    sec4 = section(4, 11)
    sec4[7:9] = (0).to_bytes(2, "big")
    sec4[9] = 3
    sec4[10] = parameter
    parts = [sec1]
    if extra_section:
        parts.append(section(2, 5))
    parts.extend((sec3, sec4, section(5, 11), section(6, 6), section(7, 6)))
    raw = b"".join(parts)
    length = 16 + len(raw) + 4
    return b"GRIB" + b"\x00\x00" + bytes([209, 2]) + length.to_bytes(8, "big") + raw + b"7777"


class NOAAOriginalMRMSPreflightTests(unittest.TestCase):
    def test_synthetic_sections_and_parameter_semantics(self) -> None:
        for number in (28, 29):
            with self.subTest(parameter=number):
                result = mrms.parse_grib2_structure(synthetic_grib(number), number)
                self.assertEqual(result["grib_discipline"], 209)
                self.assertEqual(result["originating_center"], 161)
                self.assertEqual(result["parameter_category"], 3)
                self.assertEqual(result["parameter_number"], number)
                self.assertEqual(result["source_parameter_unit_from_noaa_table"], "mm")
                self.assertEqual(result["reference_utc"], "2020-10-14T00:00:25+00:00")
                self.assertFalse(result["grid_values_decoded"])

    def test_optional_section_two_not_automatically_rejected(self) -> None:
        info = mrms.parse_grib2_structure(synthetic_grib(extra_section=True), 28)
        self.assertEqual(info["grib_section_sequence"], [1, 2, 3, 4, 5, 6, 7])

    def test_bounded_gzip_crc_and_trailing_member_checks(self) -> None:
        original = gzip.compress(synthetic_grib(), mtime=0)
        self.assertEqual(mrms.inflate_gzip_capped(original), synthetic_grib())
        bad_crc = bytearray(original)
        bad_crc[-8] ^= 1
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "CRC32"):
            mrms.inflate_gzip_capped(bytes(bad_crc))
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "extra member"):
            mrms.inflate_gzip_capped(original + original)
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "incomplete"):
            mrms.inflate_gzip_capped(original[:-8])
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "bound"):
            mrms.inflate_gzip_capped(b"X" * (mrms.MAX_COMPRESSED_BYTES + 1))

    def test_grib_wrong_discipline_and_product_id(self) -> None:
        raw = bytearray(synthetic_grib())
        raw[6] = 0
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "discipline"):
            mrms.parse_grib2_structure(bytes(raw), 28)
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "category/parameter"):
            mrms.parse_grib2_structure(synthetic_grib(parameter=28), 29)

    def test_grib_length_end_marker_and_section_structure_fail_closed(self) -> None:
        raw = bytearray(synthetic_grib())
        raw[-1] = 1
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "terminator"):
            mrms.parse_grib2_structure(bytes(raw), 28)
        raw = bytearray(synthetic_grib())
        raw[8:16] = (len(raw) + 1).to_bytes(8, "big")
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "length"):
            mrms.parse_grib2_structure(bytes(raw), 28)
        raw = bytearray(synthetic_grib())
        raw[16:20] = (0).to_bytes(4, "big")
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "section length"):
            mrms.parse_grib2_structure(bytes(raw), 28)
        raw = bytearray(synthetic_grib())
        raw[16 + 21 + 14 + 11 + 11 + 6 + 4] = 4  # section 7 -> repeated 4
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "duplicated"):
            mrms.parse_grib2_structure(bytes(raw), 28)

    def test_wrong_center_reference_date_and_point_count(self) -> None:
        raw = bytearray(synthetic_grib())
        raw[16 + 5:16 + 7] = (12).to_bytes(2, "big")
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "center"):
            mrms.parse_grib2_structure(bytes(raw), 28)
        raw = bytearray(synthetic_grib())
        raw[16 + 14] = 13
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "timestamp"):
            mrms.parse_grib2_structure(bytes(raw), 28)
        raw = bytearray(synthetic_grib())
        sec3_offset = 16 + 21
        raw[sec3_offset + 6:sec3_offset + 10] = (0).to_bytes(4, "big")
        with self.assertRaisesRegex(mrms.MRMSPreflightError, "point count"):
            mrms.parse_grib2_structure(bytes(raw), 28)

    def test_hash_bound_original_gate_with_synthetic_only(self) -> None:
        synthetic = gzip.compress(synthetic_grib(), mtime=0)
        pin = dict(mrms.SOURCE_OBJECTS["mesh"])
        pin["compressed_size"] = len(synthetic)
        pin["compressed_sha256"] = hashlib.sha256(synthetic).hexdigest()
        with patch.dict(mrms.SOURCE_OBJECTS, {"mesh": pin}):
            receipt = mrms.audit_original(synthetic, "mesh", pin["basename"])
            self.assertTrue(receipt["gzip_crc32_checked"])
            self.assertEqual(receipt["compressed_sha256"], pin["compressed_sha256"])
            self.assertFalse(receipt["source_admission_granted"])
            self.assertFalse(receipt["direct_first_party_acquisition_authenticated"])
            self.assertFalse(receipt["scientific_fitness_established"])
            self.assertFalse(receipt["model_input_approved"])
            self.assertFalse(receipt["insurer_losses_inferred"])
            self.assertNotIn("claims", json.dumps(receipt).lower())
            corrupted = bytearray(synthetic)
            corrupted[-3] ^= 1
            with self.assertRaisesRegex(mrms.MRMSPreflightError, "SHA256"):
                mrms.audit_original(bytes(corrupted), "mesh", pin["basename"])
            with self.assertRaisesRegex(mrms.MRMSPreflightError, "basename"):
                mrms.audit_original(synthetic, "mesh", "another.gz")

    def test_cli_rejects_unpinned_synthetic_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / mrms.SOURCE_OBJECTS["mesh"]["basename"]
            source.write_bytes(gzip.compress(synthetic_grib(), mtime=0))
            result = subprocess.run(
                [sys.executable, str(ROOT / "research_runners/noaa_mrms_mesh_original_preflight_v0.py"),
                 "--product", "mesh", "--gzip", str(source)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("BLOCKED", result.stderr)
            self.assertFalse(result.stdout)


if __name__ == "__main__":
    unittest.main()
