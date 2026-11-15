# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Independent synthetic-only original-archive guardrail tests; no provider data."""

from __future__ import annotations

from io import BytesIO
import struct
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from scripts.naturalearth_admin0_archive_preflight import ArchiveBlocked, BASENAME, inspect_original_zip


def header(size: int, *, bounds=(-170., -55., 170., 85.), kind=5) -> bytes:
    raw = bytearray(size)
    struct.pack_into(">I", raw, 0, 9994)
    struct.pack_into(">I", raw, 24, size // 2)
    struct.pack_into("<II", raw, 28, 1000, kind)
    struct.pack_into("<4d", raw, 36, *bounds)
    return bytes(raw)


def sample_zip(*, bad_name=False, kind=5, bounds=(-170., -55., 170., 85.), dbf_count=2, prj=True) -> bytes:
    dbf = bytearray(35)
    dbf[0] = 0x03
    struct.pack_into("<IHH", dbf, 4, dbf_count, 33, 1)
    dbf[32] = 0x0D
    members = {
        BASENAME + ".shp": header(100, bounds=bounds, kind=kind),
        BASENAME + ".shx": header(116, bounds=bounds),
        BASENAME + ".dbf": bytes(dbf),
    }
    if prj:
        members[BASENAME + ".prj"] = b'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984"]]'
    if bad_name:
        members["../" + BASENAME + ".cpg"] = b"UTF-8"
    b = BytesIO()
    with ZipFile(b, "w", compression=ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return b.getvalue()


class NaturalEarthOriginalZipPreflightTests(unittest.TestCase):
    def test_small_synthetic_archive_passes_and_hashes_original_zip(self):
        original = sample_zip()
        result = inspect_original_zip(original)
        self.assertEqual(result["shx_record_count"], 2)
        self.assertEqual(result["dbf_record_count"], 2)
        self.assertEqual(result["original_bytes"], len(original))
        self.assertEqual(len(result["original_sha256"]), 64)
        self.assertFalse(result["stored_original_bytes"])
        self.assertIn("not_scientific_admission", result["verification_scope"])

    def test_fail_closed_on_zip_slip(self):
        with self.assertRaises(ArchiveBlocked):
            inspect_original_zip(sample_zip(bad_name=True))

    def test_fail_closed_on_wrong_shape_type_and_bounds(self):
        for kwargs in ({"kind": 3}, {"bounds": (181., -55., 190., 85.)}, {"bounds": (1., 10., -1., 9.)}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ArchiveBlocked):
                inspect_original_zip(sample_zip(**kwargs))

    def test_fail_closed_on_missing_crs_and_dbf_count(self):
        for kwargs in ({"prj": False}, {"dbf_count": 3}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ArchiveBlocked):
                inspect_original_zip(sample_zip(**kwargs))

    def test_fail_closed_on_broken_zip_and_oversize_input(self):
        for bad in (b"not-a-zip", sample_zip()[:-18], b"PK\x03\x04" + b"x" * (1024 * 1024)):
            with self.subTest(size=len(bad)), self.assertRaises(ArchiveBlocked):
                inspect_original_zip(bad)


if __name__ == "__main__":
    unittest.main()
