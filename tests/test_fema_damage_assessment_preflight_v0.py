# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only negative checks for FEMA observed vs modelled evidence boundaries."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import unittest

from research_runners.fema_damage_assessment_preflight_v0 import (
    MAX_RECORDS, PreflightError, preflight,
)


def epoch(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp() * 1000)


def record(oid: int = 1, method: str = "FA", level: str = "MAJ") -> dict:
    return {"attributes": {
        "OBJECTID": oid,
        "DIS_NUMBER": "SYN-7",
        "EVENT_DATE": epoch("2020-08-25T00:00:00"),
        "ASMT_TYPE": method,
        "DMG_LEVEL": level,
        "DMG_TYPE": "FL",
        "IN_DEPTH": 2.0,
        "IMG_DATE": epoch("2020-08-26T00:00:00"),
        "PROD_DATE": epoch("2020-08-27T00:00:00"),
    }}


def fixture() -> dict:
    return {"event_disaster_number": "SYN-7", "event_day_utc": "2020-08-25", "features": [
        record(1, "FA", "MAJ"), record(2, "RS", "DES"),
        record(3, "MOD", "MAJ"), record(4, "UNK", "AFF"),
        record(5, "FA", "UNK"),
    ]}


class FEMAObservationGateTests(unittest.TestCase):
    def test_aggregate_and_nonadmission(self):
        x = preflight(fixture())
        self.assertEqual(x["record_count"], 5)
        self.assertEqual(x["assessment_counts"], {"FA": 2, "RS": 1, "MOD": 1, "OTHER_OR_UNKNOWN": 1})
        self.assertEqual(x["potential_field_observed_holdout_count"], 1)
        self.assertEqual(x["unknown_field_damage_count"], 1)
        self.assertEqual(x["unverified_assessment_method_count"], 1)
        self.assertEqual(x["non_null_inundation_depth_count"], 5)
        self.assertEqual(x["inundation_depth_unit"], "feet_provider_may_model_or_observe")
        self.assertFalse(x["scientific_independence_proven"])
        self.assertFalse(x["automatic_building_join_allowed"])
        self.assertFalse(x["model_input_admitted"])
        self.assertFalse(x["raw_data_redistribution_allowed"])
        self.assertNotIn("OBJECTID", json.dumps(x))
        self.assertNotIn("geometry", json.dumps(x))

    def test_deterministic_and_order_invariant(self):
        data = fixture()
        a = preflight(data)
        data["features"].reverse()
        self.assertEqual(a, preflight(data))
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(preflight(data), sort_keys=True))

    def test_reject_geometry_and_extra_fields(self):
        data = fixture()
        data["features"][0]["geometry"] = {"x": 123, "y": 456}
        with self.assertRaisesRegex(PreflightError, "geometry-free"):
            preflight(data)
        data = fixture()
        data["features"][0]["attributes"]["LONGITUDE"] = 12.3
        with self.assertRaisesRegex(PreflightError, "provider fields"):
            preflight(data)

    def test_reject_mixed_event_and_duplicate_ids(self):
        data = fixture()
        data["features"][0]["attributes"]["DIS_NUMBER"] = "SYN-8"
        with self.assertRaisesRegex(PreflightError, "multiple"):
            preflight(data)
        data = fixture()
        data["features"][1]["attributes"]["OBJECTID"] = 1
        with self.assertRaisesRegex(PreflightError, "OBJECTID"):
            preflight(data)

    def test_reject_event_date_mismatch_and_bad_utc(self):
        data = fixture()
        data["features"][0]["attributes"]["EVENT_DATE"] += 86400000
        with self.assertRaisesRegex(PreflightError, "event timestamp"):
            preflight(data)
        data = fixture()
        data["features"][0]["attributes"]["EVENT_DATE"] = 1.23
        with self.assertRaisesRegex(PreflightError, "epoch milliseconds"):
            preflight(data)
        data = fixture()
        data["event_day_utc"] = "2020-02-30"
        with self.assertRaisesRegex(PreflightError, "Gregorian"):
            preflight(data)

    def test_exact_provider_codes_reject_schema_drift(self):
        for field, unknown in (("ASMT_TYPE", "XYZ"), ("DMG_TYPE", "ZZ")):
            with self.subTest(field=field):
                data = fixture()
                data["features"][0]["attributes"][field] = unknown
                with self.assertRaisesRegex(PreflightError, "unrecognized provider"):
                    preflight(data)

    def test_source_known_other_and_unknown_never_promote(self):
        data = fixture()
        data["features"] = [record(1, "OTH", "NOD"), record(2, "UNK", "MIN")]
        x = preflight(data)
        self.assertEqual(x["assessment_counts"]["OTHER_OR_UNKNOWN"], 2)
        self.assertEqual(x["potential_field_observed_holdout_count"], 0)

    def test_missing_and_predisaster_images_are_diagnostic_only(self):
        data = fixture()
        data["features"][1]["attributes"]["IMG_DATE"] = None
        data["features"][0]["attributes"]["IMG_DATE"] = epoch("2020-08-24T00:00:00")
        data["features"][0]["attributes"]["PROD_DATE"] = epoch("2020-08-24T00:00:00")
        x = preflight(data)
        self.assertEqual(x["missing_imagery_date_count"], 1)
        self.assertEqual(x["imagery_before_event_count"], 1)
        self.assertEqual(x["production_before_event_count"], 1)
        self.assertEqual(x["potential_field_observed_holdout_count"], 0)

    def test_pre_event_imagery_never_enters_field_holdout(self):
        data = fixture()
        data["features"] = [record(1, "FA", "MAJ")]
        data["features"][0]["attributes"]["IMG_DATE"] = epoch("2020-08-24T00:00:00")
        x = preflight(data)
        self.assertEqual(x["imagery_before_event_count"], 1)
        self.assertEqual(x["potential_field_observed_holdout_count"], 0)

    def test_missing_production_date_is_not_proof_of_field_observation(self):
        data = fixture()
        data["features"] = [record(1, "FA", "MAJ")]
        data["features"][0]["attributes"]["PROD_DATE"] = None
        x = preflight(data)
        self.assertEqual(x["missing_production_date_count"], 1)
        self.assertEqual(x["potential_field_observed_holdout_count"], 0)

    def test_imagery_after_production_not_holdout(self):
        data = fixture()
        data["features"] = [record(1, "FA", "MAJ")]
        data["features"][0]["attributes"]["IMG_DATE"] = epoch("2020-08-28T00:00:00")
        x = preflight(data)
        self.assertEqual(x["imagery_after_production_count"], 1)
        self.assertEqual(x["potential_field_observed_holdout_count"], 0)

    def test_reject_unknown_damage_or_invalid_depth(self):
        data = fixture()
        data["features"][0]["attributes"]["DMG_LEVEL"] = "ZZZ"
        with self.assertRaisesRegex(PreflightError, "unrecognized DMG_LEVEL"):
            preflight(data)
        for bad in [-1, float("nan"), float("inf"), True, "2", 10 ** 1000]:
            with self.subTest(bad=str(bad)[:30]):
                data = fixture()
                data["features"][0]["attributes"]["IN_DEPTH"] = bad
                with self.assertRaisesRegex(PreflightError, "IN_DEPTH"):
                    preflight(data)

    def test_batch_bound_and_boolean_objectid(self):
        for length in (0, MAX_RECORDS + 1):
            data = {"event_disaster_number": "SYN-7", "event_day_utc": "2020-08-25", "features": [record(1)] * length}
            with self.assertRaisesRegex(PreflightError, "1..2000"):
                preflight(data)
        data = fixture()
        data["features"][0]["attributes"]["OBJECTID"] = True
        with self.assertRaisesRegex(PreflightError, "OBJECTID"):
            preflight(data)

    def test_nonobserved_types_never_become_ground_truth(self):
        data = fixture()
        data["features"] = [record(1, "MOD", "DES"), record(2, "RS", "MIN"), record(3, "OTH", "MAJ")]
        x = preflight(data)
        self.assertEqual(x["potential_field_observed_holdout_count"], 0)
        self.assertEqual(x["assessment_counts"]["MOD"], 1)
        self.assertEqual(x["assessment_counts"]["RS"], 1)
        self.assertEqual(x["unverified_assessment_method_count"], 1)


if __name__ == "__main__":
    unittest.main()
