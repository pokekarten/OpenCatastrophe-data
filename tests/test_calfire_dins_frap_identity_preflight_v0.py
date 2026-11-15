# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic negative-case regression for DINS–FRAP incident identity preflight."""

from __future__ import annotations

import json
import unittest

from scripts.calfire_dins_frap_identity_preflight_v0 import (
    IncidentIdentityError, MAX_BYTES, preflight_incident_pair,
)


def synthetic():
    return {
        "schema_version": "1.0.0",
        "origin": "synthetic",
        "dins_source_id": "us.calfire.dins.structure-damage",
        "frap_source_id": "us.calfire.frap.historical-fire-perimeters.firep25-1",
        "source_receipts": {"dins_sha256": None, "frap_sha256": None},
        "dins": {
            "incident_number": "CAXYZ 001234",
            "calfire_unit": "XYZ",
            "incident_start_date": "2023-08-12",
            "hazard_type": "Fire",
        },
        "frap_candidates": [{
            "inc_num": "001234",
            "unit_id": "XYZ",
            "alarm_date": "2023-08-12",
            "year": 2023,
            "irwinid": None,
        }],
    }


def evalobj(obj):
    return preflight_incident_pair(json.dumps(obj, sort_keys=True).encode())


class DinsFrapIdentityTests(unittest.TestCase):
    def test_positive_candidate_is_not_authorized_join(self):
        result = evalobj(synthetic())
        self.assertEqual(result["status"], "candidate_requires_original_identity_review")
        self.assertEqual(result["candidate_count"], 1)
        self.assertFalse(result["provider_confirmed_event_identity"])
        self.assertFalse(result["automatic_polygon_to_building_join_allowed"])
        self.assertFalse(result["model_data_admitted"])

    def test_different_incident_number_is_not_a_match(self):
        x = synthetic()
        x["frap_candidates"][0]["inc_num"] = "991234"
        self.assertEqual(evalobj(x)["status"], "no_candidate")

    def test_different_units_are_not_a_match(self):
        x = synthetic()
        x["frap_candidates"][0]["unit_id"] = "ABC"
        self.assertEqual(evalobj(x)["status"], "no_candidate")

    def test_date_drift_is_not_a_match(self):
        x = synthetic()
        x["frap_candidates"][0]["alarm_date"] = "2023-08-19"
        self.assertEqual(evalobj(x)["status"], "no_candidate")

    def test_cross_calendar_year_is_not_a_match(self):
        x = synthetic()
        x["dins"]["incident_start_date"] = "2022-12-31"
        self.assertEqual(evalobj(x)["status"], "no_candidate")

    def test_duplicate_perimeters_are_quarantined(self):
        x = synthetic()
        x["frap_candidates"].append(dict(x["frap_candidates"][0]))
        y = evalobj(x)
        self.assertEqual(y["status"], "ambiguous_candidates_quarantined")
        self.assertFalse(y["automatic_polygon_to_building_join_allowed"])

    def test_no_fuzzy_name_fallback(self):
        x = synthetic()
        x["dins"]["incident_name"] = "SYNTHETIC FIRE"
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_no_geometry_or_private_address(self):
        x = synthetic()
        x["frap_candidates"][0]["geometry"] = [1, 2]
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_no_inspection_rows(self):
        x = synthetic()
        x["dins"]["SITEADDRESS"] = "FAKE"
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_non_fire(self):
        x = synthetic()
        x["dins"]["hazard_type"] = "Earthquake"
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_unsupported_dins_identifier(self):
        x = synthetic()
        x["dins"]["incident_number"] = "1234"
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_mismatch_internal_dins_unit(self):
        x = synthetic()
        x["dins"]["calfire_unit"] = "ABC"
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_frapp_edition_unrecognized(self):
        x = synthetic()
        x["frap_source_id"] = "us.calfire.frap.other-edition"
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_year_drift(self):
        x = synthetic()
        x["frap_candidates"][0]["year"] = 2022
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_year_bool(self):
        x = synthetic()
        x["frap_candidates"][0]["year"] = True
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_invalid_day(self):
        x = synthetic()
        x["frap_candidates"][0]["alarm_date"] = "2023-02-30"
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_number_with_leading_zero_lost(self):
        x = synthetic()
        x["frap_candidates"][0]["inc_num"] = "1234"
        self.assertEqual(evalobj(x)["status"], "no_candidate")

    def test_external_receipts_are_unverified(self):
        x = synthetic()
        x["origin"] = "externally_prepared_incident_metadata"
        x["source_receipts"] = {"dins_sha256": "1" * 64, "frap_sha256": "2" * 64}
        self.assertTrue(evalobj(x)["source_receipts_supplied_not_verified"])
        self.assertFalse(evalobj(x)["provider_confirmed_event_identity"])

    def test_reject_external_unhashed(self):
        x = synthetic()
        x["origin"] = "externally_prepared_incident_metadata"
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_synthetic_fake_receipt(self):
        x = synthetic()
        x["source_receipts"]["frap_sha256"] = "a" * 64
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_overflow_list(self):
        x = synthetic()
        x["frap_candidates"] = x["frap_candidates"] * 26
        with self.assertRaises(IncidentIdentityError):
            evalobj(x)

    def test_reject_duplicate_keys(self):
        with self.assertRaises(IncidentIdentityError):
            preflight_incident_pair(b'{"x":1,"x":2}')

    def test_reject_nonfinite_json(self):
        with self.assertRaises(IncidentIdentityError):
            preflight_incident_pair(b'{"x":NaN}')

    def test_reject_input_too_large(self):
        with self.assertRaises(IncidentIdentityError):
            preflight_incident_pair(b"x" * (MAX_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
