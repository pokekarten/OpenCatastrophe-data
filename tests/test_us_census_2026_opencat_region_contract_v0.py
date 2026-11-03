# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only bridge smoke: exact 3 sample IDs, no real model or asset admission."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from research_runners.us_census_2026_opencat_region_contract_v0 import (
    ASSIGNMENT_SHA, Blocked, MAX_BYTES, ORIGINAL_SHA, PROFILE,
    SAMPLE_GEOIDS, verify_receipt, main,
)


def fake_crosswalk(**changes):
    doc = {
        "profile": PROFILE,
        "original_source_sha256": ORIGINAL_SHA,
        "source_namespace": "US_CENSUS_TIGER_2026",
        "boundary_year": 2026,
        "country_iso2": "US",
        "country_iso3": "USA",
        "synthetic_parent_regions": ["US", "US-LA"],
        "original_validated_parish_polygon_count": 64,
        "source_derived_synthetic_point_count": 64,
        "synthetic_points_with_exactly_one_polygon_interior": 64,
        "points_from_polygon_representative_point_not_real_assets": True,
        "synthetic_region_assignment_sha256": ASSIGNMENT_SHA,
        "sample_region_assignments": [
            {"asset_id": "synthetic_sample_" + geoid,
             "country_code": "US",
             "subdivisions": ["US-LA", "US-LA-" + geoid]}
            for geoid in SAMPLE_GEOIDS
        ],
        "original_source_geometry_persisted": False,
        "original_point_coordinates_emitted": False,
        "actual_asset_geolocation_demonstrated": False,
        "insured_TIV_or_policy_terms_verified": False,
        "native_OpenCat_region_loss_model_executed": False,
        "rights_and_scientific_admission_granted": False,
    }
    doc.update(changes)
    return doc


def blob(x):
    return json.dumps(x, sort_keys=True).encode("utf-8")


class SyntheticParishRollupContractTests(unittest.TestCase):
    def test_three_exact_private_region_shape_labels_but_no_model(self):
        result = verify_receipt(blob(fake_crosswalk()))
        self.assertEqual(result["sample_count"], 3)
        self.assertEqual([x["asset_id"] for x in result["sample_synthetic_region_labels"]],
                         ["synthetic_sample_" + geoid for geoid in SAMPLE_GEOIDS])
        self.assertEqual(result["sample_synthetic_region_labels"][1]["subdivisions"],
                         ["US-LA", "US-LA-22071"])
        for flag in ("private_target_code_identity_checked_by_this_script",
                     "source_receipt_original_bytes_independently_authenticated",
                     "full_64_synthetic_assignments_available_from_this_receipt",
                     "model_loss_bearing_asset_roster_matched", "region_rollup_executed",
                     "actual_property_geolocation_verified",
                     "source_license_and_scientific_admission_verified",
                     "insured_loss_or_real_model_run_proven"):
            self.assertFalse(result[flag], flag)

    def test_reject_tampered_original_source_identity_or_claimed_full_roster(self):
        original = fake_crosswalk()
        for attr, bad in (
            ("profile", "OPENCAT_REAL_PORTFOLIO"),
            ("original_source_sha256", "a" * 64),
            ("synthetic_region_assignment_sha256", "b" * 64),
            ("source_namespace", "US_CENSUS_TIGER_2025"),
            ("boundary_year", 2025),
            ("boundary_year", True),
            ("original_validated_parish_polygon_count", 63),
            ("source_derived_synthetic_point_count", 3),
            ("synthetic_points_with_exactly_one_polygon_interior", 63),
            ("synthetic_parent_regions", ["US", "US-LA", "US-LA-22051"]),
        ):
            with self.subTest(attr=attr, bad=bad):
                invalid = deepcopy(original)
                invalid[attr] = bad
                with self.assertRaises(Blocked):
                    verify_receipt(blob(invalid))

    def test_no_fake_original_geolocation_or_insured_admissions(self):
        for attr in (
            "original_source_geometry_persisted", "original_point_coordinates_emitted",
            "actual_asset_geolocation_demonstrated",
            "insured_TIV_or_policy_terms_verified",
            "native_OpenCat_region_loss_model_executed",
            "rights_and_scientific_admission_granted",
        ):
            with self.subTest(flag=attr):
                invalid = fake_crosswalk(**{attr: True})
                with self.assertRaises(Blocked):
                    verify_receipt(blob(invalid))
        with self.assertRaises(Blocked):
            verify_receipt(blob(fake_crosswalk(unreviewed_extra_key=True)))

    def test_reject_wrong_country_or_parish_nesting(self):
        base = fake_crosswalk()
        invalid_rows = [
            [{"asset_id": "REAL-INSURER-01", "country_code": "US",
              "subdivisions": ["US-LA", "US-LA-22051"]}] + base["sample_region_assignments"][1:],
            [base["sample_region_assignments"][0]] * 3,
            [{"asset_id": "synthetic_sample_22051", "country_code": "FR",
              "subdivisions": ["US-LA", "US-LA-22051"]}] + base["sample_region_assignments"][1:],
            [{"asset_id": "synthetic_sample_22051", "country_code": "US",
              "subdivisions": ["US-LA", "US-LA-22071"]}] + base["sample_region_assignments"][1:],
            [{"asset_id": "synthetic_sample_22051", "country_code": "US",
              "subdivisions": ["US-LA-22051"]}] + base["sample_region_assignments"][1:],
            [{"asset_id": "synthetic_sample_22051", "country_code": "US",
              "subdivisions": ["US-LA", "US-LA-22051"], "tiv_eur": 999}] + base["sample_region_assignments"][1:],
        ]
        for rows in invalid_rows:
            with self.subTest(rows=str(rows)[:110]), self.assertRaises(Blocked):
                verify_receipt(blob(fake_crosswalk(sample_region_assignments=rows)))

    def test_order_independent_sample_input_preserves_canonical_model_labels(self):
        x = fake_crosswalk()
        x["sample_region_assignments"].reverse()
        r = verify_receipt(blob(x))
        self.assertEqual([y["asset_id"] for y in r["sample_synthetic_region_labels"]],
                         ["synthetic_sample_" + geoid for geoid in SAMPLE_GEOIDS])

    def test_invalid_strict_json_fails_closed(self):
        for data in (b"", b" " * (MAX_BYTES + 1),
                     b'{"profile":"one","profile":"two"}',
                     b'{"boundary_year":NaN}', b"\xff\xfe", b"[]", b"null"):
            with self.subTest(data=data[:20]), self.assertRaises(Blocked):
                verify_receipt(data)

    def test_offline_cli_positive_and_negative(self):
        with tempfile.TemporaryDirectory() as work:
            p = Path(work) / "synthetic.json"
            p.write_bytes(blob(fake_crosswalk()))
            self.assertEqual(main(["--synthetic-crosswalk-receipt", str(p)]), 0)
            p.write_bytes(blob(fake_crosswalk(actual_asset_geolocation_demonstrated=True)))
            self.assertEqual(main(["--synthetic-crosswalk-receipt", str(p)]), 2)


if __name__ == "__main__":
    unittest.main()
