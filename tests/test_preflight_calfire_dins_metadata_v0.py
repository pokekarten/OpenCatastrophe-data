# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only negative and positive CAL FIRE schema preflight tests."""

from __future__ import annotations

import json
import unittest

from scripts.preflight_calfire_dins_metadata_v0 import (
    DinsMetadataError,
    MAX_METADATA_BYTES,
    preflight_metadata,
)


def synthetic_layer() -> dict:
    return {
        "id": 0,
        "name": "POSTFIRE",
        "type": "Feature Layer",
        "geometryType": "esriGeometryPoint",
        "objectIdField": "OBJECTID",
        "globalIdField": "GLOBALID",
        "typeIdField": "DAMAGE",
        "types": [
            {"id": value} for value in (
                "Destroyed (>50%)", "Major (25-50%)", "Minor (10-25%)",
                "Affected (>0-10%)", "Inaccessible", "No Damage",
            )
        ],
        "fields": [
            {"name": "OBJECTID", "type": "esriFieldTypeOID"},
            {"name": "GLOBALID", "type": "esriFieldTypeGlobalID"},
            {"name": "DAMAGE", "type": "esriFieldTypeString"},
            {"name": "STRUCTURETYPE", "type": "esriFieldTypeString"},
            {"name": "INCIDENTNUM", "type": "esriFieldTypeString"},
            {"name": "INCIDENTSTARTDATE", "type": "esriFieldTypeDate"},
            {"name": "ROOFCONSTRUCTION", "type": "esriFieldTypeString"},
            {"name": "APN", "type": "esriFieldTypeString"},
            {"name": "SITEADDRESS", "type": "esriFieldTypeString"},
        ],
    }


class DinsMetadataPreflightTests(unittest.TestCase):
    def test_synthetic_valid_no_row_emission(self):
        receipt = preflight_metadata(json.dumps(synthetic_layer()).encode())
        self.assertEqual(receipt["feature_rows_read"], 0)
        self.assertFalse(receipt["model_data_admitted"])
        self.assertEqual(receipt["layer_name"], "POSTFIRE")
        self.assertEqual(receipt["science_fields_present"], ["ROOFCONSTRUCTION"])
        self.assertIn("APN", receipt["sensitive_field_names_present"])
        self.assertFalse(receipt["damage_states_are_insurance_loss_ratios"])
        self.assertEqual(receipt["incident_time_field_type"], "esriFieldTypeDate")
        self.assertEqual(len(receipt["damage_states"]), 6)
        self.assertNotIn("SITEADDRESS value", json.dumps(receipt))

    def test_rejects_feature_rows(self):
        obj = synthetic_layer()
        obj["features"] = [{"attributes": {"SITEADDRESS": "SYNTHETIC PRIVATE VALUE"}}]
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(json.dumps(obj).encode())

    def test_rejects_wrong_layer(self):
        obj = synthetic_layer()
        obj["id"] = 1
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(json.dumps(obj).encode())

    def test_rejects_required_type_drift(self):
        obj = synthetic_layer()
        obj["fields"][2]["type"] = "esriFieldTypeDouble"
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(json.dumps(obj).encode())

    def test_rejects_duplicate_field_name(self):
        obj = synthetic_layer()
        obj["fields"].append({"name": "DAMAGE", "type": "esriFieldTypeString"})
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(json.dumps(obj).encode())

    def test_rejects_duplicate_json_key(self):
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(b'{"id":0,"id":0}')

    def test_rejects_nonfinite_value(self):
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(b'{"id":NaN}')

    def test_rejects_oversized_response(self):
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(b"x" * (MAX_METADATA_BYTES + 1))

    def test_rejects_plain_feature_collection(self):
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(b'{"features":[]}')

    def test_rejects_unexpected_damage_class(self):
        obj = synthetic_layer()
        obj["types"][1]["id"] = "Insured loss 25-50%"
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(json.dumps(obj).encode())

    def test_rejects_missing_incident_date(self):
        obj = synthetic_layer()
        obj["fields"] = [f for f in obj["fields"] if f["name"] != "INCIDENTSTARTDATE"]
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(json.dumps(obj).encode())

    def test_rejects_duplicate_damage_class(self):
        obj = synthetic_layer()
        obj["types"][0]["id"] = obj["types"][1]["id"]
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(json.dumps(obj).encode())

    def test_rejects_false_integer_id(self):
        obj = synthetic_layer()
        obj["id"] = False
        with self.assertRaises(DinsMetadataError):
            preflight_metadata(json.dumps(obj).encode())


if __name__ == "__main__":
    unittest.main()
