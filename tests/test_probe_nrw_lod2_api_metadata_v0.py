# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, offline regressions for the fixed NRW LoD2 metadata-only probe."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.probe_nrw_lod2_api_metadata_v0 import (
    MAX_BYTES, METADATA_URL, MetadataProbeError, assess, fetch_fixed_metadata, main,
)


def fixture() -> bytes:
    return json.dumps({
        "id": "building", "title": "Synthetic example collection", "itemType": "feature",
        "collectionType": "3d-container", "storageCrs": "http://www.opengis.net/def/crs/EPSG/0/5555",
        "extent": {"spatial": {"crs": "http://www.opengis.net/def/crs/OGC/0/CRS84h",
                               "bbox": [[5.7, 50.1, -4.7, 9.6, 52.7, 874.3]]}},
        "links": [{"rel": "self", "href": "https://example.invalid/not-a-real-source"},
                  {"rel": "items", "type": "application/city+json", "href": "https://example.invalid/items"}],
        "numberMatched": 10,
    }).encode()


class MetadataProbeTests(unittest.TestCase):
    def test_metadata_receipt_contains_no_source_links_or_features(self):
        receipt = assess(fixture())
        self.assertEqual(receipt["source_id"], "de.nrw.geobasis-lod2-ogc-features.2026")
        self.assertEqual(receipt["advertised_feature_count"], 10)
        self.assertEqual(receipt["fixed_url"], METADATA_URL)
        self.assertFalse(receipt["source_feature_bytes_acquired"])
        self.assertFalse(receipt["cat_model_input_approved"])
        self.assertFalse(receipt["rights_review_complete"])
        self.assertTrue(receipt["native_3d_collection"])
        self.assertTrue(receipt["cityjson_items_advertised"])
        self.assertFalse(receipt["geojson_items_advertised"])
        self.assertEqual(receipt["storage_crs"], "http://www.opengis.net/def/crs/EPSG/0/5555")
        self.assertNotIn("example.invalid", json.dumps(receipt))

    def test_fail_closed_bad_payload(self):
        variants = [
            b"", b"{}", b"[]", b"not json", b"\xff",
            b'{"id":"building","id":"building","links":[]}',
            b'{"id":"building","links":[],"numberMatched":NaN}',
            b'{"id":"building","links":[]}',
            b'{"id":"foo","links":[{}]}',
            b'{"id":"building","links":{},"features":[1]}',
            b'{"id":"building","links":[{}]}',
            b'{"id":"building","links":[{"rel":"self"}]}',
            b'{"id":"building","links":[{"href":"https://example.invalid"}]}',
            b'{"id":"building","links":[{"rel":" ","href":"https://example.invalid"}]}',
            b'{"id":"building","links":[{"rel":"self","href":" "]}',
            b'{"id":"building","links":[{}],"features":[1]}',
            b'{"id":"building","links":[{}],"numberMatched":true}',
            b'{"id":"building","links":[{}],"numberMatched":-1}',
            b'{"id":"building","links":[{}],"numberMatched":1,"itemCount":2}',
            b'{"id":"building","links":[{}],"extent":[]}',
            b" " * (MAX_BYTES + 1),
        ]
        for raw in variants:
            with self.subTest(raw=raw[:90]), self.assertRaises(MetadataProbeError):
                assess(raw)

    def test_fail_closed_html_and_unexpected_media_type(self):
        with self.assertRaises(MetadataProbeError):
            assess(fixture(), media_type="text/html")
        self.assertTrue(assess(fixture(), media_type="application/json; charset=utf-8")["collection_id_verified"])

    def test_offline_mode_never_calls_network(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_file = Path(directory) / "test.json"
            fixture_file.write_bytes(fixture())
            stdout = io.StringIO()
            with patch("scripts.probe_nrw_lod2_api_metadata_v0.fetch_fixed_metadata", side_effect=AssertionError("network")):
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(main(["--offline-json", str(fixture_file)]), 0)
            receipt = json.loads(stdout.getvalue())
            self.assertFalse(receipt["origin_verified_by_live_transport"])

    def test_live_request_has_only_fixed_url_and_rejects_redirects(self):
        class Headers(dict):
            pass
        class Response:
            status = 200
            headers = Headers({"Content-Type": "application/json", "Content-Length": str(len(fixture()))})
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def geturl(self): return METADATA_URL
            def read(self, size):
                assert size == MAX_BYTES + 1
                return fixture()
        class Opener:
            def open(self, req, timeout):
                assert req.full_url == METADATA_URL
                assert req.get_method() == "GET"
                assert timeout == 12
                return Response()
        with patch("scripts.probe_nrw_lod2_api_metadata_v0.build_opener", return_value=Opener()):
            raw, media = fetch_fixed_metadata()
        self.assertEqual(raw, fixture())
        self.assertEqual(media, "application/json")

    def test_3d_crs_and_item_semantic_drift_fails_closed(self):
        base = json.loads(fixture())
        mutations = (
            ("collectionType", "feature-collection"),
            ("itemType", "raster"),
            ("storageCrs", "http://www.opengis.net/def/crs/EPSG/0/4326"),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                changed = json.loads(json.dumps(base))
                changed[key] = value
                with self.assertRaises(MetadataProbeError):
                    assess(json.dumps(changed).encode())
        for spatial in (
            {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326", "bbox": [[5.7, 50.1, -4.7, 9.6, 52.7, 874.3]]},
            {"crs": "http://www.opengis.net/def/crs/OGC/0/CRS84h", "bbox": [[5.7, 50.1, 9.6, 52.7]]},
            {"crs": "http://www.opengis.net/def/crs/OGC/0/CRS84h", "bbox": [[9.6, 50.1, -4.7, 5.7, 52.7, 874.3]]},
        ):
            changed = json.loads(json.dumps(base))
            changed["extent"]["spatial"] = spatial
            with self.assertRaises(MetadataProbeError):
                assess(json.dumps(changed).encode())
        changed = json.loads(json.dumps(base))
        changed["links"] = [{"rel": "items", "type": "application/geo+json", "href": "https://example.invalid/items"}]
        with self.assertRaises(MetadataProbeError):
            assess(json.dumps(changed).encode())

    def test_citygml_alternative_is_accepted_but_not_geographic_validation(self):
        changed = json.loads(fixture())
        changed["links"][1]["type"] = "application/gml+xml"
        receipt = assess(json.dumps(changed).encode())
        self.assertTrue(receipt["citygml_items_advertised"])
        self.assertFalse(receipt["cityjson_items_advertised"])
        self.assertFalse(receipt["scientific_fitness_verified"])
        self.assertFalse(receipt["cat_model_input_approved"])

    def test_offline_oversize_rejected_before_parse(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "oversize.json"
            file.write_bytes(b"x" * (MAX_BYTES + 1))
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--offline-json", str(file)]), 1)


if __name__ == "__main__":
    unittest.main()
