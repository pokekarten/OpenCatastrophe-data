# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic tests only: never bundle or fetch external GRIP4 data."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
from io import BytesIO
import unittest
import zipfile

from research_runners.grip4_density_archive_preflight_v0 import (
    Grip4PreflightError, inspect_zip, read_archive_bounded, write_receipt_exclusive,
    MAX_ARCHIVE_BYTES,
)


def fake_zip(files: dict[str, bytes]) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path, data in files.items():
            z.writestr(path, data)
    return buf.getvalue()


def examine(data: bytes, *, pin: str | None = None, md5: str | None = None) -> dict:
    return inspect_zip(data, expected_sha256=pin or hashlib.sha256(data).hexdigest(),
                       expected_published_md5=md5 or hashlib.md5(data, usedforsecurity=False).hexdigest())


def sample_files() -> dict[str, bytes]:
    return {
        "GRIP4_density_m_km2.lyr": b"synthetic layer",
        "ReadMe.txt": b"synthetic description",
        "grip4_area_land_km2.asc": b"ncols 1\nnrows 1\n1\n",
        "grip4_total_dens_m_km2.asc": b"ncols 1\nnrows 1\n2\n",
    }


class GRIP4DensityArchiveTests(unittest.TestCase):
    def test_good_synthetic_archive_stays_not_admitted(self):
        result = examine(fake_zip(sample_files()))
        self.assertEqual(result["raster_member_count"], 2)
        self.assertFalse(result["raster_values_or_georeferencing_validated"])
        self.assertTrue(result["published_md5_matched"])
        self.assertFalse(result["license_rights_cleared"])
        self.assertFalse(result["model_source_admission_approved"])
        self.assertFalse(result["zip_member_payloads_decompressed_or_parsed"])

    def test_reject_sha256_mismatch(self):
        data = fake_zip(sample_files())
        with self.assertRaisesRegex(Grip4PreflightError, "SHA-256"):
            examine(data, pin="0" * 64)

    def test_reject_published_md5_mismatch(self):
        data = fake_zip(sample_files())
        with self.assertRaisesRegex(Grip4PreflightError, "MD5"):
            examine(data, md5="0" * 32)

    def test_reject_unsafe_zip_traversal(self):
        with self.assertRaisesRegex(Grip4PreflightError, "unsafe path"):
            examine(fake_zip({"../escape.asc": b"test"}))

    def test_reject_duplicate_case_insensitive_names(self):
        with self.assertRaisesRegex(Grip4PreflightError, "duplicate"):
            examine(fake_zip({**sample_files(), "GRID.asc": b"1", "grid.asc": b"2"}))

    def test_reject_zip_without_raster(self):
        with self.assertRaisesRegex(Grip4PreflightError, "publisher archive"):
            examine(fake_zip({"notes.txt": b"hello"}))

    def test_reject_excessively_compressible_member(self):
        with self.assertRaisesRegex(Grip4PreflightError, "expansion ratio"):
            examine(fake_zip({**sample_files(), "grip4_total_dens_m_km2.asc": b"0" * 250000}))

    def test_reject_non_zip(self):
        data = b"not a zip"
        with self.assertRaisesRegex(Grip4PreflightError, "not a well-formed ZIP"):
            examine(data)

    def test_reject_unexpected_extra_raster(self):
        files = sample_files()
        files["unexpected.asc"] = b"3"
        with self.assertRaisesRegex(Grip4PreflightError, "publisher archive"):
            examine(fake_zip(files))

    def test_reject_removed_original_raster(self):
        files = sample_files()
        del files["grip4_area_land_km2.asc"]
        with self.assertRaisesRegex(Grip4PreflightError, "publisher archive"):
            examine(fake_zip(files))

    def test_bounded_reader_rejects_oversize_before_reading(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "GRIP4_density_total.zip"
            with path.open("wb") as file:
                file.truncate(MAX_ARCHIVE_BYTES + 1)
            with self.assertRaisesRegex(Grip4PreflightError, "10 MiB"):
                read_archive_bounded(path)

    def test_bounded_reader_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            original = Path(d) / "real.zip"
            original.write_bytes(fake_zip(sample_files()))
            alias = Path(d) / "alias.zip"
            alias.symlink_to(original)
            with self.assertRaisesRegex(Grip4PreflightError, "opened safely"):
                read_archive_bounded(alias)

    def test_receipt_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "receipt.json"
            out.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(Grip4PreflightError, "already exists"):
                write_receipt_exclusive(out, {"data": False})
            self.assertEqual(out.read_text(encoding="utf-8"), "keep")

    def test_receipt_created_once_with_restricted_mode(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "receipt.json"
            write_receipt_exclusive(out, {"model_source_admission_approved": False})
            self.assertFalse(__import__("json").loads(out.read_text())["model_source_admission_approved"])
            with self.assertRaises(Grip4PreflightError):
                write_receipt_exclusive(out, {})


if __name__ == "__main__":
    unittest.main()
