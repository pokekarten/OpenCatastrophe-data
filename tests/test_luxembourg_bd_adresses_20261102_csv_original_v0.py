# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only tiny fully fabricated ACT address CSV fixtures are used here."""
from __future__ import annotations
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from research_runners.luxembourg_bd_adresses_20261102_csv_original_v0 import (
    AddressCsvError, inspect, main, _coordinates, _numeric,
)


def test_csv(text, inspect_kwargs=None):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "synthetic.csv"
        raw = text.encode("utf-8")
        p.write_bytes(raw)
        kw = {"expected_size": len(raw), "expected_md5": hashlib.md5(raw).hexdigest()}
        if inspect_kwargs:
            kw.update(inspect_kwargs)
        return inspect(p, **kw)


class OriginalCsvQualityTests(unittest.TestCase):
    def test_synthetic_exact_bytes_but_never_model_admission(self):
        r = test_csv("WGS84 Latitude;WGS84 Longitude;address\n49.6;6.1;fictional A\n49.6;6.1;fictional B\n49.7;6.2;fictional C\n")
        self.assertEqual(r["observed_data_rows"], 3)
        self.assertTrue(r["wgs84_coordinate_columns_identified"])
        self.assertEqual(r["coordinate_quality"]["duplicate_exact_coordinate_text_pairs_excess"], 1)
        self.assertFalse(r["cat_model_input_admitted"])
        self.assertFalse(r["independent_building_identity_proven"])
        self.assertEqual(r["raw_address_rows_exported"], 0)
        self.assertNotIn("fictional", json.dumps(r))

    def test_no_coordinate_columns_never_assumes_geo_validity(self):
        r = test_csv("easting,northing,addr\n1,2,synth\n")
        self.assertFalse(r["wgs84_coordinate_columns_identified"])
        self.assertIsNone(r["coordinate_quality"])

    def test_missing_and_invalid_coordinate_totals(self):
        r = test_csv("latitude,longitude,fake\n49.5,6.1,A\n,6.2,B\n999,6.0,C\n")
        self.assertEqual(r["coordinate_quality"]["valid_wgs84_coordinate_pairs"], 1)
        self.assertEqual(r["coordinate_quality"]["missing_coordinate_pairs"], 1)
        self.assertEqual(r["coordinate_quality"]["malformed_or_out_of_range_pairs"], 1)

    def test_utf8_bom_and_tab(self):
        r = test_csv("\ufefflatitude\tlongitude\ttest\n49.5\t6.1\tx\n")
        self.assertEqual(r["csv_delimiter"], "\t")
        self.assertEqual(r["observed_data_rows"], 1)

    def test_resource_checksum_and_size_are_required(self):
        raw = "lat,lon,fake\n49.5,6.1,synthetic\n"
        for extra in ({"expected_md5":"0"*32}, {"expected_size":10}, {"expected_size":True}):
            with self.subTest(extra=extra), self.assertRaises(AddressCsvError):
                test_csv(raw, extra)

    def test_duplicate_header_and_row_width_block(self):
        for raw in ["lat,lat,fake\n49,6,x\n",
                    "lat,lon,fake\n49,6\n",
                    "lat,lon,fake\n49,6,x,surplus\n"]:
            with self.subTest(raw=raw), self.assertRaises(AddressCsvError):
                test_csv(raw)

    def test_empty_data_blocked(self):
        with self.assertRaises(AddressCsvError):
            test_csv("lat,lon,fake\n")

    def test_known_coordinate_names_are_conservative(self):
        self.assertIsNone(_coordinates(["lat", "latitude", "lon"]))
        self.assertIsNone(_coordinates(["northing", "easting"]))
        self.assertEqual(_coordinates(["latitude", "longitude"]), (0,1))

    def test_coordinate_numbers_reject_nonfinite_and_invalid(self):
        self.assertIsNone(_numeric("nan", 90))
        self.assertIsNone(_numeric("Infinity", 180))
        self.assertIsNone(_numeric("91", 90))
        self.assertEqual(_numeric("49,5",90),49.5)

    def test_no_real_address_in_cli_errors(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"BAD_CUSTOMER_ADDRESS.csv"
            p.write_text("x,y\n1,2\n",encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()) as e:
                code=main(["--source-csv",str(p)])
            self.assertEqual(code,2)
            self.assertNotIn("BAD_CUSTOMER_ADDRESS",e.getvalue())


if __name__=="__main__":
    unittest.main()
