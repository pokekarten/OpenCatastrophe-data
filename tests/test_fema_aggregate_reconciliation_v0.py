# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only FEMA aggregate reconstruction, privacy and leakage tests."""

from __future__ import annotations

from copy import deepcopy
import json
import unittest

from research_runners.fema_aggregate_reconciliation_v0 import (
    ReconciliationError, reconcile,
)


def fixture() -> dict:
    return {
        "service_item_id": "e56e3d16fa144684bd532edbf298042c",
        "disaster_number": "DR-4399",
        "event_date_utc_ms": 1539129600000,
        "assessment_type": "RS",
        "damage_type": "WI",
        "census_count": 7,
        "level_counts": {"AFF": 6, "DES": 1},
        "county_level_counts": [
            {"state": "FL", "county": "Bay", "damage_level": "AFF", "count": 4},
            {"state": "FL", "county": "Bay", "damage_level": "DES", "count": 1},
            {"state": "FL", "county": "Gulf", "damage_level": "AFF", "count": 2},
        ],
        "date_groups": [
            {"event_date_utc_ms": 1539129600000, "image_date_utc_ms": None,
             "production_date_utc_ms": None, "count": 7},
        ],
    }


class FEMAAggregateReconciliationTests(unittest.TestCase):
    def test_synthetic_aggregates_reconcile_without_property_ids(self):
        report = reconcile(fixture())
        self.assertEqual(report["total_assessments"], 7)
        self.assertEqual(report["unique_counties"], 2)
        self.assertEqual(report["missing_image_date_assessments"], 7)
        self.assertEqual(report["missing_production_date_assessments"], 7)
        self.assertEqual(report["event_day_utc"], "2018-10-10")
        self.assertAlmostEqual(report["largest_county_share"], 5 / 7)
        self.assertFalse(report["scientific_independence_proven"])
        self.assertFalse(report["automatic_building_join_allowed"])
        self.assertFalse(report["model_input_admitted"])
        self.assertFalse(report["property_count_verified"])
        self.assertFalse(report["source_bytes_downloaded"])
        self.assertNotIn("Bay", json.dumps(report))
        self.assertNotIn("OBJECTID", json.dumps(report))
        self.assertNotIn("LATITUDE", json.dumps(report))

    def test_group_order_does_not_change_result(self):
        p = fixture()
        v = reconcile(p)
        p["county_level_counts"].reverse()
        self.assertEqual(v, reconcile(p))
        self.assertEqual(v, reconcile(deepcopy(p)))

    def test_census_must_agree_with_damage_and_region_counts(self):
        p = fixture()
        p["census_count"] = 8
        with self.assertRaisesRegex(ReconciliationError, "damage-level counts"):
            reconcile(p)
        p = fixture()
        p["county_level_counts"][0]["count"] += 1
        with self.assertRaisesRegex(ReconciliationError, "county-class"):
            reconcile(p)
        p = fixture()
        p["date_groups"][0]["count"] = 6
        with self.assertRaisesRegex(ReconciliationError, "date aggregate"):
            reconcile(p)

    def test_duplicate_county_cell_is_not_a_new_building(self):
        p = fixture()
        p["county_level_counts"].append(dict(p["county_level_counts"][0]))
        with self.assertRaisesRegex(ReconciliationError, "duplicate county"):
            reconcile(p)

    def test_reject_coordinate_or_raw_property_fields(self):
        p = fixture()
        p["county_level_counts"][0]["LATITUDE"] = 30.0
        with self.assertRaisesRegex(ReconciliationError, "extra/missing"):
            reconcile(p)
        p = fixture()
        p["geometry"] = {"x": 5}
        with self.assertRaisesRegex(ReconciliationError, "contract fields"):
            reconcile(p)

    def test_never_treat_modelled_or_field_as_remote_sensed_wind(self):
        for field, wrong in (("assessment_type", "FA"),
                             ("assessment_type", "MOD"),
                             ("damage_type", "FL")):
            with self.subTest(field=field, value=wrong):
                p = fixture()
                p[field] = wrong
                with self.assertRaisesRegex(ReconciliationError, "only remote sensing wind"):
                    reconcile(p)

    def test_timestamp_and_missing_dates_are_source_native(self):
        p = fixture()
        p["date_groups"][0]["image_date_utc_ms"] = 1539302400000
        self.assertEqual(reconcile(p)["missing_image_date_assessments"], 0)
        p = fixture()
        p["event_date_utc_ms"] += 3600000
        with self.assertRaisesRegex(ReconciliationError, "exact UTC date"):
            reconcile(p)
        p = fixture()
        p["date_groups"][0]["production_date_utc_ms"] = "2018-10-14"
        with self.assertRaisesRegex(ReconciliationError, "epoch milliseconds"):
            reconcile(p)

    def test_unique_disaster_number_and_source_version(self):
        p = fixture()
        p["disaster_number"] = "Hurricane Michael"
        with self.assertRaisesRegex(ReconciliationError, "disaster number"):
            reconcile(p)
        p = fixture()
        p["service_item_id"] = "different"
        with self.assertRaisesRegex(ReconciliationError, "service item"):
            reconcile(p)

    def test_reject_bool_nan_negative_zero_and_unreviewed_levels(self):
        for bad in (0, -1, True, 1.5, float("nan")):
            with self.subTest(value=str(bad)):
                p = fixture()
                p["census_count"] = bad
                with self.assertRaises(ReconciliationError):
                    reconcile(p)
        p = fixture()
        p["level_counts"] = {"AFF": 6, "BAD": 1}
        with self.assertRaisesRegex(ReconciliationError, "invalid/unreviewed"):
            reconcile(p)


if __name__ == "__main__":
    unittest.main()
