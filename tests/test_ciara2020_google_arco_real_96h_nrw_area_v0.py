# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline adversarial 96h×160-node original Google ERA5 10fg grid reader gates."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_google_arco_real_96h_nrw_area_v0 as m


def hourly_grid(h: int):
    g = [[15.0 for _ in m.LONGITUDE] for _ in m.LATITUDE]
    g[0][0] = 25.0 + h * 0.25
    g[1][1] = 40.0 if h == 7 else 10.0
    if h == m.ONEHOUR_INDEX:
        g[m.ONEHOUR_GRID[0]][m.ONEHOUR_GRID[1]] = 20.320262908935547
    return g


def feed(acc: m.WindAreaAccumulator, h: int, **kwargs):
    timestamp = (m.START + m.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ")
    acc.ingest(
        timestamp=kwargs.get("timestamp", timestamp),
        latitudes=kwargs.get("latitudes", list(m.LATITUDE)),
        longitudes=kwargs.get("longitudes", list(m.LONGITUDE)),
        gust_grid=kwargs.get("grid", hourly_grid(h)),
    )


class RealGoogleFullCiaraSourceTests(unittest.TestCase):
    def test_real_single_hour_original_pinned_float32_parity_on_96h_synthetic_sequence(self):
        acc = m.WindAreaAccumulator()
        for h in range(m.HOURS):
            feed(acc, h)
        receipt = acc.finish()
        self.assertEqual(receipt["actual_hourly_ERA5_original_grid_timestamps_verified"], 96)
        self.assertEqual(receipt["original_source_0p25_degree_nodes"], 160)
        self.assertEqual(receipt["single_2020_02_09_12_51N_7E_source_crosscheck_sha256"],
                         m.EXPECTED_ONEHOUR_20200209_12_LAT51_LON7_GUST_SHA)
        self.assertEqual(receipt["event_max_over_96h_gust_mps_at_160_nodes_max"], 48.75)
        self.assertEqual(receipt["node_count_event_peak_gust_above_threshold_mps"],
                         {"25": 2, "30": 2, "35": 2, "40": 2})
        self.assertEqual(len(receipt[
            "normalized_decoded_96h_10x16_float32_le_sha256_not_original_chunk_sha256"
        ]), 64)
        self.assertFalse(receipt["original_compressed_GCS_chunk_SHAs_independently_verified"])

    def test_incomplete_duplicate_extra_shifted_or_wrong_start_hour_is_rejected(self):
        with self.assertRaisesRegex(m.RealGridBlocked, "missing"):
            m.WindAreaAccumulator().finish()
        with self.assertRaisesRegex(m.RealGridBlocked, "96"):
            m.WindAreaAccumulator(expected_hours=97)
        a = m.WindAreaAccumulator(expected_hours=1)
        with self.assertRaisesRegex(m.RealGridBlocked, "contiguous"):
            feed(a, 1)
        feed(a, 0)
        with self.assertRaisesRegex(m.RealGridBlocked, "extra"):
            feed(a, 0)
        with self.assertRaisesRegex(m.RealGridBlocked, "96"):
            a.finish(require_first_original_point=True)

    def test_corrupt_2020_hour_parity_and_injected_realwind_value_rejected(self):
        acc = m.WindAreaAccumulator()
        for h in range(m.HOURS):
            g = hourly_grid(h)
            if h == m.ONEHOUR_INDEX:
                g[m.ONEHOUR_GRID[0]][m.ONEHOUR_GRID[1]] = 20.0
            feed(acc, h, grid=g)
        with self.assertRaisesRegex(m.RealGridBlocked, "parity"):
            acc.finish()
        self.assertIsNotNone(acc.finish(require_first_original_point=False))

    def test_incorrect_spatial_axis_order_resolution_or_bounds_is_rejected(self):
        edits = (
            {"latitudes": list(reversed(m.LATITUDE))},
            {"latitudes": [v + 0.125 for v in m.LATITUDE]},
            {"longitudes": list(reversed(m.LONGITUDE))},
            {"longitudes": [v + 0.25 for v in m.LONGITUDE]},
            {"grid": [[5.0 for _ in range(15)] for _ in range(10)]},
            {"grid": [[5.0 for _ in range(16)] for _ in range(9)]},
        )
        for edit in edits:
            with self.subTest(edit=next(iter(edit))):
                with self.assertRaisesRegex(m.RealGridBlocked, "grid"):
                    feed(m.WindAreaAccumulator(), 0, **edit)

    def test_nan_inf_negative_outlier_or_boolean_10fg_gust_rejected(self):
        for val in (math.nan, math.inf, -0.01, 150.1, True, "20.1"):
            with self.subTest(val=val):
                g = hourly_grid(0)
                g[2][4] = val
                with self.assertRaisesRegex(m.RealGridBlocked, "gust"):
                    feed(m.WindAreaAccumulator(), 0, grid=g)

    def test_dry_run_must_not_attempt_real_public_era5_network(self):
        with patch.object(sys, "argv", ["prog", "--dry-run"]), \
             patch.object(m, "original_96h_grid",
                          side_effect=AssertionError("DO NOT ACCESS ORIGINAL SOURCE")):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(m.main(), 0)
            receipt = json.loads(output.getvalue())
        self.assertEqual(receipt["hours_requested"], 96)
        self.assertEqual(receipt["grid_nodes_requested"], 160)
        self.assertFalse(receipt["original_Ciara_96h_values_retrieved"])
        self.assertFalse(receipt["German_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted"])


if __name__ == "__main__":
    unittest.main()
