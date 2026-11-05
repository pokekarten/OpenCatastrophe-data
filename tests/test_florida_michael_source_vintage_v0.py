# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline metadata-only tests for 2017/2018 Florida source lineage controls."""

from __future__ import annotations

from copy import deepcopy
import json
import unittest

from research_runners.florida_michael_source_vintage_v0 import (
    MichaelSourceVintageError, assess_source_metadata, reconcile_source_family,
)


def make_source(sid: str, role: str, start: str | None,
                end: str | None, publication: str | None) -> dict:
    return {
        "source_id": sid,
        "role": role,
        "content_start": start,
        "content_end": end,
        "publication_date": publication,
        "actual_file_bytes_verified": False,
        "building_footprint_version_verified": False,
        "fema_image_lineage_verified": False,
        "dataset_access_and_license_verified": False,
    }


PARCELS2017 = make_source("florida.fgdl.parcels-2017", "parcel_polygon",
                          "2017-09-26", "2017-12-22", "2018-01-19")
PARCELS2018 = make_source("florida.fgdl.parcels-2018", "parcel_polygon",
                          "2018-07-24", "2018-12-28", "2019-03-12")
NOAA = make_source(
    "noaa.ngs.hurricane-michael-2018-emergency-imagery",
    "post_event_imagery", "2018-10-11", "2018-10-14", None,
)
NICB = make_source(
    "nicb.gic.hurricane-michael-2018-imagery",
    "post_event_imagery", None, None, "2018-11-05",
)
FEMA = make_source(
    "us.fema.historical-geospatial-damage-assessments",
    "remote_sensing_assessment", None, None, "2021-06-22",
)


class MichaelSourceVintageTests(unittest.TestCase):
    def test_2017_florida_parcel_is_pre_event_context_not_roof_geometry(self):
        result = assess_source_metadata(PARCELS2017)
        self.assertEqual(result["temporal_relation_to_event"], "pre_event_content_interval")
        self.assertTrue(result["pre_event_parcel_context_candidate"])
        self.assertFalse(result["pre_event_building_footprint_proven"])
        self.assertFalse(result["parcel_polygon_is_building_footprint"])
        self.assertFalse(result["model_input_admitted"])
        self.assertFalse(result["personal_address_or_owner_information_processed"])

    def test_2018_parcels_straddle_event_despite_2018_annual_label(self):
        result = assess_source_metadata(PARCELS2018)
        self.assertEqual(result["temporal_relation_to_event"], "content_interval_crosses_event")
        self.assertFalse(result["pre_event_parcel_context_candidate"])
        self.assertEqual(result["provider_publication_date"], "2019-03-12")
        self.assertFalse(result["model_input_admitted"])

    def test_exact_noaa_collection_and_nicb_unknown_specific_flight(self):
        noaa = assess_source_metadata(NOAA)
        nicb = assess_source_metadata(NICB)
        self.assertEqual(noaa["temporal_relation_to_event"], "post_event_content_interval")
        self.assertEqual(nicb["temporal_relation_to_event"], "image_acquisition_date_unverified")
        for row in (noaa, nicb):
            self.assertFalse(row["independent_image_label_validation_proven"])
            self.assertFalse(row["fema_assessment_original_image_proven"])

    def test_fema_img_date_null_is_not_event_time(self):
        result = assess_source_metadata(FEMA)
        self.assertIsNone(result["provider_content_start"])
        self.assertEqual(result["temporal_relation_to_event"], "imagery_date_missing_in_public_fema_cohort")
        self.assertFalse(result["fema_assessment_original_image_proven"])

    def test_five_way_source_reconciliation_never_grants_admission(self):
        result = reconcile_source_family([NOAA, PARCELS2018, FEMA, NICB, PARCELS2017])
        self.assertEqual(result["metadata_records_reconciled"], 5)
        self.assertEqual(result["pre_event_parcel_candidate_source_ids"],
                         ["florida.fgdl.parcels-2017"])
        self.assertEqual(result["event_crossing_parcel_source_ids"],
                         ["florida.fgdl.parcels-2018"])
        self.assertTrue(result["fema_original_image_identity_missing"])
        for key in ("two_organizations_make_label_independence_proven",
                    "parcels_can_be_autojoined_to_roof_or_fema_points",
                    "building_damage_training_labels_admitted", "model_input_admitted"):
            self.assertFalse(result[key])
        self.assertNotIn("owner", json.dumps(result).lower())
        self.assertNotIn("geometry", json.dumps(result).lower())

    def test_no_unknown_source_or_raw_parcel_rows(self):
        for key, value in (
            ("owner_name", "SENSITIVE"),
            ("features", []),
            ("parcelid", "00001"),
            ("longitude", -85.5),
        ):
            bad = deepcopy(PARCELS2017)
            bad[key] = value
            with self.subTest(key=key):
                with self.assertRaises(MichaelSourceVintageError):
                    assess_source_metadata(bad)
        bad = deepcopy(PARCELS2017)
        bad["source_id"] = "synthetic.source.without.review"
        with self.assertRaisesRegex(MichaelSourceVintageError, "identity"):
            assess_source_metadata(bad)

    def test_cannot_relabel_parcels_as_building_footprints_or_observed_damage(self):
        for role in ("building_footprint", "field_assessed_damage", "post_event_imagery"):
            bad = dict(PARCELS2017, role=role)
            with self.subTest(role=role):
                with self.assertRaisesRegex(MichaelSourceVintageError, "relabeled"):
                    assess_source_metadata(bad)
        for flag in ("building_footprint_version_verified", "fema_image_lineage_verified"):
            bad = dict(PARCELS2017, **{flag: True})
            with self.assertRaises(MichaelSourceVintageError):
                assess_source_metadata(bad)

    def test_dates_and_ranges_must_be_well_formed_and_not_reinterpreted(self):
        for date_value in ("2018-02-30", "2018-2-1", "2018-10-10Z", 20181010, True, "2031-01-01"):
            bad = dict(PARCELS2017, content_start=date_value)
            with self.subTest(value=str(date_value)):
                with self.assertRaises(MichaelSourceVintageError):
                    assess_source_metadata(bad)
        with self.assertRaisesRegex(MichaelSourceVintageError, "inconsistent"):
            assess_source_metadata(dict(PARCELS2017, content_end=None))
        with self.assertRaisesRegex(MichaelSourceVintageError, "inconsistent"):
            assess_source_metadata(dict(PARCELS2017, content_end="2017-01-01"))
        with self.assertRaisesRegex(MichaelSourceVintageError, "after event"):
            assess_source_metadata(dict(NOAA, content_start="2018-10-10"))

    def test_source_claim_types_and_duplicate_detection(self):
        for bad in (None, "true", 1, 0):
            with self.subTest(status=repr(bad)):
                with self.assertRaisesRegex(MichaelSourceVintageError, "boolean"):
                    assess_source_metadata(dict(FEMA, dataset_access_and_license_verified=bad))
        with self.assertRaisesRegex(MichaelSourceVintageError, "duplicate"):
            reconcile_source_family([PARCELS2017, deepcopy(PARCELS2017)])
        with self.assertRaisesRegex(MichaelSourceVintageError, "bounded"):
            reconcile_source_family([])
        with self.assertRaisesRegex(MichaelSourceVintageError, "bounded"):
            reconcile_source_family([PARCELS2017] * 6)


if __name__ == "__main__":
    unittest.main()
