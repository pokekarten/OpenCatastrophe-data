# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only count conservation and admission tests for public LINZ ArcGIS canary."""

from __future__ import annotations

import copy
import unittest

from scripts.nz_linz_public_arcgis_aggregate_canary_v0 import (
    BOUND, BUILDING, PROPERTY, CanaryError, CATEGORIES, _getcount, _query, validate,
)


def example():
    pmeta = {
        "extent": {"spatialReference": {"wkid": 2193}},
        "fields": [{"name": n} for n in ("OBJECTID", "source", "unit_of_property_id")],
        "editingInfo": {"dataLastEditDate": 1234567890000},
    }
    bmeta = {
        "extent": {"spatialReference": {"wkid": 2193}},
        "fields": [{"name": n} for n in ("OBJECTID", "building_id", "capture_source_to")],
    }
    counts = {
        "properties_all": 10, "properties_with_unit_id": 6,
        "properties_without_unit_id": 4, "buildings_all": 7,
        "buildings_with_building_id": 7, "buildings_without_building_id": 0,
        "bbox_properties_all": 3, "bbox_properties_rateable": 2,
        "bbox_buildings_all": 2,
    }
    grouped = {"features": [{"attributes": {"source": src, "n": number}}
                             for src, number in zip(CATEGORIES, (6, 1, 1, 1, 1))]}
    return pmeta, bmeta, counts, grouped


class ArcGISAggregateTests(unittest.TestCase):
    def test_clean_conservation_is_never_model_admission(self):
        output = validate(*example())
        self.assertEqual(output["source_categories"]["NZ Unit of Property"], 6)
        self.assertEqual(output["counts"]["properties_without_unit_id"], 4)
        self.assertFalse(output["admission"]["valuation_to_roof_join_observed"])
        self.assertFalse(output["admission"]["cat_model_input_admitted"])
        self.assertIn("not linked", output["spatial_probe"]["warning"])

    def test_property_missing_id_partition_fails(self):
        args = example()
        args[2]["properties_without_unit_id"] = 3
        with self.assertRaisesRegex(CanaryError, "identifier partition"):
            validate(*args)

    def test_unknown_source_or_duplicate_group_fails(self):
        args = example()
        args[3]["features"][0]["attributes"]["source"] = "synthetic unknown"
        with self.assertRaises(CanaryError):
            validate(*args)
        args = example()
        args[3]["features"].append(copy.deepcopy(args[3]["features"][0]))
        with self.assertRaises(CanaryError):
            validate(*args)

    def test_missing_field_and_crs_fails(self):
        args = example()
        args[0]["fields"].pop()
        with self.assertRaises(CanaryError):
            validate(*args)
        args = example()
        args[1]["extent"]["spatialReference"]["wkid"] = 4326
        with self.assertRaises(CanaryError):
            validate(*args)

    def test_noninteger_counts_and_bbox_excess_fail(self):
        args = example()
        args[2]["properties_all"] = True
        with self.assertRaises(CanaryError):
            validate(*args)
        args = example()
        args[2]["bbox_buildings_all"] = 8
        with self.assertRaises(CanaryError):
            validate(*args)
        with self.assertRaises(CanaryError):
            _getcount({"count": False})

    def test_only_count_only_or_group_queries_and_fixed_provider(self):
        url = _query(PROPERTY, {"where": "1=1", "returnCountOnly": "true", **BOUND})
        self.assertIn("returnCountOnly=true", url)
        self.assertIn("geometryType=esriGeometryEnvelope", url)
        self.assertTrue(url.startswith("https://services.arcgis.com/"))
        self.assertIn("/LINZ_NZ_Property_Boundaries/FeatureServer/0/query?", url)
        self.assertIn("LINZ_NZ_Building_Outlines", BUILDING)
        self.assertNotIn("property_address", url.casefold())


if __name__ == "__main__":
    unittest.main()
