# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fictional BAG WFS propertyName response. Never use real household data."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_pdok_bag_wfs_private_area_v0 import (
    BagWfsPrivacyError, audit, load_private, main, validate_wfs_request,
)

URL = (
    "https://service.pdok.nl/kadaster/bag/wfs/v2_0"
    "?service=WFS&version=2.0.0&request=GetFeature"
    "&typeNames=bag:verblijfsobject&count=50"
    "&outputFormat=application/json"
    "&propertyName=identificatie,oppervlakte,pandidentificatie,status,gebruiksdoel"
    "&bbox=136701.28,455804.71,136728.86,455849.32,EPSG:28992"
)


def feature(i, *, active=True):
    return {
        "type": "Feature",
        "properties": {
            "identificatie": f"UNIT-{i}",
            "oppervlakte": 80 + i,
            "pandidentificatie": f"PAND-{i % 3}",
            "status": "Verblijfsobject in gebruik" if active else "Niet gerealiseerd verblijfsobject",
            "gebruiksdoel": "woonfunctie",
        },
        "geometry": {"type": "Point", "coordinates": [136708.0 + i, 455820.0]},
        "bbox": [136708.0 + i, 455820.0, 136708.0 + i, 455820.0],
    }


def fixture():
    rows = [feature(i) for i in range(8)] + [feature(8, active=False)]
    return {
        "type": "FeatureCollection", "name": "verblijfsobject",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::28992"}},
        "numberMatched": len(rows), "features": rows,
        "bbox": [136701.28, 455804.71, 136728.86, 455849.32],
    }


class BagWfsPrivateAreaTests(unittest.TestCase):
    def test_aggregate_observed_usable_area_once_without_individual_data(self):
        result = audit(fixture(), source_url=URL)
        self.assertEqual(result["all_records"], 9)
        self.assertEqual(result["active_unit_count"], 8)
        self.assertEqual(result["inactive_unit_count"], 1)
        self.assertEqual(result["active_usable_area_total_m2"], sum(80 + i for i in range(8)))
        self.assertEqual(result["active_units_with_singular_wfs_reference"], 8)
        self.assertEqual(result["active_usage_groups_minimum_5"], {"woonfunctie": 8})
        self.assertFalse(result["count_suppressed_for_privacy"])
        self.assertTrue(result["conservation_check_passed"])
        for k in ("source_admitted", "insured_tiv_verified", "per_building_usable_area_assigned",
                  "complete_multi_pand_links_verified", "individual_source_ids_included_in_output",
                  "provider_geometry_included_in_output"):
            self.assertFalse(result[k])
        out = json.dumps(result)
        self.assertNotIn("UNIT-", out)
        self.assertNotIn("PAND-", out)
        self.assertNotIn("136708", out)
        self.assertNotIn("postcode", out)

    def test_small_cell_suppression(self):
        data = fixture()
        data["features"] = data["features"][:4]
        data["numberMatched"] = 4
        result = audit(data, source_url=URL)
        self.assertTrue(result["count_suppressed_for_privacy"])
        self.assertIsNone(result["active_unit_count"])
        self.assertIsNone(result["active_usable_area_total_m2"])
        self.assertEqual(result["active_usage_groups_minimum_5"], {})

    def test_zero_results_not_false_data_gap(self):
        data = fixture()
        data["features"] = []
        data["numberMatched"] = 0
        result = audit(data, source_url=URL)
        self.assertTrue(result["count_suppressed_for_privacy"])
        self.assertTrue(result["conservation_check_passed"])

    def test_rejects_unfiltered_or_address_bearing_response(self):
        for extra in ("postcode", "huisnummer", "openbare_ruimte"):
            with self.subTest(extra=extra):
                data = fixture()
                data["features"][0]["properties"][extra] = "forbidden"
                with self.assertRaisesRegex(BagWfsPrivacyError, "address-bearing"):
                    audit(data, source_url=URL)
        data = fixture()
        del data["features"][0]["properties"]["oppervlakte"]
        with self.assertRaises(BagWfsPrivacyError):
            audit(data, source_url=URL)

    def test_rejects_duplicate_ids_and_bad_area(self):
        data = fixture()
        data["features"][1]["properties"]["identificatie"] = "UNIT-0"
        with self.assertRaises(BagWfsPrivacyError):
            audit(data, source_url=URL)
        for area in (None, -5, 0, 5.5, "80", True, 100001):
            with self.subTest(area=area):
                data = fixture()
                data["features"][0]["properties"]["oppervlakte"] = area
                with self.assertRaises(BagWfsPrivacyError):
                    audit(data, source_url=URL)

    def test_rejects_incomplete_count_or_wrong_geometry(self):
        data = fixture()
        data["numberMatched"] = 17
        with self.assertRaisesRegex(BagWfsPrivacyError, "incomplete"):
            audit(data, source_url=URL)
        data = fixture()
        data["features"][0]["geometry"]["type"] = "Polygon"
        with self.assertRaises(BagWfsPrivacyError):
            audit(data, source_url=URL)
        data = fixture()
        data["crs"]["properties"]["name"] = "EPSG:4326"
        with self.assertRaises(BagWfsPrivacyError):
            audit(data, source_url=URL)

    def test_rejects_unsafe_wfs_request(self):
        candidates = [
            URL.replace("https://service.pdok.nl", "https://evil.example"),
            URL.replace("https://", "http://"),
            URL.replace("EPSG:28992", "EPSG:4326"),
            URL.replace("count=50", "count=5000"),
            URL.replace("136728.86", "138000.00"),
            URL.replace("gebruiksdoel", "postcode"),
            URL + "&extra=1",
            URL + "&bbox=1,2,3,4,EPSG:28992",
        ]
        for candidate in candidates:
            with self.subTest(candidate=candidate), self.assertRaises(BagWfsPrivacyError):
                validate_wfs_request(candidate)

    def test_singular_reference_missing_is_not_assumed_mapping(self):
        data = fixture()
        data["features"][0]["properties"]["pandidentificatie"] = None
        result = audit(data, source_url=URL)
        self.assertEqual(result["active_units_without_wfs_reference"], 1)
        self.assertFalse(result["complete_multi_pand_links_verified"])

    def test_cli_private_aggregate_and_duplicate_json_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Path(temp) / "bounded-private.json"
            f.write_text(json.dumps(fixture()), encoding="utf-8")
            self.assertEqual(main(["--input", str(f), "--source-url", URL]), 0)
            f.write_text('{"type":"x","type":"y"}', encoding="utf-8")
            with self.assertRaises(BagWfsPrivacyError):
                load_private(f)
            self.assertEqual(main(["--input", str(f), "--source-url", URL]), 2)


if __name__ == "__main__":
    unittest.main()
