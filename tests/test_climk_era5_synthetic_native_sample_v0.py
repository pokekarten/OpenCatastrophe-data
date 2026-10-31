# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only source-identity and native-grid nearest-cell science tests."""
import json
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

from scripts import climk_era5_synthetic_native_sample_v0 as mod


class FakeVariable:
    def __init__(self, data=None, value=None):
        self.data, self.value = data, value
        self.sampled = []

    def __getitem__(self, key):
        self.sampled.append(key)
        if self.data is not None:
            return self.data[key] if not isinstance(key, slice) else self.data[key]
        return self.value


class FakeDataset:
    def __init__(self, abs_value=34.5, rel_value=1.12):
        self.abs_var = FakeVariable(value=abs_value)
        self.rel_var = FakeVariable(value=rel_value)
        self.variables = {
            "longitude": FakeVariable(data=[9.75, 10.0, 10.25]),
            "latitude": FakeVariable(data=[50.25, 50.0, 49.75]),
            "absolute_maxwindgusts": self.abs_var,
            "relative_maxwindgusts": self.rel_var,
        }

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def sites(points):
    return json.dumps({
        "schema_version": "oc-effis-synthetic-sites-v0",
        "crs": "OGC:CRS84", "synthetic_only": True,
        "sites": [{"site_id": ident, "longitude": lon, "latitude": lat}
                  for ident, lon, lat in points],
    }).encode("utf-8")


def staged_sample(ds, points, storm_index=0):
    with patch.object(mod, "verify_source_bytes", return_value={
        "sha256_observed": "a"*64, "sha256_pinned": True,
    }), patch.object(mod, "inspect_netcdf_header", return_value={
        "dimensions": mod.EXPECTED_DIMENSIONS,
    }), patch.dict(sys.modules, {"netCDF4": SimpleNamespace(Dataset=lambda *_args, **_kwargs: ds)}):
        return mod.sample_climk_era5(
            original=b"synthetic stub",
            synthetic_sites_json=sites(points),
            storm_index=storm_index,
        )


class CLIMKSyntheticSiteSamplingTests(unittest.TestCase):
    def test_regular_ascending_axis_exact(self):
        self.assertEqual(mod.nearest_native_cell((1.0, 1.25, 1.5), 1.25), (1, 1.25))

    def test_regular_descending_axis_round(self):
        self.assertEqual(mod.nearest_native_cell((5.0, 4.75, 4.5), 4.51), (2, 4.5))

    def test_halfway_tie_break_low_coordinate(self):
        self.assertEqual(mod.nearest_native_cell((2.0, 2.25, 2.5), 2.125), (0, 2.0))

    def test_out_of_coverage_no_extrapolation(self):
        for x in (-5.0, 200):
            with self.subTest(x=x), self.assertRaises(mod.WindPointError):
                mod.nearest_native_cell((0.0, 0.25, 0.5), x)

    def test_nonregular_axis_rejected(self):
        with self.assertRaises(mod.WindPointError):
            mod.nearest_native_cell((0.0, 0.25, 0.6), 0.2)

    def test_duplicate_grid_center_rejected(self):
        with self.assertRaises(mod.WindPointError):
            mod.nearest_native_cell((0.0, 0.25, 0.25), 0.2)

    def test_nonfinite_axis_rejected(self):
        with self.assertRaises(mod.WindPointError):
            mod.nearest_native_cell((0.0, float("nan"), 0.5), 0.2)

    def test_native_cell_sampling_and_no_loss(self):
        ds = FakeDataset()
        result = staged_sample(ds, [("SYNTH_DE", 10.1, 50.1)], storm_index=12)
        self.assertEqual(result["site_count"], 1)
        self.assertEqual(result["event_key"], "climk-winds:v2:ERA5:storm-index:12")
        self.assertEqual(result["site_samples"][0]["native_cell_x"], 1)
        self.assertEqual(result["site_samples"][0]["native_cell_y"], 1)
        self.assertEqual(result["site_samples"][0]["absolute_max_gust_m_s"], 34.5)
        self.assertEqual(result["site_samples"][0]["relative_max_gust_dimensionless"], 1.12)
        self.assertEqual(ds.abs_var.sampled[0], (12,1,1))
        self.assertFalse(result["damage_or_insured_loss_computed"])
        self.assertFalse(result["source_event_frequency_inferred"])
        self.assertFalse(result["scientifically_admitted"])

    def test_reject_missing_gust_not_zero(self):
        with self.assertRaises(mod.WindPointError):
            staged_sample(FakeDataset(abs_value=float("nan")),
                          [("A",10.0,50.0)])

    def test_reject_unphysical_gust(self):
        with self.assertRaises(mod.WindPointError):
            staged_sample(FakeDataset(abs_value=-1.0), [("A",10.0,50.0)])

    def test_reject_unphysical_climatology_ratio(self):
        with self.assertRaises(mod.WindPointError):
            staged_sample(FakeDataset(rel_value=-0.5), [("A",10.0,50.0)])

    def test_reject_outside_source_grid(self):
        with self.assertRaises(mod.WindPointError):
            staged_sample(FakeDataset(), [("A", 11.0, 50.0)])

    def test_reject_unsupported_event_index(self):
        for idx in (-1, 50, True):
            with self.subTest(idx=idx), self.assertRaises(mod.WindPointError):
                mod.sample_climk_era5(
                    original=b"none",
                    synthetic_sites_json=sites([("A",10.0,50.0)]),
                    storm_index=idx,
                )

    def test_source_bytes_must_be_pinned(self):
        with self.assertRaises(ValueError):
            mod.sample_climk_era5(original=b"invalid source",
                                  synthetic_sites_json=sites([("A",10.0,50.0)]),
                                  storm_index=0)


if __name__ == "__main__":
    unittest.main()
