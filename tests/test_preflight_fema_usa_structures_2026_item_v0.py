# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic tests only. No network or source geometry."""
from __future__ import annotations

import json
import unittest

from scripts.preflight_fema_usa_structures_2026_item_v0 import (
    inspect_source_item_and_view, StructuresMetadataBlocked, ITEM_ID,
    SERVICE, MAX_BYTES, WRONG_REGIONAL_ITEM_ID,
)


def item() -> dict:
    return {
        "id": ITEM_ID, "type": "Feature Service", "owner": "Esri_US_Federal_Data",
        "access": "public", "url": SERVICE,
        "licenseInfo": "<p>CC BY 4.0</p>",
        "contact_email": "synthetic-hidden@invalid.test",
    }


def service() -> dict:
    return {
        "serviceItemId": ITEM_ID,
        "fullExtent": {
            "xmin": -19668242.6307, "ymin": -1615916.1893,
            "xmax": 19386342.9397, "ymax": 11528307.4866,
            "spatialReference": {"wkid": 102100, "latestWkid": 3857},
        },
        "layers": [{
            "id": 0, "name": "USA_Structures_A",
            "type": "Feature Layer", "geometryType": "esriGeometryPolygon",
        }],
        "returned_asset_url": "https://invalid.test/not-requested",
    }


def evaluate(a=None, b=None):
    return inspect_source_item_and_view(
        json.dumps(item() if a is None else a, sort_keys=True).encode(),
        json.dumps(service() if b is None else b, sort_keys=True).encode(),
    )


class Structures2026SourceIdentityTests(unittest.TestCase):
    def test_valid_national_source_identity_metadata_only(self):
        z = evaluate()
        self.assertTrue(z["service_item_identity_matches"])
        self.assertEqual(z["full_extent_wkid"], 3857)
        self.assertEqual(z["provider_features_read"], 0)
        self.assertFalse(z["source_data_or_model_input_approved"])
        self.assertEqual(len(z["item_response_sha256"]), 64)
        self.assertNotIn("synthetic-hidden", json.dumps(z))
        self.assertNotIn("invalid.test", json.dumps(z))

    def test_reject_old_wrong_regional_item(self):
        b = service()
        b["serviceItemId"] = WRONG_REGIONAL_ITEM_ID
        with self.assertRaises(StructuresMetadataBlocked):
            evaluate(b=b)

    def test_reject_old_regional_coordinate_system_even_if_relabelled(self):
        b = service()
        b["fullExtent"]["spatialReference"]["latestWkid"] = 3452
        b["fullExtent"]["xmin"], b["fullExtent"]["xmax"] = 3658907., 3787029.
        with self.assertRaises(StructuresMetadataBlocked):
            evaluate(b=b)

    def test_reject_different_public_item_or_service(self):
        for key, value in [("id", "wrong"), ("url", "https://invalid.test"),
                           ("owner", "unreviewed"), ("access", "private"),
                           ("type", "Web Mapping Application")]:
            with self.subTest(key=key):
                a = item()
                a[key] = value
                with self.assertRaises(StructuresMetadataBlocked):
                    evaluate(a=a)

    def test_reject_cc_by_label_removed(self):
        a = item()
        a["licenseInfo"] = ""
        with self.assertRaises(StructuresMetadataBlocked):
            evaluate(a=a)

    def test_reject_layer_identity_change(self):
        b = service()
        b["layers"][0]["name"] = "unreviewed-other-data"
        with self.assertRaises(StructuresMetadataBlocked):
            evaluate(b=b)

    def test_reject_changed_geom_or_layer_count(self):
        b = service()
        b["layers"].append(b["layers"][0].copy())
        with self.assertRaises(StructuresMetadataBlocked):
            evaluate(b=b)

    def test_reject_oversize_and_nonfinite(self):
        with self.assertRaises(StructuresMetadataBlocked):
            inspect_source_item_and_view(b"x" * (MAX_BYTES + 1), b"{}")
        with self.assertRaises(StructuresMetadataBlocked):
            inspect_source_item_and_view(
                json.dumps(item()).encode(), b'{"serviceItemId":NaN}'
            )

    def test_reject_duplicate_keys_and_invalid_utf8(self):
        with self.assertRaises(StructuresMetadataBlocked):
            inspect_source_item_and_view(b'{"id":"a","id":"b"}', b"{}")
        with self.assertRaises(StructuresMetadataBlocked):
            inspect_source_item_and_view(b"\xff\xfe", b"{}")


if __name__ == "__main__":
    unittest.main()
