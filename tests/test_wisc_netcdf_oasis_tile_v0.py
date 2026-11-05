# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent synthetic-only Oasis footprint tests, including optional NetCDF-4 integration."""

from __future__ import annotations

import contextlib
from decimal import Decimal
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research_runners.wisc_netcdf_oasis_tile_v0 import (
    WiscTileError, bins_from_text, convert_netcdf, hash_original,
    main, parse_source_name, render_tile,
)

FILENAME = "fp_ga3ups_199311201800_1708_002_v1.nc"
SHA = "a" * 64


def synthetic(
    grid=None, *, lat=None, lon=None, edges=None, filename=FILENAME,
    method="1.2", member=2, event=7, start_row=0, start_col=0,
):
    return render_tile(
        original_filename=filename, original_sha256=SHA, event_id=event,
        synthetic_set=method, ensemble_member=member,
        grid_row_start=start_row, grid_col_start=start_col,
        full_latitudes=lat if lat is not None else [50.0, 49.0],
        full_longitudes=lon if lon is not None else [10.0, 11.0, 12.0],
        gust_tile=grid if grid is not None else [[0, 10, None], [20, 30, 40]],
        intensity_edges=edges if edges is not None else bins_from_text("0,10,20,30,40,50"),
    )


class WiscTileOfflineTests(unittest.TestCase):
    def test_explicit_original_filename_decoded_not_to_real_weather(self):
        result = parse_source_name("C3S_EvenSet_" + FILENAME)
        self.assertEqual(result, {"time": "199311201800", "track": "1708", "code": "002"})
        _, receipt = synthetic()
        self.assertTrue(receipt["source_time_is_simulated_not_actual_event_date"])
        self.assertFalse(receipt["filename_set_ensemble_crosswalk_independently_verified"])

    def test_exact_oasis_csv_columns_and_bin_edges(self):
        files, receipt = synthetic()
        self.assertEqual(set(files), {"events.csv", "footprint.csv",
                                      "intensity_bin_dict.csv", "areaperil_dict.csv"})
        self.assertEqual(files["events.csv"], b"event_id\n7\n")
        rows = files["footprint.csv"].decode().splitlines()
        self.assertEqual(rows[0], "event_id,areaperil_id,intensity_bin_index,prob")
        self.assertEqual(rows[1:], [
            "7,1,1,1.0",
            "7,2,2,1.0",
            "7,4,3,1.0",
            "7,5,4,1.0",
            "7,6,5,1.0",
        ])
        self.assertEqual(receipt["valid_cells"], 5)
        self.assertEqual(receipt["missing_gust_cells_weather_unknown"], 1)
        self.assertFalse(receipt["annual_oep_aep_authorized"])
        self.assertFalse(receipt["occurrence_file_created"])
        self.assertFalse(receipt["native_oasis_run_verified"])
        self.assertFalse(receipt["source_rights_and_asset_admission_approved"])

    def test_grid_original_shape_stabilises_areaperil_id_across_tiles(self):
        files, receipt = synthetic(grid=[[30, 40]], start_row=1, start_col=1)
        self.assertEqual(
            files["footprint.csv"].decode().splitlines()[1:],
            ["7,5,4,1.0", "7,6,5,1.0"],
        )
        self.assertEqual(receipt["full_grid_shape"], [2, 3])

    def test_intensity_last_edge_included_no_clipping(self):
        files, _ = synthetic(grid=[[50]], edges=bins_from_text("0,10,50"))
        self.assertIn(b"7,1,2,1.0", files["footprint.csv"])
        with self.assertRaisesRegex(WiscTileError, "finite bounds"):
            synthetic(grid=[[201]])

    def test_nodata_not_zero_wind(self):
        files, receipt = synthetic(grid=[[None, 0, math.nan]])
        self.assertEqual(receipt["missing_gust_cells_weather_unknown"], 2)
        self.assertEqual(receipt["valid_cells"], 1)
        self.assertEqual(files["footprint.csv"].decode().splitlines()[1], "7,2,1,1.0")

    def test_missing_everywhere_fails_closed(self):
        with self.assertRaisesRegex(WiscTileError, "no valid observed"):
            synthetic(grid=[[None, math.nan]])

    def test_bad_source_name_and_simulated_date_rejected(self):
        for name in ("events.csv", "fp_ga3ups_199313201800_1708_002_v1.nc",
                     "fp_ga3ups_202311201800_1708_002_v1.nc",
                     "fp_ga3ups_199311201800_1708_002_v2.nc"):
            with self.subTest(name=name), self.assertRaises(WiscTileError):
                synthetic(filename=name)

    def test_invalid_source_identity_and_method_rejected(self):
        with self.assertRaisesRegex(WiscTileError, "synthetic set"):
            synthetic(method="all")
        with self.assertRaisesRegex(WiscTileError, "ensemble"):
            synthetic(member=0)
        with self.assertRaisesRegex(WiscTileError, "event_id"):
            synthetic(event=0)
        with self.assertRaisesRegex(WiscTileError, "expected exact"):
            render_tile(
                original_filename=FILENAME, original_sha256="not-a-hash",
                event_id=7, synthetic_set="1.2", ensemble_member=2,
                grid_row_start=0, grid_col_start=0,
                full_latitudes=[50], full_longitudes=[10],
                gust_tile=[[10]], intensity_edges=bins_from_text("0,20"),
            )

    def test_invalid_geographic_coordinate_or_duplicate_rejected(self):
        for lon in ([181], [10, 10, 12], [10, 9, 11]):
            with self.subTest(lon=lon), self.assertRaises(WiscTileError):
                synthetic(lon=lon)

    def test_no_inferred_coverage_from_bad_grid(self):
        with self.assertRaisesRegex(WiscTileError, "nonrectangular"):
            synthetic(grid=[[1, 2], [3]])
        with self.assertRaisesRegex(WiscTileError, "beyond declared"):
            synthetic(grid=[[1, 2]], start_row=2)
        with self.assertRaisesRegex(WiscTileError, "numeric"):
            synthetic(grid=[["25"]])
        with self.assertRaisesRegex(WiscTileError, "finite bounds"):
            synthetic(grid=[[-1]])
        with self.assertRaisesRegex(WiscTileError, "finite bounds"):
            synthetic(grid=[[math.inf]])
        with self.assertRaisesRegex(WiscTileError, "not finite"):
            synthetic(grid=[[10**1000]])

    def test_bin_contract_rejects_ambiguous_limits(self):
        for bins in ("5,10", "0,10,10", "0,NaN", "0,inf", "0,-1", "0,250", "0", "0,10,abc"):
            with self.subTest(bins=bins), self.assertRaises(WiscTileError):
                bins_from_text(bins)

    def test_output_identities_and_determinism(self):
        a, receipt_a = synthetic()
        b, receipt_b = synthetic()
        self.assertEqual(a, b)
        self.assertEqual(receipt_a, receipt_b)
        for filename, data in a.items():
            self.assertEqual(receipt_a["output_files"][filename]["bytes"], len(data))
            self.assertEqual(
                receipt_a["output_files"][filename]["sha256"],
                hashlib.sha256(data).hexdigest(),
            )

    def test_reject_binary_with_wrong_hash_or_wrong_type(self):
        with TemporaryDirectory() as d:
            original = Path(d) / FILENAME
            original.write_bytes(b"definitely not NetCDF")
            with self.assertRaisesRegex(WiscTileError, "NetCDF-4 HDF5"):
                hash_original(original, hashlib.sha256(original.read_bytes()).hexdigest())
            original.write_bytes(b"\x89HDF\r\n\x1a\nhello")
            with self.assertRaisesRegex(WiscTileError, "SHA-256 mismatch"):
                hash_original(original, "b" * 64)


@unittest.skipUnless(importlib.util.find_spec("netCDF4") and importlib.util.find_spec("xarray"),
                     "integration requires explicit netCDF4 and xarray packages")
class WiscNetcdf4SyntheticIntegration(unittest.TestCase):
    @staticmethod
    def original(path: Path) -> str:
        from netCDF4 import Dataset
        with Dataset(path, "w", format="NETCDF4") as ds:
            ds.createDimension("latitude", 2)
            ds.createDimension("longitude", 3)
            lat = ds.createVariable("latitude", "f8", ("latitude",))
            lon = ds.createVariable("longitude", "f8", ("longitude",))
            gust = ds.createVariable("max_gust", "f8", ("latitude", "longitude"), fill_value=-9999.)
            lat[:] = [50, 49]
            lon[:] = [10, 11, 12]
            lat.units = "degrees_north"
            lon.units = "degrees_east"
            gust.units = "m/s"
            gust[:] = [[0., 10., -9999.], [20., 30., 40.]]
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_real_synthetic_netcdf4_binary_to_four_oasis_csvs(self):
        with TemporaryDirectory() as d:
            original = Path(d) / FILENAME
            digest = self.original(original)
            files, receipt = convert_netcdf(
                original, expected_sha256=digest,
                variable="max_gust", latitude_name="latitude", longitude_name="longitude",
                event_id=7, synthetic_set="1.2", ensemble_member=2,
                row_start=0, col_start=0, height=2, width=3,
                bin_edges=bins_from_text("0,10,20,30,40,50"),
            )
            self.assertEqual(receipt["original_sha256_verified"], digest)
            self.assertEqual(receipt["valid_cells"], 5)
            self.assertEqual(receipt["missing_gust_cells_weather_unknown"], 1)
            self.assertEqual(len(files), 4)
            out = Path(d) / "output"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = main([
                    "--netcdf", str(original), "--original-sha256", digest,
                    "--variable", "max_gust", "--latitude-variable", "latitude",
                    "--longitude-variable", "longitude", "--event-id", "7",
                    "--synthetic-set", "1.2", "--ensemble-member", "2",
                    "--row-start", "0", "--col-start", "0", "--height", "2", "--width", "3",
                    "--bin-edges", "0,10,20,30,40,50", "--out", str(out),
                ])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["valid_cells"], 5)
            self.assertEqual((out / "footprint.csv").read_bytes(), files["footprint.csv"])
            self.assertEqual(len(list(out.iterdir())), 5)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                again = main([
                    "--netcdf", str(original), "--original-sha256", digest,
                    "--variable", "max_gust", "--latitude-variable", "latitude",
                    "--longitude-variable", "longitude", "--event-id", "7",
                    "--synthetic-set", "1.2", "--ensemble-member", "2",
                    "--row-start", "0", "--col-start", "0", "--height", "2", "--width", "3",
                    "--out", str(out),
                ])
            self.assertEqual(again, 2)
            self.assertIn("refuse overwrite", stderr.getvalue())

    def test_netcdf_wrong_units_block(self):
        from netCDF4 import Dataset
        with TemporaryDirectory() as d:
            original = Path(d) / FILENAME
            self.original(original)
            with Dataset(original, "a") as ds:
                ds["max_gust"].units = "km/h"
            digest = hashlib.sha256(original.read_bytes()).hexdigest()
            with self.assertRaisesRegex(WiscTileError, "gust units"):
                convert_netcdf(
                    original, expected_sha256=digest, variable="max_gust",
                    latitude_name="latitude", longitude_name="longitude",
                    event_id=7, synthetic_set="1.2", ensemble_member=2,
                    row_start=0, col_start=0, height=2, width=3,
                    bin_edges=bins_from_text("0,10,20,30,40,50"),
                )


if __name__ == "__main__":
    unittest.main()
