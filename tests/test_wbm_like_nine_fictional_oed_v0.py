# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure stdlib nine-fictional commercial OED smoke and anti-WBM/insurer claims."""
from __future__ import annotations

import copy
import csv
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from research_runners import wbm_like_nine_fictional_oed_v0 as m
from research_runners.export_synthetic_oed_v0 import (
    ACCOUNT_FIELDS, LOCATION_FIELDS, SyntheticOedError,
)


class WBMNineFictionalOedTests(unittest.TestCase):
    def setUp(self):
        self.loc, self.acc, self.manifest = m.prepare()

    def test_exact_nine_not_actual_wbm_sites(self):
        self.assertEqual(len(self.loc), 9)
        self.assertEqual(len(self.acc), 1)
        self.assertTrue(all(x["LocNumber"].startswith("FICTITIOUS-SITE-")
                            for x in self.loc))
        self.assertTrue(self.manifest["all_site_coordinates_invented"])
        self.assertFalse(self.manifest["real_property_ownership_or_location_verified"])

    def test_exact_9_by_3x3_nonactual_berlin_grid(self):
        self.assertEqual(
            [(r["Latitude"], r["Longitude"]) for r in self.loc],
            [(lat, lon) for lat in m.LATITUDES for lon in m.LONGITUDES])
        self.assertEqual(len(set((r["Latitude"], r["Longitude"]) for r in self.loc)), 9)

    def test_total_108m_is_arbitrary_and_source_not_used(self):
        tiv = sum(Decimal(x["BuildingTIV"]) for x in self.loc)
        self.assertEqual(tiv, Decimal("108000000"))
        self.assertEqual(self.manifest["sum_building_eur_entirely_invented"], 108000000)
        self.assertTrue(self.manifest["all_tiv_values_invented"])
        self.assertFalse(self.manifest["wBM_group_asset_portfolio_valuation_used_for_tiv"])
        self.assertFalse(self.manifest["source_estimated_property_replacement_tiv_obtained"])

    def test_oed_5_columns_account_integrity(self):
        self.assertEqual(tuple(self.loc[0]), LOCATION_FIELDS)
        self.assertEqual(tuple(self.acc[0]), ACCOUNT_FIELDS)
        self.assertEqual(self.acc[0]["PolNumber"], m.POLICY)
        self.assertTrue(all(r["AccNumber"] == m.ACCOUNT and
                            r["PortNumber"] == m.PORT for r in self.loc))
        self.assertTrue(all(r["OEDVersion"] == "5.0.0" for r in self.loc))

    def test_hypothetical_perils_only(self):
        self.assertEqual({r["LocPerilsCovered"] for r in self.loc}, {"WW2;OO1"})
        self.assertEqual(self.acc[0]["PolPerilsCovered"], "WW2;OO1")
        self.assertTrue(self.manifest["coverage_perils_WW2_OO1_invented"])
        self.assertFalse(self.manifest["real_insurance_policy_coverage_or_2027_inception_confirmed"])

    def test_no_real_insurer_contract_or_coinsurance(self):
        self.assertIsNone(self.manifest["insurer_legal_entity_or_carrier_share"])
        self.assertFalse(self.manifest["actual_insurer_CAT_exposure_admitted"])
        self.assertFalse(self.manifest["gross_or_net_model_loss_simulated"])
        self.assertNotIn("R+V", json.dumps(self.loc + self.acc))
        self.assertNotIn("WBM", json.dumps(self.loc + self.acc))

    def test_raise_if_any_company_coinsurance_replaced(self):
        man = copy.deepcopy(self.manifest)
        man["insurer_legal_entity_or_carrier_share"] = "R+V 10%"
        with self.assertRaisesRegex(SyntheticOedError, "company identity"):
            m.validate(self.loc, self.acc, man)

    def test_real_insurance_admission_claim_must_fail(self):
        for key in (
            "real_property_ownership_or_location_verified",
            "source_estimated_property_replacement_tiv_obtained",
            "wBM_group_asset_portfolio_valuation_used_for_tiv",
            "actual_insurer_CAT_exposure_admitted",
            "ods_tools_validation_performed_by_this_generator",
        ):
            man = copy.deepcopy(self.manifest)
            man[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(SyntheticOedError, "prohibited"):
                m.validate(self.loc, self.acc, man)

    def test_real_location_address_or_tiv_drift_rejected(self):
        for field, value in (
            ("Latitude", "52.532100"),
            ("BuildingTIV", "5900000000"),
            ("LocNumber", "WBM-IHZ"),
            ("LocPerilsCovered", "AA1"),
        ):
            loc = copy.deepcopy(self.loc)
            loc[2][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(SyntheticOedError, "modified"):
                m.validate(loc, self.acc, self.manifest)

    def test_actual_carrier_policy_in_fictional_acc_rejected(self):
        acc = copy.deepcopy(self.acc)
        acc[0]["PolNumber"] = "REAL-CON-0003"
        with self.assertRaisesRegex(SyntheticOedError, "real or edited account"):
            m.validate(self.loc, acc, self.manifest)

    def test_ten_sites_cannot_be_mislabelled_as_nine_notice_count(self):
        with self.assertRaisesRegex(SyntheticOedError, "nine fictional"):
            m.validate(self.loc + [copy.deepcopy(self.loc[-1])],
                       self.acc, self.manifest)

    def test_scenario_count_or_real_world_provenance_drift_rejected(self):
        for key, newval in (("location_count", 34),
                             ("only_real_world_input_used", "2025_wbm_real_property_database")):
            man = copy.deepcopy(self.manifest)
            man[key] = newval
            with self.subTest(key=key), self.assertRaisesRegex(SyntheticOedError, "bound or count"):
                m.validate(self.loc, self.acc, man)

    def test_save_csv_and_manifest_with_verified_row_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/"unaffiliated"
            location, account, manifest = m.export(out)
            with location.open(encoding="utf-8", newline="") as f:
                source_locations = list(csv.DictReader(f))
            with account.open(encoding="utf-8", newline="") as f:
                source_accounts = list(csv.DictReader(f))
            self.assertEqual(source_locations, self.loc)
            self.assertEqual(source_accounts, self.acc)
            self.assertEqual(json.loads(manifest.read_text()), self.manifest)

    def test_existing_target_directory_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(SyntheticOedError, "must be new"):
                m.export(Path(tmp))

    def test_double_export_same_directory_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/"export"
            m.export(target)
            with self.assertRaisesRegex(SyntheticOedError, "must be new"):
                m.export(target)

    def test_deterministic_byte_for_byte_exposure_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = m.export(Path(tmp)/"first")
            b = m.export(Path(tmp)/"second")
            self.assertEqual([f.read_bytes() for f in a],
                             [f.read_bytes() for f in b])


if __name__ == "__main__":
    unittest.main()
