# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic tests only: never bundle or fetch external GRIP4 data."""
from __future__ import annotations

import hashlib
from io import BytesIO
import unittest
import zipfile

from research_runners.grip4_density_archive_preflight_v0 import (
    Grip4PreflightError, inspect_zip,
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


class GRIP4DensityArchiveTests(unittest.TestCase):
    def test_good_synthetic_archive_stays_not_admitted(self):
        result = examine(fake_zip({"total.asc": b"ncols 1\nnrows 1\n1\n", "readme.txt": b"synthetic"}))
        self.assertEqual(result["raster_member_count"], 1)
        self.assertTrue(result["published_md5_matched"])
        self.assertFalse(result["license_rights_cleared"])
        self.assertFalse(result["model_source_admission_approved"])
        self.assertFalse(result["zip_member_payloads_decompressed_or_parsed"])

    def test_reject_sha256_mismatch(self):
        data = fake_zip({"total.asc": b"a"})
        with self.assertRaisesRegex(Grip4PreflightError, "SHA-256"):
            examine(data, pin="0" * 64)

    def test_reject_published_md5_mismatch(self):
        data = fake_zip({"total.asc": b"a"})
        with self.assertRaisesRegex(Grip4PreflightError, "MD5"):
            examine(data, md5="0" * 32)

    def test_reject_unsafe_zip_traversal(self):
        with self.assertRaisesRegex(Grip4PreflightError, "unsafe path"):
            examine(fake_zip({"../escape.asc": b"test"}))

    def test_reject_duplicate_case_insensitive_names(self):
        with self.assertRaisesRegex(Grip4PreflightError, "duplicate"):
            examine(fake_zip({"GRID.asc": b"1", "grid.asc": b"2"}))

    def test_reject_zip_without_raster(self):
        with self.assertRaisesRegex(Grip4PreflightError, "no expected geospatial"):
            examine(fake_zip({"notes.txt": b"hello"}))

    def test_reject_excessively_compressible_member(self):
        with self.assertRaisesRegex(Grip4PreflightError, "expansion ratio"):
            examine(fake_zip({"grid.asc": b"0" * 250000}))

    def test_reject_non_zip(self):
        data = b"not a zip"
        with self.assertRaisesRegex(Grip4PreflightError, "not a well-formed ZIP"):
            examine(data)


if __name__ == "__main__":
    unittest.main()
