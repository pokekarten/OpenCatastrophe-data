# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline allowlist, original-byte and non-admission tests for XWS Kyrill."""
from __future__ import annotations

import io
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from xws_kyrill_original_netcdf_hazard_receipt_v0 import (
    ROOT as PUBLISHER_ROOT, PRODUCTS, MAX_SOURCE_BYTES, download,
    inspect, SourceBlocked, EXPECTED_CDF_MAGIC, REQUIRED_RAW_HEADER
)


class FakeHTTP:
    def __init__(self, raw: bytes, url: str):
        self.body=io.BytesIO(raw)
        self.url=url

    def geturl(self):
        return self.url

    def read(self, n):
        return self.body.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


def fake_cdf() -> bytes:
    head = EXPECTED_CDF_MAGIC+b"\x00\x00\x00\x00"
    for field in REQUIRED_RAW_HEADER:
        head += b"\x00" + field + b"\x00"
    return head+b"0"*(13000-len(head))


class XWSOriginalSourceTests(unittest.TestCase):
    def test_four_products_are_one_historical_storm(self):
        self.assertEqual(set(PRODUCTS),{
            "uncontaminated_raw", "recalibrated_lower_95",
            "recalibrated_mean", "recalibrated_upper_95",
        })
        self.assertEqual(len(set(PRODUCTS.values())),4)
        self.assertTrue(all(x.startswith("Kyrill_") and x.endswith(".nc")
                            for x in PRODUCTS.values()))

    def test_unapproved_url_fails_before_network(self):
        with self.assertRaisesRegex(SourceBlocked,"nonallowlisted"):
            download("https://bad.example/Kyrill_biasMean.nc")

    def test_nonpublisher_redirect_fails(self):
        with self.assertRaisesRegex(SourceBlocked,"nonissuer"):
            download(PUBLISHER_ROOT+PRODUCTS["recalibrated_mean"],
                     opener=lambda req,timeout:FakeHTTP(fake_cdf(),"https://bad.example/file.nc"))

    def test_valid_shape_bounded_original_bytes(self):
        p=PUBLISHER_ROOT+PRODUCTS["recalibrated_mean"]
        self.assertEqual(download(p,opener=lambda req,timeout:FakeHTTP(fake_cdf(),p)),fake_cdf())

    def test_truncated_or_wrong_file_type_fails_closed(self):
        p=PUBLISHER_ROOT+PRODUCTS["recalibrated_mean"]
        for raw in (b"CDF\x01",b"%PDF-"+b"x"*20000,b"CDF\x02"+b"x"*20000):
            with self.subTest(prefix=raw[:4]),self.assertRaises(SourceBlocked):
                download(p,opener=lambda req,timeout:FakeHTTP(raw,p))

    def test_missing_original_rotated_coordinates_fail(self):
        p=PUBLISHER_ROOT+PRODUCTS["recalibrated_mean"]
        raw=EXPECTED_CDF_MAGIC+b"0"*30000
        with self.assertRaisesRegex(SourceBlocked,"header"):
            download(p,opener=lambda req,timeout:FakeHTTP(raw,p))

    def test_large_source_fails_without_storing(self):
        p=PUBLISHER_ROOT+PRODUCTS["recalibrated_upper_95"]
        raw=fake_cdf()+b"x"*(MAX_SOURCE_BYTES+1)
        with self.assertRaisesRegex(SourceBlocked,"too large"):
            download(p,opener=lambda req,timeout:FakeHTTP(raw,p))

    def test_inspect_rejects_bad_content_before_optional_scipy(self):
        with self.assertRaisesRegex(SourceBlocked,"invalid"):
            inspect("recalibrated_mean",b"NOT_A_NETCDF")
        with self.assertRaisesRegex(SourceBlocked,"unrecognized"):
            inspect("not_a_source_product",fake_cdf())

    def test_every_source_projection_remains_explicitly_unadmitted(self):
        code=(ROOT/"research_runners/xws_kyrill_original_netcdf_hazard_receipt_v0.py"
              ).read_text(encoding="utf-8")
        for marker in (
            '"source_coordinates_are_WGS84_lonlat": False',
            '"physical_original_grid_reprojected_to_WGS84": False',
            '"physical_historical_storm_count": 1',
            '"distinct_annual_events_inferred": False',
            '"German_GUL_IL_RI_run": False',
            '"Gross_Net_OEP_AEP_calibrated": False',
            '"source_raw_files_redistributed": False',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, code)


if __name__=="__main__":
    unittest.main()
