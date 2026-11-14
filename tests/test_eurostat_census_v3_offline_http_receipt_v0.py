# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely synthetic offline HTTP receipt checks: no provider requests/files."""
from __future__ import annotations

import hashlib
import json
import unittest

from research_runners.eurostat_census_v3_offline_complete_zip_parity_v0 import (
    ORIGINAL_ZIP_BYTES,
)
from research_runners.eurostat_census_v3_full_csv_member_parity_v0 import (
    CSVParityBlocked, PROVIDER_ARCHIVE,
)
from research_runners.eurostat_census_v3_offline_http_receipt_v0 import (
    RECEIPT_SCHEMA, verify_local_zip_http_receipt,
)

SYNTHETIC_FILE_SHA = "f" * 64


def fake_dict(**updates):
    fields = {
        "schema": RECEIPT_SCHEMA,
        "source_url": PROVIDER_ARCHIVE,
        "requested_url": PROVIDER_ARCHIVE,
        "final_url": PROVIDER_ARCHIVE,
        "http_method": "GET",
        "http_status": 200,
        "redirect_count": 0,
        "content_encoding": "identity",
        "content_type": "application/zip",
        "content_length_bytes": ORIGINAL_ZIP_BYTES,
        "saved_bytes": ORIGINAL_ZIP_BYTES,
        "local_file_sha256": SYNTHETIC_FILE_SHA,
        "retrieved_at_utc": "2026-11-13T16:00:00Z",
        "source_access_review_reference": "review/census2021-v3",
    }
    fields.update(updates)
    return fields


def verify(fields):
    raw = json.dumps(fields,sort_keys=True,separators=(",",":")).encode("utf-8")
    return verify_local_zip_http_receipt(
        raw, expected_zip_sha256=SYNTHETIC_FILE_SHA,
        local_zip_bytes=ORIGINAL_ZIP_BYTES)


class OriginalProviderTransportReceiptTests(unittest.TestCase):
    def test_consistent_full_object_receipt_is_not_provider_attestation(self):
        raw=json.dumps(fake_dict(),sort_keys=True,separators=(",",":")).encode()
        result=verify_local_zip_http_receipt(
            raw,expected_zip_sha256=SYNTHETIC_FILE_SHA,
            local_zip_bytes=ORIGINAL_ZIP_BYTES)
        self.assertEqual(result["receipt_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertTrue(result["transport_receipt_consistent_with_local_zip"])
        self.assertTrue(result["strict_full_get_no_redirect"])
        self.assertFalse(result["independently_signed_provider_origin_verified"])
        self.assertFalse(result["access_review_approval_verified_by_this_script"])
        self.assertFalse(result["same_release_csv_tiff_14_band_parity_verified_by_this_script"])
        self.assertFalse(result["cat_model_input_approved"])

    def test_wrong_hostname_or_version_or_redirect_block(self):
        cases=[
            {"source_url":"https://example.org/Eurostat_Census-GRID_2021_V3.zip"},
            {"requested_url":PROVIDER_ARCHIVE.replace("_V3.zip","_V2.zip")},
            {"final_url":"https://proxy.example.org/census_v3.zip"},
            {"redirect_count":1},
            {"http_method":"HEAD"},
            {"http_status":206},
            {"http_status":True},
        ]
        for c in cases:
            with self.subTest(change=c):
                with self.assertRaises(CSVParityBlocked):
                    verify(fake_dict(**c))

    def test_hash_content_length_and_encoding_mismatch_block(self):
        cases=[
            {"local_file_sha256":"1"*64},
            {"local_file_sha256":None},
            {"content_length_bytes":ORIGINAL_ZIP_BYTES-1},
            {"saved_bytes":ORIGINAL_ZIP_BYTES-1},
            {"content_length_bytes":True},
            {"content_encoding":"gzip"},
            {"content_type":"text/html"},
            {"content_type":[]},
            {"content_type":"application/pdf"},
        ]
        for c in cases:
            with self.subTest(change=c):
                with self.assertRaises(CSVParityBlocked):
                    verify(fake_dict(**c))

    def test_missing_extra_and_duplicate_json_fields_fail_closed(self):
        no_schema=fake_dict()
        del no_schema["schema"]
        with self.assertRaisesRegex(CSVParityBlocked,"schema fields"):
            verify(no_schema)
        with self.assertRaisesRegex(CSVParityBlocked,"schema fields"):
            verify(fake_dict(debug="unapproved"))
        raw=(json.dumps(fake_dict())[:-1]+',"http_status":200}').encode()
        with self.assertRaisesRegex(CSVParityBlocked,"duplicate"):
            verify_local_zip_http_receipt(raw,
                expected_zip_sha256=SYNTHETIC_FILE_SHA,
                local_zip_bytes=ORIGINAL_ZIP_BYTES)

    def test_untrusted_retrieval_time_and_approval_reference_block(self):
        cases=[
            {"retrieved_at_utc":"2026-05-29T10:00:00Z"},
            {"retrieved_at_utc":"2099-01-01T10:00:00Z"},
            {"retrieved_at_utc":"2026-11-13T12:00:00+01:00"},
            {"retrieved_at_utc":"not-a-date"},
            {"source_access_review_reference":""},
            {"source_access_review_reference":"https://unreviewed.example.org"},
            {"source_access_review_reference":False},
        ]
        for c in cases:
            with self.subTest(change=c):
                with self.assertRaises(CSVParityBlocked):
                    verify(fake_dict(**c))


if __name__=="__main__":
    unittest.main()
