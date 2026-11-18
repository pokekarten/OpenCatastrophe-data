# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

import csv
import io
import unittest

from research_runners.climk_kyrill_native_gul_synthetic_v0 import (
    ASSET_COUNT,
    ASSET_TIV_EUR,
    KyrillNativeGULError,
    authored_damage_ratio,
    synthetic_location_csv,
    validate_gul_output,
)


class KyrillNativeGULSyntheticTests(unittest.TestCase):
    def test_curve_uses_rounded_integer_mm_per_second_vlt_input(self):
        ratio = authored_damage_ratio(35.21054044063598)
        self.assertAlmostEqual(ratio, 0.2010230303030303, places=15)

    def test_location_roster_is_fictional_and_value_conserving(self):
        raw = synthetic_location_csv()
        rows = list(csv.DictReader(io.StringIO(raw.decode())))
        self.assertEqual(len(rows), ASSET_COUNT)
        self.assertEqual(len({row["LocNumber"] for row in rows}), ASSET_COUNT)
        self.assertEqual(sum(int(row["BuildingTIV"]) for row in rows), ASSET_COUNT * ASSET_TIV_EUR)
        self.assertEqual({row["LocPerilsCovered"] for row in rows}, {"WEC"})
        self.assertEqual({row["LocCurrency"] for row in rows}, {"EUR"})

    def test_native_summary_and_sample_rows_validate(self):
        raw = (
            b"Period,PeriodWeight,EventId,Year,Month,Day,Hour,Minute,SummaryId,SampleId,Loss,ImpactedExposure\n"
            b"1,1.0,1,1,1,1,0,0,1,-1,48245536.00,240000000.00\n"
            b"1,1.0,1,1,1,1,0,0,1,1,48245536.00,240000000.00\n"
        )
        rows = validate_gul_output(raw, expected_loss=48_245_527.27272727,
                                   expected_tiv=240_000_000)
        self.assertEqual(len(rows), 2)

    def test_wrong_event_or_sample_rows_fail_closed(self):
        raw = (
            b"Period,PeriodWeight,EventId,Year,Month,Day,Hour,Minute,SummaryId,SampleId,Loss,ImpactedExposure\n"
            b"1,1.0,2,1,1,1,0,0,1,-1,48245536.00,240000000.00\n"
            b"1,1.0,2,1,1,1,0,0,1,1,48245536.00,240000000.00\n"
        )
        with self.assertRaises(KyrillNativeGULError):
            validate_gul_output(raw, expected_loss=48_245_527.27, expected_tiv=240_000_000)

    def test_tiv_conservation_and_loss_tolerance_are_required(self):
        raw = (
            b"Period,PeriodWeight,EventId,Year,Month,Day,Hour,Minute,SummaryId,SampleId,Loss,ImpactedExposure\n"
            b"1,1.0,1,1,1,1,0,0,1,-1,100.00,240000000.00\n"
            b"1,1.0,1,1,1,1,0,0,1,1,100.00,240000000.00\n"
        )
        with self.assertRaises(KyrillNativeGULError):
            validate_gul_output(raw, expected_loss=48_245_527.27, expected_tiv=240_000_000)


if __name__ == "__main__":
    unittest.main()
