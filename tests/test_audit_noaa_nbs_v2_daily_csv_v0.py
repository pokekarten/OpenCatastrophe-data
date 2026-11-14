# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for NOAA NBSv2 Science Quality ocean/model mask semantics."""
from __future__ import annotations

import json
import unittest

from scripts.audit_noaa_nbs_v2_daily_csv_v0 import (
    EXPECTED_DAY, MAX_BYTES, NOAAWindBlocked, inspect_nbs_daily_csv,
)

HEADER = "time,zlev,latitude,longitude,windspeed,mask"
UNITS = "UTC,meters,degrees_north,degrees_east,m s-1,"
PREFIX = HEADER + "\n" + UNITS + "\n"


def row(*, time="2024-01-01T00:00:00Z", zlev="10", lat="25.0",
        lon="285.0", wind="12.5", mask="1"):
    return ",".join([time, zlev, lat, lon, wind, mask])


def body(*rows, header=HEADER, units=UNITS):
    return ("\n".join([header, units, *rows]) + "\n").encode("utf-8")


class NOAAWindMaskScienceTests(unittest.TestCase):
    def test_ocean_blended_is_not_independently_observed(self):
        x = inspect_nbs_daily_csv(body(row()))
        self.assertEqual(x["grid_cell_count"], 1)
        self.assertEqual(x["ocean_blended"], 1)
        self.assertEqual(x["independent_in_situ_observation_cells_proven"], 0)
        self.assertTrue(x["ocean_cells_are_blended_not_independently_observed"])
        self.assertFalse(x["commercial_use_or_cat_model_admitted"])
        self.assertFalse(x["provider_original_response_verified"])
        self.assertEqual(len(x["input_byte_sha256"]), 64)

    def test_model_flag_six_never_counts_as_ocean_observation(self):
        x = inspect_nbs_daily_csv(body(row(mask="6")))
        self.assertEqual(x["model_flagged"], 1)
        self.assertEqual(x["ocean_blended"], 0)

    def test_land_lake_river_and_nodata_are_not_eligible(self):
        x = inspect_nbs_daily_csv(body(
            row(mask="0"),
            row(lon="285.25", mask="2"),
            row(lon="285.5", mask="3"),
            row(lon="285.75", wind="-9999", mask="1"),
            row(lon="286.0", wind="-9999", mask="-9999"),
        ))
        self.assertEqual(x["inland_or_land"], 3)
        self.assertEqual(x["missing_wind"], 2)
        self.assertEqual(x["ocean_blended"], 0)
        self.assertEqual(x["unknown_mask"], 1)

    def test_bad_mask_or_missing_mask_not_silently_ocean(self):
        for mask in ("4", "5", "", "1.0", "NaN"):
            with self.subTest(mask=mask), self.assertRaises(NOAAWindBlocked):
                inspect_nbs_daily_csv(body(row(mask=mask)))

    def test_wrong_science_variable_list_and_units(self):
        for changed in (HEADER.replace("windspeed", "u_wind"),
                        HEADER.replace(",mask", ""), HEADER + ",token"):
            with self.subTest(changed=changed), self.assertRaises(NOAAWindBlocked):
                inspect_nbs_daily_csv(body(row(), header=changed))
        with self.assertRaises(NOAAWindBlocked):
            inspect_nbs_daily_csv(body(row(), units=UNITS.replace("m s-1", "knots")))

    def test_bad_time_and_height(self):
        for overrides in ({"time": "2023-01-01T00:00:00Z"},
                          {"time": "2024-01-01T00:00:00+02:00"},
                          {"time": "not-a-time"}, {"zlev": "100"}):
            with self.subTest(overrides=overrides), self.assertRaises(NOAAWindBlocked):
                inspect_nbs_daily_csv(body(row(**overrides)))
        self.assertEqual(EXPECTED_DAY, "2024-01-01")

    def test_bad_grid_range_and_alignment(self):
        for overrides in ({"lat": "90"}, {"lon": "-75"}, {"lon": "360"},
                          {"lat": "25.123"}, {"lon": "285.124"}):
            with self.subTest(overrides=overrides), self.assertRaises(NOAAWindBlocked):
                inspect_nbs_daily_csv(body(row(**overrides)))

    def test_bad_wind_values_never_imputed(self):
        for wind in ("-1", "-12.5", "999", "NaN", "1e999", "garbage", ""):
            with self.subTest(wind=wind), self.assertRaises(NOAAWindBlocked):
                inspect_nbs_daily_csv(body(row(wind=wind)))
        x = inspect_nbs_daily_csv(body(row(wind="-9999")))
        self.assertEqual(x["missing_wind"], 1)
        self.assertEqual(x["ocean_blended"], 0)

    def test_duplicate_cell_rejected(self):
        with self.assertRaises(NOAAWindBlocked):
            inspect_nbs_daily_csv(body(row(), row()))

    def test_missing_rows_and_malformed_bytes_rejected(self):
        for data in (b"", b"\xff", b"<html>failed</html>",
                     PREFIX.encode(), body(row()).replace(b"285.0", b"285.0\x00"),
                     b"x" * (MAX_BYTES + 1)):
            with self.subTest(data=data[:20]), self.assertRaises(NOAAWindBlocked):
                inspect_nbs_daily_csv(data)

    def test_no_raw_rows_or_provider_values_in_report(self):
        original = body(row(wind="91.25"))
        output = inspect_nbs_daily_csv(original)
        self.assertNotIn("91.25", json.dumps(output))
        self.assertFalse(output["source_bytes_persisted"])
        self.assertTrue(output["era5_direction_lineage_must_be_preserved"])


if __name__ == "__main__":
    unittest.main()
