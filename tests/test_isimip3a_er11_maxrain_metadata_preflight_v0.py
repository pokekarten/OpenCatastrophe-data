# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic regression tests for original ISIMIP3a publisher metadata contract."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.isimip3a_er11_maxrain_metadata_preflight_v0 import (
    CC0,
    DATASET_UUID,
    EXPECTED_SIZE_BYTES,
    EXPECTED_YEARS,
    FILE_PREFIX,
    ISIMIPMetadataError,
    MAX_METADATA_BYTES,
    PRODUCT_NAME,
    SOURCE_ID,
    VERSION,
    inspect_metadata_bytes,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture() -> dict:
    prefix = "er11-wind_obsclim_historical_maxrain_"
    uniform = EXPECTED_SIZE_BYTES // 72
    files = []
    for i, year in enumerate(EXPECTED_YEARS):
        name = f"{prefix}{year}.nc"
        fid = f"00000000-0000-4000-8000-{year:012d}"
        files.append({
            "id": fid,
            "name": name,
            "path": FILE_PREFIX + name,
            "version": VERSION,
            "size": uniform if i < 71 else EXPECTED_SIZE_BYTES - uniform * 71,
            "checksum_type": "sha512",
            "checksum": "a" * 128,
            "url": f"https://data.isimip.org/api/v1/files/{fid}/",
            "file_url": f"https://files.isimip.org/{FILE_PREFIX}{name}",
            "rights": {"short": "CC0 1.0", "rights_uri": CC0},
        })
    return {
        "id": DATASET_UUID,
        "name": PRODUCT_NAME,
        "version": VERSION,
        "public": True,
        "restricted": False,
        "rights": {"short": "CC0 1.0", "rights_uri": CC0},
        "url": f"https://data.isimip.org/api/v1/datasets/{DATASET_UUID}/",
        "filelist_url": f"https://data.isimip.org/api/v1/datasets/{DATASET_UUID}/filelist/",
        "specifiers": {
            "region": "global",
            "product": "InputData",
            "category": "climate",
            "wind_model": "er11-wind",
            "subcategory": "tropical_cyclones",
            "climate_scenario": "obsclim",
            "climate_variable": "maxrain",
            "simulation_round": "ISIMIP3a",
        },
        "size": EXPECTED_SIZE_BYTES,
        "files": files,
    }


def b(value: dict) -> bytes:
    return (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()


def audit(value: dict) -> dict:
    raw = b(value)
    return inspect_metadata_bytes(raw, hashlib.sha256(raw).hexdigest())


class TestOriginalISIMIPPublisherMetadata(unittest.TestCase):
    def test_valid_fixture_is_nonadmitted(self) -> None:
        result = audit(fixture())
        self.assertEqual(result["source_id"], SOURCE_ID)
        self.assertEqual(result["dataset_version"], VERSION)
        self.assertEqual(result["annual_file_count"], 72)
        self.assertEqual((result["first_year"], result["last_year"]), (1950, 2021))
        self.assertEqual(result["declared_total_netcdf_bytes"], EXPECTED_SIZE_BYTES)
        self.assertEqual(result["published_sha512_declarations_count"], 72)
        self.assertTrue(result["dataset_and_all_files_declared_cc0_1_0"])
        self.assertFalse(result["published_sha512_independently_verified"])
        self.assertFalse(result["netcdf_source_bytes_acquired"])
        self.assertFalse(result["commercial_insurance_rights_cleared"])
        self.assertEqual(result["admission_status"], "not_admitted")

    def test_data_id_mismatch(self) -> None:
        f = fixture()
        f["id"] = "not-our-dataset"
        with self.assertRaisesRegex(ISIMIPMetadataError, "dataset identity"):
            audit(f)

    def test_unauthorised_dataset_rights_change(self) -> None:
        f = fixture()
        f["rights"]["short"] = "CC BY-NC 4.0"
        with self.assertRaisesRegex(ISIMIPMetadataError, "CC0"):
            audit(f)

    def test_one_file_license_conflict(self) -> None:
        f = fixture()
        f["files"][-1]["rights"]["rights_uri"] = "https://creativecommons.org/licenses/by-nc/4.0/"
        with self.assertRaisesRegex(ISIMIPMetadataError, "CC0"):
            audit(f)

    def test_changed_version(self) -> None:
        f = fixture()
        f["version"] = "20261103"
        with self.assertRaisesRegex(ISIMIPMetadataError, "version"):
            audit(f)

    def test_file_version_mismatch(self) -> None:
        f = fixture()
        f["files"][-1]["version"] = "20261103"
        with self.assertRaisesRegex(ISIMIPMetadataError, "file version"):
            audit(f)

    def test_total_size_mismatch(self) -> None:
        f = fixture()
        f["files"][10]["size"] += 100
        with self.assertRaisesRegex(ISIMIPMetadataError, "size sum"):
            audit(f)

    def test_bool_not_accepted_as_size(self) -> None:
        f = fixture()
        f["files"][0]["size"] = True
        with self.assertRaisesRegex(ISIMIPMetadataError, "byte count"):
            audit(f)

    def test_wrong_checksum_type(self) -> None:
        f = fixture()
        f["files"][0]["checksum_type"] = "md5"
        with self.assertRaisesRegex(ISIMIPMetadataError, "SHA512"):
            audit(f)

    def test_bad_published_checksum(self) -> None:
        f = fixture()
        f["files"][0]["checksum"] = "abcd"
        with self.assertRaisesRegex(ISIMIPMetadataError, "SHA512"):
            audit(f)

    def test_missing_one_year(self) -> None:
        f = fixture()
        f["files"].pop()
        with self.assertRaisesRegex(ISIMIPMetadataError, "72"):
            audit(f)

    def test_duplicate_file_id(self) -> None:
        f = fixture()
        f["files"][1]["id"] = f["files"][0]["id"]
        with self.assertRaisesRegex(ISIMIPMetadataError, "duplicate"):
            audit(f)

    def test_year_out_of_order(self) -> None:
        f = fixture()
        f["files"][0], f["files"][1] = f["files"][1], f["files"][0]
        with self.assertRaisesRegex(ISIMIPMetadataError, "unordered"):
            audit(f)

    def test_no_cyclone_variable_substitution(self) -> None:
        f = fixture()
        f["specifiers"]["climate_variable"] = "windlifetimemax"
        with self.assertRaisesRegex(ISIMIPMetadataError, "specifiers"):
            audit(f)

    def test_unexpected_file_path(self) -> None:
        f = fixture()
        f["files"][0]["path"] = "../escape.nc"
        with self.assertRaisesRegex(ISIMIPMetadataError, "file path"):
            audit(f)

    def test_redirect_to_other_domain(self) -> None:
        f = fixture()
        f["files"][0]["file_url"] = f["files"][0]["file_url"].replace("files.isimip.org", "evil.example.com")
        with self.assertRaisesRegex(ISIMIPMetadataError, "provider URL mismatch"):
            audit(f)

    def test_no_source_access_permission_from_public_flag(self) -> None:
        f = fixture()
        f["restricted"] = True
        with self.assertRaisesRegex(ISIMIPMetadataError, "public"):
            audit(f)

    def test_invalid_pinned_sha(self) -> None:
        raw = b(fixture())
        with self.assertRaisesRegex(ISIMIPMetadataError, "SHA256 mismatch"):
            inspect_metadata_bytes(raw, "0" * 64)

    def test_duplicate_json_key(self) -> None:
        raw = b(fixture())
        raw = raw.replace(b'"id":"f08ab32e-b3ad-4984-81d1-495235765b6c"', b'"id":"f08ab32e-b3ad-4984-81d1-495235765b6c","id":"f08ab32e-b3ad-4984-81d1-495235765b6c"', 1)
        with self.assertRaisesRegex(ISIMIPMetadataError, "duplicate JSON key"):
            inspect_metadata_bytes(raw, hashlib.sha256(raw).hexdigest())

    def test_metadata_byte_cap(self) -> None:
        raw = b"x" * (MAX_METADATA_BYTES + 1)
        with self.assertRaisesRegex(ISIMIPMetadataError, "1 MiB"):
            inspect_metadata_bytes(raw, hashlib.sha256(raw).hexdigest())

    def test_cli_writes_aggregate_only_and_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            f = Path(folder) / "dataset.json"
            out = Path(folder) / "receipt.json"
            original = b(fixture())
            f.write_bytes(original)
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/isimip3a_er11_maxrain_metadata_preflight_v0.py"),
                "--metadata", str(f),
                "--expected-sha256", hashlib.sha256(original).hexdigest(),
                "--out", str(out),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(receipt["admission_status"], "not_admitted")
            self.assertEqual(receipt["annual_file_count"], 72)
            self.assertNotIn("files", receipt)
            self.assertEqual(f.read_bytes(), original)
            failed = subprocess.run(cmd[:-1] + [str(f)], capture_output=True, text=True, check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(f.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
