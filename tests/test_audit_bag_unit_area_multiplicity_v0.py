# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""BAG unit/pand mapping test data is invented and contains no addresses."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_bag_unit_area_multiplicity_v0 import (
    BagUnitAreaError, audit, load, main,
)


def fixture():
    return {
        "schema": "bag-unit-area-normalised-v0",
        "as_of_date": "2026-11-05",
        "buildings": [
            {"pand_id": "B1", "active": True},
            {"pand_id": "B2", "active": True},
            {"pand_id": "B3", "active": False},
        ],
        "units": [
            {"unit_id": "U1", "area_m2": 80, "pand_ids": ["B1"],
             "status": "Verblijfsobject in gebruik"},
            {"unit_id": "U2", "area_m2": 60, "pand_ids": ["B1", "B2"],
             "status": "Verblijfsobject in gebruik"},
            {"unit_id": "U3", "area_m2": 55, "pand_ids": ["B3"],
             "status": "Verblijfsobject in gebruik"},
            {"unit_id": "U4", "area_m2": 30, "pand_ids": ["UNKNOWN"],
             "status": "Verblijfsobject in gebruik"},
            {"unit_id": "U5", "area_m2": 25, "pand_ids": [],
             "status": "Verblijfsobject in gebruik"},
            {"unit_id": "U6", "area_m2": 70, "pand_ids": ["B1"],
             "status": "Niet gerealiseerd verblijfsobject"},
            {"unit_id": "U7", "area_m2": 90, "pand_ids": ["B2"],
             "status": "Verblijfsobject in gebruik"},
        ],
    }


class BagUnitAreaMultiplicityTests(unittest.TestCase):
    def test_do_not_duplicate_units_across_panden(self):
        result = audit(fixture())
        self.assertEqual(result["building_reference_count"], 3)
        self.assertEqual(result["building_reference_active_count"], 2)
        self.assertEqual(result["unit_count"], 7)
        self.assertEqual(result["active_unit_count"], 6)
        self.assertEqual(result["active_total_usable_area_m2"], 340)
        self.assertEqual(result["active_unambiguously_linked_usable_area_m2"], 170)
        self.assertEqual(result["active_units_with_single_active_building"], 2)
        self.assertEqual(result["active_units_spanning_multiple_buildings"], 1)
        self.assertEqual(result["area_ambiguous_multiple_buildings_m2"], 60)
        self.assertEqual(result["area_with_unresolved_building_ids_m2"], 30)
        self.assertEqual(result["area_with_non_active_building_link_m2"], 55)
        self.assertEqual(result["area_without_building_link_m2"], 25)
        self.assertEqual(result["excluded_nonstandard_or_inactive_units"], 1)
        self.assertTrue(result["conservation_check_passed"])
        for field in ("source_admitted", "rights_reviewed", "gross_floor_area_verified",
                      "rebuilding_volume_verified",
                      "rebuild_value_or_insured_tiv_authorized"):
            self.assertFalse(result[field])
        result_text = json.dumps(result)
        self.assertNotIn("U1", result_text)
        self.assertNotIn("B1", result_text)

    def test_not_yet_realised_unit_is_not_usable_area(self):
        data = fixture()
        data["units"] = [data["units"][5]]
        result = audit(data)
        self.assertEqual(result["active_unit_count"], 0)
        self.assertEqual(result["active_total_usable_area_m2"], 0)
        self.assertEqual(result["excluded_nonstandard_or_inactive_units"], 1)

    def test_reject_personal_or_address_fields_at_any_level(self):
        for target in ("unit", "building", "payload"):
            with self.subTest(target=target), self.assertRaises(BagUnitAreaError):
                data = fixture()
                node = (data if target == "payload" else
                        data["units"][0] if target == "unit" else data["buildings"][0])
                node["postcode"] = "not_permitted"
                audit(data)

    def test_reject_same_unit_twice_and_duplicate_building_references(self):
        data = fixture()
        data["units"].append(copy.deepcopy(data["units"][0]))
        with self.assertRaisesRegex(BagUnitAreaError, "duplicate BAG verblijfsobject"):
            audit(data)
        data = fixture()
        data["units"][1]["pand_ids"] = ["B1", "B1"]
        with self.assertRaisesRegex(BagUnitAreaError, "duplicate BAG pand reference"):
            audit(data)

    def test_invalid_values_and_types_are_fail_closed(self):
        for area in (0, -1, True, 5.5, "80", 10_000_001):
            with self.subTest(area=area), self.assertRaises(BagUnitAreaError):
                data = fixture()
                data["units"][0]["area_m2"] = area
                audit(data)
        data = fixture()
        data["buildings"][0]["active"] = "true"
        with self.assertRaises(BagUnitAreaError):
            audit(data)

    def test_reject_invalid_date_or_id(self):
        data = fixture()
        data["as_of_date"] = "2026-02-30"
        with self.assertRaises(BagUnitAreaError):
            audit(data)
        data = fixture()
        data["units"][0]["unit_id"] = "a'b"
        with self.assertRaises(BagUnitAreaError):
            audit(data)

    def test_cli_and_reject_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Path(temp) / "synthetic.json"
            f.write_text(json.dumps(fixture()), encoding="utf-8")
            self.assertEqual(main(["--input", str(f)]), 0)
            f.write_text('{"schema":"x","schema":"y"}', encoding="utf-8")
            with self.assertRaises(BagUnitAreaError):
                load(f)
            self.assertEqual(main(["--input", str(f)]), 2)


if __name__ == "__main__":
    unittest.main()
