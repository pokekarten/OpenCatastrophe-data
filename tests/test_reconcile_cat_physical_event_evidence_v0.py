# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only, fail-closed tests for real-source event evidence reconciliation."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from scripts import reconcile_cat_physical_event_evidence_v0 as mod


def manifest():
    return json.dumps({
        "schema_version": "oc-effis-synthetic-sites-v0",
        "crs": "OGC:CRS84",
        "synthetic_only": True,
        "sites": [
            {"site_id": "SYNTH_DE", "longitude": 10.0, "latitude": 50.0},
            {"site_id": "SYNTH_FR", "longitude": 2.0, "latitude": 48.0},
        ],
    }).encode("utf-8")


EFFIS = b"synthetic EFFIS source stub"
CLIMK = b"synthetic CLIMK source stub"


def fire_report():
    return {
        "event_key": "effis:burntarea:646790",
        "event_timestamp": "2026-08-25T13:01:00+02:00",
        "peril": "WILDFIRE",
        "measure": "BINARY_BURNT_AREA_MEMBERSHIP_NOT_INTENSITY",
        "source_payload_sha256": hashlib.sha256(EFFIS).hexdigest(),
        "provider_source_mutable": True,
        "site_count": 2,
        "site_hits": [
            {"site_id": "SYNTH_DE", "within_observed_burnt_polygon": True},
            {"site_id": "SYNTH_FR", "within_observed_burnt_polygon": False},
        ],
        "real_exposure_used": False,
        "vulnerability_applied": False,
        "gross_loss_calculated": False,
        "insured_loss_calculated": False,
        "model_admitted": False,
    }


def wind_report():
    return {
        "event_key": "climk-winds:v2:ERA5:storm-index:0",
        "peril": "WINDSTORM",
        "physical_intensity_unit": "m s**-1",
        "source_sha256": mod.PINNED_SHA256,
        "source_sha_pinned": True,
        "event_identity_cross_model_matched": False,
        "site_count": 2,
        "site_samples": [
            {"site_id": "SYNTH_DE", "absolute_max_gust_m_s": 35.25396882156413,
             "relative_max_gust_dimensionless": 1.5823830716229241,
             "native_cell_x": 128, "native_cell_y": 88},
            {"site_id": "SYNTH_FR", "absolute_max_gust_m_s": 22.580119654033496,
             "relative_max_gust_dimensionless": 1.0244869616542147,
             "native_cell_x": 96, "native_cell_y": 96},
        ],
        "site_asset_ownership_admitted": False,
        "source_event_frequency_inferred": False,
        "damage_or_insured_loss_computed": False,
        "scientifically_admitted": False,
    }


def reconcile(fire=None, wind=None, sites=None):
    fire = fire_report() if fire is None else fire
    wind = wind_report() if wind is None else wind
    with patch.object(mod, "audit_synthetic_overlay", return_value=fire) as fire_adapter, \
         patch.object(mod, "sample_climk_era5", return_value=wind) as wind_adapter:
        result = mod.reconcile_original_physical_sources(
            effis_bytes=EFFIS,
            climk_era5_bytes=CLIMK,
            site_manifest_bytes=manifest() if sites is None else sites,
            effis_event_id=646790,
            climk_storm_index=0,
        )
    fire_adapter.assert_called_once()
    wind_adapter.assert_called_once()
    return result


class PhysicalEventEvidenceTests(unittest.TestCase):
    def test_two_physical_events_not_collapsed_or_lossified(self):
        report = reconcile()
        self.assertEqual(report["schema_version"], mod.SCHEMA)
        self.assertEqual(report["site_count"], 2)
        self.assertEqual(len(report["events"]), 2)
        self.assertEqual([e["peril"] for e in report["events"]], ["WILDFIRE", "WINDSTORM"])
        self.assertEqual(report["events"][0]["event_time"]["utc"], "2026-08-25T11:01:00Z")
        self.assertEqual(report["events"][1]["event_time"]["state"],
                         "UNEXPORTED_IN_V0_SOURCE_SAMPLER")
        self.assertIsNone(report["events"][1]["event_time"]["utc"])
        self.assertFalse(report["events_are_the_same_physical_occurrence"])
        for flag in ("cross_peril_dependency_inferred",
                     "event_frequency_or_simulation_year_inferred",
                     "real_insurer_assets_mapped", "vulnerability_used",
                     "ground_up_loss_computed", "insured_loss_computed",
                     "reinsurance_or_retro_computed", "model_admitted"):
            self.assertIs(report[flag], False)
        self.assertNotIn("longitude", json.dumps(report))
        self.assertNotIn("latitude", json.dumps(report))
        self.assertEqual(report["receipt_sha256"],
                         mod._hash(mod._canonical({k:v for k,v in report.items()
                                                   if k != "receipt_sha256"})))

    def test_physical_units_are_distinct(self):
        report = reconcile()
        self.assertEqual(report["events"][0]["observations"][0]["unit"], "boolean")
        self.assertIs(report["events"][0]["observations"][0]["value"], True)
        self.assertEqual(report["events"][1]["observations"][0]["unit"], "m s**-1")
        self.assertAlmostEqual(report["events"][1]["observations"][0]["value"],
                               35.25396882156413)
        self.assertEqual(report["events"][1]["observations"][0]["native_grid_cell"],
                         [88, 128])

    def test_report_is_deterministic(self):
        self.assertEqual(reconcile(), reconcile())

    def test_mutated_effis_source_digest_refused(self):
        fire = fire_report()
        fire["source_payload_sha256"] = "0"*64
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(fire=fire)

    def test_wind_source_digest_cannot_be_self_declaration(self):
        wind = wind_report()
        wind["source_sha256"] = "0"*64
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(wind=wind)

    def test_wind_source_must_be_pinned(self):
        wind = wind_report()
        wind["source_sha_pinned"] = False
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(wind=wind)

    def test_wind_peril_and_unit_mismatch_refused(self):
        for field, replacement in (
            ("peril", "FLOOD"), ("physical_intensity_unit", "km/h"),
            ("event_identity_cross_model_matched", True),
        ):
            with self.subTest(field=field):
                wind = wind_report()
                wind[field] = replacement
                with self.assertRaises(mod.PhysicalEventEvidenceError):
                    reconcile(wind=wind)

    def test_fire_measure_cannot_be_silent_wildfire_intensity(self):
        fire = fire_report()
        fire["measure"] = "WILDFIRE_FIRELINE_INTENSITY_KW_M"
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(fire=fire)

    def test_no_financial_or_admission_flags(self):
        for f in ("real_exposure_used", "vulnerability_applied", "gross_loss_calculated",
                  "insured_loss_calculated", "model_admitted"):
            with self.subTest(field=f):
                fire = fire_report()
                fire[f] = True
                with self.assertRaises(mod.PhysicalEventEvidenceError):
                    reconcile(fire=fire)
        for f in ("site_asset_ownership_admitted", "source_event_frequency_inferred",
                  "damage_or_insured_loss_computed", "scientifically_admitted"):
            with self.subTest(field=f):
                wind = wind_report()
                wind[f] = True
                with self.assertRaises(mod.PhysicalEventEvidenceError):
                    reconcile(wind=wind)

    def test_missing_or_extra_synthetic_site_fails(self):
        wind = wind_report()
        wind["site_samples"].pop()
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(wind=wind)
        fire = fire_report()
        fire["site_hits"][1]["site_id"] = "SYNTH_EXTRA"
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(fire=fire)

    def test_duplicate_or_unsorted_sites_refused(self):
        wind = wind_report()
        wind["site_samples"][1]["site_id"] = "SYNTH_DE"
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(wind=wind)
        wind = wind_report()
        wind["site_samples"].reverse()
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(wind=wind)

    def test_missing_not_imputed_as_zero(self):
        for gust in (None, float("nan"), float("inf"), -1.0, 201.0):
            wind = wind_report()
            wind["site_samples"][0]["absolute_max_gust_m_s"] = gust
            with self.subTest(gust=gust), self.assertRaises(mod.PhysicalEventEvidenceError):
                reconcile(wind=wind)

    def test_invalid_relative_ratio_and_grid_cell(self):
        for field, value in (
            ("relative_max_gust_dimensionless", float("nan")),
            ("relative_max_gust_dimensionless", -1),
            ("native_cell_x", 269),
            ("native_cell_y", -1),
        ):
            wind = wind_report()
            wind["site_samples"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(
                    mod.PhysicalEventEvidenceError):
                reconcile(wind=wind)

    def test_fire_membership_must_be_boolean(self):
        fire = fire_report()
        fire["site_hits"][0]["within_observed_burnt_polygon"] = 1
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(fire=fire)

    def test_missing_timezone_fails(self):
        fire = fire_report()
        fire["event_timestamp"] = "2026-08-25T13:01:00"
        with self.assertRaises(mod.PhysicalEventEvidenceError):
            reconcile(fire=fire)

    def test_wind_no_event_time_is_not_imputed_from_fire(self):
        report = reconcile()
        wind_time = report["events"][1]["event_time"]
        self.assertEqual(wind_time["utc"], None)
        self.assertNotEqual(wind_time, report["events"][0]["event_time"])

    def test_site_manifest_must_stay_synthetic(self):
        payload = json.loads(manifest())
        payload["synthetic_only"] = False
        with self.assertRaises(ValueError):
            reconcile(sites=json.dumps(payload).encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
