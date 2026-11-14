# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""NetCDF4 byte-reader with invented Ciara hourly gust and legal no-go checks."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from decimal import Decimal
import hashlib
import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_nrw_era5_normalized_netcdf_v0 as intake

NETCDF4_AVAILABLE = importlib.util.find_spec("netCDF4") is not None
if NETCDF4_AVAILABLE:
    import netCDF4
    import numpy as np

NODES = Counter({(202, 24): 2, (203, 25): 1, (210, 38): 1})
TIVS = Counter({(202, 24): 300_000, (203, 25): 100_000, (210, 38): 200_000})
SIGNATURE = "".join(f"{a}:{b}:{NODES[(a,b)]}\n" for a, b in sorted(NODES)).encode()


def fake_plan():
    return {
        "schema": "CIARA2020_NRW_HU22_10K_ERA5_10FG_AREA_REQUEST_PLAN_V0",
        "request": {"area": [52.5, 5.75, 50.25, 9.5]},
        "event_hourly_timesteps": 96,
        "original_CDS_source_data_acquired_or_attested": False,
        "German_wind_vulnerability_or_gross_net_EP_model_admitted": False,
        "occupied_grid_nodes_by_public_building_candidates": len(NODES),
        "occupied_nodes_count_sha256": hashlib.sha256(SIGNATURE).hexdigest(),
        "source_2022_NRW_counties": 2,
        "historical_original_NRW_HU2022_zip_sha256": "a" * 64,
    }


def grid_preview():
    peaks = {(int(lat * 4), int(lon * 4)): (Decimal("12"), 0)
             for lat in intake.LAT_NODES for lon in intake.LON_NODES}
    peaks[(202, 24)] = (Decimal("28"), 9)
    peaks[(203, 25)] = (Decimal("33"), 11)
    peaks[(210, 38)] = (Decimal("44"), 13)
    return {
        "sha256_of_local_normalized_netcdf": "b" * 64,
        "size_bytes": 123456,
        "grid_peaks": peaks,
    }


class CIARAOneStormResearchGate(unittest.TestCase):
    def test_occupied_node_counts_tiv_and_threshold_math_no_damage(self):
        result = intake.summarize_grid_exposure(
            fake_plan(), grid_preview(), NODES, TIVS, expected_sites=4, expected_tiv=600000
        )
        self.assertEqual(result["matched_public_building_candidates"], 4)
        self.assertEqual(result["validated_grid_nodes"], 160)
        self.assertEqual(result["grid_points_with_public_candidate"], 3)
        self.assertEqual(result["pointwise_max_2020_ciara_gust_mps_thresholds"], {
            "25": {"public_building_candidate_count": 4, "fictional_original_TIV_eur": 600000, "occupied_grid_nodes": 3},
            "30": {"public_building_candidate_count": 2, "fictional_original_TIV_eur": 300000, "occupied_grid_nodes": 2},
            "35": {"public_building_candidate_count": 1, "fictional_original_TIV_eur": 200000, "occupied_grid_nodes": 1},
            "40": {"public_building_candidate_count": 1, "fictional_original_TIV_eur": 200000, "occupied_grid_nodes": 1},
        })
        self.assertFalse(result["CDS_original_bytes_and_license_independently_verified"])
        self.assertFalse(result["NetCDF_original_CDS_provider_structure_directly_parsed"])
        self.assertFalse(result["vulnerability_or_native_GUL_IL_RI_OEP_AEP_admitted"])
        self.assertNotIn("SYN-NRW", str(result))

    def test_no_grid_count_tamper_and_no_unsafe_admission(self):
        for key, new_value in (
            ("occupied_nodes_count_sha256", "c" * 64),
            ("original_CDS_source_data_acquired_or_attested", True),
            ("German_wind_vulnerability_or_gross_net_EP_model_admitted", True),
            ("event_hourly_timesteps", 95),
        ):
            with self.subTest(key=key):
                plan = fake_plan()
                plan[key] = new_value
                with self.assertRaises(intake.CiaraNetCDFBlocked):
                    intake.summarize_grid_exposure(
                        plan, grid_preview(), NODES, TIVS, expected_sites=4, expected_tiv=600000
                    )
        wrong = Counter(TIVS)
        wrong[(202, 24)] += 1
        with self.assertRaises(intake.CiaraNetCDFBlocked):
            intake.summarize_grid_exposure(fake_plan(), grid_preview(), NODES, wrong, expected_sites=4, expected_tiv=600000)

    def test_regular_file_and_original_source_nonbypass(self):
        with TemporaryDirectory() as t:
            archive = Path(t) / "not-original.zip"
            archive.write_bytes(b"fabricated source ZIP")
            normalized = Path(t) / "synthetic.nc"
            normalized.write_bytes(b"fake")
            with self.assertRaises(ValueError):
                intake.run(archive, normalized)
            with self.assertRaisesRegex(intake.CiaraNetCDFBlocked, "regular bounded"):
                intake.read_normalized_grid(normalized)


@unittest.skipUnless(NETCDF4_AVAILABLE, "requires requirements-glofas-acquisition.txt")
class NormalizedNetCDF4BytesTests(unittest.TestCase):
    def write_synthetic_netcdf(self, dest: Path, *, alteration=None, **kw):
        dims = dict(intake.DIMENSIONS)
        dims.update(kw.get("dimension_override", {}))
        with netCDF4.Dataset(dest, "w", format="NETCDF4") as f:
            for name, count in dims.items():
                f.createDimension(name, count)
            time = f.createVariable("time", "f8", ("time",))
            time.units = kw.get("time_units", intake.TIME_UNITS)
            time.calendar = kw.get("calendar", intake.CALENDAR)
            time[:] = np.arange(dims["time"], dtype=float)
            if kw.get("shift_time"):
                time[:] = np.arange(dims["time"], dtype=float) + 1
            lat = f.createVariable("latitude", "f8", ("latitude",))
            lat.units = "degrees_north"
            lat[:] = [float(v) for v in intake.LAT_NODES[:dims["latitude"]]]
            lon = f.createVariable("longitude", "f8", ("longitude",))
            lon.units = "degrees_east"
            lon[:] = [float(v) for v in intake.LON_NODES[:dims["longitude"]]]
            if kw.get("wrong_coordinate"):
                lat[0] = float(lat[0]) + 0.125
            gust = f.createVariable(intake.GUST_NAME, "f4",
                                    ("time", "latitude", "longitude"),
                                    fill_value=-9999.0)
            gust.units = kw.get("gust_units", "m/s")
            gust.original_era5_variable = kw.get("source_variable", intake.GUST_SOURCE_NAME)
            gust[:] = np.full((dims["time"],dims["latitude"],dims["longitude"]), 12.0, dtype="f4")
            if kw.get("masked_gust"):
                gust[4,1,1] = -9999.0
            if kw.get("bad_gust"):
                gust[4,1,1] = kw["bad_gust"]
            if alteration:
                alteration(f)
        return dest

    def test_real_synthetic_netcdf4_bytes_and_96_hour_validation(self):
        with TemporaryDirectory() as t:
            p = self.write_synthetic_netcdf(Path(t) / "local_normalized.nc")
            grid = intake.read_normalized_grid(p)
            self.assertEqual(grid["sha256_of_local_normalized_netcdf"], hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(grid["temporal_records"], 96)
            self.assertEqual(grid["grid_nodes"], 160)
            self.assertEqual(len(grid["grid_peaks"]), 160)
            self.assertTrue(all(val == Decimal("12") and hour == 0
                                for val, hour in grid["grid_peaks"].values()))

    def test_time_shift_length_units_grid_and_malformed_original_variable_fail(self):
        cases = (
            {"shift_time": True},
            {"dimension_override": {"time": 95}},
            {"dimension_override": {"longitude": 15}},
            {"time_units": "hours since 2020-02-09 00:00:00"},
            {"calendar": "360_day"},
            {"gust_units": "km/h"},
            {"source_variable": "10m_u_component_of_wind"},
            {"wrong_coordinate": True},
        )
        for kw in cases:
            with self.subTest(kw=kw), TemporaryDirectory() as t:
                p = self.write_synthetic_netcdf(Path(t) / "bad.nc", **kw)
                with self.assertRaises(intake.CiaraNetCDFBlocked):
                    intake.read_normalized_grid(p)

    def test_nonfinite_masked_negative_and_outlier_rejected(self):
        for kw in ({"bad_gust": float("nan")},
                   {"bad_gust": float("inf")},
                   {"bad_gust": -0.1},
                   {"bad_gust": 150.1},
                   {"masked_gust": True}):
            with self.subTest(kw=kw), TemporaryDirectory() as t:
                p = self.write_synthetic_netcdf(Path(t) / "bad.nc", **kw)
                with self.assertRaises(intake.CiaraNetCDFBlocked):
                    intake.read_normalized_grid(p)


if __name__ == "__main__":
    unittest.main()
