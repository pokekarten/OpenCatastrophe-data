# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only synthetic NASA COOLR distinct-product layer metadata tests."""
import copy
import hashlib
import json
import unittest

from scripts.coolr_polygon_layer_metadata_preflight_v0 import (
    CoolrMetadataError, LAYERS, MAX_METADATA_BYTES,
    screen_coolr_polygon_layer_metadata,
)


def fixture(kind):
    cfg = LAYERS[kind]
    return {
        "id": 0, "name": cfg["name"], "type": "Feature Layer",
        "geometryType": "esriGeometryPolygon", "objectIdField": "objectid",
        "hasZ": False, "hasM": False, "isDataVersioned": False,
        "supportsQueryWithHistoricMoment": False, "capabilities": "Query,Uploads",
        "maxRecordCount": 2000,
        "extent": {"xmin": -74.2, "xmax": 143.4, "ymin": -6.6, "ymax": 29.2,
                   "spatialReference": {"wkid": 4326}},
        "fields": [{"name": name, "type": value}
                   for name, value in cfg["required"].items()],
    }


def encoded(obj):
    return json.dumps(obj, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("utf-8")


class CoolrMetadataTests(unittest.TestCase):
    def test_both_layers_are_distinct_nonadmitted_products(self):
        for kind in LAYERS:
            with self.subTest(kind=kind):
                raw = encoded(fixture(kind))
                result = screen_coolr_polygon_layer_metadata(raw, layer_kind=kind)
                self.assertEqual(result["original_caller_supplied_metadata_sha256"], hashlib.sha256(raw).hexdigest())
                self.assertEqual(result["layer_kind"], kind)
                for flag in ("report_records_observed", "event_inventory_records_observed",
                             "report_event_deduplication_proven", "provider_byte_provenance_verified",
                             "dataset_or_api_commercial_rights_verified", "cat_model_input_admitted"):
                    self.assertFalse(result[flag])

    def test_cannot_label_report_layer_as_events_or_reverse(self):
        for kind in LAYERS:
            other = "events_polygon" if kind == "reports_polygon" else "reports_polygon"
            with self.assertRaises(CoolrMetadataError):
                screen_coolr_polygon_layer_metadata(encoded(fixture(kind)), layer_kind=other)

    def test_adversarial_metadata_inputs_rejected(self):
        mutations = [
            lambda o: o.update(id=1),
            lambda o: o.update(id=True),
            lambda o: o.update(name="egdb.sde.nasa_coolr_reports_poly"),
            lambda o: o.update(type="Table"),
            lambda o: o.update(geometryType="esriGeometryPoint"),
            lambda o: o.update(objectIdField="event_id"),
            lambda o: o.update(hasZ=True),
            lambda o: o.update(isDataVersioned=True),
            lambda o: o.update(supportsQueryWithHistoricMoment=True),
            lambda o: o.update(capabilities="Uploads"),
            lambda o: o.update(maxRecordCount=2001),
            lambda o: o["extent"]["spatialReference"].update(wkid=3857),
            lambda o: o["extent"].update(xmin=-190),
            lambda o: o["extent"].update(ymin=50, ymax=10),
            lambda o: o["fields"].pop(),
            lambda o: o["fields"][0].update(type="esriFieldTypeString"),
            lambda o: o["fields"].append(copy.deepcopy(o["fields"][0])),
            lambda o: o["fields"].append({"name":"OBJECTID", "type":"esriFieldTypeOID"}),
            lambda o: o["fields"].append({"name":"event_import_source","type":"esriFieldTypeString"}),
            lambda o: o["fields"].append({"name":"bad-name","type":"esriFieldTypeString"}),
            lambda o: o.update(error={"code":403}),
        ]
        for mutate in mutations:
            item = fixture("events_polygon")
            mutate(item)
            with self.subTest(idx=mutations.index(mutate)):
                with self.assertRaises(CoolrMetadataError):
                    screen_coolr_polygon_layer_metadata(encoded(item), layer_kind="events_polygon")
        for original in (b"", b"invalid", b'{"id":0,"id":0}', b'{"id":NaN}', b"x"*(MAX_METADATA_BYTES+1)):
            with self.assertRaises(CoolrMetadataError):
                screen_coolr_polygon_layer_metadata(original, layer_kind="events_polygon")


if __name__ == "__main__":
    unittest.main()
