# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict source provenance and NextGen C3S spatial grid contract on fake OED."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_nrw_hu22_to_nextgen_c3s_spatial_v0 import (
    build,write_zip,CrosswalkBlocked,SOURCE_SCHEMA,SOURCE_SHA,OUTPUT_SCHEMA,GRID_SCHEMA
)


def demo_grid():
    return {
        "schema":GRID_SCHEMA,
        "spatial_status":"INVENTED_RECTANGULAR_GRID_NOT_AUTHENTICATED_C3S",
        "grid":{
            "grid_id":"SYNTH-NRW-025DEG-NOT-C3S",
            "west_lon_e6":5_500_000,"south_lat_e6":50_000_000,
            "width_e6":250000,"height_e6":250000,
            "num_lon":20,"num_lat":13,"crs":"EPSG:4326",
        },
    }


def _csv(rows,headers):
    s=io.StringIO(newline="")
    writer=csv.DictWriter(s,fieldnames=headers,lineterminator="\n")
    writer.writeheader();writer.writerows(rows)
    return s.getvalue().encode()


def make_source(path,*,invalid_gfk=False,invalid_geo=False,invalid_source=False,duplicate_oi=False):
    locations=[
        {"PortNumber":"FICT","AccNumber":"FAKE-01","LocNumber":"FAKE-01",
         "LocGroup":"KREIS-05362","CountryCode":"DE","Latitude":"50.8043820",
         "Longitude":"7.0203810","BuildingTIV":"450000","LocPerilsCovered":"WW2","OEDVersion":"5.0.0"},
        {"PortNumber":"FICT","AccNumber":"FAKE-02","LocNumber":"FAKE-02",
         "LocGroup":"KREIS-05974","CountryCode":"DE","Latitude":"51.4533770",
         "Longitude":"8.3780070","BuildingTIV":"1000000","LocPerilsCovered":"WW2","OEDVersion":"5.0.0"},
        {"PortNumber":"FICT","AccNumber":"FAKE-03","LocNumber":"FAKE-03",
         "LocGroup":"KREIS-05774","CountryCode":"DE","Latitude":"51.5194380",
         "Longitude":"8.6589740","BuildingTIV":"150000","LocPerilsCovered":"WW2","OEDVersion":"5.0.0"},
    ]
    if invalid_geo:locations[0]["Longitude"]="5.5000000"
    accounts=[{"PortNumber":"FICT","AccNumber":r["AccNumber"],"PolNumber":r["AccNumber"]} for r in locations]
    evidence=[
        {"LocNumber":r["LocNumber"],"KreisAGS2022":r["LocGroup"][6:],
         "SourceOiSHA256":("0" if duplicate_oi else str(i))*64,
         "SourceGFK":("31001_2463" if invalid_gfk and i==1 else ("31001_1010" if i!=3 else "31001_1222")),
         "SourceFootprintAreaM2":"90.25","SourcePhysicalCandidateNotInsuredSite":"true"}
        for i,r in enumerate(locations,1)
    ]
    blobs={
        "location.csv":_csv(locations,list(locations[0])),
        "account.csv":_csv(accounts,list(accounts[0])),
        "physical_candidate_evidence.csv":_csv(evidence,list(evidence[0])),
    }
    info={
        "schema":SOURCE_SCHEMA,"status":"GEOCODED_FICTIONAL_INSURANCE_NOT_MODEL_ADMITTED",
        "source_original_2022_HU_complete_archive_SHA256":SOURCE_SHA if not invalid_source else "a"*64,
        "source_original_2022_HU_full_CRCs_verified":True,
        "physical_building_candidates_selected":3,"fictional_policy_count":3,
        "real_source_counties_represented":3,
        "model_input_approved":False,"insurer_building_TIV_observed":False,
        "physical_building_footprints_are_actual_RV_insured_sites":False,
        "output_file_SHA256":{k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()},
    }
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in blobs.items():z.writestr(name,data)
        z.writestr("manifest.json",json.dumps(info,sort_keys=True))


class TestNextGenC3SSpatialHandoff(unittest.TestCase):
    def test_three_physical_points_project_to_stable_0p25_grid_no_real_wind(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"fictional_source.zip"
            make_source(src)
            result=build(src,demo_grid(),expected_sites=3,expected_counties=3)
            receipt=result["receipt"]
            self.assertEqual(receipt["schema"],OUTPUT_SCHEMA)
            self.assertEqual(receipt["source_physical_synthetic_OED_count"],3)
            self.assertEqual(receipt["synthetic_source_building_TIV_eur"],1600000)
            self.assertEqual(receipt["original_NRW_counties"],3)
            self.assertFalse(receipt["actual_C3S_NetCDF_original_bytes_authenticated"])
            self.assertFalse(receipt["wind_damage_probability_law_supplied"])
            self.assertFalse(receipt["gross_insured_net_reinsurance_or_EP_executed"])
            self.assertTrue(receipt["grid_is_fictional_not_C3S_NetCDF"])
            handoff=result["handoff"]
            self.assertEqual(set(handoff),{"grid","crosswalk_assignments","insured_asset_values"})
            self.assertEqual(len(handoff["crosswalk_assignments"]),3)
            self.assertEqual(len(handoff["insured_asset_values"]),3)
            self.assertTrue(all(x["taxonomy"].startswith("UNMAPPED_HU22_GFK_")
                                for x in handoff["crosswalk_assignments"]))
            self.assertTrue(all(x["cedant_id"].startswith("FICTITIOUS_")
                                for x in handoff["crosswalk_assignments"]))
            self.assertEqual({v["asset_id"] for v in handoff["insured_asset_values"]},
                             {v["asset_id"] for v in handoff["crosswalk_assignments"]})
            for x in handoff["crosswalk_assignments"]:
                grid=handoff["grid"]
                self.assertEqual(x["col"],(x["lon_e6"]-grid["west_lon_e6"])//250000)
                self.assertEqual(x["row"],(x["lat_e6"]-grid["south_lat_e6"])//250000)
                self.assertEqual(x["cell_id"],f"{grid['grid_id']}:x{x['col']:05d}:y{x['row']:05d}")
            out=Path(d)/"handoff.zip"
            written=write_zip(result,out)
            with zipfile.ZipFile(out) as z:
                self.assertIsNone(z.testzip())
                data=z.read("nextgen_c3s_spatial_handoff.json")
                self.assertEqual(hashlib.sha256(data).hexdigest(),written["handoff_json_sha256"])
                self.assertEqual(json.loads(data),handoff)
            with self.assertRaises(CrosswalkBlocked):
                write_zip(result,out)

    def test_no_implicit_provider_grid_or_calibrated_vulnerability_admission(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"source.zip";make_source(p)
            for spec in (
                dict(demo_grid(),spatial_status="AUTHENTICATED_C3S"),
                dict(demo_grid(),schema="NEXTGEN_VERIFIED_C3S"),
                dict(demo_grid(),grid=dict(demo_grid()["grid"],crs="EPSG:4647")),
                dict(demo_grid(),grid=dict(demo_grid()["grid"],grid_id="REAL-C3S-WIND")),
                dict(demo_grid(),grid=dict(demo_grid()["grid"],width_e6=16000)),
                dict(demo_grid(),grid=dict(demo_grid()["grid"],num_lon=1)),
                dict(demo_grid(),grid=dict(demo_grid()["grid"],west_lon_e6=9_000_000)),
            ):
                with self.subTest(spec=spec),self.assertRaises(CrosswalkBlocked):
                    build(p,spec,expected_sites=3,expected_counties=3)

    def test_invalid_source_rights_location_gfk_dedup_or_boundary_fail_closed(self):
        for kwargs in (
            {"invalid_gfk":True},
            {"invalid_geo":True},
            {"invalid_source":True},
            {"duplicate_oi":True},
        ):
            with self.subTest(kwargs=kwargs),tempfile.TemporaryDirectory() as d:
                p=Path(d)/"source.zip";make_source(p,**kwargs)
                with self.assertRaises(CrosswalkBlocked):
                    build(p,demo_grid(),expected_sites=3,expected_counties=3)


if __name__=="__main__":
    unittest.main()
