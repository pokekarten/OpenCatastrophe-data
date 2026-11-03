# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic forecast issue/validity claims; never a source licence or model admission."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from research_runners.wfp_chirps_gefs_issue_vintage_gate_v0 import (
    ALLOWED_ROLE, Blocked, MAX_BYTES, PRODUCT_VERSION, SOURCE_ID,
    inspect_claim, main,
)


def sample(**updates):
    payload = {
        "source_id": SOURCE_ID,
        "product_version": PRODUCT_VERSION,
        "issue_date": "2026-09-05",
        "valid_date": "2026-09-20",
        "lead_days": 15,
        "asset_sha256": "a" * 64,
        "research_role": ALLOWED_ROLE,
    }
    payload.update(updates)
    return json.dumps(payload, sort_keys=True).encode()


class WfpChirpsGefsVintageGateTests(unittest.TestCase):
    def test_strict_valid_claim_never_proves_backtest_or_event(self):
        result = inspect_claim(sample())
        self.assertEqual(result["lead_days"], 15)
        self.assertTrue(result["issue_valid_lead_consistent"])
        self.assertFalse(result["historical_issue_archive_verified"])
        self.assertFalse(result["original_issue_bytes_verified"])
        self.assertFalse(result["as_of_backtesting_authorized"])
        self.assertFalse(result["independent_rainfall_observation"])
        self.assertFalse(result["insured_loss_model_input_admitted"])

    def test_boundary_lead_zero_and_15(self):
        for n in (0, 15):
            with self.subTest(lead=n):
                obj = inspect_claim(sample(lead_days=n, valid_date=f"2026-09-{5+n:02d}"))
                self.assertEqual(obj["lead_days"], n)

    def test_block_mixed_forecast_issue_and_valid_times(self):
        for overrides in (
            {"valid_date": "2026-09-19"},
            {"issue_date": "2026-09-06"},
            {"issue_date": "2026-09-30"},
            {"issue_date": "2000-01-01", "valid_date": "2000-01-16"},
            {"valid_date": "2026-02-30"},
            {"valid_date": "2026-09-21"},
            {"issue_date": "2026-09-05T00:00:00Z"},
            {"lead_days": 16},
            {"lead_days": -1},
            {"lead_days": True},
            {"lead_days": 15.0},
        ):
            with self.subTest(p=overrides), self.assertRaises(Blocked):
                inspect_claim(sample(**overrides))

    def test_block_unverified_products_and_role_promotion(self):
        for changes in (
            {"source_id": "ucsb.chc.chirps.v3.0"},
            {"source_id": "wfp.hdc.chirps3-gefs-dekad-forecast.v3"},
            {"product_version": "v2.0"},
            {"research_role": "historical_forecast_skill"},
            {"research_role": "observed_event"},
            {"research_role": "insured_loss"},
            {"research_role": "actual_forecast_replay"},
            {"asset_sha256": "A" * 64},
            {"asset_sha256": "missing"},
            {"extra_field": "unreviewed"},
        ):
            with self.subTest(p=changes), self.assertRaises(Blocked):
                inspect_claim(sample(**changes))

    def test_reject_duplicate_keys_nonfinite_oversize_and_nonutf8(self):
        inputs = (
            b"", b" " * (MAX_BYTES + 1), b'{"source_id":"a","source_id":"b"}',
            b'{"lead_days":NaN}', b"\xff\xfe", b"[]", b"null"
        )
        for raw in inputs:
            with self.subTest(raw=raw[:40]), self.assertRaises(Blocked):
                inspect_claim(raw)

    def test_offline_cli_success_and_block(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "synthetic.json"
            p.write_bytes(sample())
            self.assertEqual(main(["--claim-json", str(p)]), 0)
            p.write_bytes(sample(research_role="as_of_backtest"))
            self.assertEqual(main(["--claim-json", str(p)]), 2)


if __name__ == "__main__":
    unittest.main()
