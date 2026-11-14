# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only test fixtures for exact EPA original JSON city-response receipts."""
from __future__ import annotations

import hashlib
import json
import unittest

from research_runners import epa_frs_eia860_original_json_city_v0 as w


def program(plant="3136", acronym="EIA-860"):
    return {"ProgramSystemAcronym": acronym, "ProgramSystemId": plant}


def facility(fid="110000538525", city="DOVER", programs=None):
    return {
        "RegistryId": fid, "CityName": city, "StateAbbr": "DE",
        "Latitude83": "41.1", "Longitude83": "-75.9",
        "FacilityName": "SYNTHETIC ONLY", "ProgramFacilities": [program()] if programs is None else programs,
    }


def run(rows=None, cohort="DOVER", date="2026-11-04"):
    payload = json.dumps({"Results": {"FRSFacility": [facility()] if rows is None else rows}},
                         separators=(",", ":"), sort_keys=True).encode()
    return w.inspect_original_response(payload, hashlib.sha256(payload).hexdigest(),
                                       cohort=cohort, observed_date=date)


class OriginalJSONReceiptTests(unittest.TestCase):
    def test_single_original_response_yields_research_not_model_admission(self):
        r = run()
        self.assertEqual(r["eia860_program_link_rows"], 1)
        self.assertEqual(r["state"], "RESEARCH_SOURCE_IDS_ONLY")
        self.assertEqual(r["api_url"], w.COHORTS["DOVER"])
        for k in ("provider_original_full_frs_zip_authenticated", "eia_annual_2025_membership_verified",
                  "gem_asset_identity_confirmed", "corporate_ownership_or_insurance_inferred",
                  "source_http_headers_and_transport_independently_verified",
                  "frs_name_or_coordinate_proves_powerplant_location",
                  "source_rights_or_model_admission_granted"):
            self.assertFalse(r[k])
        self.assertNotIn("110000538525", json.dumps(r))
        self.assertNotIn("SYNTHETIC", json.dumps(r))

    def test_two_eia_ids_one_frs_produces_cardinality_review(self):
        r = run(rows=[facility(programs=[program("593"), program("7153")])])
        self.assertEqual(r["eia860_program_link_rows"], 2)
        self.assertEqual(r["frs_facilities_with_multiple_plant_ids"], 1)
        self.assertEqual(r["state"], "REVIEW_CARDINALITY")

    def test_same_plant_at_two_frs_records_flags_multiplicity(self):
        r = run(rows=[facility(), facility(fid="110000538526")])
        self.assertEqual(r["eia860_plant_ids_with_multiple_frs_records"], 1)
        self.assertEqual(r["state"], "REVIEW_CARDINALITY")

    def test_absent_program_is_unknown_not_nonexistent(self):
        r = run(rows=[facility(programs=[program("A1", acronym="NPDES")])])
        self.assertEqual(r["frs_facilities_without_eia860_link"], 1)
        self.assertEqual(r["state"], "REVIEW_CARDINALITY")

    def test_other_programs_do_not_multiply_eia_rows(self):
        r = run(rows=[facility(programs=[program("3136"), program("OTHER", acronym="RCRAINFO")])])
        self.assertEqual(r["eia860_program_link_rows"], 1)
        self.assertEqual(r["other_program_link_rows"], 1)

    def test_leading_zero_plant_ids_are_normalized(self):
        r = run(rows=[facility(programs=[program("003136")])])
        self.assertEqual(r["distinct_eia860_plant_ids"], 1)

    def test_duplicate_original_program_after_zero_padding_rejected(self):
        with self.assertRaisesRegex(w.FRSOriginalReceiptBlocked, "duplicate FRS-EIA"):
            run(rows=[facility(programs=[program("3136"), program("003136")])])

    def test_duplicate_registry_id_rejected(self):
        with self.assertRaisesRegex(w.FRSOriginalReceiptBlocked, "duplicate FRS"):
            run(rows=[facility(), facility()])

    def test_wrong_city_and_state_rejected(self):
        with self.assertRaisesRegex(w.FRSOriginalReceiptBlocked, "outside exact"):
            run(rows=[facility(city="NEWARK")])
        wrong = facility()
        wrong["StateAbbr"] = "PA"
        with self.assertRaises(w.FRSOriginalReceiptBlocked):
            run(rows=[wrong])

    def test_invalid_plant_id_rejected(self):
        for pid in ("", "0", "3136X", "1000000"):
            with self.subTest(pid=pid), self.assertRaises(w.FRSOriginalReceiptBlocked):
                run(rows=[facility(programs=[program(pid)])])

    def test_wrong_hash_rejected(self):
        raw = json.dumps({"Results":{"FRSFacility":[facility()]}}).encode()
        with self.assertRaisesRegex(w.FRSOriginalReceiptBlocked, "body SHA-256 mismatch"):
            w.inspect_original_response(raw, "0" * 64, cohort="DOVER", observed_date="2026-11-04")

    def test_repeated_json_keys_rejected(self):
        raw = b'{"Results":{"FRSFacility":[]},"Results":{"FRSFacility":[]}}'
        with self.assertRaises(w.FRSOriginalReceiptBlocked):
            w.inspect_original_response(raw, hashlib.sha256(raw).hexdigest(),
                                        cohort="DOVER", observed_date="2026-11-04")

    def test_invalid_date_or_cohort_rejected(self):
        for dt in ("2026-11-03", "2026-02-30", "2099-01-01", "today"):
            with self.subTest(dt=dt), self.assertRaises(w.FRSOriginalReceiptBlocked):
                run(date=dt)
        with self.assertRaises(w.FRSOriginalReceiptBlocked):
            run(cohort="UNKNOWN")

    def test_empty_and_oversized_block(self):
        for data in (b"", b"x" * (w.MAX_BYTES + 1)):
            with self.assertRaises(w.FRSOriginalReceiptBlocked):
                w.inspect_original_response(data, hashlib.sha256(data).hexdigest(),
                                            cohort="DOVER", observed_date="2026-11-04")

    def test_malformed_response_structure_rejected(self):
        for obj in ({}, {"Results": None}, {"Results": []},
                    {"Results":{"FRSFacility":{}}}, {"Results":{"FRSFacility":[]}}):
            raw=json.dumps(obj).encode()
            with self.assertRaises(w.FRSOriginalReceiptBlocked):
                w.inspect_original_response(raw, hashlib.sha256(raw).hexdigest(),
                                            cohort="DOVER", observed_date="2026-11-04")

    def test_report_counts_independent_of_input_row_order(self):
        a=facility(programs=[program("593"),program("7153")])
        b=facility(fid="110000538526",programs=[program("599")])
        first=run(rows=[a,b])
        second=run(rows=[b,a])
        for key in ("eia860_program_link_rows","frs_facilities_with_multiple_plant_ids",
                    "eia860_plant_ids_with_multiple_frs_records"):
            self.assertEqual(first[key],second[key])


if __name__ == "__main__":
    unittest.main()
