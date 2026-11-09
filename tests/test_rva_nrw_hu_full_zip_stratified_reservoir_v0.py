# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline tiny invented SHP/DBF fixtures for strict 11m-record streaming prototype."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_nrw_hu_full_zip_stratified_reservoir_v0 import (
    sample_hu_stream, sample_full_official_zip, SourceBlocked,sha256_regular_file
)
from rva_nrw_hu22_full_source_to_fictional_oed_v0 import (
    build_geocoded_oed
)


def fake_source():
    records=(
        ("05362001","DENW000000000001","31001_1010"),
        ("05362002","DENW000000000002","31001_1222"),
        ("05362003","DENW000000000003","31002_1010"),
        ("05974001","DENW000000000004","31001_1100"),
        ("05974002","DENW000000000005","31001_2460"),
        ("05974003","DENW000000000006","31001_1024"),
    )
    header=bytearray(100)
    struct.pack_into(">I",header,0,9994)
    struct.pack_into("<I",header,28,1000)
    struct.pack_into("<I",header,32,5)
    chunks=[bytes(header)]
    d=bytearray(161)
    struct.pack_into("<I",d,4,len(records))
    struct.pack_into("<H",d,8,161)
    struct.pack_into("<H",d,10,46)
    d[160]=13
    for index,(ags,oi,gfk) in enumerate(records,1):
        base=32280450.+index*100
        top=5578000.+index*100
        ring=[(base,top),(base+60,top),(base+60,top+70),(base,top+70),(base,top)]
        payload=(struct.pack("<I",5)+struct.pack("<dddd",base,top,base+60,top+70)+
                 struct.pack("<II",1,len(ring))+struct.pack("<I",0)+
                 b"".join(struct.pack("<dd",x,y) for x,y in ring))
        assert len(payload)%2==0
        chunks.append(struct.pack(">II",index,len(payload)//2)+payload)
        data=b" "+ags.encode()+oi.encode().ljust(17,b" ")+gfk.encode()+b"2022-01-01"
        assert len(data)==46
        d.extend(data)
    d.extend(b"\x1a")
    return b"".join(chunks),bytes(d),len(records)


def base_oed(directory):
    directory.mkdir()
    with (directory/"location.csv").open("w",encoding="utf8",newline="") as f:
        fields=("PortNumber","AccNumber","LocNumber","LocGroup","CountryCode",
                "Latitude","Longitude","BuildingTIV","OEDVersion","LocPerilsCovered")
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for index,county in enumerate(("05362","05974"),1):
            key=f"SYN-NRW-{county}-{index:06}"
            w.writerow({"PortNumber":"TEST","AccNumber":key,"LocNumber":key,
                "LocGroup":"KREIS-"+county,"CountryCode":"DE","Latitude":"",
                "Longitude":"","BuildingTIV":"450000","OEDVersion":"5.0.0",
                "LocPerilsCovered":"WW2"})
    with (directory/"account.csv").open("w",encoding="utf8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=("PortNumber","AccNumber","PolNumber"))
        w.writeheader()
        for index,county in enumerate(("05362","05974"),1):
            key=f"SYN-NRW-{county}-{index:06}"
            w.writerow({"PortNumber":"TEST","AccNumber":key,"PolNumber":key})


class SyntheticFixtureTransformer:
    """Offline geometric fixture only; never a tested EPSG:4647 projection.

    The actual EPSG:4647 -> EPSG:4326 transformation runs under the
    pinned GIS dependencies in the dedicated original-source workflow.
    """
    def transform(self, x: float, y: float) -> tuple[float, float]:
        if not (32_200_000 < x < 32_600_000 and 5_500_000 < y < 5_900_000):
            raise AssertionError("fictional projected source coordinate out of fixture range")
        return 7.5 + (x - 32_280_000) / 1_000_000, 51.2 + (y - 5_578_000) / 1_000_000


class TestOriginalFullSourceReservoir(unittest.TestCase):
    @unittest.skipUnless(
        importlib.util.find_spec("pyproj") is not None and importlib.util.find_spec("shapely") is not None,
        "pinned geospatial runtime is optional in generic repository CI")
    @patch("rva_nrw_hu_full_zip_stratified_reservoir_v0._pinned_transformer",
           return_value=SyntheticFixtureTransformer())
    def test_six_original_style_records_all_gfk_categories_and_two_counties(self, _fixture_crs):
        s,d,n=fake_source()
        target={"05362":1,"05974":1}
        selected,audit=sample_hu_stream(io.BytesIO(s),io.BytesIO(d),
            expected_count=n,shx_length=100+n*8,county_targets=target)
        self.assertEqual(set(selected),set(target))
        self.assertEqual(len(selected["05362"]),1)
        self.assertEqual(len(selected["05974"]),1)
        self.assertEqual(audit["original_shp_and_dbf_records_scanned"],n)
        self.assertEqual(audit["source_gfk_and_schema_quarantine_counts"]["gfk_residential_function_candidate_only"],3)
        self.assertEqual(audit["source_gfk_and_schema_quarantine_counts"]["gfk_non_building_object_quarantine"],1)
        self.assertEqual(audit["source_gfk_and_schema_quarantine_counts"]["gfk_special_occupancy_quarantine"],1)
        self.assertEqual(audit["source_gfk_and_schema_quarantine_counts"]["gfk_known_nonresidential_example"],1)
        self.assertEqual(audit["source_residential_function_candidates_by_Kreis"],{"05362":2,"05974":1})
        self.assertEqual(audit["selected_source_physical_candidate_count"],2)
        self.assertTrue(all(site["source_gfk"].startswith("31001_") for s in selected.values() for site in s))
        self.assertEqual(selected, sample_hu_stream(io.BytesIO(s),io.BytesIO(d),
            expected_count=n,shx_length=100+n*8,county_targets=target)[0])

    def test_invalid_count_and_unsupported_counties_fail(self):
        s,d,n=fake_source()
        with self.assertRaises(SourceBlocked):
            sample_hu_stream(io.BytesIO(s),io.BytesIO(d),
                expected_count=n+1,shx_length=100+n*8,county_targets={"05362":1})
        for target in ({"99999":1},{"05362":0},{"05362":10001},{}):
            with self.assertRaises(SourceBlocked):
                sample_hu_stream(io.BytesIO(s),io.BytesIO(d),
                    expected_count=n,shx_length=100+n*8,county_targets=target)

    @unittest.skipUnless(
        importlib.util.find_spec("pyproj") is not None and importlib.util.find_spec("shapely") is not None,
        "pinned geospatial runtime is optional in generic repository CI")
    @patch("rva_nrw_hu_full_zip_stratified_reservoir_v0._pinned_transformer",
           return_value=SyntheticFixtureTransformer())
    def test_mock_real_geometry_join_preserves_fictional_insurance_identity(self, _fixture_crs):
        s,d,n=fake_source()
        selected,audit=sample_hu_stream(io.BytesIO(s),io.BytesIO(d),
            expected_count=n,shx_length=100+n*8,county_targets={"05362":1,"05974":1})
        audit["full_original_source_zip_sha256"]="f"*64
        audit["all_four_original_member_CRCs_verified_by_ZipExtFile_EOF"]=True
        with tempfile.TemporaryDirectory() as t:
            parent=Path(t)
            base=parent/"fake_nrw_oed"
            base_oed(base)
            output=parent/"result"
            manifest=build_geocoded_oed(base,selected,audit,output,expected_count=2)
            self.assertEqual(manifest["fictional_policy_count"],2)
            self.assertFalse(manifest["physical_building_footprints_are_actual_RV_insured_sites"])
            self.assertTrue(manifest["source_original_2022_HU_full_CRCs_verified"])
            with (output/"location.csv").open(newline="",encoding="utf8") as f:
                loc=list(csv.DictReader(f))
            self.assertEqual(len(loc),2)
            self.assertEqual(sum(int(x["BuildingTIV"]) for x in loc),900000)
            self.assertEqual({x["LocGroup"] for x in loc},{"KREIS-05362","KREIS-05974"})
            self.assertTrue(all(float(x["Latitude"])>50 and float(x["Longitude"])>5 for x in loc))
            with (output/"physical_candidate_evidence.csv").open(newline="",encoding="utf8") as f:
                physical=list(csv.DictReader(f))
            self.assertEqual(len(physical),2)
            self.assertTrue(all(p["SourcePhysicalCandidateNotInsuredSite"]=="true" for p in physical))
            self.assertTrue(all(len(p["SourceOiSHA256"])==64 for p in physical))
            for filename,sha in manifest["output_file_SHA256"].items():
                self.assertEqual(hashlib.sha256((output/filename).read_bytes()).hexdigest(),sha)
            with self.assertRaises(SourceBlocked):
                build_geocoded_oed(base,selected,audit,output,expected_count=2)

    def test_source_sha_mismatch_blocks_before_any_zip_parse(self):
        # The local-original replay path must defend itself even if a caller
        # bypasses the guarded HTTP download and supplies a same-size archive.
        with patch("rva_nrw_hu_full_zip_stratified_reservoir_v0.sha256_regular_file",
                   return_value="0"*64), \
             patch("rva_nrw_hu_full_zip_stratified_reservoir_v0.zipfile.ZipFile") as opening:
            with self.assertRaisesRegex(SourceBlocked, "SHA256 identity drift"):
                sample_full_official_zip(Path("not-opened.zip"), {"05362": 1})
            opening.assert_not_called()

    def test_original_zip_regular_file_expected_full_size(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"original.zip"
            p.write_bytes(b"fake source example")
            self.assertEqual(sha256_regular_file(p,expected_size=19),
                             hashlib.sha256(b"fake source example").hexdigest())
            with self.assertRaises(SourceBlocked):
                sha256_regular_file(p,expected_size=901092946)


if __name__=="__main__":
    unittest.main()
