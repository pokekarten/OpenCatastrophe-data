# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely synthetic regression tests; no vendor archives, raster or census rows."""
from __future__ import annotations

import hashlib
import io
import csv
import json
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from research_runners.eu_grid_native_sample_preflight_v0 import (
    CSV_FIELDS, DWD_BASE, GHSL_MEMBER, GHSL_ROWS, SourceGateError,
    parse_census_prefix, parse_ghsl_legend,
    classify_dwd_radklim_2021_archive, verify_ghsl_zip,
)


def census(*records):
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return buf.getvalue().encode("utf-8")


def row(i=1, **overrides):
    record = {
        "GRD_ID": f"CRS3035RES1000mN2683000E4285{i:03d}",
        "T":"25", "M":"14", "F":"12",
        "Y_LT15":"6","Y_1564":"18","Y_GE65":"3", "EMP":"2",
        "NAT":"22","EU_OTH":"0","OTH":"1",
        "SAME":"23","CHG_IN":"0","CHG_OUT":"0",
        "LAND_SURFACE":"0.903667","POPULATED":"1","CNTR_ID":"AT-CH-LI"}
    record.update(overrides)
    return record


def sha(raw): return hashlib.sha256(raw).hexdigest()


def synthetic_ghsl_legend():
    # Synthetic different RGB values, deliberately not original JRC bytes.
    lines = ["gridcode,epoch_num,epoch_txt,R,G,B"]
    for i,(code,epoch,label) in enumerate(GHSL_ROWS):
        rgb = ("100","200","250") if i < 2 else ("10","20","30")
        lines.append(f"{code},{epoch},{label},{','.join(rgb)}")
    raw = ("\r\n".join(lines) + "\r\n").encode("ascii")
    assert len(raw) == 209, len(raw)
    return raw


class EUGridQA(unittest.TestCase):
    def test_eurostat_original_schema_and_confidentiality(self):
        data = census(
            row(1), row(2,T="-8888",M="-8888",F="-8888"),
            row(3,T="-9999",M="-9999",F="-9999"),
            row(4,T="0",M="0",F="0",POPULATED="1"))
        result = parse_census_prefix(data,sha(data))
        stat = result["summary"]
        self.assertEqual(stat["row_count"],4)
        self.assertEqual(stat["known_total_population_sum"],25)
        self.assertEqual(stat["missing_by_reason"]["confidentiality"],1)
        self.assertEqual(stat["missing_by_reason"]["other_missing"],1)
        self.assertEqual(stat["zero_total_cells"],1)
        self.assertEqual(stat["mf_total_mismatches"],1)
        self.assertEqual(stat["multicountry_cells"],4)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["source_cells_or_geometries_exported"])
        self.assertNotIn("CRS3035",json.dumps(result))

    def test_eurostat_invalid_grids_and_malformed_values_block(self):
        mutations = (
            {"GRD_ID":"BAD"},
            {"GRD_ID":"CRS4326RES1000mN12E45"},
            {"T":"-1"},
            {"T":"NA"},
            {"T":"2.5"},
            {"T":"false"},
            {"LAND_SURFACE":"1.01"},
            {"LAND_SURFACE":"NaN"},
            {"CNTR_ID":"AUS"},
            {"POPULATED":"2"},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                src=census(row(1,**mutation))
                with self.assertRaises(SourceGateError):
                    parse_census_prefix(src,sha(src))

    def test_eurostat_unallocated_rows_and_checksum(self):
        src=census(row(1, GRD_ID="LU_unallocated", CNTR_ID="LU"))
        result=parse_census_prefix(src,sha(src))
        self.assertEqual(result["summary"]["unallocated_rows"],1)
        with self.assertRaisesRegex(SourceGateError,"SHA-256 mismatch"):
            parse_census_prefix(src,"0"*64)
        with self.assertRaises(SourceGateError):
            parse_census_prefix(src.rstrip(b"\n"),sha(src.rstrip(b"\n")))

    def test_ghsl_class_semantics_without_original_rgb_bytes(self):
        raw=synthetic_ghsl_legend()
        result=parse_ghsl_legend(raw,sha(raw))
        self.assertEqual(result["class_codes"],list(range(6)))
        self.assertEqual(result["epoch_labels"][0],"not built-up")
        self.assertFalse(result["raster_pixel_count_verified"])
        modified=raw.replace(b"2010 - 2020", b"2000 - 2020")
        with self.assertRaises(SourceGateError):
            parse_ghsl_legend(modified,sha(modified))

    def test_ghsl_zip_requires_original_crc_and_full_original_sha(self):
        buf=io.BytesIO()
        with ZipFile(buf,"w",compression=ZIP_DEFLATED) as zf:
            zf.writestr(GHSL_MEMBER, synthetic_ghsl_legend())
        data=buf.getvalue()
        with self.assertRaisesRegex(SourceGateError,"legend ZIP metadata mismatch"):
            verify_ghsl_zip(data,sha(data))
        with self.assertRaisesRegex(SourceGateError,"SHA-256 mismatch"):
            verify_ghsl_zip(data,"0"*64)

    def test_dwd_2021_invalid_original_rejected(self):
        bad = DWD_BASE + "2021/RW2017.002_2021_netcdf.tar.gz"
        with self.assertRaisesRegex(SourceGateError,"incorrect"):
            classify_dwd_radklim_2021_archive(bad)
        good = DWD_BASE + "supplement/RW2017.002_2021_netcdf_supplement.tar.gz"
        result = classify_dwd_radklim_2021_archive(good)
        self.assertFalse(result["netcdf_raster_scientifically_approved"])
        self.assertFalse(result["corrected_archive_bytes_validated"])
        with self.assertRaises(SourceGateError):
            classify_dwd_radklim_2021_archive(good + "?version=1")


if __name__ == "__main__":
    unittest.main()
