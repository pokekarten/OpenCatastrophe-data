# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline 1990 source-variant 3-second gust to 2022 public NRW OED handoracle."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import rva_nrw_xws_daria_10k_original_gust_overlay_v0 as overlay
from rva_nrw_hu22_to_nextgen_c3s_spatial_v0 import SOURCE_SHA,SOURCE_SCHEMA


def csv_bytes(rows,fields):
    f=io.StringIO(newline="")
    w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
    w.writeheader();w.writerows(rows)
    return f.getvalue().encode()


def fake_nrw_oed(path:Path,*,wrong_gfk=False):
    sites=[
        ("SYN-NRW-05362-01-000001","05362","50.8043820","7.0203810",100000),
        ("SYN-NRW-05974-01-000001","05974","51.4533770","8.3780070",200000),
        ("SYN-NRW-05774-01-000001","05774","51.5194380","8.6589740",300000),
    ]
    locations=[{
        "PortNumber":"FAKE","AccNumber":a,"LocNumber":a,
        "LocGroup":"KREIS-"+c,"CountryCode":"DE","OEDVersion":"5.0.0",
        "LocPerilsCovered":"WW2","BuildingTIV":str(t),"Latitude":lat,"Longitude":lon
    } for a,c,lat,lon,t in sites]
    acc=[{"AccNumber":a,"PolNumber":a,"PortNumber":"FAKE"} for a,*_ in sites]
    ev=[{
        "LocNumber":a,"KreisAGS2022":c,
        "SourceOiSHA256":hashlib.sha256(a.encode()).hexdigest(),
        "SourceGFK":"31001_2463" if wrong_gfk and i==0 else "31001_1010",
        "SourceFootprintAreaM2":"110.00",
        "SourcePhysicalCandidateNotInsuredSite":"true",
    } for i,(a,c,*_) in enumerate(sites)]
    inputs={
        "location.csv":csv_bytes(locations,list(locations[0])),
        "account.csv":csv_bytes(acc,list(acc[0])),
        "physical_candidate_evidence.csv":csv_bytes(ev,list(ev[0])),
    }
    manifest={
        "schema":SOURCE_SCHEMA,
        "status":"GEOCODED_FICTIONAL_INSURANCE_NOT_MODEL_ADMITTED",
        "source_original_2022_HU_complete_archive_SHA256":SOURCE_SHA,
        "source_original_2022_HU_full_CRCs_verified":True,
        "physical_building_candidates_selected":3,
        "real_source_counties_represented":3,
        "fictional_policy_count":3,
        "model_input_approved":False,
        "insurer_building_TIV_observed":False,
        "physical_building_footprints_are_actual_RV_insured_sites":False,
        "output_file_SHA256":{k:hashlib.sha256(v).hexdigest() for k,v in inputs.items()},
    }
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in inputs.items():z.writestr(name,data)
        z.writestr("manifest.json",json.dumps(manifest))


def fake_xws_source(*,inverted=False, missing=False):
    n=1000
    points=[(7.020,50.804),(8.378,51.453),(8.659,51.519)]
    points.extend((-25+(i%30)*.1,35+(i//30)*.1) for i in range(n-3))
    grid=("Grid number,Longitude,Latitde\n"+
          "".join(f"{i},{lon:.3f},{lat:.3f}\n" for i,(lon,lat) in enumerate(points))).encode()
    source={"grid":grid}
    for name,field in (("daria_lower95",[10,20,30]),
                       ("daria_mean",[15,25,35]),
                       ("daria_upper95",[20,30,40])):
        values=field+[10]*(n-3)
        if inverted and name=="daria_upper95":values[1]=21
        if missing and name=="daria_mean":values.pop()
        source[name]="".join(f"{i},{s}.000\n" for i,s in enumerate(values)).encode()
    return source


class TestXWSDariaOriginalGustOverlay(unittest.TestCase):
    def setUp(self):
        # The real 28,124-grid four original Daria file SHA-256s are frozen in
        # production. Invented microfixture hashes are test-only scope changes.
        src=fake_xws_source()
        mocked={name:(len(blob),hashlib.sha256(blob).hexdigest())
                for name,blob in src.items()}
        self.fake_source_pin=patch.object(overlay,"PINNED_SOURCE_FILES",mocked)
        self.fake_source_pin.start()
        self.addCleanup(self.fake_source_pin.stop)

    def test_original_historical_gust_on_toy_public_geocodes_no_loss(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/"nrw.zip";out=root/"hazard.zip"
            fake_nrw_oed(source)
            result=overlay.overlay(fake_xws_source(),source,
                                   expected_sites=3,expected_counties=3,expected_tiv=600000)
            lines=result["site_rows"]
            receipt=result["receipt"]
            self.assertEqual(len(lines),3)
            self.assertEqual(receipt["source_physical_building_site_count"],3)
            self.assertEqual(receipt["source_2022_NRW_Kreise_count"],3)
            self.assertEqual(receipt["unique_nearest_original_XWS_source_grid_points"],3)
            self.assertEqual(receipt["fictional_building_TIV_eur"],600000)
            self.assertEqual(receipt["fictional_buildings_with_mean_wind_ge25_mps"],2)
            self.assertEqual(receipt["fictional_TIV_exposed_to_mean_wind_ge25_mps_eur"],500000)
            self.assertFalse(receipt["native_Oasis_or_NextGen_GUL_IL_RI_OEP_AEP_executed"])
            self.assertFalse(receipt["German_wind_vulnerability_by_material_roof_construction_validated"])
            self.assertEqual([int(x["XWS1990DariaNearestSourceGridId"]) for x in lines],[0,1,2])
            self.assertEqual([x["Daria1990MeanGustMps"] for x in lines],
                             ["15.000","25.000","35.000"])
            self.assertTrue(all(float(x["NearestXWSGridPointKm"])<0.08 for x in lines))
            saved=overlay.write_zip(out,result)
            with zipfile.ZipFile(out) as z:
                self.assertIsNone(z.testzip())
                for filename,sha in saved["output_sha256"].items():
                    self.assertEqual(hashlib.sha256(z.read(filename)).hexdigest(),sha)
                rows=list(csv.DictReader(io.StringIO(z.read(
                    "daria_1990_original_source_site_gust_only.csv").decode())))
                self.assertEqual(len(rows),3)
                self.assertTrue(all(x["ActualRVInsuredSiteObserved"]=="false" for x in rows))

    def test_changed_source_values_wrong_geography_gfk_and_annual_admission_blocked(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"nrw.zip";fake_nrw_oed(p)
            for data in (fake_xws_source(inverted=True),fake_xws_source(missing=True)):
                with self.assertRaises((overlay.XWSSourceBlocked,overlay.OverlayBlocked)):
                    overlay.overlay(data,p,expected_sites=3,expected_counties=3,expected_tiv=600000)
            with self.assertRaises(overlay.OverlayBlocked):
                overlay.overlay(fake_xws_source(),p,expected_sites=3,
                                expected_counties=3,expected_tiv=600001)
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"bad.zip";fake_nrw_oed(p,wrong_gfk=True)
            with self.assertRaises(overlay.OverlayBlocked):
                overlay.overlay(fake_xws_source(),p,expected_sites=3,
                                expected_counties=3,expected_tiv=600000)

    def test_nearest_original_geographic_sphere_with_max_distance(self):
        grid={0:(overlay.Decimal("7.020"),overlay.Decimal("50.804")),
              1:(overlay.Decimal("8.378"),overlay.Decimal("51.453"))}
        b=overlay._nearest_index(grid)
        self.assertEqual(overlay._match(7.020381,50.804382,b)[0],0)
        self.assertEqual(overlay._match(8.378007,51.453377,b)[0],1)
        with self.assertRaises(overlay.OverlayBlocked):
            overlay._match(0.0,0.0,b)


if __name__=="__main__":
    unittest.main()
