# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic only: source YOA vs financial year and loss ordering challenges."""
from __future__ import annotations

from copy import deepcopy
import unittest
from research_runners.synthetic_sidecar_yoa_allocation_v0 import allocate, SidecarAllocationBlocked, SHARES


def toy(year=2025):
    return {"schema_version": "0.1.0", "scenario_kind": "fully_synthetic_test_only",
            "unit": "USD", "year_of_account": year, "financial_year": 2025,
            "source_basis": "lloyds_6117_2025_audited_accounts_yoa_disclosure",
            "external_reinsurance_order": "host_external_reinsurance_before_sidecar",
            "events": [{"event_id": "SYNTH_A", "host_gross_loss": "100.00",
                        "host_external_reinsurance_recovery": "30.00"}]}


class SyntheticSidecarYOATests(unittest.TestCase):
    def test_correct_post_external_allocation_and_conservation(self):
        r = allocate(toy())
        self.assertEqual(r["sidecar_fraction"], "0.1527")
        self.assertEqual(r["sidecar_6117_loss_total"], "10.6890")
        self.assertEqual(r["other_post_external_allocation_unresolved_total"], "59.3110")
        self.assertEqual(r["host_external_reinsurance_recovery_total"], "30.00")
        self.assertEqual(r["gross_total"], "100.00")
        self.assertFalse(r["host_ultimate_retention_established"])
        self.assertFalse(r["other_sidecars_resolved"])
        self.assertFalse(r["actual_underwriting_losses_established"])
        self.assertFalse(r["cat_policy_treaty_or_model_admission_granted"])

    def test_yoa_fractions_are_not_flat_calendar_year_rate(self):
        for year, expected in ((2023, "8.1760"), (2024, "9.2960"), (2025, "10.6890")):
            with self.subTest(year=year):
                self.assertEqual(allocate(toy(year))["sidecar_6117_loss_total"], expected)
        self.assertEqual(SHARES[2026][1], "proposed_future_yoa")
        with self.assertRaisesRegex(SidecarAllocationBlocked, "proposed"):
            allocate(toy(2026))

    def test_double_apply_external_reinsurance_blocked(self):
        data = toy()
        data["external_reinsurance_order"] = "sidecar_first_then_host_external_again"
        with self.assertRaisesRegex(SidecarAllocationBlocked, "prior external"):
            allocate(data)

    def test_actual_1910_or_6117_records_must_not_be_smuggled_as_synthetic(self):
        data = toy()
        data["events"][0]["event_id"] = "1910_HURRICANE"
        with self.assertRaisesRegex(SidecarAllocationBlocked, "SYNTH_"):
            allocate(data)
        data = toy()
        data["scenario_kind"] = "actual_insurer_loss"
        with self.assertRaisesRegex(SidecarAllocationBlocked, "fictional"):
            allocate(data)

    def test_external_recovery_cannot_exceed_gul(self):
        data = toy()
        data["events"][0]["host_external_reinsurance_recovery"] = "100.01"
        with self.assertRaisesRegex(SidecarAllocationBlocked, "exceed"):
            allocate(data)

    def test_no_mixed_financial_and_underwriting_year(self):
        data = toy()
        data["financial_year"] = 2024
        with self.assertRaisesRegex(SidecarAllocationBlocked, "financial-report"):
            allocate(data)

    def test_zero_and_multiple_events_still_conserved(self):
        data = toy()
        data["events"].append({"event_id": "SYNTH_ZERO", "host_gross_loss": "0", "host_external_reinsurance_recovery": "0"})
        data["events"].append({"event_id": "SYNTH_B", "host_gross_loss": "40", "host_external_reinsurance_recovery": "40"})
        r = allocate(data)
        self.assertEqual(r["gross_total"], "140.00")
        self.assertEqual(r["sidecar_6117_loss_total"], "10.6890")

    def test_duplicate_or_nonfictional_ids_block(self):
        data = toy()
        data["events"].append(deepcopy(data["events"][0]))
        with self.assertRaises(SidecarAllocationBlocked):
            allocate(data)
        data = toy()
        data["events"][0]["event_id"] = "SYNTH_thing"
        with self.assertRaises(SidecarAllocationBlocked):
            allocate(data)

    def test_noncanonical_money_values_rejected(self):
        for amount in ("-1", "1e5", "NaN", "01.00", "0.12345", 100, True, None):
            with self.subTest(amount=amount):
                data = toy()
                data["events"][0]["host_gross_loss"] = amount
                with self.assertRaises(SidecarAllocationBlocked):
                    allocate(data)

    def test_zero_rows_and_oversized_batch_rejected(self):
        data = toy()
        data["events"] = []
        with self.assertRaises(SidecarAllocationBlocked):
            allocate(data)
        data = toy()
        data["events"] = data["events"] * 129
        with self.assertRaises(SidecarAllocationBlocked):
            allocate(data)

    def test_unknown_key_wrong_source_and_bad_year_rejected(self):
        data = toy()
        data["net_premium"] = "10"
        with self.assertRaises(SidecarAllocationBlocked):
            allocate(data)
        data = toy()
        data["source_basis"] = "unreviewed_web_claim"
        with self.assertRaises(SidecarAllocationBlocked):
            allocate(data)
        data = toy()
        data["year_of_account"] = "2025"
        with self.assertRaises(SidecarAllocationBlocked):
            allocate(data)


if __name__ == "__main__":
    unittest.main()
