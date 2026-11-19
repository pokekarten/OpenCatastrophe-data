# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic and frozen provider-metadata negative controls. No network."""
import copy
import unittest

from research_runners.loing2016_clery_wfs_spatial_exclusion_v0 import (
    SourceScopeBlocked, audit_scope,
)


def reviewed_metadata():
    # Official first-party publication and official hydrometric flood mark
    # sourced in an offline research review. NOT a WFS feature fixture.
    return {
        "dataset_id": "67377bc98609c51859c40b28",
        "source_role": "MULTI_EVENT_HISTORICAL_FLOOD_ENVELOPE",
        "site_id": "CER_LO_16_S_174",
        "site_wgs84_lon_lat": ["2.72937190", "48.00108820"],
        "advertised_wfs_wgs84_bbox": [
            "2.76257501317139", "48.0382890910261",
            "3.13472665244762", "48.1469782244935"
        ]
    }


class CleryMontargisNegativeControlTests(unittest.TestCase):
    def test_reviewed_clery_wfs_bbox_excludes_montargis_physical_mark(self):
        r = audit_scope(reviewed_metadata())
        self.assertFalse(r["published_wfs_bbox_contains_montargis_2016_mark"])
        self.assertEqual(r["test_site_id"], "CER_LO_16_S_174")
        self.assertIn("SPATIALLY_EXCLUDED", r["scientific_verdict"])

    def test_even_published_open_license_does_not_authenticate_geometry(self):
        r = audit_scope(reviewed_metadata())
        self.assertEqual(r["catalogue_dataset_licence"], "Licence Ouverte 2.0")
        for key in (
            "provider_geometry_bytes_acquired_or_sha256_attested",
            "provider_feature_schema_or_topology_verified",
            "individual_flood_event_date_per_feature_verified",
            "layer_is_2016_event_specific",
            "layer_is_independent_montargis_2016_extent",
            "building_2016_depth_or_loss_admitted",
        ):
            self.assertFalse(r[key], key)

    def test_false_2016_event_identity_injected_is_blocked(self):
        d = reviewed_metadata()
        d["source_role"] = "OBSERVED_LOING_JUNE_2016"
        with self.assertRaises(SourceScopeBlocked):
            audit_scope(d)

    def test_unreviewed_site_must_not_pass_as_montargis(self):
        d = reviewed_metadata()
        d["site_id"] = "ANY_OTHER_2016_GAUGE"
        with self.assertRaises(SourceScopeBlocked):
            audit_scope(d)

    def test_expanded_provider_bbox_requires_re_review_not_auto_admission(self):
        d = reviewed_metadata()
        d["advertised_wfs_wgs84_bbox"][0] = "2.60000000000000"
        d["advertised_wfs_wgs84_bbox"][1] = "47.9000000000000"
        with self.assertRaises(SourceScopeBlocked):
            audit_scope(d)

    def test_unreviewed_dataset_and_extra_admission_fields_blocked(self):
        d = reviewed_metadata()
        d["dataset_id"] = "another_dataset"
        with self.assertRaises(SourceScopeBlocked):
            audit_scope(d)
        d = reviewed_metadata()
        d["model_ready"] = True
        with self.assertRaises(SourceScopeBlocked):
            audit_scope(d)

    def test_coordinates_are_decimal_strings_not_floats_or_bools(self):
        for value in (2.7293719, True, None, "nan", "1e30"):
            with self.subTest(value=value), self.assertRaises(SourceScopeBlocked):
                d = reviewed_metadata()
                d["site_wgs84_lon_lat"][0] = value
                audit_scope(d)

    def test_site_and_bounds_must_have_exact_cardinality(self):
        d = reviewed_metadata()
        d["site_wgs84_lon_lat"].append("123")
        with self.assertRaises(SourceScopeBlocked):
            audit_scope(d)
        d = reviewed_metadata()
        d["advertised_wfs_wgs84_bbox"].pop()
        with self.assertRaises(SourceScopeBlocked):
            audit_scope(d)

    def test_unknown_or_incorrect_bbox_precision_does_not_assert_provenance(self):
        for value in ("2.7625", "-99", "10000000", "NaN"):
            with self.subTest(value=value), self.assertRaises(SourceScopeBlocked):
                d = reviewed_metadata()
                d["advertised_wfs_wgs84_bbox"][0] = value
                audit_scope(d)

    def test_no_independent_holdout_claim_even_when_source_ids_verified(self):
        r = audit_scope(reviewed_metadata())
        self.assertEqual(r["source_semantics"],
                         "MULTI_EVENT_HISTORICAL_FLOOD_ENVELOPE")
        self.assertFalse(r["layer_is_independent_montargis_2016_extent"])


if __name__ == "__main__":
    unittest.main()
