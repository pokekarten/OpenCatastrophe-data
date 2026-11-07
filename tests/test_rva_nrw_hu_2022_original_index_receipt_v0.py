# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-listing security, vintage and provenance tests."""
import io
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_nrw_hu_2022_original_index_receipt_v0 import (
    validate_official_index,fetch_index,ListingBlocked,MAX_HTML,URL,ZIP_URL
)

def html(*,href="2022_hu_EPSG4647_Shape.zip",size="859.3 MB",
         license="Datenlizenz Deutschland - Zero - Version 2.0",crs="EPSG 4647"):
    return f"""<!DOCTYPE html><html><title>Historische Hausumringe</title>
    <body><p>Historical publisher original metadata {license}, Koordinatenreferenzsystem:
    {crs}, source release year 2022</p><table><tr><td>
    <a href="{href}">2022_hu_EPSG4647_Shape.zip</a></td><td>{size}</td>
    </tr></table></body></html>""".encode("utf-8")

class DummyResponse:
    def __init__(self,content,status=200,ctype="text/html",url=URL,length=None):
        self.content=content
        self.status=status
        self.headers={"Content-Type":ctype}
        if length is not None:self.headers["Content-Length"]=str(length)
        self.url=url
    def geturl(self):return self.url
    def read(self,n):return self.content[:n]
    def __enter__(self):return self
    def __exit__(self,*args):pass

class TestHUIndex(unittest.TestCase):
    def test_accept_only_exact_source_and_fail_closed_admission(self):
        result=validate_official_index(html())
        self.assertEqual(result["source_year"],"2022")
        self.assertEqual(result["original_publisher_zip_url"],ZIP_URL)
        self.assertEqual(result["original_source_spatial_reference_declared"],"EPSG:4647")
        for key in ("original_zip_full_bytes_acquired","original_zip_sha256_verified",
                    "source_spatial_reference_transformed_to_EPSG4326",
                    "2022_house_outlines_are_RV_insured_risk_sites",
                    "original_source_approved_for_German_Oasis_GUL"):
            self.assertIs(result[key],False)

    def test_provider_size_license_crs_link_and_document_mutations_rejected(self):
        invalid=(
            html(size="50 KB"),html(license="CC0"),html(crs="EPSG 4326"),
            html(href="https://evil.example.com/2022_hu_EPSG4647_Shape.zip"),
            html(href="../2022_hu_EPSG4647_Shape.zip"),
            html(href="2022_hu_EPSG4647_Shape.zip?token=abc"),
            html(href="2022_hu_EPSG4647_Shape.zip#frag"),
            html().replace(b"Historische Hausumringe",b"Another listing"),
            html()+html(),
            b"\xff"*130,
            b"0"*(MAX_HTML+1),
        )
        for value in invalid:
            with self.subTest(size=len(value),prefix=value[:55]):
                with self.assertRaises(ListingBlocked):
                    validate_official_index(value)

    def test_live_client_only_reads_at_most_bound_and_does_not_request_zip(self):
        recorded=[]
        def fake_open(req,timeout):
            recorded.append((req.full_url,req.get_method(),timeout))
            return DummyResponse(html(),length=len(html()))
        value=fetch_index(urlopen_=fake_open)
        self.assertEqual(value["original_index_full_bytes"],len(html()))
        self.assertEqual(recorded,[(URL,"GET",20)])
        with self.assertRaises(ListingBlocked):
            fetch_index(urlopen_=lambda req,timeout:DummyResponse(html(),status=206))
        with self.assertRaises(ListingBlocked):
            fetch_index(urlopen_=lambda req,timeout:DummyResponse(html(),length=MAX_HTML+1))
        with self.assertRaises(ListingBlocked):
            fetch_index(urlopen_=lambda req,timeout:DummyResponse(html(),ctype="application/zip"))

if __name__=="__main__":
    unittest.main()
