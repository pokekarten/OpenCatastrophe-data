# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for bounded original GRWL Zenodo API metadata canary."""
import json
import unittest

from research_runners.grwl_zenodo_original_metadata_probe_v0 import (
    CONCEPT_ID, FULL_VECTOR, HOST, LICENSE, MASK, MAX_BYTES, MetadataError,
    RECORDS, SCHEMA, default_fetch, main, reconcile, validate_original_record,
)


def fake_record(record_id):
    simplified = RECORDS[record_id]
    files = [{"key": key, "checksum": checksum, "size": size} for key, checksum, size in (simplified, FULL_VECTOR, MASK)]
    return {
        "id": record_id,
        "doi": f"10.5281/zenodo.{record_id}",
        "conceptrecid": CONCEPT_ID,
        "metadata": {"title": "Global River Widths from Landsat (GRWL) Database",
                     "version": "V01.01", "license": {"id": LICENSE}},
        "files": files,
    }


def encode(record):
    return json.dumps(record, separators=(",", ":")).encode()


class FakeFetch:
    def __init__(self):
        self.data = {rid: fake_record(rid) for rid in RECORDS}
        self.calls = []

    def __call__(self, url, limit):
        self.calls.append((url, limit))
        if limit != MAX_BYTES or url not in {HOST + str(rid) for rid in RECORDS}:
            raise AssertionError("non-allowlisted metadata GET")
        return encode(self.data[int(url.removeprefix(HOST))])


class GRWLOriginalMetadataTests(unittest.TestCase):
    def test_expected_two_versions_no_admission(self):
        f = FakeFetch()
        result = reconcile(fetch=f)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual(result["simplified_archive_size_difference_bytes"], 88699)
        self.assertTrue(result["same_provider_claim_for_mask"])
        self.assertTrue(result["same_provider_claim_for_full_vector"])
        self.assertTrue(result["same_provider_displayed_version_but_different_simplified_filenames"])
        self.assertEqual(f.calls, [(HOST + str(rid), MAX_BYTES) for rid in sorted(RECORDS)])
        self.assertEqual({r["record_id"] for r in result["records"]}, set(RECORDS))
        for key in ("original_source_zip_bytes_downloaded", "original_source_file_sha256_verified",
                    "licensed_for_production_use", "scientific_validation_completed",
                    "model_input_approved", "neon_modified"):
            self.assertIs(result[key], False)

    def test_metadata_sha_does_not_pretend_to_be_source_sha(self):
        r = validate_original_record(encode(fake_record(1297434)),1297434)
        self.assertEqual(len(r["metadata_json_sha256"]), 64)
        self.assertTrue(all("provider_md5_unverified" in f for f in r["original_files_metadata"]))
        self.assertTrue(all("provider_file_bytes_unverified" in f for f in r["original_files_metadata"]))

    def test_wrong_record_id(self):
        r = fake_record(1297434)
        r["id"] = 18624542
        with self.assertRaises(MetadataError):validate_original_record(encode(r), 1297434)

    def test_wrong_concept_id(self):
        r=fake_record(1297434);r["conceptrecid"]="other"
        with self.assertRaises(MetadataError):validate_original_record(encode(r),1297434)

    def test_wrong_doi(self):
        r=fake_record(1297434);r["doi"]="10.5281/zenodo.1269594"
        with self.assertRaises(MetadataError):validate_original_record(encode(r),1297434)

    def test_wrong_provider_license(self):
        r=fake_record(1297434);r["metadata"]["license"]={"id":"restricted"}
        with self.assertRaises(MetadataError):validate_original_record(encode(r),1297434)

    def test_version_change_requires_new_review(self):
        r=fake_record(18624542);r["metadata"]["version"]="V01.02"
        with self.assertRaises(MetadataError):validate_original_record(encode(r),18624542)

    def test_duplicate_file_names(self):
        r=fake_record(1297434);r["files"][1]["key"]=r["files"][0]["key"]
        with self.assertRaises(MetadataError):validate_original_record(encode(r),1297434)

    def test_file_checksum_modified(self):
        r=fake_record(18624542);r["files"][0]["checksum"]="md5:"+"a"*32
        with self.assertRaises(MetadataError):validate_original_record(encode(r),18624542)

    def test_file_size_modified(self):
        r=fake_record(1297434);r["files"][0]["size"] += 1
        with self.assertRaises(MetadataError):validate_original_record(encode(r),1297434)

    def test_duplicate_json_property_rejected(self):
        blob=b'{"id":1297434,"id":1297434}'
        with self.assertRaises(MetadataError):validate_original_record(blob,1297434)

    def test_invalid_json_and_oversize(self):
        for blob in (b"{}",b"NaN",b"x"* (MAX_BYTES+1), b"", b"\xff"):
            with self.subTest(blob=blob[:8]),self.assertRaises(MetadataError):
                validate_original_record(blob,1297434)

    def test_non_numeric_size(self):
        r=fake_record(1297434);r["files"][0]["size"]=True
        with self.assertRaises(MetadataError):validate_original_record(encode(r),1297434)

    def test_missing_original_file(self):
        r=fake_record(1297434);r["files"].pop()
        with self.assertRaises(MetadataError):validate_original_record(encode(r),1297434)

    def test_block_non_allowlisted_live_url_without_io(self):
        with self.assertRaises(MetadataError):default_fetch("https://zenodo.org/api/records/999999", MAX_BYTES)

    def test_opt_in_live_disabled_by_default(self):
        self.assertEqual(main([]), 2)


if __name__ == "__main__":
    unittest.main()
