# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Scale regression: 220,619 SYNTHETIC OQ3.13 loss rows, never real Kosovo data.

The real historical action disclosed only a 220,619-row checksum commitment.
This test deliberately uses fabricated constant binary32 numbers, so it proves
capacity and exact transport invariants but NEVER reconstructs the real run.
"""
from __future__ import annotations

import hashlib
import json
import unittest

from scripts import project_oq313_event_loss_handoff_v0 as producer
from scripts import project_oq313_risk_by_event_receipt as numerical
from scripts import validate_oq313_event_loss_handoff_v0 as consumer

SYNTHETIC_ROW_COUNT = 220_619


class RealisticCardinalitySyntheticHandoffTest(unittest.TestCase):
    def test_replay_exact_historical_row_count_with_entirely_synthetic_losses(self):
        source_rows = [
            {
                "event_id": event_id,
                "rup_id": event_id,
                "rlz_id": event_id % 3,
                "loss_f32_be_hex": "3f800000",  # purely synthetic 1.0 EUR
                "variance_f32_be_hex": "00000000",
            }
            for event_id in range(1, SYNTHETIC_ROW_COUNT + 1)
        ]
        receipt, source_identity = numerical.project_oq313_risk_by_event_receipt(
            source_rows,
            portfolio_agg_id=0,
            structural_loss_id=0,
            concurrent_tasks=1,
        )
        del source_rows  # bound peak memory in multi-version CI
        self.assertLessEqual(len(receipt), producer.MAX_INPUT_BYTES)
        ledger, manifest = producer.project_event_loss_handoff(
            receipt, expected_receipt_sha256=source_identity["sha256"],
        )
        self.assertLessEqual(len(ledger), producer.MAX_OUTPUT_BYTES)
        observed_manifest = json.loads(manifest)
        self.assertEqual(observed_manifest["output"]["row_count"], SYNTHETIC_ROW_COUNT)
        self.assertEqual(observed_manifest["output"]["sha256"], hashlib.sha256(ledger).hexdigest())
        self.assertEqual(ledger.count(b"\n"), SYNTHETIC_ROW_COUNT)
        self.assertTrue(ledger.startswith(b'{"event_id":1,'))
        self.assertIn(b'"loss_f32_be_hex":"3f800000"', ledger)
        self.assertFalse(observed_manifest["annualization_authorized"])
        self.assertFalse(observed_manifest["insured_loss_calculated"])

        # Consumer rechecks every row, pinning both its source and manifest.
        result = consumer.validate_event_loss_handoff(
            ledger, manifest,
            expected_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
            expected_source_receipt_sha256=source_identity["sha256"],
        )
        self.assertEqual(result["row_count"], SYNTHETIC_ROW_COUNT)
        self.assertFalse(result["canonical_source_rows_reconciled"])
        self.assertFalse(result["annualized_loss_established"])
        # When full source exists, independently reproduce every transport byte.
        reconciled = consumer.validate_event_loss_handoff(
            ledger, manifest,
            expected_manifest_sha256=hashlib.sha256(manifest).hexdigest(),
            expected_source_receipt_sha256=source_identity["sha256"],
            source_receipt=receipt,
        )
        self.assertTrue(reconciled["canonical_source_rows_reconciled"])
        self.assertFalse(reconciled["origin_authenticated_by_this_validation"])


if __name__ == "__main__":
    unittest.main()
