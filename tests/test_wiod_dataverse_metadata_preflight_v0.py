# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline synthetic tests for original WIOD Dataverse metadata identity."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.wiod_dataverse_metadata_preflight_v0 import (
    DATASET_ID,
    MAX_METADATA_BYTES,
    PINNED_FILES,
    RELEASE_TIME,
    SOURCE_DOI,
    WIODPreflightError,
    audit_dataset,
    inspect_file,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture() -> dict:
    return {
        "status": "OK",
        "data": {
            "id": DATASET_ID,
            "persistentUrl": SOURCE_DOI,
            "authority": "10.34894",
            "identifier": "PJ2M1C",
            "protocol": "doi",
            "latestVersion": {
                "versionNumber": 2,
                "versionMinorNumber": 1,
                "versionState": "RELEASED",
                "releaseTime": RELEASE_TIME,
                "termsOfUse": "The WIOD is licensed under a Creative Commons Attribution 4.0 International-license.",
                "files": [
                    {
                        "restricted": False,
                        "dataFile": {
                            "filename": name,
                            "id": file_id,
                            "filesize": file_size,
                            "checksum": {"type": "SHA-1", "value": sha1},
                        },
                    }
                    for name, (file_id, file_size, sha1) in PINNED_FILES.items()
                ],
            },
        },
    }


class TestWIODSourceMetadata(unittest.TestCase):
    def test_pinned_original_metadata_stays_non_admitted(self) -> None:
        receipt = audit_dataset(fixture(), "a" * 64)
        self.assertEqual(receipt["dataverse_dataset_id"], DATASET_ID)
        self.assertEqual(receipt["dataset_version"], "2.1")
        self.assertEqual(len(receipt["files"]), 2)
        self.assertFalse(receipt["selected_model_year_2011_verified_within_archive"])
        self.assertFalse(receipt["original_archive_bytes_acquired"])
        self.assertFalse(receipt["licensed_use_independently_reviewed"])
        self.assertFalse(receipt["model_input_approved"])
        self.assertEqual(receipt["admission_status"], "not_admitted")

    def test_dataset_or_release_drift_is_rejected(self) -> None:
        for path, value in (
            (("status",), "ERROR"),
            (("data", "id"), 1234),
            (("data", "persistentUrl"), "https://example.org"),
            (("data", "latestVersion", "versionMinorNumber"), 2),
            (("data", "latestVersion", "versionState"), "DRAFT"),
            (("data", "latestVersion", "releaseTime"), "2024-01-01T00:00:00Z"),
            (("data", "latestVersion", "termsOfUse"), "all rights reserved"),
        ):
            with self.subTest(path=path):
                d = fixture()
                pointer = d
                for key in path[:-1]:
                    pointer = pointer[key]
                pointer[path[-1]] = value
                with self.assertRaises(WIODPreflightError):
                    audit_dataset(d, "b" * 64)

    def test_archive_identity_and_rights_drift_rejected(self) -> None:
        for mutation in ("missing", "duplicate", "file_id", "bytes", "checksum", "checksum_type", "restricted"):
            with self.subTest(mutation=mutation):
                d = fixture()
                files = d["data"]["latestVersion"]["files"]
                selected = files[0]
                if mutation == "missing":
                    files.pop()
                elif mutation == "duplicate":
                    files.append(copy.deepcopy(selected))
                elif mutation == "file_id":
                    selected["dataFile"]["id"] += 1
                elif mutation == "bytes":
                    selected["dataFile"]["filesize"] -= 1
                elif mutation == "checksum":
                    selected["dataFile"]["checksum"]["value"] = "f" * 40
                elif mutation == "checksum_type":
                    selected["dataFile"]["checksum"]["type"] = "MD5"
                else:
                    selected["restricted"] = True
                with self.assertRaises(WIODPreflightError):
                    audit_dataset(d, "c" * 64)

    def test_bounded_file_and_command_line_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "synthetic.json"
            raw = json.dumps(fixture()).encode()
            p.write_bytes(raw)
            self.assertEqual(inspect_file(p)["original_metadata_sha256"], hashlib.sha256(raw).hexdigest())
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts/wiod_dataverse_metadata_preflight_v0.py"),
                "--dataset-json", str(p),
            ], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)["model_input_approved"])
            p.write_bytes(b"x" * (MAX_METADATA_BYTES + 1))
            with self.assertRaisesRegex(WIODPreflightError, "oversized"):
                inspect_file(p)


if __name__ == "__main__":
    unittest.main()
