# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic Dryad file inventories only; no provider bytes checked into Git."""
import copy
import hashlib
import json
import unittest

from research_runners import wumi2026a_dryad_original_asset_receipt_v0 as mod


def fixture():
    files = []
    for i, name in enumerate(sorted(mod.EXPECTED_FILES)):
        id_ = mod.ASSET_ID if name == mod.ASSET_NAME else str(4000000+i)
        path = "/api/v2/files/" + id_
        files.append({
            "path": name,
            "size": mod.ASSET_BYTES if name == mod.ASSET_NAME else 100+i,
            "digestType": "sha-256",
            "digest": mod.ASSET_SHA256 if name == mod.ASSET_NAME else hashlib.sha256(name.encode()).hexdigest(),
            "_links": {
                "self": {"href": path},
                "stash:version": {"href": "/api/v2/versions/458442"},
                "stash:download": {"href": path+"/download"},
            },
        })
    return {"count": 7, "total": 7, "_embedded": {"stash:files": files}}


def encode(v):
    b = json.dumps(v, sort_keys=True, separators=(",", ":")).encode()
    return b, hashlib.sha256(b).hexdigest()


def audit(v=None, *, version=458442):
    raw, sha = encode(fixture() if v is None else v)
    return mod.inspect_dryad_files_metadata(raw, sha, expected_version=version)


class DryadWumiOriginalMetadataTests(unittest.TestCase):
    def test_exact_publisher_asset_identity_is_not_verified_archive_bytes(self):
        result = audit()
        self.assertEqual(result["state"], "PUBLISHER_METADATA_MATCH_NOT_ASSET_VALIDATED")
        self.assertEqual(result["target_asset_bytes_publisher_claim"], 4683571)
        self.assertEqual(result["target_asset_sha256_publisher_claim"], mod.ASSET_SHA256)
        self.assertEqual(result["version_specific_file_count"], 7)
        for key in ("publisher_metadata_origin_authenticated", "target_file_downloaded",
                    "target_original_file_sha256_verified", "target_original_zip_integrity_checked",
                    "actual_event_list_schema_or_event_count_verified",
                    "source_rights_or_CAT_model_admission_granted"):
            self.assertFalse(result[key])

    def test_2024a_version_rejected(self):
        with self.assertRaisesRegex(mod.DryadReceiptBlocked, "wrong Dryad dataset version"):
            audit(version=413220)

    def test_small_archive_size_drift_rejected(self):
        v = fixture()
        next(x for x in v["_embedded"]["stash:files"] if x["path"] == mod.ASSET_NAME)["size"] += 1
        with self.assertRaisesRegex(mod.DryadReceiptBlocked, "hash/bytes/ID"):
            audit(v)

    def test_small_archive_hash_drift_rejected(self):
        v = fixture()
        next(x for x in v["_embedded"]["stash:files"] if x["path"] == mod.ASSET_NAME)["digest"] = "f"*64
        with self.assertRaises(mod.DryadReceiptBlocked):
            audit(v)

    def test_unknown_added_asset_even_when_count_seven_blocked(self):
        v = fixture()
        v["_embedded"]["stash:files"][0]["path"] = "unexpected.zip"
        with self.assertRaises(mod.DryadReceiptBlocked):
            audit(v)

    def test_duplicate_name_and_missing_files_blocked(self):
        v = fixture()
        v["_embedded"]["stash:files"][0]["path"] = v["_embedded"]["stash:files"][1]["path"]
        with self.assertRaises(mod.DryadReceiptBlocked):
            audit(v)

    def test_truncated_pagination_not_silently_admitted(self):
        v = fixture()
        v["_embedded"]["stash:files"].pop()
        with self.assertRaises(mod.DryadReceiptBlocked):
            audit(v)

    def test_wrong_version_per_file_and_bad_download_url_blocked(self):
        for field in ("stash:version", "stash:download"):
            v = fixture()
            v["_embedded"]["stash:files"][0]["_links"][field]["href"] = "/api/v2/versions/413220"
            with self.subTest(field=field), self.assertRaises(mod.DryadReceiptBlocked):
                audit(v)

    def test_wrong_digest_type_bool_size_and_bad_sha_blocked(self):
        for value in ("md5", None):
            v = fixture()
            v["_embedded"]["stash:files"][0]["digestType"] = value
            with self.assertRaises(mod.DryadReceiptBlocked):
                audit(v)
        v = fixture()
        v["_embedded"]["stash:files"][0]["size"] = True
        with self.assertRaises(mod.DryadReceiptBlocked):
            audit(v)

    def test_json_duplicate_key_or_nonfinite_rejected(self):
        for blob in (b'{"count":7,"count":7}', b'{"count":NaN}'):
            with self.assertRaises(mod.DryadReceiptBlocked):
                mod.inspect_dryad_files_metadata(
                    blob, hashlib.sha256(blob).hexdigest(), expected_version=458442
                )

    def test_original_metadata_sha_mismatch_rejected(self):
        raw, _ = encode(fixture())
        with self.assertRaisesRegex(mod.DryadReceiptBlocked, "SHA256 mismatch"):
            mod.inspect_dryad_files_metadata(raw, "0"*64, expected_version=458442)
