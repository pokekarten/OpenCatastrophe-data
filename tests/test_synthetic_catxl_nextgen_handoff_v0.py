# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original synthetic-only handoff integrity/adversarial tests."""
import copy
import unittest

from research_runners.synthetic_catxl_nextgen_handoff_v0 import (
    HandoffError, _sha256, build_handoff, validate_handoff,
)


def sample():
    rows = [
        {"label": "FICTIONAL-E1", "date": "2026-11-02", "peril": "windstorm",
         "physical_event_id": None, "contractual_occurrence_id": None,
         "gross_insured_loss_eur": 100, "ceded_loss_eur": 20,
         "net_insured_loss_eur": 80, "reinstatement_premium_cents": 5,
         "layer_rows": [{"layer_id": "FICTIONAL-L1", "ceded_loss_eur": 10,
                         "reinstatement_premium_cents": 3},
                        {"layer_id": "FICTIONAL-L2", "ceded_loss_eur": 10,
                         "reinstatement_premium_cents": 2}]},
        {"label": "FICTIONAL-E2", "date": "2026-11-03", "peril": "flood",
         "physical_event_id": None, "contractual_occurrence_id": None,
         "gross_insured_loss_eur": 300, "ceded_loss_eur": 60,
         "net_insured_loss_eur": 240, "reinstatement_premium_cents": 10,
         "layer_rows": [{"layer_id": "FICTIONAL-L1", "ceded_loss_eur": 50,
                         "reinstatement_premium_cents": 7},
                        {"layer_id": "FICTIONAL-L2", "ceded_loss_eur": 10,
                         "reinstatement_premium_cents": 3}]},
    ]
    payload = {
        "profile": "OC-SYNTHETIC-CATXL-LEDGER-0.1",
        "admission": "RESEARCH_SYNTHETIC_ONLY_NOT_ADMITTED",
        "nextgen_execution_authorized": False,
        "ord_compatibility_attested": False,
        "currency": "EUR", "loss_unit": "whole_EUR", "premium_unit": "EUR_cent",
        "event_identity_semantics": "fictional_label_only_not_physical_or_contractual_occurrence",
        "input_fixture_sha256": "a" * 64,
        "gross_insured_loss_eur": 400, "ceded_loss_eur": 80,
        "net_insured_loss_eur": 320, "reinstatement_premium_cents": 15,
        "base_premium_cents": 500,
        "event_rows": rows,
        "layer_totals": [
            {"layer_id": "FICTIONAL-L1", "ceded_loss_eur": 60,
             "reinstatement_premium_cents": 10},
            {"layer_id": "FICTIONAL-L2", "ceded_loss_eur": 20,
             "reinstatement_premium_cents": 5},
        ],
    }
    return {"payload": payload, "payload_sha256": _sha256(payload)}


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.receipt = sample()

    def rehash(self):
        self.receipt["payload_sha256"] = _sha256(self.receipt["payload"])

    def fails(self, rehash=True):
        if rehash:
            self.rehash()
        with self.assertRaises(HandoffError):
            validate_handoff(self.receipt)

    def test_valid(self):
        self.assertIsNone(validate_handoff(self.receipt))

    def test_deterministic(self):
        self.assertEqual(self.receipt, sample())

    def test_unrehashed_change_rejected(self):
        self.receipt["payload"]["ceded_loss_eur"] = 1
        self.fails(rehash=False)

    def test_even_rehashed_bad_annual_conservation_rejected(self):
        self.receipt["payload"]["gross_insured_loss_eur"] = 399
        self.fails()

    def test_event_conservation_rejected(self):
        self.receipt["payload"]["event_rows"][0]["net_insured_loss_eur"] = 81
        self.fails()

    def test_layer_total_mismatch_rejected(self):
        self.receipt["payload"]["layer_totals"][0]["ceded_loss_eur"] = 61
        self.fails()

    def test_event_layer_sum_rejected(self):
        self.receipt["payload"]["event_rows"][0]["layer_rows"][0]["ceded_loss_eur"] = 11
        self.fails()

    def test_reinstatement_premium_layer_mismatch_rejected(self):
        self.receipt["payload"]["event_rows"][1]["layer_rows"][0]["reinstatement_premium_cents"] = 9
        self.fails()

    def test_duplicate_event_rejected(self):
        self.receipt["payload"]["event_rows"][1]["label"] = "FICTIONAL-E1"
        self.fails()

    def test_order_rejected(self):
        self.receipt["payload"]["event_rows"].reverse()
        self.fails()

    def test_same_day_rejected(self):
        self.receipt["payload"]["event_rows"][1]["date"] = "2026-11-02"
        self.fails()

    def test_bogus_date_rejected(self):
        self.receipt["payload"]["event_rows"][1]["date"] = "2026-13-44"
        self.fails()

    def test_physical_event_invented_rejected(self):
        self.receipt["payload"]["event_rows"][0]["physical_event_id"] = "MET-FAKE"
        self.fails()

    def test_occurrence_invented_rejected(self):
        self.receipt["payload"]["event_rows"][0]["contractual_occurrence_id"] = "OCC-FAKE"
        self.fails()

    def test_model_launch_promotion_rejected(self):
        self.receipt["payload"]["nextgen_execution_authorized"] = True
        self.fails()

    def test_ord_attestation_rejected(self):
        self.receipt["payload"]["ord_compatibility_attested"] = True
        self.fails()

    def test_premium_unit_promotion_rejected(self):
        self.receipt["payload"]["premium_unit"] = "EUR"
        self.fails()

    def test_boolean_money_rejected(self):
        self.receipt["payload"]["event_rows"][0]["gross_insured_loss_eur"] = True
        self.fails()

    def test_extra_fields_rejected(self):
        self.receipt["payload"]["event_rows"][0]["real_insurer_id"] = "123"
        self.fails()

    def test_missing_layer_row_rejected(self):
        self.receipt["payload"]["event_rows"][0]["layer_rows"].pop()
        self.fails()

    def test_layer_order_rejected(self):
        self.receipt["payload"]["event_rows"][0]["layer_rows"].reverse()
        self.fails()

    def test_duplicate_layer_rejected(self):
        self.receipt["payload"]["layer_totals"][1]["layer_id"] = "FICTIONAL-L1"
        self.fails()

    def test_duplicate_input_hash_or_bad_digest_not_trusted(self):
        self.receipt["payload"]["input_fixture_sha256"] = "weak"
        self.fails()

    def test_actual_tower_integration(self):
        from research_runners.synthetic_catxl_tower_v0 import fictional_example, calculate_toy_tower
        pos, events, treaty = fictional_example()
        result = calculate_toy_tower(pos, events, treaty)
        receipt = build_handoff(pos, events, treaty, result)
        validate_handoff(receipt)
        self.assertEqual(receipt["payload"]["gross_insured_loss_eur"], 2000000)
        self.assertEqual(receipt["payload"]["ceded_loss_eur"], 1100000)
        self.assertEqual(receipt["payload"]["net_insured_loss_eur"], 900000)
        self.assertFalse(receipt["payload"]["nextgen_execution_authorized"])
        self.assertTrue(all(e["physical_event_id"] is None for e in receipt["payload"]["event_rows"]))
        altered = copy.deepcopy(result)
        altered["ceded_eur"] += 1
        with self.assertRaises(HandoffError):
            build_handoff(pos, events, treaty, altered)


if __name__ == "__main__":
    unittest.main()
