# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only negative/regression tests for NHSL release metadata."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.nhsl_release_metadata_preflight_v0 import (
    API_URL,
    ASSET_PREFIX,
    MAX_METADATA_BYTES,
    NHSLPreflightError,
    RELEASE_URL,
    REQUIRED_ASSETS,
    audit_release,
    inspect_file,
)

ROOT = Path(__file__).resolve().parents[1]


def synthetic_release() -> dict:
    return {
        "tag_name": "v1.0",
        "html_url": RELEASE_URL,
        "draft": False,
        "prerelease": False,
        "assets": [
            {
                "name": name,
                "size": 128 + index * 100,
                "browser_download_url": ASSET_PREFIX + name,
            }
            for index, name in enumerate(REQUIRED_ASSETS)
        ] + [{"name": "other-release-asset.zip", "size": 100}],
    }


class TestNHSLReleasePreflight(unittest.TestCase):
    def test_valid_release_is_metadata_only(self) -> None:
        receipt = audit_release(synthetic_release(), "1" * 64)
        self.assertEqual(receipt["metadata_source_url"], API_URL)
        self.assertEqual(len(receipt["assets"]), 3)
        self.assertFalse(receipt["source_asset_bytes_acquired"])
        self.assertFalse(receipt["dataset_rights_reviewed"])
        self.assertFalse(receipt["scientific_fitness_reviewed"])
        self.assertFalse(receipt["model_input_approved"])
        self.assertEqual(receipt["admission_status"], "not_admitted")
        self.assertIn("centroids", receipt["spatial_semantics"])
        self.assertTrue(all(not a["checksum_independently_verified"] for a in receipt["assets"]))

    def test_wrong_release_identity_or_state_is_blocked(self) -> None:
        for field, value in (
            ("tag_name", "v2.0"),
            ("html_url", "https://example.org/release"),
            ("draft", True),
            ("prerelease", True),
        ):
            with self.subTest(field=field):
                data = synthetic_release()
                data[field] = value
                with self.assertRaises(NHSLPreflightError):
                    audit_release(data, "0" * 64)

    def test_missing_duplicate_and_asset_spoof_are_blocked(self) -> None:
        for mutation in ("missing", "duplicate", "url", "size", "bool-size", "digest"):
            with self.subTest(mutation=mutation):
                data = synthetic_release()
                a = data["assets"]
                if mutation == "missing":
                    a.pop(0)
                elif mutation == "duplicate":
                    a.append(copy.deepcopy(a[0]))
                elif mutation == "url":
                    a[0]["browser_download_url"] = "https://evil.example/" + a[0]["name"]
                elif mutation == "size":
                    a[0]["size"] = 0
                elif mutation == "bool-size":
                    a[0]["size"] = True
                elif mutation == "digest":
                    a[0]["digest"] = "sha256:not-a-sha"
                with self.assertRaises(NHSLPreflightError):
                    audit_release(data, "a" * 64)

    def test_wrong_sha_and_unbounded_metadata_are_blocked(self) -> None:
        with self.assertRaisesRegex(NHSLPreflightError, "SHA-256"):
            audit_release(synthetic_release(), "abc")
        with self.assertRaises(NHSLPreflightError):
            audit_release({"tag_name": "v1.0", "html_url": RELEASE_URL, "draft": False, "prerelease": False, "assets": [{}] * 501}, "a" * 64)

    def test_offline_file_hash_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "synthetic-release.json"
            raw = json.dumps(synthetic_release(), separators=(",", ":")).encode()
            file_path.write_bytes(raw)
            self.assertEqual(inspect_file(file_path)["original_metadata_sha256"], hashlib.sha256(raw).hexdigest())
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/nhsl_release_metadata_preflight_v0.py"),
                 "--release-json", str(file_path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)["model_input_approved"])

    def test_oversize_and_invalid_utf8_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "release.json"
            file_path.write_bytes(b"x" * (MAX_METADATA_BYTES + 1))
            with self.assertRaisesRegex(NHSLPreflightError, "limit"):
                inspect_file(file_path)
            file_path.write_bytes(b"\xff")
            with self.assertRaisesRegex(NHSLPreflightError, "UTF-8"):
                inspect_file(file_path)


if __name__ == "__main__":
    unittest.main()
