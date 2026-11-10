# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only Blue Heart highway-gully ZIP inventory regression tests."""

import io
import stat
import unittest
import zipfile

from research_runners.blue_heart_gully_zip_inventory_v0 import (
    BlueHeartZipError,
    inspect_zip_structure,
)

ROOT = "6_highway_gully_telemetry_data"


def make_archive(*, missing_qc=None, extra=None, broken=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        directory = zipfile.ZipInfo(ROOT + "/")
        directory.compress_type = zipfile.ZIP_STORED
        zf.writestr(directory, b"")
        for i in range(15):
            stem = f"SYNTHETIC_{i:02d}"
            zf.writestr(f"{ROOT}/{stem}.csv", b"timestamp,value\n2025-01-01T00:00:00+00:00,0\n")
            if missing_qc != i:
                zf.writestr(
                    f"{ROOT}/{stem}_quality_flags.csv",
                    b"timestamp,flag\n2025-01-01T00:00:00+00:00,1\n",
                )
        if extra is not None:
            zf.writestr(extra, b"synthetic")
        if broken is not None:
            zf.writestr(broken, b"synthetic")
    buf.seek(0)
    return buf


def inspect(buf):
    with zipfile.ZipFile(buf) as archive:
        return inspect_zip_structure(archive)


class BlueHeartGullyZipInventoryTests(unittest.TestCase):
    def test_synthetic_fifteen_pairs_pass_without_reading_rows(self):
        report = inspect(make_archive())
        self.assertEqual(report["zip_member_count"], 31)
        self.assertEqual(report["measurement_csv_count"], 15)
        self.assertEqual(report["quality_csv_count"], 15)
        self.assertFalse(report["measurement_rows_or_timestamps_read"])
        self.assertFalse(report["source_bytes_admitted"])

    def test_one_missing_quality_file_rejected(self):
        with self.assertRaisesRegex(BlueHeartZipError, "member count"):
            inspect(make_archive(missing_qc=3))

    def test_unpaired_quality_stem_rejected_with_constant_member_count(self):
        archive = make_archive(missing_qc=3, extra=f"{ROOT}/UNPAIRED_quality_flags.csv")
        with self.assertRaisesRegex(BlueHeartZipError, "one-to-one"):
            inspect(archive)

    def test_path_traversal_rejected(self):
        archive = make_archive(missing_qc=0, extra=f"{ROOT}/../outside.csv")
        with self.assertRaisesRegex(BlueHeartZipError, "unsafe ZIP path"):
            inspect(archive)

    def test_extra_nested_path_rejected(self):
        archive = make_archive(missing_qc=0, extra=f"{ROOT}/nested/stray.csv")
        with self.assertRaisesRegex(BlueHeartZipError, "path or format"):
            inspect(archive)

    def test_case_insensitive_path_collision_rejected(self):
        buf = make_archive(missing_qc=0, extra=f"{ROOT}/synthetic_00.csv")
        with self.assertRaisesRegex(BlueHeartZipError, "duplicate ZIP path"):
            inspect(buf)

    def test_other_extension_rejected(self):
        archive = make_archive(missing_qc=0, extra=f"{ROOT}/other.exe")
        with self.assertRaisesRegex(BlueHeartZipError, "path or format"):
            inspect(archive)

    def test_symlink_member_rejected(self):
        buf = make_archive(missing_qc=0)
        with zipfile.ZipFile(buf, "a") as zf:
            info = zipfile.ZipInfo(f"{ROOT}/UNPAIRED_quality_flags.csv")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            zf.writestr(info, b"synthetic")
        buf.seek(0)
        with self.assertRaisesRegex(BlueHeartZipError, "symbolic link"):
            inspect(buf)

    def test_high_compression_ratio_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            directory = zipfile.ZipInfo(ROOT + "/")
            directory.compress_type = zipfile.ZIP_STORED
            zf.writestr(directory, b"")
            for i in range(15):
                stem = f"SYNTHETIC_{i:02d}"
                data = b"0" * 200_000 if i == 0 else b"data"
                zf.writestr(f"{ROOT}/{stem}.csv", data)
                zf.writestr(f"{ROOT}/{stem}_quality_flags.csv", b"flag")
        buf.seek(0)
        with self.assertRaisesRegex(BlueHeartZipError, "expansion ratio"):
            inspect(buf)


if __name__ == "__main__":
    unittest.main()
