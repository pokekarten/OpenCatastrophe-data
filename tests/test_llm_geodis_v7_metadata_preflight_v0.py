# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Fail-closed synthetic tests for 2026 LLM-GeoDis v7 Zenodo metadata only."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.zenodo_cat_metadata_preflight_v0 import (
    LLM_GEODIS_SOURCE,
    LLM_GEODIS_V7_FILES,
    MetadataPreflightError,
    RECORDS,
    audit_record,
)

ROOT = Path(__file__).resolve().parents[1]
RID = 18935447


def synthetic_metadata() -> dict:
    assert RECORDS[LLM_GEODIS_SOURCE] == RID
    return {
        "id": RID,
        "doi": f"10.5281/zenodo.{RID}",
        "metadata": {
            "title": "Synthetic test fixture: LLM-GeoDis geocoded events",
            "access_right": "open",
            "version": "v7",
            "license": {"id": "cc-by-4.0"},
        },
        "files": [
            {
                "key": filename,
                "size": 1000 + index,
                "checksum": "md5:" + format(index + 1, "032x"),
                "links": {"self": f"https://zenodo.org/api/records/{RID}/files/{filename}/content"},
            }
            for index, filename in enumerate(sorted(LLM_GEODIS_V7_FILES))
        ],
    }


class LLMGeoDisMetadataPreflightTests(unittest.TestCase):
    def test_valid_synthetic_metadata_never_claims_acquisition_or_rights(self) -> None:
        response = audit_record(synthetic_metadata(), LLM_GEODIS_SOURCE, "a" * 64)
        self.assertEqual(response["original_zenodo_record_id"], RID)
        self.assertEqual(response["original_doi"], f"10.5281/zenodo.{RID}")
        self.assertEqual(response["file_count"], 14)
        self.assertEqual(response["record_version"], "v7")
        self.assertFalse(response["source_bytes_acquired"])
        self.assertFalse(response["rights_and_science_reviewed"])
        self.assertFalse(response["model_input_approved"])
        self.assertEqual(response["admission_status"], "not_admitted")
        self.assertTrue(all(not item["original_checksum_independently_verified"] for item in response["files"]))

    def test_wrong_version_rejected(self) -> None:
        data = synthetic_metadata()
        data["metadata"]["version"] = "v1"
        with self.assertRaisesRegex(MetadataPreflightError, "version"):
            audit_record(data, LLM_GEODIS_SOURCE, "b" * 64)

    def test_concept_doi_or_v1_record_rejected(self) -> None:
        for original_id, doi in [(17544932, "10.5281/zenodo.17544932"), (17544931, "10.5281/zenodo.17544931")]:
            with self.subTest(original_id=original_id):
                data = synthetic_metadata()
                data["id"] = original_id
                data["doi"] = doi
                with self.assertRaisesRegex(MetadataPreflightError, "ID mismatch"):
                    audit_record(data, LLM_GEODIS_SOURCE, "c" * 64)

    def test_incomplete_source_file_inventory_rejected(self) -> None:
        data = synthetic_metadata()
        data["files"] = [file for file in data["files"] if file["key"] != "gdis_disnos.csv"]
        with self.assertRaisesRegex(MetadataPreflightError, "inventory"):
            audit_record(data, LLM_GEODIS_SOURCE, "d" * 64)

    def test_wrong_declared_license_rejected_without_relicensing(self) -> None:
        data = synthetic_metadata()
        data["metadata"]["license"] = {"id": "cc0-1.0"}
        with self.assertRaisesRegex(MetadataPreflightError, "license"):
            audit_record(data, LLM_GEODIS_SOURCE, "e" * 64)

    def test_nonoriginal_download_host_rejected(self) -> None:
        data = synthetic_metadata()
        data["files"][0]["links"]["self"] = "https://example.net/file"
        with self.assertRaisesRegex(MetadataPreflightError, "zenodo.org"):
            audit_record(data, LLM_GEODIS_SOURCE, "f" * 64)

    def test_duplicate_file_path_rejected(self) -> None:
        data = synthetic_metadata()
        data["files"][1] = copy.deepcopy(data["files"][0])
        with self.assertRaisesRegex(MetadataPreflightError, "duplicate"):
            audit_record(data, LLM_GEODIS_SOURCE, "0" * 64)

    def test_no_network_cli_and_deterministic_receipt(self) -> None:
        data = synthetic_metadata()
        raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "source-metadata.json"
            path.write_bytes(raw)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/zenodo_cat_metadata_preflight_v0.py"),
                 "--source-id", LLM_GEODIS_SOURCE, "--metadata", str(path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt["metadata_body_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(receipt["file_count"], 14)
            self.assertFalse(receipt["source_bytes_acquired"])


if __name__ == "__main__":
    unittest.main()
