# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic tests for a Git-pinned third-party ZIP receipt script."""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from research_runners import plateau_hokota_official_sample_receipt_v0 as sample

SYNTHETIC_GML = (
    '<core:CityModel xmlns:core="http://www.opengis.net/citygml/2.0" '
    'xmlns:gml="http://www.opengis.net/gml" '
    'xmlns:bldg="http://www.opengis.net/citygml/building/2.0">'
    '<gml:boundedBy><gml:Envelope '
    'srsName="http://www.opengis.net/def/crs/EPSG/0/6697" srsDimension="3">'
    '<gml:lowerCorner>36.1 140.5 0</gml:lowerCorner>'
    '<gml:upperCorner>36.2 140.6 30</gml:upperCorner>'
    '</gml:Envelope></gml:boundedBy>'
    '<core:cityObjectMember><bldg:Building gml:id="synthetic_bldg_1">'
    '<bldg:measuredHeight uom="m">12</bldg:measuredHeight>'
    '</bldg:Building></core:cityObjectMember></core:CityModel>'
).encode()


def zip_data(*, gml: bytes = SYNTHETIC_GML) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("08234_hokota_synthetic/udx/bldg/small.gml", gml)
        archive.writestr("08234_hokota_synthetic/metadata/readme.txt", "Synthetic only")
    return buf.getvalue()


def git_blob_hash(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


class OfficialHokotaOfflineReceiptTests(unittest.TestCase):
    def run_pinned(self, data: bytes, *, correct_hash=True) -> dict:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic-citygml.zip"
            path.write_bytes(data)
            pinned_sha = git_blob_hash(data) if correct_hash else "a" * 40
            with patch.object(sample, "PINNED_GIT_BLOB_SHA1", pinned_sha), patch.object(
                sample, "PINNED_ZIP_BYTE_COUNT", len(data)
            ):
                return sample.profile(path)

    def test_original_zip_and_small_gml_have_distinct_sha_receipts(self):
        data = zip_data()
        result = self.run_pinned(data)
        self.assertEqual(result["git_blob_sha1"], git_blob_hash(data))
        self.assertEqual(result["original_zip_sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(result["building_gml_member_count"], 1)
        self.assertEqual(result["sampled_gml_members_count"], 1)
        self.assertEqual(result["samples"][0]["structure_screen"], "pass")
        self.assertEqual(result["samples"][0]["building_count"], 1)
        self.assertEqual(result["samples"][0]["sha256"], hashlib.sha256(SYNTHETIC_GML).hexdigest())
        self.assertTrue(result["sample_member_crc_checked_only"])
        for key in (
            "all_archive_member_crcs_checked", "all_building_geometries_checked",
            "per_asset_license_review_completed", "archive_city_release_independently_proven",
            "cat_model_input_admitted", "provider_network_access_by_this_script"
        ):
            self.assertFalse(result[key], key)
        output = json.dumps(result)
        self.assertNotIn("synthetic_bldg_1", output)
        self.assertNotIn("140.5", output)
        self.assertNotIn("small.gml", output)

    def test_immutable_git_blob_identity_mismatch_blocks(self):
        with self.assertRaisesRegex(sample.OfficialSampleError, "pinned Git blob"):
            self.run_pinned(zip_data(), correct_hash=False)

    def test_wrong_archive_size_blocks_before_archive_reader(self):
        data = zip_data()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.zip"
            path.write_bytes(data)
            with patch.object(sample, "PINNED_ZIP_BYTE_COUNT", len(data) + 1):
                with self.assertRaisesRegex(sample.OfficialSampleError, "byte count"):
                    sample.profile(path)

    def test_invalid_small_gml_is_reported_as_blocked_not_admitted(self):
        result = self.run_pinned(zip_data(gml=b"<broken-gml"))
        self.assertEqual(result["sampled_gml_members_count"], 1)
        self.assertEqual(result["samples"][0]["structure_screen"], "blocked")
        self.assertFalse(result["cat_model_input_admitted"])

    def test_missing_input_cli_redacts_path_and_returns_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unavailable-provider-original.zip"
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                status = sample.main(["--input", str(path)])
            self.assertEqual(status, 2)
            self.assertEqual(out.getvalue(), "")
            self.assertIn("BLOCKED:", err.getvalue())
            self.assertNotIn(str(path), err.getvalue())

    def test_archive_contains_only_large_gml_is_not_passed_as_checked(self):
        with patch.object(sample, "MAX_GML_BYTES", 10):
            result = self.run_pinned(zip_data())
        self.assertEqual(result["building_gml_member_count"], 1)
        self.assertEqual(result["sampled_gml_members_count"], 0)
        self.assertFalse(result["sample_member_crc_checked_only"])
        self.assertFalse(result["all_building_geometries_checked"])


if __name__ == "__main__":
    unittest.main()
