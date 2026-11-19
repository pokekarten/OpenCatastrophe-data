# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic publisher metadata: no real address records or web requests."""
from __future__ import annotations
import json
import unittest
from scripts.probe_lu_bd_adresses_metadata_v0 import ASSETS, MAX_METADATA_BYTES, MetadataReceiptError, _parse, collect, main


def fake_record(asset):
    rid, filename, timestamp, md5, lo, hi = asset
    return {"id": rid, "title": filename, "url": f"https://download.data.public.lu/resources/adresses-georeferencees-bd-adresses/{timestamp}/{filename}",
            "checksum": {"type": "md5", "value": md5}, "filesize": (lo + hi) // 2, "last_modified": "2026-11-02T03:01:01Z"}


def raw(obj):
    return json.dumps(obj).encode("utf-8")


class Response:
    def __init__(self, value): self.value = value
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def getcode(self): return 200
    def read(self, length): return self.value[:length]


class FakeOpener:
    def __init__(self): self.requests = []
    def open(self, req, timeout):
        self.requests.append((req.full_url, req.get_method(), timeout))
        asset = next(a for a in ASSETS if a[0] in req.full_url)
        return Response(raw(fake_record(asset)))


class MetadataTests(unittest.TestCase):
    def test_single_original_receipt(self):
        record = _parse(raw(fake_record(ASSETS[0])), ASSETS[0])
        self.assertEqual(record["source_bytes_downloaded"], 0)
        self.assertFalse(record["model_admitted"])
        self.assertEqual(record["publisher_md5"], ASSETS[0][3])

    def test_fixed_three_requests_and_no_file_bytes(self):
        opener = FakeOpener()
        receipt = collect(opener)
        self.assertEqual(len(receipt["resources"]), 3)
        self.assertEqual(len(opener.requests), 3)
        for request, method, _ in opener.requests:
            self.assertEqual(method, "GET")
            self.assertTrue(request.startswith("https://data.public.lu/api/1/datasets/"))
        self.assertEqual(receipt["asset_bytes_downloaded"], 0)

    def test_rejects_resource_identity_swap(self):
        f = fake_record(ASSETS[0]); f["id"] = ASSETS[1][0]
        with self.assertRaises(MetadataReceiptError): _parse(raw(f), ASSETS[0])

    def test_rejects_unexpected_origins_and_redirect_targets(self):
        for u in ["http://download.data.public.lu/evil", "https://evil.example/addresses.geojson",
                  fake_record(ASSETS[0])["url"] + "?token=x"]:
            f = fake_record(ASSETS[0]); f["url"] = u
            with self.subTest(u=u), self.assertRaises(MetadataReceiptError): _parse(raw(f), ASSETS[0])

    def test_rejects_changed_file_vintage(self):
        f = fake_record(ASSETS[0]); f["url"] = f["url"].replace("20261102", "20261103")
        with self.assertRaises(MetadataReceiptError): _parse(raw(f), ASSETS[0])
        f = fake_record(ASSETS[0]); f["last_modified"] = "2026-11-03T00:00:00Z"
        with self.assertRaises(MetadataReceiptError): _parse(raw(f), ASSETS[0])

    def test_rejects_md5_change(self):
        f = fake_record(ASSETS[1]); f["checksum"]["value"] = "0" * 32
        with self.assertRaises(MetadataReceiptError): _parse(raw(f), ASSETS[1])

    def test_rejects_bad_byte_count(self):
        for val in [True, -1, 0, "20000000", 10**12]:
            f = fake_record(ASSETS[1]); f["filesize"] = val
            with self.subTest(val=val), self.assertRaises(MetadataReceiptError): _parse(raw(f), ASSETS[1])

    def test_rejects_bad_filename(self):
        f = fake_record(ASSETS[2]); f["title"] = "address-shp.zip"
        with self.assertRaises(MetadataReceiptError): _parse(raw(f), ASSETS[2])

    def test_rejects_overlong_and_duplicate_json(self):
        with self.assertRaises(MetadataReceiptError): _parse(b"x" * (MAX_METADATA_BYTES + 1), ASSETS[0])
        malformed = raw(fake_record(ASSETS[0]))[:-1] + b',"id":"duplicated"}'
        with self.assertRaises(MetadataReceiptError): _parse(malformed, ASSETS[0])

    def test_nested_data_wrapper_allowed(self):
        self.assertEqual(_parse(raw({"data": fake_record(ASSETS[1])}), ASSETS[1])["name"], "addresses.csv")

    def test_offline_default_no_network(self):
        self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
