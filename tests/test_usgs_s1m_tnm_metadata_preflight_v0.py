# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic offline regressions for TNM S1M metadata identity gate."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from research_runners.usgs_s1m_tnm_metadata_preflight_v0 import (
    Blocked, DATASET_TAG, LEGACY_TAG, MAX_BYTES, check_catalog, check_products, load_receipt
)


class TNMS1MTests(unittest.TestCase):
    @staticmethod
    def catalogue(name=DATASET_TAG, id_="seamless-1m-dem"):
        return [{"parentCategory": "Data", "tags": [{"sbDatasetTag": LEGACY_TAG, "id": "one-meter-dem"},
                                                        {"sbDatasetTag": name, "id": id_}]}]

    @staticmethod
    def product(dataset=DATASET_TAG, host="prd-tnm.s3.amazonaws.com"):
        return {"total": 1, "items": [{"sourceId": "a" * 24, "datasets": [dataset], "format": "GeoTIFF",
                                       "downloadURL": f"https://{host}/StagedProducts/Elevation/S1M/test.tif",
                                       "boundingBox": {"minX": -110.9, "minY": 43.4, "maxX": -110.8, "maxY": 43.5}}]}

    def test_s1m_exact_identity(self):
        self.assertEqual(check_catalog(self.catalogue())["dataset_tag"], DATASET_TAG)

    def test_legacy_name_is_not_s1m(self):
        with self.assertRaises(Blocked):
            check_catalog(self.catalogue(LEGACY_TAG))

    def test_duplicate_s1m_rejected(self):
        with self.assertRaises(Blocked):
            check_catalog(self.catalogue() + self.catalogue())

    def test_product_exact_tag(self):
        self.assertEqual(check_products(self.product())["admission"], "not_admitted")

    def test_missing_product_tag_fail_closed(self):
        p = self.product()
        p["items"][0]["datasets"] = []
        with self.assertRaises(Blocked):
            check_products(p)

    def test_wrong_product_does_not_auto_substitute(self):
        with self.assertRaises(Blocked):
            check_products(self.product(LEGACY_TAG))

    def test_untrusted_product_download_host(self):
        with self.assertRaises(Blocked):
            check_products(self.product(host="example.org"))

    def test_false_zero_result(self):
        with self.assertRaises(Blocked):
            check_products({"total": 0, "items": []})

    def test_raw_byte_sha_and_duplicate_key(self):
        raw = b'{"total":1,"total":2}'
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "original.json"
            p.write_bytes(raw)
            with self.assertRaises(Blocked):
                load_receipt(p, hashlib.sha256(raw).hexdigest())
            p.write_bytes(b'{"items":[],"total":0}')
            with self.assertRaises(Blocked):
                load_receipt(p, hashlib.sha256(raw).hexdigest())

    def test_byte_limit(self):
        raw = b" " * (MAX_BYTES + 1)
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "original.json"
            p.write_bytes(raw)
            with self.assertRaises(Blocked):
                load_receipt(p, hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
