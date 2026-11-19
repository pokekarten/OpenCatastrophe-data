# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic normalized metadata tests; no original 4TU API or track downloads."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.storm_v4_4tu_landing_inventory_preflight_v0 import (
    Blocked, DOI, EXPECTED_FILES, MAX_BYTES, PAGE, SCHEMA, inspect_listing,
)

ROOT = Path(__file__).resolve().parents[1]


def sample() -> dict:
    return {
        "schema_version": SCHEMA,
        "record_doi": DOI,
        "publisher_page": PAGE,
        "version": 4,
        "observation_basis": "manual_transcription_of_provider_landing_listing",
        "files": [
            {"name": name, "size_bytes": size, "publisher_md5": md5}
            for name, (size, md5) in EXPECTED_FILES.items()
        ],
    }


def encode(data: dict) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True, allow_nan=False).encode("utf-8")


def audit(data: dict) -> dict:
    raw = encode(data)
    return inspect_listing(raw, hashlib.sha256(raw).hexdigest())


class StormV4LandingListingTests(unittest.TestCase):
    def test_exact_three_original_publisher_labels_nonadmission(self) -> None:
        result = audit(sample())
        self.assertEqual(result["published_file_count"], 3)
        self.assertEqual(result["published_file_total_bytes"], 543256758)
        self.assertTrue(result["file_metadata_labels_match_frozen_publisher_listing"])
        for key in ("original_provider_api_response_retrieved", "original_api_uuid_verified",
                    "provider_original_file_bytes_downloaded", "independent_file_sha256_verified",
                    "commercial_asset_rights_reviewed", "model_input_approved", "neon_write_performed"):
            with self.subTest(key=key):
                self.assertFalse(result[key])
        self.assertEqual(result["admission_status"], "not_admitted")

    def test_listing_order_is_immaterial_but_identity_is_not(self) -> None:
        payload = sample()
        payload["files"].reverse()
        self.assertEqual(audit(payload)["published_file_count"], 3)

    def test_reject_wrong_release_or_version(self) -> None:
        for field, value in (
            ("record_doi", "10.4121/12706085.v3"),
            ("version", 3),
            ("version", True),
            ("publisher_page", "https://data.4tu.nl/articles/_/12706085/3"),
            ("schema_version", "storm-v4-4tu-publisher-listing-v99"),
        ):
            with self.subTest(field=field, value=value):
                payload = sample()
                payload[field] = value
                with self.assertRaises(Blocked):
                    audit(payload)

    def test_no_claim_that_normalized_listing_is_original_api(self) -> None:
        data = sample()
        data["observation_basis"] = "verified_original_4tu_api_json"
        with self.assertRaisesRegex(Blocked, "observation basis"):
            audit(data)

    def test_reject_duplicate_filename(self) -> None:
        data = sample()
        data["files"][1] = copy.deepcopy(data["files"][0])
        with self.assertRaisesRegex(Blocked, "duplicate"):
            audit(data)

    def test_reject_missing_or_extra_files(self) -> None:
        for make in ("missing", "extra"):
            data = sample()
            if make == "missing":
                data["files"].pop()
            else:
                data["files"].append(copy.deepcopy(data["files"][0]))
            with self.subTest(make=make), self.assertRaises(Blocked):
                audit(data)

    def test_reject_path_traversal_and_nonv4_archive(self) -> None:
        for name in ("../STORMV4.zip", "/tmp/STORMV4.zip", "STORMV3.zip",
                     "STORMV4.zip/../../secret", "STORMV4.ZIP"):
            data = sample()
            data["files"][2]["name"] = name
            with self.subTest(name=name), self.assertRaises(Blocked):
                audit(data)

    def test_reject_one_byte_or_md5_drift(self) -> None:
        data = sample()
        data["files"][2]["size_bytes"] += 1
        with self.assertRaisesRegex(Blocked, "size or MD5 mismatch"):
            audit(data)
        data = sample()
        data["files"][2]["publisher_md5"] = "f" * 32
        with self.assertRaisesRegex(Blocked, "size or MD5 mismatch"):
            audit(data)

    def test_reject_bad_sizes_and_digest_formats(self) -> None:
        for size in (False, 0, -1, 1.5, "543251824"):
            data = sample()
            data["files"][0]["size_bytes"] = size
            with self.subTest(size=size), self.assertRaises(Blocked):
                audit(data)
        for checksum in ("0" * 31, "G" * 32, "ABCDEF" * 5 + "AB", None):
            data = sample()
            data["files"][0]["publisher_md5"] = checksum
            with self.subTest(checksum=checksum), self.assertRaises(Blocked):
                audit(data)

    def test_reject_unknown_fields(self) -> None:
        data = sample()
        data["rights_reviewed"] = True
        with self.assertRaisesRegex(Blocked, "schema"):
            audit(data)
        data = sample()
        data["files"][0]["downloaded_bytes_verified"] = True
        with self.assertRaisesRegex(Blocked, "entry"):
            audit(data)

    def test_reject_invalid_snapshot_sha_and_body_identity(self) -> None:
        raw = encode(sample())
        with self.assertRaisesRegex(Blocked, "SHA-256"):
            inspect_listing(raw, "0" * 64)
        with self.assertRaises(Blocked):
            inspect_listing(raw, "A" * 64)

    def test_strict_json_rejects_duplicate_keys_and_nonfinite(self) -> None:
        for raw in (
            b'{"schema_version":"x","schema_version":"x"}',
            b'{"record_doi":NaN}',
            b'{"version":1e400}',
        ):
            with self.subTest(raw=raw), self.assertRaises(Blocked):
                inspect_listing(raw, hashlib.sha256(raw).hexdigest())

    def test_reject_invalid_utf8_and_oversize(self) -> None:
        for raw in (b'{"record_doi":"\xff"}', b" " * (MAX_BYTES + 1), b""):
            with self.subTest(size=len(raw)), self.assertRaises(Blocked):
                inspect_listing(raw, hashlib.sha256(raw).hexdigest())

    def test_cli_receipt_hash_binds_normalized_snapshot_not_source_files(self) -> None:
        raw = encode(sample())
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "operator-transcription.json"
            target.write_bytes(raw)
            result = subprocess.run(
                [sys.executable, str(ROOT / "research_runners/storm_v4_4tu_landing_inventory_preflight_v0.py"),
                 "--snapshot", str(target), "--expected-sha256", hashlib.sha256(raw).hexdigest()],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt["normalized_snapshot_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertFalse(receipt["provider_original_file_bytes_downloaded"])
            self.assertFalse(receipt["original_api_uuid_verified"])


if __name__ == "__main__":
    unittest.main()
