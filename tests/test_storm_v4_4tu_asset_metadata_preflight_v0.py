# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict synthetic-only original STORM v4 asset-metadata reconciliation gates."""
from __future__ import annotations

import copy
import hashlib
import json
import unittest

from research_runners.storm_v4_4tu_asset_metadata_preflight_v0 import (
    ARTICLE_UUID, Blocked, DOI, EXPECTED, MAX_LIST_BYTES, inspect,
)

FILE_UUIDS = {
    "README.txt": "00000000-0000-4000-8000-000000000001",
    "Basins of STORM IBTrACS dataset.kml": "00000000-0000-4000-8000-000000000002",
    "STORMV4.zip": "00000000-0000-4000-8000-000000000003",
}


def article():
    return {
        "uuid": ARTICLE_UUID,
        "doi": DOI,
        "version": 4,
        "title": "STORM IBTrACS present climate synthetic tropical cyclone tracks",
    }


def file_list():
    return [
        {"uuid": FILE_UUIDS[name], "name": name, "size": size, "computed_md5": md5}
        for name, (size, md5) in EXPECTED.items()
    ]


def wire(x):
    return json.dumps(x, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def check(a=None, rows=None):
    article_raw = wire(article() if a is None else a)
    list_raw = wire(file_list() if rows is None else rows)
    return inspect(article_raw, hashlib.sha256(article_raw).hexdigest(),
                   list_raw, hashlib.sha256(list_raw).hexdigest())


class STORMv4OriginalAssetMetadataTests(unittest.TestCase):
    def test_valid_metadata_reconciles_only_declared_file_inventory(self):
        receipt = check()
        self.assertTrue(receipt["provider_asset_metadata_reconciled"])
        self.assertEqual([x["filename"] for x in receipt["files"]], sorted(EXPECTED))
        self.assertTrue(receipt["provider_declared_md5_is_not_independent_original_sha256"])
        for flag in ("original_asset_bytes_acquired", "original_asset_sha256_verified",
                     "source_licensing_approved_for_acquisition", "asset_download_authorized",
                     "track_fields_verified_from_v4_original", "source_admission_extended",
                     "model_input_authorized"):
            self.assertFalse(receipt[flag])

    def test_reject_other_original_versions_even_same_title(self):
        for value in (1, 2, 3, "3", True, None, "v4", 5):
            a = article()
            a["version"] = value
            with self.subTest(value=value), self.assertRaises(Blocked):
                check(a=a)

    def test_reject_wrong_doi_uuid_and_title(self):
        changes = (
            ("doi", "10.4121/12706085.v3"),
            ("doi", None),
            ("uuid", "01b2ebc7-7903-42ef-b46b-f43b9175dbf5"),
            ("title", "STORM climate-change track generator"),
        )
        for field, value in changes:
            a = article()
            a[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(Blocked):
                check(a=a)

    def test_file_size_or_checksum_drift_rejected(self):
        for field, value in (
            ("size", 543251823),
            ("size", True),
            ("computed_md5", "0" * 32),
            ("computed_md5", "A" * 32),
            ("computed_md5", None),
        ):
            rows = file_list()
            row = next(r for r in rows if r["name"] == "STORMV4.zip")
            row[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(Blocked):
                check(rows=rows)

    def test_empty_and_extra_file_list_blocked(self):
        for rows in ([], file_list()[:-1], file_list() + [copy.deepcopy(file_list()[0])]):
            with self.subTest(n=len(rows)), self.assertRaises(Blocked):
                check(rows=rows)

    def test_earlier_version_archive_is_never_substituted(self):
        rows = file_list()
        rows[2]["name"] = "STORM_data.zip"
        rows[2]["size"] = 545853257
        rows[2]["computed_md5"] = "b745159cf1523dcecbb716bf6899d746"
        with self.assertRaises(Blocked):
            check(rows=rows)

    def test_path_traversal_and_unknown_file_names_blocked(self):
        for name in ("../STORMV4.zip", "VERSIE4/STORMV4.zip",
                     "STORMV4.zip/evil", "/tmp/STORMV4.zip", "readme.txt"):
            rows = file_list()
            rows[2]["name"] = name
            with self.subTest(name=name), self.assertRaises(Blocked):
                check(rows=rows)

    def test_conflicting_md5_fields_rejected(self):
        rows = file_list()
        rows[0]["supplied_md5"] = "f" * 32
        with self.assertRaises(Blocked):
            check(rows=rows)

    def test_missing_and_duplicated_file_uuid_blocked(self):
        cases = (
            None,
            "not-a-uuid",
            FILE_UUIDS["README.txt"],
        )
        for value in cases:
            rows = file_list()
            if value is None:
                rows[1].pop("uuid")
            else:
                rows[1]["uuid"] = value
            with self.subTest(value=value), self.assertRaises(Blocked):
                check(rows=rows)

    def test_hostile_download_url_blocked_and_safe_url_is_metadata_only(self):
        row = file_list()[0]
        safe_url = f"https://data.4tu.nl/file/{ARTICLE_UUID}/{row['uuid']}"
        rows = file_list()
        rows[0]["download_url"] = safe_url
        receipt = check(rows=rows)
        self.assertFalse(receipt["asset_download_authorized"])
        for url in ("http://data.4tu.nl/file/a/b",
                    "https://evil.example/file/a/b",
                    safe_url + "?token=secret",
                    safe_url + "/other",
                    "https://data.4tu.nl@evil.example/file/a/b"):
            rows[0]["download_url"] = url
            with self.subTest(url=url), self.assertRaises(Blocked):
                check(rows=rows)

    def test_4tu_v2_file_shape_with_null_legacy_id_accepted(self):
        rows = file_list()
        for row in rows:
            row["id"] = None
            row["supplied_md5"] = None
            row["is_incomplete"] = False
            row["is_link_only"] = False
            row["download_url"] = (
                f"https://data.4tu.nl/file/{ARTICLE_UUID}/{row['uuid']}"
            )
        receipt = check(rows=rows)
        self.assertEqual(len(receipt["files"]), 3)
        self.assertFalse(receipt["asset_download_authorized"])

    def test_link_only_and_incomplete_provider_assets_blocked(self):
        for flag, value in (("is_link_only", True), ("is_incomplete", True),
                            ("is_link_only", "false"), ("is_incomplete", 0)):
            rows = file_list()
            rows[2][flag] = value
            with self.subTest(flag=flag, value=value), self.assertRaises(Blocked):
                check(rows=rows)

    def test_wrong_response_sha_rejected(self):
        a, files = wire(article()), wire(file_list())
        with self.assertRaisesRegex(Blocked, "SHA-256 mismatch"):
            inspect(a, "0" * 64, files, hashlib.sha256(files).hexdigest())
        with self.assertRaisesRegex(Blocked, "SHA-256 mismatch"):
            inspect(a, hashlib.sha256(a).hexdigest(), files, "0" * 64)

    def test_duplicate_keys_nonfinite_oversized_and_non_utf8_blocked(self):
        valid_a, valid_list = wire(article()), wire(file_list())
        for bad in (b'{"uuid":"a","uuid":"b"}', b'{"version":NaN}',
                    b'{"version":1e400}', b'\xff',
                    b" " * (MAX_LIST_BYTES + 1), b""):
            with self.subTest(bad=bad[:24]), self.assertRaises(Blocked):
                inspect(valid_a, hashlib.sha256(valid_a).hexdigest(),
                        bad, hashlib.sha256(bad).hexdigest())
        with self.assertRaises(Blocked):
            inspect(b'{"uuid":true,"uuid":false}', hashlib.sha256(
                b'{"uuid":true,"uuid":false}').hexdigest(),
                valid_list, hashlib.sha256(valid_list).hexdigest())


if __name__ == "__main__":
    unittest.main()
