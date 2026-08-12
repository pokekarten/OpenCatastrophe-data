# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import dwd_metadata_temporal_evidence as evidence  # noqa: E402


class DwdMetadataTemporalEvidenceTests(unittest.TestCase):
    def _zip(self, members: dict[str, bytes]) -> tuple[tempfile.TemporaryDirectory, Path]:
        tempdir = tempfile.TemporaryDirectory()
        path = Path(tempdir.name) / "Meta_Daten_zehn_min_fx_00003.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in members.items():
                archive.writestr(name, content)
        return tempdir, path

    def _write_zip(self, path: Path, members: dict[str, bytes]) -> None:
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in members.items():
                archive.writestr(name, content)

    def _inspection(self, path: Path, families: list[str]) -> dict[str, object]:
        blob = path.read_bytes()
        with zipfile.ZipFile(path) as archive:
            members = [
                {"path": info.filename, "uncompressed_bytes": info.file_size, "crc32": f"{info.CRC:08x}"}
                for info in archive.infolist()
            ]
        return {
            "input": {"local_filename": path.name, "byte_size": len(blob), "sha256": hashlib.sha256(blob).hexdigest()},
            "zip": {"members": members},
            "observed": {"station_ids": ["00003"], "metadata_families": families},
        }

    def test_binds_required_member_bytes_but_remains_fail_closed(self) -> None:
        tempdir, path = self._zip({
            "Metadaten_Geographie_00003.txt": b"geo-content",
            "Metadaten_Geraete_00003.txt": b"equipment-content",
            "Metadaten_Parameter_00003.txt": b"parameter-content",
        })
        self.addCleanup(tempdir.cleanup)
        inspection = self._inspection(path, ["equipment", "geography", "parameter"])
        with patch.object(evidence, "inspect_zip", return_value=inspection):
            result = evidence._collect(path, inspection["input"]["sha256"], "00003")
        self.assertEqual(result["temporal_coverage_status"], "unverified")
        self.assertEqual(result["format_status"], "blocked_member_format_spec_required")
        self.assertFalse(result["claims"]["publication_authorized"])
        self.assertEqual(
            result["required_family_members"]["geography"][0]["sha256"],
            hashlib.sha256(b"geo-content").hexdigest(),
        )

    def test_rejects_path_replacement_after_inspection(self) -> None:
        tempdir, path = self._zip({
            "Metadaten_Geographie_00003.txt": b"geo-content",
            "Metadaten_Geraete_00003.txt": b"equipment-content",
            "Metadaten_Parameter_00003.txt": b"parameter-content",
        })
        self.addCleanup(tempdir.cleanup)
        inspection = self._inspection(path, ["equipment", "geography", "parameter"])

        def inspect_then_replace(_: Path) -> dict[str, object]:
            self._write_zip(path, {
                "Metadaten_Geographie_00003.txt": b"changed-geo",
                "Metadaten_Geraete_00003.txt": b"changed-equipment",
                "Metadaten_Parameter_00003.txt": b"changed-parameter",
            })
            return inspection

        with patch.object(evidence, "inspect_zip", side_effect=inspect_then_replace):
            with self.assertRaisesRegex(evidence.TemporalEvidenceError, "changed after ZIP inspection"):
                evidence._collect(path, inspection["input"]["sha256"], "00003")

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "secure no-follow open is not available")
    def test_rejects_byte_identical_symlink_replacement_after_inspection(self) -> None:
        tempdir, path = self._zip({
            "Metadaten_Geographie_00003.txt": b"geo-content",
            "Metadaten_Geraete_00003.txt": b"equipment-content",
            "Metadaten_Parameter_00003.txt": b"parameter-content",
        })
        self.addCleanup(tempdir.cleanup)
        inspection = self._inspection(path, ["equipment", "geography", "parameter"])
        target = path.with_name("frozen-target.zip")

        def inspect_then_symlink(_: Path) -> dict[str, object]:
            path.replace(target)
            path.symlink_to(target.name)
            return inspection

        with patch.object(evidence, "inspect_zip", side_effect=inspect_then_symlink):
            with self.assertRaisesRegex(evidence.TemporalEvidenceError, "no-follow regular file"):
                evidence._collect(path, inspection["input"]["sha256"], "00003")

    def test_rejects_oversized_replacement_before_read(self) -> None:
        tempdir, path = self._zip({
            "Metadaten_Geographie_00003.txt": b"geo-content",
            "Metadaten_Geraete_00003.txt": b"equipment-content",
            "Metadaten_Parameter_00003.txt": b"parameter-content",
        })
        self.addCleanup(tempdir.cleanup)
        inspection = self._inspection(path, ["equipment", "geography", "parameter"])

        def inspect_then_oversize(_: Path) -> dict[str, object]:
            path.write_bytes(b"x" * (inspection["input"]["byte_size"] + 1))
            return inspection

        with patch.object(evidence, "inspect_zip", side_effect=inspect_then_oversize):
            with patch.object(evidence.os, "read", side_effect=AssertionError("read must not occur")):
                with self.assertRaisesRegex(evidence.TemporalEvidenceError, "byte size changed"):
                    evidence._collect(path, inspection["input"]["sha256"], "00003")

    def test_member_hashes_use_immutable_snapshot(self) -> None:
        tempdir, path = self._zip({
            "Metadaten_Geographie_00003.txt": b"geo-content",
            "Metadaten_Geraete_00003.txt": b"equipment-content",
            "Metadaten_Parameter_00003.txt": b"parameter-content",
        })
        self.addCleanup(tempdir.cleanup)
        inspection = self._inspection(path, ["equipment", "geography", "parameter"])
        original_member_sha256 = evidence._member_sha256
        mutated = False

        def mutate_path_then_hash(archive: zipfile.ZipFile, name: str) -> str:
            nonlocal mutated
            if not mutated:
                mutated = True
                self._write_zip(path, {
                    "Metadaten_Geographie_00003.txt": b"changed-geo",
                    "Metadaten_Geraete_00003.txt": b"changed-equipment",
                    "Metadaten_Parameter_00003.txt": b"changed-parameter",
                })
            return original_member_sha256(archive, name)

        with patch.object(evidence, "inspect_zip", return_value=inspection):
            with patch.object(evidence, "_member_sha256", side_effect=mutate_path_then_hash):
                result = evidence._collect(path, inspection["input"]["sha256"], "00003")

        self.assertTrue(mutated)
        self.assertEqual(
            result["required_family_members"]["geography"][0]["sha256"],
            hashlib.sha256(b"geo-content").hexdigest(),
        )
        self.assertNotEqual(hashlib.sha256(path.read_bytes()).hexdigest(), inspection["input"]["sha256"])

    def test_rejects_wrong_frozen_sha(self) -> None:
        tempdir, path = self._zip({"Metadaten_Geographie_00003.txt": b"x"})
        self.addCleanup(tempdir.cleanup)
        inspection = self._inspection(path, ["equipment", "geography", "parameter"])
        inspection["input"]["sha256"] = "0" * 64
        with patch.object(evidence, "inspect_zip", return_value=inspection):
            with self.assertRaisesRegex(evidence.TemporalEvidenceError, "SHA-256"):
                evidence._collect(path, "1" * 64, "00003")

    def test_rejects_station_mismatch(self) -> None:
        tempdir, path = self._zip({"Metadaten_Geographie_00003.txt": b"x"})
        self.addCleanup(tempdir.cleanup)
        inspection = self._inspection(path, ["equipment", "geography", "parameter"])
        inspection["observed"]["station_ids"] = ["00004"]
        with patch.object(evidence, "inspect_zip", return_value=inspection):
            with self.assertRaisesRegex(evidence.TemporalEvidenceError, "station identity"):
                evidence._collect(path, inspection["input"]["sha256"], "00003")

    def test_rejects_missing_required_family(self) -> None:
        tempdir, path = self._zip({"Metadaten_Geographie_00003.txt": b"x"})
        self.addCleanup(tempdir.cleanup)
        inspection = self._inspection(path, ["geography", "parameter"])
        with patch.object(evidence, "inspect_zip", return_value=inspection):
            with self.assertRaisesRegex(evidence.TemporalEvidenceError, "equipment"):
                evidence._collect(path, inspection["input"]["sha256"], "00003")

    def test_embedded_provider_token_is_not_accepted(self) -> None:
        self.assertIsNone(evidence._family_for_member("xMetadaten_Geographie_00003.txt"))


if __name__ == "__main__":
    unittest.main()
