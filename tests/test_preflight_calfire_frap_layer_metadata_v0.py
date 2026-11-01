# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only provider schema drift and privacy checks for FRAP metadata."""

from __future__ import annotations

import copy
import json
import unittest

from scripts.preflight_calfire_frap_layer_metadata_v0 import (
    FrapMetadataError, MAX_METADATA_BYTES, preflight_frap_layer,
)

FIELD_TYPES = {
    "OBJECTID": "esriFieldTypeOID",
    "YEAR_": "esriFieldTypeSmallInteger",
    "UNIT_ID": "esriFieldTypeString",
    "FIRE_NAME": "esriFieldTypeString",
    "INC_NUM": "esriFieldTypeString",
    "IRWINID": "esriFieldTypeString",
    "ALARM_DATE": "esriFieldTypeDate",
    "CONT_DATE": "esriFieldTypeDate",
    "GlobalID": "esriFieldTypeGlobalID",
}


def synthetic_layer():
    return {
        "id": 0,
        "name": "California_Fire_Perimeters__all_",
        "type": "Feature Layer",
        "geometryType": "esriGeometryPolygon",
        "objectIdField": "OBJECTID",
        "globalIdField": "GlobalID",
        "extent": {"spatialReference": {"wkid": 102100, "latestWkid": 3857}},
        "timeInfo": {"startTimeField": "ALARM_DATE", "endTimeField": "CONT_DATE"},
        "fields": [{"name": k, "type": v} for k, v in FIELD_TYPES.items()],
    }


def execute(obj):
    return preflight_frap_layer(json.dumps(obj, sort_keys=True).encode("utf-8"))


class FrapLayerMetadataTests(unittest.TestCase):
    def test_good_synthetic_schema_is_metadata_only(self):
        result = execute(synthetic_layer())
        self.assertEqual(result["year_field_type"], "esriFieldTypeSmallInteger")
        self.assertEqual(result["gis_view_crs_wkid"], 102100)
        self.assertEqual(result["feature_rows_read"], 0)
        self.assertFalse(result["external_source_use_authorized"])
        self.assertFalse(result["provider_revision_verified"])
        self.assertFalse(result["model_data_admitted"])

    def test_webmercator_latest_alias_accepted(self):
        x = synthetic_layer()
        x["extent"]["spatialReference"] = {"wkid": 3857}
        self.assertEqual(execute(x)["gis_view_crs_wkid"], 3857)

    def test_reject_2023_text_year_field_from_different_version(self):
        x = synthetic_layer()
        x["fields"][1]["type"] = "esriFieldTypeString"
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_old_epsg3310_endpoint(self):
        x = synthetic_layer()
        x["extent"]["spatialReference"] = {"wkid": 3310}
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_bad_latest_crs_alias(self):
        x = synthetic_layer()
        x["extent"]["spatialReference"]["latestWkid"] = 4326
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_other_perimeter_layer_name(self):
        x = synthetic_layer()
        x["name"] = "FirePerimeters"
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_other_feature_layer_id(self):
        x = synthetic_layer()
        x["id"] = 1
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_boolean_layer_id(self):
        x = synthetic_layer()
        x["id"] = False
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_points_instead_of_polygons(self):
        x = synthetic_layer()
        x["geometryType"] = "esriGeometryPoint"
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_different_globalid_case(self):
        x = synthetic_layer()
        x["globalIdField"] = "GLOBALID"
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_wrong_event_time_fields(self):
        x = synthetic_layer()
        x["timeInfo"]["startTimeField"] = "EDITDATE"
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_missing_containment_time_field(self):
        x = synthetic_layer()
        del x["timeInfo"]["endTimeField"]
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_missing_incident_number(self):
        x = synthetic_layer()
        x["fields"] = [f for f in x["fields"] if f["name"] != "INC_NUM"]
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_wrong_alarm_date_data_type(self):
        x = synthetic_layer()
        for f in x["fields"]:
            if f["name"] == "ALARM_DATE":
                f["type"] = "esriFieldTypeString"
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_duplicate_fields(self):
        x = synthetic_layer()
        x["fields"].append(copy.deepcopy(x["fields"][0]))
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_feature_payload(self):
        x = synthetic_layer()
        x["features"] = [{"attributes": {"INC_NUM": "fake"}}]
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_geometry_payload(self):
        x = synthetic_layer()
        x["geometry"] = {"rings": []}
        with self.assertRaises(FrapMetadataError):
            execute(x)

    def test_reject_duplicate_json_keys(self):
        with self.assertRaises(FrapMetadataError):
            preflight_frap_layer(b'{"id":0,"id":0}')

    def test_reject_nan_json(self):
        with self.assertRaises(FrapMetadataError):
            preflight_frap_layer(b'{"id":NaN}')

    def test_reject_large_source_dump(self):
        with self.assertRaises(FrapMetadataError):
            preflight_frap_layer(b"x" * (MAX_METADATA_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
