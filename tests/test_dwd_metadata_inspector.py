# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import importlib.util
import stat
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "inspect_dwd_metadata_zip.py"
SPEC = importlib.util.spec_from_file_location("inspect_dwd_metadata_zip", MODULE_PATH)
assert SPEC and SPEC.loader
inspector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspector)


class DwdMetadataInspectorTests(unittest.TestCase):
    def _zip(self, entries: list[tuple[str, bytes]], *, symlink: str | None = None) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "metadata.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in entries:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    archive.writestr(name, content)
            if symlink is not None:
                info = zipfile.ZipInfo(symlink)
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, b"target")
        return path

    def test_report_is_deterministic_for_exact_input_bytes(self) -> None:
        path = self._zip(
            [
                ("Meta_Daten_zehn_min_ff_01234.zip", b"station"),
                ("equipment_01234.txt", b"instrument"),
                ("station_05678.txt", b"location"),
            ]
        )
        first = inspector.inspect_zip(path)
        second = inspector.inspect_zip(path)
        self.assertEqual(first, second)
        self.assertEqual(first["input"]["local_filename"], "metadata.zip")
        self.assertRegex(first["input"]["sha256"], r"^[a-f0-9]{64}$")
        self.assertEqual(first["observed"]["station_ids"], ["01234", "05678"])
        self.assertEqual(first["observed"]["metadata_families"], ["equipment", "metadata", "station"])
        self.assertFalse(first["claims"]["admission_changed"])
        self.assertFalse(first["claims"]["scientific_fitness_assessed"])
        member_paths = [item["path"] for item in first["zip"]["members"]]
        self.assertEqual(member_paths, sorted(member_paths))

    def test_parent_traversal_member_is_rejected(self) -> None:
        path = self._zip([("../secret.txt", b"no")])
        with self.assertRaises(inspector.InspectionError):
            inspector.inspect_zip(path)

    def test_absolute_member_is_rejected(self) -> None:
        path = self._zip([("/absolute.txt", b"no")])
        with self.assertRaises(inspector.InspectionError):
            inspector.inspect_zip(path)

    def test_windows_absolute_member_is_rejected(self) -> None:
        path = self._zip([("C:/absolute.txt", b"no")])
        with self.assertRaises(inspector.InspectionError):
            inspector.inspect_zip(path)

    def test_backslash_member_is_rejected(self) -> None:
        path = self._zip([("folder\\file.txt", b"no")])
        with self.assertRaises(inspector.InspectionError):
            inspector.inspect_zip(path)

    def test_dot_and_empty_segments_are_rejected(self) -> None:
        for member in ("folder/./file.txt", "folder//file.txt"):
            path = self._zip([(member, b"no")])
            with self.subTest(member=member), self.assertRaises(inspector.InspectionError):
                inspector.inspect_zip(path)

    def test_directory_member_is_allowed(self) -> None:
        path = self._zip([("metadata/", b""), ("metadata/station_01234.txt", b"ok")])
        result = inspector.inspect_zip(path)
        self.assertEqual(result["zip"]["member_count"], 2)
        self.assertEqual(result["observed"]["station_ids"], ["01234"])

    def test_duplicate_member_path_is_rejected(self) -> None:
        path = self._zip([("station_01234.txt", b"one"), ("station_01234.txt", b"two")])
        with self.assertRaises(inspector.InspectionError):
            inspector.inspect_zip(path)

    def test_symlink_member_is_rejected(self) -> None:
        path = self._zip([], symlink="station_01234.txt")
        with self.assertRaises(inspector.InspectionError):
            inspector.inspect_zip(path)

    def test_symlink_input_is_rejected(self) -> None:
        path = self._zip([("station_01234.txt", b"ok")])
        link = path.with_name("metadata-link.zip")
        link.symlink_to(path)
        with self.assertRaises(inspector.InspectionError):
            inspector.inspect_zip(link)

    def test_input_byte_change_during_inspection_is_rejected(self) -> None:
        path = self._zip([("station_01234.txt", b"ok")])
        real_hash = inspector._sha256_stream
        calls = 0

        def changing_hash(handle: object) -> str:
            nonlocal calls
            calls += 1
            digest = real_hash(handle)
            return digest if calls == 1 else ("0" * 64)

        with mock.patch.object(inspector, "_sha256_stream", side_effect=changing_hash):
            with self.assertRaisesRegex(inspector.InspectionError, "changed during inspection"):
                inspector.inspect_zip(path)

    def test_non_zip_file_is_rejected(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "not-a-zip.bin"
        path.write_bytes(b"not a zip")
        with self.assertRaises(inspector.InspectionError):
            inspector.inspect_zip(path)


if __name__ == "__main__":
    unittest.main()
