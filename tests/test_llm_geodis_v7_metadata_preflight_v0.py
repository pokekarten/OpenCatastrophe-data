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
    LLM_GEODIS_V7_PUBLISHED_MD5,
    LLM_GEODIS_V7_PUBLISHED_SIZES,
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
                "size": LLM_GEODIS_V7_PUBLISHED_SIZES[filename],
                "checksum": "md5:" + LLM_GEODIS_V7_PUBLISHED_MD5[filename],
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

    def test_inveniordm_public_metadata_shape_accepts_synthetic_input(self) -> None:
        data = synthetic_metadata()
        data["id"] = str(RID)
        data["pids"] = {"doi": {"identifier": data.pop("doi")}}
        data["access"] = {"record": "public", "files": "public"}
        data["metadata"].pop("access_right")
        data["metadata"]["rights"] = [data["metadata"].pop("license")]
        files = data["files"]
        data["files"] = {"enabled": True, "count": len(files), "entries": files}
        for entry in files:
            entry["links"]["content"] = entry["links"]["self"]
            entry["links"]["self"] = entry["links"]["content"].removesuffix("/content")
        result = audit_record(data, LLM_GEODIS_SOURCE, "c" * 64)
        self.assertEqual(result["metadata_api_shape"], "inveniordm")
        self.assertEqual(result["file_count"], 14)
        self.assertFalse(result["model_input_approved"])

    def test_inveniordm_hidden_file_fails_closed(self) -> None:
        data = synthetic_metadata()
        data["access"] = {"record": "public", "files": "restricted"}
        with self.assertRaisesRegex(MetadataPreflightError, "not public"):
            audit_record(data, LLM_GEODIS_SOURCE, "a" * 64)

    def test_inveniordm_file_inventory_count_disagreement_fails(self) -> None:
        data = synthetic_metadata()
        files = data["files"]
        data["files"] = {"enabled": True, "count": len(files) + 1, "entries": files}
        with self.assertRaisesRegex(MetadataPreflightError, "count mismatch"):
            audit_record(data, LLM_GEODIS_SOURCE, "b" * 64)

    def test_inveniordm_conflicting_doi_fails(self) -> None:
        data = synthetic_metadata()
        data["pids"] = {"doi": {"identifier": "10.5281/zenodo.17544932"}}
        with self.assertRaisesRegex(MetadataPreflightError, "conflicting"):
            audit_record(data, LLM_GEODIS_SOURCE, "c" * 64)

    def test_inveniordm_conflicting_license_fails(self) -> None:
        data = synthetic_metadata()
        data["metadata"]["rights"] = [{"id": "cc0-1.0"}]
        with self.assertRaisesRegex(MetadataPreflightError, "contradictory"):
            audit_record(data, LLM_GEODIS_SOURCE, "c" * 64)

    def test_duplicate_json_keys_and_nonfinite_values_rejected(self) -> None:
        base = json.dumps(synthetic_metadata(), separators=(",", ":"))
        dup = '{"id":18935447,"id":18935447,' + base[1:]
        first_size = synthetic_metadata()["files"][0]["size"]
        nonfinite = base.replace(f'"size":{first_size}', '"size":NaN', 1)
        self.assertNotEqual(nonfinite, base)
        for raw in (dup, nonfinite):
            with self.subTest(payload=raw[:70]):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "untrusted.json"
                    path.write_text(raw, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "scripts/zenodo_cat_metadata_preflight_v0.py"),
                         "--source-id", LLM_GEODIS_SOURCE, "--metadata", str(path)],
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("BLOCKED", result.stderr)

    def test_original_zenodo_api_relation_index_six_is_version_seven(self) -> None:
        data = synthetic_metadata()
        data["metadata"].pop("version")
        data["conceptrecid"] = "17544931"
        data["conceptdoi"] = "10.5281/zenodo.17544931"
        data["metadata"]["relations"] = {"version": [
            {"index": 6, "is_last": True, "parent": {"pid_type": "recid", "pid_value": "17544931"}}
        ]}
        result = audit_record(data, LLM_GEODIS_SOURCE, "1" * 64)
        self.assertEqual(result["record_version"], "v7")
        self.assertEqual(result["version_evidence"], "zenodo_relation_index_6")
        self.assertEqual(result["file_count"], 14)
        self.assertFalse(result["source_bytes_acquired"])

    def test_wrong_original_relation_index_or_concept_parent_rejected(self) -> None:
        data = synthetic_metadata()
        data["metadata"].pop("version")
        data["metadata"]["relations"] = {"version": [
            {"index": 7, "parent": {"pid_type": "recid", "pid_value": "17544931"}}
        ]}
        with self.assertRaisesRegex(MetadataPreflightError, "version index"):
            audit_record(data, LLM_GEODIS_SOURCE, "2" * 64)
        data["metadata"]["relations"]["version"][0]["index"] = 6
        data["metadata"]["relations"]["version"][0]["parent"]["pid_value"] = "99999999"
        with self.assertRaisesRegex(MetadataPreflightError, "concept parent"):
            audit_record(data, LLM_GEODIS_SOURCE, "3" * 64)

    def test_missing_both_explicit_and_original_relation_version_rejected(self) -> None:
        data = synthetic_metadata()
        data["metadata"].pop("version")
        with self.assertRaisesRegex(MetadataPreflightError, "release/version evidence missing"):
            audit_record(data, LLM_GEODIS_SOURCE, "4" * 64)

    def test_original_published_byte_length_drift_rejected(self) -> None:
        data = synthetic_metadata()
        data["files"][0]["size"] += 1
        with self.assertRaisesRegex(MetadataPreflightError, "byte length mismatch"):
            audit_record(data, LLM_GEODIS_SOURCE, "5" * 64)

    def test_published_original_v7_checksums_are_pinned(self) -> None:
        self.assertEqual(set(LLM_GEODIS_V7_PUBLISHED_MD5), LLM_GEODIS_V7_FILES)
        data = synthetic_metadata()
        target = next(entry for entry in data["files"] if entry["key"] == "gdis_disnos.csv")
        target["checksum"] = "md5:" + "1" * 32
        with self.assertRaisesRegex(MetadataPreflightError, "published source checksum mismatch"):
            audit_record(data, LLM_GEODIS_SOURCE, "d" * 64)

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
