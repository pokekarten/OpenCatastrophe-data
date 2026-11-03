# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Negative, offline-only regression tests for fixed Zenodo CAT record receipts."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.zenodo_cat_metadata_preflight_v0 import (
    MAX_METADATA_BYTES,
    RECORDS,
    MetadataPreflightError,
    audit_record,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "nl.vu.european-multihazard-sparse-events.v1"
RID = RECORDS[SOURCE]


def fixture() -> dict:
    return {
        "id": RID,
        "doi": f"10.5281/zenodo.{RID}",
        "metadata": {
            "title": "Example synthetic compound events (test fixture only)",
            "access_right": "open",
            "version": "v1",
            "license": {"id": "cc-by-4.0"},
        },
        "files": [
            {
                "key": "synthetic_example.csv",
                "size": 123,
                "checksum": "md5:" + "a" * 32,
                "links": {"self": f"https://zenodo.org/api/records/{RID}/files/synthetic_example.csv/content"},
            }
        ],
    }


class TestZenodoCatMetadataPreflight(unittest.TestCase):
    def test_valid_receipt_keeps_rights_and_model_blocked(self) -> None:
        result = audit_record(fixture(), SOURCE, "b" * 64)
        self.assertEqual(result["file_count"], 1)
        self.assertEqual(result["listed_source_bytes"], 123)
        self.assertEqual(result["original_doi"], f"10.5281/zenodo.{RID}")
        self.assertFalse(result["source_bytes_acquired"])
        self.assertFalse(result["rights_and_science_reviewed"])
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["files"][0]["original_checksum_independently_verified"])

    def test_unknown_source_blocked(self) -> None:
        with self.assertRaises(MetadataPreflightError):
            audit_record(fixture(), "example.other", "0" * 64)

    def test_latest_transclima_catalogue_restricted_blocked(self) -> None:
        with self.assertRaisesRegex(MetadataPreflightError, "restricted"):
            audit_record(fixture(), "ihcantabria.transclima.tropical-cyclone-data-catalogue.v1", "0" * 64)

    def test_wrong_record_id_blocked(self) -> None:
        data = fixture()
        data["id"] = RID + 1
        with self.assertRaisesRegex(MetadataPreflightError, "ID mismatch"):
            audit_record(data, SOURCE, "0" * 64)

    def test_other_version_doi_blocked(self) -> None:
        data = fixture()
        data["doi"] = "10.5281/zenodo.999999"
        with self.assertRaisesRegex(MetadataPreflightError, "DOI/version"):
            audit_record(data, SOURCE, "0" * 64)

    def test_closed_record_blocked(self) -> None:
        data = fixture()
        data["metadata"]["access_right"] = "restricted"
        with self.assertRaisesRegex(MetadataPreflightError, "open-access"):
            audit_record(data, SOURCE, "0" * 64)

    def test_missing_license_blocked(self) -> None:
        data = fixture()
        del data["metadata"]["license"]
        with self.assertRaisesRegex(MetadataPreflightError, "license"):
            audit_record(data, SOURCE, "0" * 64)

    def test_path_traversal_blocked(self) -> None:
        data = fixture()
        data["files"][0]["key"] = "../not-allowed.csv"
        with self.assertRaisesRegex(MetadataPreflightError, "unsafe"):
            audit_record(data, SOURCE, "0" * 64)

    def test_duplicate_file_blocked(self) -> None:
        data = fixture()
        data["files"].append(copy.deepcopy(data["files"][0]))
        with self.assertRaisesRegex(MetadataPreflightError, "duplicate"):
            audit_record(data, SOURCE, "0" * 64)

    def test_untrusted_file_link_blocked(self) -> None:
        data = fixture()
        data["files"][0]["links"]["self"] = "https://example.com/file.csv"
        with self.assertRaisesRegex(MetadataPreflightError, "zenodo.org"):
            audit_record(data, SOURCE, "0" * 64)

    def test_other_zenodo_record_link_blocked(self) -> None:
        data = fixture()
        data["files"][0]["links"]["self"] = "https://zenodo.org/api/records/123/files/test.csv/content"
        with self.assertRaisesRegex(MetadataPreflightError, "identity mismatch"):
            audit_record(data, SOURCE, "0" * 64)

    def test_signed_file_link_blocked(self) -> None:
        data = fixture()
        data["files"][0]["links"]["self"] += "?token=secret"
        with self.assertRaisesRegex(MetadataPreflightError, "signed"):
            audit_record(data, SOURCE, "0" * 64)

    def test_invalid_checksum_blocked(self) -> None:
        data = fixture()
        data["files"][0]["checksum"] = "md5:abcd"
        with self.assertRaisesRegex(MetadataPreflightError, "checksum"):
            audit_record(data, SOURCE, "0" * 64)

    def test_bool_size_blocked(self) -> None:
        data = fixture()
        data["files"][0]["size"] = True
        with self.assertRaisesRegex(MetadataPreflightError, "size"):
            audit_record(data, SOURCE, "0" * 64)

    def test_cli_receipt_is_offline_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts/zenodo_cat_metadata_preflight_v0.py"),
                       "--source-id", SOURCE, "--metadata", str(path)]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["admission_status"], "not_admitted")
            path.write_bytes(b"x" * (MAX_METADATA_BYTES + 1))
            failed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(failed.returncode, 2)
            self.assertIn("5 MiB", failed.stderr)


if __name__ == "__main__":
    unittest.main()
