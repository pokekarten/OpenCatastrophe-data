# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline mocked original-provider S3 listing and Parquet boundary checks."""
import copy
import struct
import unittest
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

from research_runners.overture_osm_bridge_original_probe_v0 import (
    BUCKET, PREFIX, ProbeError, probe, _list_objects,
)

ETAG = '"' + "a" * 32 + '-6"'
KEYS = [PREFIX + f"part-{i:05d}-5eacc0d5-7529-4a0a-85fa-1c7fe4b343e0.c000.snappy.parquet"
        for i in range(2)]
SIZES = [390230643, 390145222]


class FixtureTransport:
    def __init__(self):
        self.keys = list(KEYS)
        self.sizes = list(SIZES)
        self.receipts = []
        self.root = "ListBucketResult"
        self.truncated = "true"
        self.prefix = PREFIX
        self.bucket = BUCKET
        self.list_status = 200
        self.range_status = 206
        self.range_etag = ETAG
        self.range_length_offset = 0
        self.bad_prefix_magic = False
        self.bad_suffix_magic = False
        self.footer_length = 4281
        self.oversized_list = False

    def xml(self):
        parts = []
        for key, size in zip(self.keys, self.sizes):
            parts.append(f"<Contents><Key>{escape(key)}</Key><Size>{size}</Size>"
                         f"<LastModified>2026-10-21T17:36:57.000Z</LastModified>"
                         f"<ETag>{escape(ETAG)}</ETag></Contents>")
        return (f'<?xml version="1.0" encoding="UTF-8"?>'
                f'<{self.root} xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
                f"<Name>{self.bucket}</Name><Prefix>{self.prefix}</Prefix>"
                f"<MaxKeys>2</MaxKeys><IsTruncated>{self.truncated}</IsTruncated>"
                + "".join(parts) + f"</{self.root}>").encode()

    def __call__(self, request, limit):
        url = urlsplit(request.full_url)
        if "list-type" in url.query:
            body = self.xml()
            if self.oversized_list:
                body = body + b"x" * 33000
            return self.list_status, {"content-length": str(len(body))}, body
        key = url.path.lstrip("/")
        if key not in self.keys:
            raise AssertionError("unexpected original object")
        size = self.sizes[self.keys.index(key)]
        byte_range = request.get_header("Range")
        if byte_range == "bytes=0-3":
            body = b"NOPE" if self.bad_prefix_magic else b"PAR1"
            start, end = 0, 3
        elif byte_range == f"bytes={size - 8}-{size - 1}":
            body = struct.pack("<I", self.footer_length) + (b"NOPE" if self.bad_suffix_magic else b"PAR1")
            start, end = size - 8, size - 1
        else:
            raise AssertionError(f"unbounded request: {byte_range}")
        self.receipts.append((key, byte_range, limit))
        headers = {"content-range": f"bytes {start}-{end}/{size}",
                   "content-length": str(len(body) + self.range_length_offset),
                   "etag": self.range_etag}
        return self.range_status, headers, body


class OriginalBridgeProbeTests(unittest.TestCase):
    def test_two_exact_original_access_candidates(self):
        fake = FixtureTransport()
        data = probe(fetch=fake)
        self.assertEqual(data["sampled_object_count"], 2)
        self.assertTrue(data["listing_truncated"])
        self.assertEqual(len(fake.receipts), 4)
        self.assertEqual(sum(s for _, _, s in fake.receipts), 24)
        for row in data["objects"]:
            self.assertEqual(row["footer_metadata_length_bytes"], 4281)
            self.assertTrue(row["parquet_magic_prefix_verified"])
            self.assertTrue(row["parquet_magic_suffix_verified"])
            self.assertFalse(row["original_rows_read"])
            self.assertFalse(row["whole_object_sha256_verified"])
        for key in ("full_object_downloaded", "rights_review_approved",
                    "scientific_model_input_approved", "neon_import_performed"):
            self.assertIs(data[key], False)

    def test_no_global_completeness_from_listing(self):
        fake = FixtureTransport()
        _, truncated = _list_objects(fake)
        self.assertTrue(truncated)

    def test_reject_foreign_prefix(self):
        fake = FixtureTransport()
        fake.prefix = PREFIX.replace("provider=osm", "provider=microsoft")
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_wrong_bucket(self):
        fake = FixtureTransport()
        fake.bucket = "some-other-bucket"
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_unexpected_object(self):
        fake = FixtureTransport()
        fake.keys[0] = "bridgefiles/other/part-00000-file.parquet"
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_duplicate_source_objects(self):
        fake = FixtureTransport()
        fake.keys[1] = fake.keys[0]
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_unbounded_listing(self):
        fake = FixtureTransport()
        fake.oversized_list = True
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_invalid_root(self):
        fake = FixtureTransport()
        fake.root = "OtherResult"
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_implicit_or_missing_truncation(self):
        fake = FixtureTransport()
        fake.truncated = "unknown"
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_bad_parquet_header(self):
        fake = FixtureTransport()
        fake.bad_prefix_magic = True
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_bad_parquet_tail(self):
        fake = FixtureTransport()
        fake.bad_suffix_magic = True
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_bad_206_range_status(self):
        fake = FixtureTransport()
        fake.range_status = 200
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_bad_content_length(self):
        fake = FixtureTransport()
        fake.range_length_offset = 1
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_inconsistent_object_etag(self):
        fake = FixtureTransport()
        fake.range_etag = '"' + "f" * 32 + '-3"'
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_impossible_footer(self):
        fake = FixtureTransport()
        fake.footer_length = 200000
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_huge_source_file(self):
        fake = FixtureTransport()
        fake.sizes[0] = 1_000_000_001
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_unbounded_many_files(self):
        fake = FixtureTransport()
        fake.keys.append(PREFIX + "part-00003-5eacc0d5-7529-4a0a-85fa-1c7fe4b343e0.c000.snappy.parquet")
        fake.sizes.append(390000000)
        with self.assertRaises(ProbeError):
            probe(fetch=fake)

    def test_reject_non_xml_listing(self):
        fake = FixtureTransport()
        fake.xml = lambda: b"not XML"
        with self.assertRaises(ProbeError):
            probe(fetch=fake)


if __name__ == "__main__":
    unittest.main()
