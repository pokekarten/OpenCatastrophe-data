# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
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
