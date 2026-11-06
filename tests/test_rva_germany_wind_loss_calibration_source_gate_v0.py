# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No GDV TDM / EIOPA sample promotion / HANZE economic-loss calibration."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import rva_germany_wind_loss_calibration_source_gate_v0 as gate


class SourceRightsAndCalibrationNoGoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.register = json.loads(gate.DEFAULT.read_text(encoding="utf-8"))

    def altered(self):
        return deepcopy(self.register)

    def record(self, d, sid):
        return next(x for x in d["records"] if x["id"] == sid)

    def test_six_original_public_source_references_but_zero_fit_admission(self):
        status = gate.validate_registry(self.register)
        self.assertEqual(status["source_count"], 6)
        self.assertEqual(status["observed_partial_insurer_sample_sources"], 1)
        self.assertEqual(status["status"],
                         "ALL_SIX_CALIBRATION_SOURCES_REFERENCE_ONLY_NO_MODEL_FIT")
        for f in ("recorded_GDV_TDM_permission",
                  "German_site_specific_GUL_vulnerability_fit_approved",
                  "annual_OEP_AEP_return_frequency_estimated",
                  "external_workbook_original_bytes_ingested",
                  "licence_or_data_reuse_approval_inferred"):
            self.assertIs(status[f], False)

    def test_gdv_text_data_mining_must_not_be_claimed_approved(self):
        doc = self.altered()
        gdv = self.record(doc, "gdv_naturgefahrenreport_2026")
        gdv["licence_review"] = "OPEN_TDM_AND_COMMERCIAL_ML_ALLOWED"
        with self.assertRaisesRegex(gate.SourceRightsBlocked, "rights|metadata|boundaries"):
            gate.validate_registry(doc)
        doc = self.altered()
        self.record(doc, "gdv_naturgefahrenreport_2026")["access"] = "AUTO_SCRAPE_FOR_ML"
        with self.assertRaises(gate.SourceRightsBlocked):
            gate.validate_registry(doc)

    def test_eiopa_insurer_sample_is_not_rv_market_or_full_geocoded_loss(self):
        doc = self.altered()
        self.record(doc, "eiopa_catastrophe_data_hub_2023")["observed_measure"] = (
            "ACTUAL_RV_OR_NRW_10000_INDEPENDENT_GUL_CLAIMS")
        with self.assertRaises(gate.SourceRightsBlocked):
            gate.validate_registry(doc)
        doc = self.altered()
        self.record(doc, "eiopa_catastrophe_data_hub_2023")["approval_evidence"] = (
            "ORIGINAL_INSURER_SITE_CLAIMS_ADMITTED")
        with self.assertRaises(gate.SourceRightsBlocked):
            gate.validate_registry(doc)

    def test_hanze_economic_and_c3s_modelled_must_never_be_claimed_insured(self):
        for sid in ("hanze_european_windstorm_impacts_v1_2025",
                    "c3s_european_windstorm_tier3_reanalysis",
                    "eea_1980_2023_economic_insured_catdat"):
            with self.subTest(source=sid):
                doc = self.altered()
                self.record(doc, sid)["observed_measure"] = (
                    "INDEPENDENT_ACTUAL_INSURED_RV_SITE_STORM_CLAIMS")
                with self.assertRaises(gate.SourceRightsBlocked):
                    gate.validate_registry(doc)

    def test_hu22_physical_source_cannot_turn_into_claim_or_loss_calibration(self):
        doc = self.altered()
        hu = self.record(doc, "nrw_hu22_2022_building_footprints")
        hu["source_file_sha256"] = "0" * 64
        with self.assertRaisesRegex(gate.SourceRightsBlocked, "HU22|source|rights"):
            gate.validate_registry(doc)
        doc = self.altered()
        self.record(doc, "nrw_hu22_2022_building_footprints")["access"] = "CALIBRATED_RV_GUL"
        with self.assertRaises(gate.SourceRightsBlocked):
            gate.validate_registry(doc)

    def test_nonapproved_data_import_and_redirected_external_publisher_fail(self):
        doc = self.altered()
        self.record(doc, "hanze_european_windstorm_impacts_v1_2025")[
            "source_file_sha256"] = "a" * 64
        with self.assertRaises(gate.SourceRightsBlocked):
            gate.validate_registry(doc)
        for fake_url in ("http://www.gdv.de/gdv", "https://www.gdv.de@evil.example/gdv",
                         "https://evil.example/gdv", "ftp://www.gdv.de/data"):
            with self.subTest(fake_url=fake_url):
                doc = self.altered()
                self.record(doc, "gdv_naturgefahrenreport_2026")[
                    "landing_url"] = fake_url
                with self.assertRaises(gate.SourceRightsBlocked):
                    gate.validate_registry(doc)

    def test_false_model_readiness_and_missing_legal_denominator_gates_fail(self):
        flags = (
            "all_sources_reference_only_or_source_replay",
            "independent_German_wind_damage_calibration_completed",
            "actual_RV_policy_geography_or_claims_observed",
            "loss_frequency_per_year_model_admitted",
            "gross_net_annual_OEP_AEP_admitted",
        )
        for name in flags:
            doc = self.altered()
            doc[name] = not doc[name]
            with self.subTest(flag=name):
                with self.assertRaises(gate.SourceRightsBlocked):
                    gate.validate_registry(doc)
        for needed in gate.REQUIRED_GATES:
            doc = self.altered()
            doc["required_before_any_loss_fit"].remove(needed)
            with self.subTest(gate=needed):
                with self.assertRaises(gate.SourceRightsBlocked):
                    gate.validate_registry(doc)

    def test_source_injection_wrong_count_and_unknown_additional_fields_fail(self):
        changes = (
            lambda d: d["records"].pop(),
            lambda d: d["records"].append(deepcopy(d["records"][0])),
            lambda d: d["records"][0].__setitem__("actual_RV_loss_cents", 100000),
            lambda d: d.__setitem__("model_admitted", True),
            lambda d: d["records"][1].__setitem__("denominator", ""),
        )
        for i, change in enumerate(changes):
            doc = self.altered()
            change(doc)
            with self.subTest(case=i):
                with self.assertRaises(gate.SourceRightsBlocked):
                    gate.validate_registry(doc)


if __name__ == "__main__":
    unittest.main()
