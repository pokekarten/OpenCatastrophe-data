# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline negative-source-fixture tests for authentic XWS original-CSV gate."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import xws_daria_1990_original_csv_preflight_v0 as source


def fixture(n=1000):
    grid = "Grid number,Longitude,Latitude\n" + "".join(
        f"{i},{-10+(i%40)*0.2:.3f},{40+(i//40)*0.2:.3f}\n" for i in range(n))
    speeds = {}
    for name,wind in (("daria_lower95","10.0"),("daria_mean","20.0"),
                      ("daria_upper95","30.0")):
        speeds[name] = "".join(f"{i},{wind}\n" for i in range(n))
    return {k:v.encode() for k,v in dict(grid=grid,**speeds).items()}


class DummyResponse:
    def __init__(self,body,*,length=None,status=200,url=None):
        self.status=status
        self.url=url
        self.headers={"Content-Length":str(length)} if length is not None else {}
        self.body=body
    def geturl(self):
        return self.url
    def read(self,lim):
        return self.body[:lim]
    def __enter__(self):
        return self
    def __exit__(self,*args):
        pass


class TestOriginalXWSDaria(unittest.TestCase):
    def test_original_csv_bytes_and_exact_grid_event_variant_alignment(self):
        f=fixture()
        receipt=source.validate_original_bundle(f)
        self.assertEqual(receipt["schema"],source.SCHEMA)
        self.assertEqual(receipt["source_grid_original_points"],1000)
        self.assertEqual(len(receipt["original_files"]),4)
        self.assertEqual(receipt["wind_gust_unit"],"m/s")
        self.assertEqual(receipt["source_license"],"CC-BY-4.0")
        self.assertFalse(receipt["full_Germany_modelled_GUL_IL_RI_OEP_AEP"])
        self.assertFalse(receipt["original_XWS_storms_are_complete_unbiased_annual_event_catalogue"])
        self.assertEqual(receipt["three_uncertainty_variants"]["daria_mean"]["wind_gust_mps_min"],"20.0")
        self.assertEqual(receipt["three_uncertainty_variants"]["daria_upper95"]["points_ge_25_mps"],1000)

    def test_bad_original_row_grid_loss_lineage_or_units_block(self):
        for key,blob in (
            ("grid",b"no-grid"),
            ("grid",fixture()["grid"].replace(b"Grid number,Longitude,Latitude",
                                              b"Grid,Longitude,Latitude")),
            ("grid",fixture()["grid"].replace(b"0,-10.000",b"1,-10.000",1)),
            ("daria_mean",fixture()["daria_mean"].replace(b"5,20.0",b"5,-999.0",1)),
            ("daria_mean",fixture()["daria_mean"].replace(b"5,20.0",b"5,999.0",1)),
            ("daria_mean",fixture()["daria_mean"].replace(b"4,20.0",b"4,NaN",1)),
            ("daria_mean",fixture()["daria_mean"].replace(b"2,20.0",b"2,40.0",1)),
            ("daria_upper95",fixture()["daria_upper95"].replace(b"7,30.0",b"7,5.0",1)),
            ("daria_lower95",fixture()["daria_lower95"].rsplit(b"\n",2)[0]+b"\n"),
        ):
            with self.subTest(key=key,first=blob[:35]):
                f=fixture()
                f[key]=blob
                with self.assertRaises(source.XWSSourceBlocked):
                    source.validate_original_bundle(f)
        with self.assertRaises(source.XWSSourceBlocked):
            source.validate_original_bundle({"daria_mean":fixture()["daria_mean"]})

    def test_exact_public_urls_and_bounded_fully_read_get(self):
        f=fixture()
        visited=[]
        by_url={url:f[key] for key,url in source.ORIGINAL_URLS.items()}
        def fake(req,timeout):
            visited.append((req.full_url,req.get_method(),timeout))
            b=by_url[req.full_url]
            return DummyResponse(b,length=len(b),url=req.full_url)
        actual=source.download_official_original(opener=fake)
        self.assertEqual(actual,f)
        self.assertEqual([x[0] for x in visited],list(source.ORIGINAL_URLS.values()))
        self.assertTrue(all(x[1:] == ("GET",40) for x in visited))
        with self.assertRaises(source.XWSSourceBlocked):
            source.download_official_original(opener=lambda req,timeout:
                DummyResponse(f["grid"],length=source.MAX_SOURCE_BYTES+1,url=req.full_url))
        with self.assertRaises(source.XWSSourceBlocked):
            source.download_official_original(opener=lambda req,timeout:
                DummyResponse(f["grid"],length=len(f["grid"]),status=206,url=req.full_url))
        with self.assertRaises(source.XWSSourceBlocked):
            source.download_official_original(opener=lambda req,timeout:
                DummyResponse(f["grid"],length=len(f["grid"]),url="https://evil.example/data.csv"))


if __name__=="__main__":
    unittest.main()
