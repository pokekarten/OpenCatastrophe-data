# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""One REAL Google ARCO hour is independently gated; unit tests use invented gust."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import sys
import tomllib
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO
import json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_google_arco_real_onehour_gust_v0 as m
import ciara2020_google_arco_public_10fg_metadata_v0 as s


def original_fake_proof():
    with m.FROZEN.open("rb") as f:
        pin = tomllib.load(f)
    records = {}
    for name, item in pin["original_variables"].items():
        records[name] = {
            "original_metadata_sha256": item["sha256"],
            "original_metadata_bytes": item["metadata_bytes"],
            "shape": item["shape"],
            "chunks": item["chunks"],
            "dtype": item["dtype"],
        }
    return pin, {
        "schema": s.SCHEMA,
        "public_original_cloud_metadata_fetched_without_cds_token": True,
        "source_original_2020_10fg_hourly_values_fetched": False,
        "original_public_gcs_url": s.SOURCE_ERA5_DATA_URL,
        "public_original_zarr_v2_metadata": records,
    }


class GoogleOriginalCiaraSingleHourTests(unittest.TestCase):
    def test_actual_source_metadata_receipt_bound_not_just_source_name(self):
        source, proof = original_fake_proof()
        self.assertIsNone(m.verify_original_zarr_metadata(proof, source))
        for name, field, false_value in (
            (s.VAR, "original_metadata_sha256", "f"*64),
            ("time", "shape", [5]),
            ("latitude", "dtype", ">f8"),
            ("longitude", "chunks", [2]),
        ):
            with self.subTest(var=name, field=field):
                altered = deepcopy(proof)
                altered["public_original_zarr_v2_metadata"][name][field] = false_value
                with self.assertRaises(m.OriginalWindBlocked):
                    m.verify_original_zarr_metadata(altered, source)
        altered = deepcopy(source)
        altered["original_wind_data_values_read"] = True
        with self.assertRaises(m.OriginalWindBlocked):
            m.verify_original_zarr_metadata(proof, altered)

    def test_2020_hour_one_gridpoint_is_hazard_not_insured_loss(self):
        result = m.validate_hour_sample(
            variable=s.VAR, time_iso="2020-02-09T12:00:00Z",
            latitude="51.0", longitude="7.0",
            source_units="m s**-1", value="28.125"
        )
        self.assertEqual(result["gust_mps"], "28.125")
        self.assertEqual(result["grid_lat"], 51.0)
        self.assertEqual(len(result["gridpoint_value_float32_le_sha256_not_source_chunk_sha"]), 64)
        self.assertTrue(result["source_ERA5_reanalysis_not_station_or_insured_claim"])
        self.assertFalse(result["source_original_GCS_full_chunk_sha256_verified"])
        self.assertFalse(result["German_wind_damage_vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted"])

    def test_other_date_hours_units_and_10m_mean_wind_fail(self):
        cases = (
            dict(time_iso="2020-02-09T13:00:00Z"),
            dict(time_iso="2020-02-08T12:00:00Z"),
            dict(time_iso="2020-02-09T12:00:00"),
            dict(latitude="51.25"),
            dict(longitude="7.25"),
            dict(variable="10m_u_component_of_wind"),
            dict(source_units="km/h"),
            dict(value="-1"),
            dict(value="NaN"),
            dict(value="Infinity"),
            dict(value="150.1"),
        )
        base = dict(variable=s.VAR, time_iso="2020-02-09T12:00:00Z",
                    latitude="51", longitude="7", source_units="m/s", value="28")
        for edit in cases:
            with self.subTest(edit=edit):
                bad = {**base, **edit}
                with self.assertRaises(m.OriginalWindBlocked):
                    m.validate_hour_sample(**bad)

    def test_dry_run_only_uses_canonical_public_probe_no_google_access(self):
        with patch.object(sys, "argv", ["script", "--dry-run"]), \
             patch.object(m, "actual_original_onehour", side_effect=AssertionError("NO NETWORK")):
            out = StringIO()
            with redirect_stdout(out):
                self.assertEqual(m.main(), 0)
            result = json.loads(out.getvalue())
            self.assertFalse(result["original_2020_10fg_values_fetched"])
            self.assertFalse(result["insured_loss_calibrated"])
            self.assertEqual(result["time_utc"], "2020-02-09T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
