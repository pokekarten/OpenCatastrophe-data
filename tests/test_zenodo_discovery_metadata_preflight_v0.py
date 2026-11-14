# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic metadata-only regressions for two pinned Zenodo sources."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.zenodo_cat_metadata_preflight_v0 import (
    PINNED_DISCOVERIES,
    RECORDS,
    MetadataPreflightError,
    audit_record,
)

ROOT = Path(__file__).resolve().parents[1]
GROUND = "google.groundsource.flash-flood-reports.v1"
LANDSLIDE = "dlr.gfz.s1s2.landslide-reference.v3"


def fixture(source_id: str) -> dict:
    """A wholly synthetic JSON record using only original public metadata keys."""
    pin = PINNED_DISCOVERIES[source_id]
    record_id = RECORDS[source_id]
    return {
        "id": record_id,
        "doi": f"10.5281/zenodo.{record_id}",
        "conceptrecid": pin["conceptrecid"],
        "conceptdoi": f"10.5281/zenodo.{pin['conceptrecid']}",
        "status": "published",
        "metadata": {
            "title": "Synthetic test-only publisher record",
            "access_right": "open",
            "license": {"id": "cc-by-4.0"},
            "relations": {
                "version": [{
                    "index": pin["version_index"],
                    "is_last": True,
                    "parent": {"pid_type": "recid", "pid_value": pin["conceptrecid"]},
                }],
            },
        },
        "files": [
            {
                "key": filename,
                "size": size,
                "checksum": "md5:" + checksum,
                "links": {
                    "self": f"https://zenodo.org/api/records/{record_id}/files/{filename}/content"
                },
            }
            for filename, (size, checksum) in pin["files"].items()
        ],
    }


class TestPinnedZenodoDiscoveryMetadata(unittest.TestCase):
    def test_both_pinned_versions_remain_research_only(self) -> None:
        for source_id, version in ((GROUND, "v1"), (LANDSLIDE, "v3")):
            with self.subTest(source=source_id):
                receipt = audit_record(fixture(source_id), source_id, "9" * 64)
                self.assertEqual(receipt["source_candidate_id"], source_id)
                self.assertEqual(receipt["record_version"], version)
                self.assertEqual(receipt["file_count"], len(PINNED_DISCOVERIES[source_id]["files"]))
                self.assertEqual(receipt["admission_status"], "not_admitted")
                self.assertFalse(receipt["source_bytes_acquired"])
                self.assertFalse(receipt["rights_and_science_reviewed"])
                self.assertFalse(receipt["model_input_approved"])
                for file_info in receipt["files"]:
                    self.assertFalse(file_info["original_checksum_independently_verified"])

    def test_bad_concept_version_and_status_rejected(self) -> None:
        for source in (GROUND, LANDSLIDE):
            for variant in ("concept", "doi", "status", "version", "last", "parent"):
                with self.subTest(source=source, variant=variant):
                    data = fixture(source)
                    if variant == "concept":
                        data["conceptrecid"] = "123"
                    elif variant == "doi":
                        data["conceptdoi"] = "10.5281/zenodo.123"
                    elif variant == "status":
                        data["status"] = "draft"
                    elif variant == "version":
                        data["metadata"]["relations"]["version"][0]["index"] += 1
                    elif variant == "last":
                        data["metadata"]["relations"]["version"][0]["is_last"] = False
                    else:
                        data["metadata"]["relations"]["version"][0]["parent"]["pid_value"] = "123"
                    with self.assertRaisesRegex(MetadataPreflightError, "concept|version|status"):
                        audit_record(data, source, "0" * 64)

    def test_publisher_license_change_rejected_not_resolved(self) -> None:
        data = fixture(LANDSLIDE)
        data["metadata"]["license"] = {"id": "cc-by-nc-4.0"}
        with self.assertRaisesRegex(MetadataPreflightError, "license"):
            audit_record(data, LANDSLIDE, "0" * 64)

    def test_file_drift_detected(self) -> None:
        for source in (GROUND, LANDSLIDE):
            for variant in ("missing", "extra", "size", "md5", "key_link"):
                with self.subTest(source=source, variant=variant):
                    data = copy.deepcopy(fixture(source))
                    if variant == "missing":
                        data["files"].pop()
                    elif variant == "extra":
                        item = copy.deepcopy(data["files"][0])
                        item["key"] = "unexpected.json"
                        item["links"]["self"] = (
                            f"https://zenodo.org/api/records/{RECORDS[source]}/"
                            "files/unexpected.json/content"
                        )
                        data["files"].append(item)
                    elif variant == "size":
                        data["files"][0]["size"] += 1
                    elif variant == "md5":
                        data["files"][0]["checksum"] = "md5:" + "f" * 32
                    elif variant == "key_link":
                        data["files"][0]["links"]["self"] = (
                            f"https://zenodo.org/api/records/{RECORDS[source]}/files/other.txt/content"
                        )
                    with self.assertRaises(MetadataPreflightError):
                        audit_record(data, source, "0" * 64)

    def test_bounded_offline_cli_outputs_no_admission(self) -> None:
        for source in (GROUND, LANDSLIDE):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                metadata = Path(tmp) / "record.json"
                metadata.write_text(json.dumps(fixture(source)), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/zenodo_cat_metadata_preflight_v0.py"),
                     "--source-id", source, "--metadata", str(metadata)],
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                receipt = json.loads(result.stdout)
                self.assertEqual(receipt["admission_status"], "not_admitted")
                self.assertFalse(receipt["source_bytes_acquired"])


if __name__ == "__main__":
    unittest.main()
