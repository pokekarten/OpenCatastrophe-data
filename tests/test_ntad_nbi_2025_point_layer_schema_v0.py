# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic NTAD original metadata corruption and admission regressions."""
from __future__ import annotations
import copy
import json
import unittest
from research_runners import ntad_nbi_2025_point_layer_schema_v0 as gate


def fixture():
    fields = [{"name": name, "type": typ} for name, typ in gate.REQUIRED.items()]
    fields[2]["length"] = 8
    fields[3]["length"] = 9
    fields += [{"name": f"EXTRA_{i}", "type": "esriFieldTypeString"} for i in range(50)]
    return {"id": 0, "type": "Feature Layer", "name": "National Bridge Inventory",
            "serviceItemId": gate.ITEM_ID, "geometryType": "esriGeometryPoint",
            "spatialReference": {"wkid": 4326},
            "extent": {"spatialReference": {"wkid": 4326}},
            "description": "FHWA dataset as of June 20, 2025",
            "fields": fields, "rawCoordinates": ["not to be output"]}


def wire(obj):
    return json.dumps(obj).encode("utf-8")


class NTADOriginalLayerSchemaTests(unittest.TestCase):
    def test_original_layer_identity_schema_and_non_admission(self):
        proof = gate.audit_layer(wire(fixture()))
        self.assertEqual(proof["declared_layer_epsg"], 4326)
        self.assertEqual(proof["NBI_legacy_lat_lon_code_widths"], [8, 9])
        self.assertEqual(proof["source_vintage_declared"], "2025-06-20")
        self.assertFalse(proof["individual_NTAD_geometries_audited"])
        self.assertFalse(proof["model_input_admitted"])
        self.assertNotIn("not to be output", json.dumps(proof))

    def test_changed_layer_identity_year_or_crs_fails(self):
        for key, value in (
            ("id", 1), ("name", "wrong"), ("serviceItemId", "new"),
            ("type", "Table"), ("geometryType", "esriGeometryPolygon"),
            ("description", "current, no as-of date"),
            ("spatialReference", {"wkid": 3857}),
            ("extent", {"spatialReference": {"wkid": 3857}}),
        ):
            doc = fixture()
            doc[key] = value
            with self.subTest(key=key), self.assertRaises(gate.Blocked):
                gate.audit_layer(wire(doc))

    def test_changed_fields_and_coordinate_lengths_fail(self):
        for key in gate.REQUIRED:
            doc = fixture()
            next(x for x in doc["fields"] if x["name"] == key)["type"] = "other"
            with self.subTest(key=key), self.assertRaises(gate.Blocked):
                gate.audit_layer(wire(doc))
        doc = fixture()
        next(x for x in doc["fields"] if x["name"] == "LAT_016")["length"] = 9
        with self.assertRaises(gate.Blocked):
            gate.audit_layer(wire(doc))

    def test_duplicate_field_name_and_duplicate_json_key_fail(self):
        doc = fixture()
        doc["fields"][1]["name"] = doc["fields"][0]["name"]
        with self.assertRaisesRegex(gate.Blocked, "duplicate NTAD"):
            gate.audit_layer(wire(doc))
        raw = wire(fixture()).replace(b'"id": 0,', b'"id": 0, "id": 0,', 1)
        with self.assertRaises(gate.Blocked):
            gate.audit_layer(raw)

    def test_error_html_nonfinite_and_incomplete_json_block(self):
        for raw in (b"<html>error</html>" * 40, b"\xff" * 900,
                    b'{"n": NaN}' * 80, b"{}", None):
            with self.subTest(raw=repr(raw)[:20]), self.assertRaises(gate.Blocked):
                gate.audit_layer(raw)
        doc = fixture()
        doc["error"] = {"code": 403}
        with self.assertRaises(gate.Blocked):
            gate.audit_layer(wire(doc))


if __name__ == "__main__":
    unittest.main()
