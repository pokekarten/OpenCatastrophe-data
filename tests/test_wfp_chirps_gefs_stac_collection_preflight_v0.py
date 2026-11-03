# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic original-STAC shape tests; no data, user assets or HTTP."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from research_runners.wfp_chirps_gefs_stac_collection_preflight_v0 import (
    Blocked, COLLECTION_IDS, MAX_BYTES, inspect, main, verify,
)


def source_bytes(collection="daily", **kw):
    cid = COLLECTION_IDS[collection]
    x = {
        "id": cid, "type": "Collection", "stac_version": "1.0.0",
        "license": "CC-BY-4.0",
        "extent": {"spatial": {"bbox": [[-180, -60, 180, 60]]},
                   "temporal": {"interval": [["2001-01-01T00:00:00Z", None]]}},
        "providers": [{"name": "Climate Hazards Center (CHC)", "roles": ["producer"]}],
        "links": [{"rel": "self", "href": "https://api.earthobservation.vam.wfp.org/stac/collections/" + cid}],
        "item_assets": {"band": {
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "raster:bands": [{"unit": "1", "nodata": -9999, "data_type": "float32"}],
        }},
    }
    x.update(kw)
    return json.dumps(x, sort_keys=True).encode()


class WfpStacMetadataTests(unittest.TestCase):
    def test_both_exact_collection_metadata_only(self):
        for kind in COLLECTION_IDS:
            with self.subTest(kind=kind):
                info = inspect(source_bytes(kind), kind)
                self.assertEqual(info["raster_band_unit_as_published"], "1")
                self.assertEqual(info["raster_band_nodata"], -9999)
                self.assertFalse(info["precipitation_unit_mm_verified"])
                self.assertFalse(info["original_issue_time_verified"])
                self.assertFalse(info["insured_loss_model_input_admitted"])

    def test_changed_scientific_source_shape_rejected(self):
        changes = [
            {"id": "chirps_dekad"},
            {"type": "FeatureCollection"},
            {"stac_version": "2.0.0"},
            {"license": "proprietary"},
            {"extent": {"spatial": {"bbox": [[-180, -90, 180, 90]]},
                        "temporal": {"interval": [["2001-01-01T00:00:00Z", None]]}}},
            {"providers": [{"name": "Other", "roles": ["producer"]}]},
            {"links": []},
            {"item_assets": {"band": {"type": "image/tiff",
                                     "raster:bands": [{"unit": "1", "nodata": -9999, "data_type": "float32"}]}}},
            {"item_assets": {"band": {"type": "image/tiff; application=geotiff; profile=cloud-optimized",
                                     "raster:bands": [{"unit": "mm", "nodata": -9999, "data_type": "float32"}]}}},
            {"item_assets": {"band": {"type": "image/tiff; application=geotiff; profile=cloud-optimized",
                                     "raster:bands": [{"unit": "1", "nodata": 0, "data_type": "float32"}]}}},
            {"error": {"code": 401}},
            {"features": [{"type": "Feature"}]},
        ]
        for change in changes:
            with self.subTest(change=str(change)[:80]), self.assertRaises(Blocked):
                inspect(source_bytes(**change), "daily")

    def test_strict_original_metadata_size_and_json_guards(self):
        for raw in (b"", b" "*(MAX_BYTES+1), b'{"id":"a","id":"b"}',
                    b'{"id":Infinity}', b"\xff\xfe", b"[]"):
            with self.subTest(raw=raw[:20]), self.assertRaises(Blocked):
                inspect(raw, "daily")

    def test_exact_original_sha_and_cli(self):
        raw = source_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.json"
            path.write_bytes(raw)
            result = verify(path, digest, "daily")
            self.assertTrue(result["original_metadata_bytes_checked"])
            self.assertFalse(result["http_response_provenance_independently_verified"])
            self.assertFalse(result["provider_bytes_committed"])
            self.assertEqual(main(["--collection", "daily", "--original-json", str(path),
                                   "--expected-sha256", digest]), 0)
            for bad in ("0"*64, "INVALID", "A"*64):
                self.assertEqual(main(["--collection", "daily", "--original-json", str(path),
                                       "--expected-sha256", bad]), 2)

    def test_cross_product_mislabelling_rejected(self):
        with self.assertRaises(Blocked):
            inspect(source_bytes("daily"), "dekad")
        with self.assertRaises(Blocked):
            inspect(source_bytes("dekad"), "daily")


if __name__ == "__main__":
    unittest.main()
