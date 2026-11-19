# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline OED footprint-area valuation: hypothetical values and source gates."""
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
import rva_nrw_hu22_geocoded_area_rebuild_tiv_v0 as m


FIELDS_LOC=["PortNumber","AccNumber","LocNumber","LocGroup","CountryCode",
            "Latitude","Longitude","BuildingTIV","OEDVersion"]
FIELDS_ACC=["PortNumber","AccNumber","PolNumber"]
FIELDS_EV=["LocNumber","KreisAGS2022","SourceOiSHA256","SourceGFK",
           "SourceFootprintAreaM2","SourcePhysicalCandidateNotInsuredSite"]


def csv_bytes(rows,fields):
    s=io.StringIO(newline="")
    w=csv.DictWriter(s,fieldnames=fields,lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return s.getvalue().encode("utf-8")


def make_input(path:Path,*,tamper_gfk=False,admit=False,source_sha=None,missing_hash=False):
    original=[
        {"PortNumber":"FICT","AccNumber":"FICT-1","LocNumber":"FICT-1","LocGroup":"KREIS-05111",
         "CountryCode":"DE","Latitude":"51.200001","Longitude":"6.900000",
         "BuildingTIV":"450000","OEDVersion":"5.0.0"},
        {"PortNumber":"FICT","AccNumber":"FICT-2","LocNumber":"FICT-2","LocGroup":"KREIS-05974",
         "CountryCode":"DE","Latitude":"51.450000","Longitude":"8.350000",
         "BuildingTIV":"450000","OEDVersion":"5.0.0"},
        {"PortNumber":"FICT","AccNumber":"FICT-3","LocNumber":"FICT-3","LocGroup":"KREIS-05111",
         "CountryCode":"DE","Latitude":"51.220000","Longitude":"6.950000",
         "BuildingTIV":"450000","OEDVersion":"5.0.0"},
    ]
    accounts=[{"PortNumber":"FICT","AccNumber":x["AccNumber"],"PolNumber":x["LocNumber"]} for x in original]
    areas=("100.50","120.00","80.25")
    evidence=[
        {"LocNumber":x["LocNumber"],"KreisAGS2022":x["LocGroup"][6:],
         "SourceOiSHA256":f"{index:064x}",
         "SourceGFK":"31001_2463" if tamper_gfk and index==1 else ("31001_1010" if index<3 else "31001_1100"),
         "SourceFootprintAreaM2":area,"SourcePhysicalCandidateNotInsuredSite":"true"}
        for index,(x,area) in enumerate(zip(original,areas),1)
    ]
    assets={
        "location.csv":csv_bytes(original,FIELDS_LOC),
        "account.csv":csv_bytes(accounts,FIELDS_ACC),
        "physical_candidate_evidence.csv":csv_bytes(evidence,FIELDS_EV),
    }
    receipt={
        "schema":"RVA_NRW_2022_HU_STRATIFIED_PHYSICAL_CANDIDATES_GEO_OED_V0",
        "status":"GEOCODED_FICTIONAL_INSURANCE_NOT_MODEL_ADMITTED",
        "source_original_2022_HU_full_CRCs_verified":True,
        "source_original_2022_HU_complete_archive_SHA256":source_sha or m.EXPECTED_ORIGINAL_SHA256,
        "physical_building_candidates_selected":3,
        "real_source_counties_represented":2,
        "fictional_policy_count":3,
        "model_input_approved":bool(admit),
        "insurer_building_TIV_observed":False,
        "physical_building_footprints_are_actual_RV_insured_sites":False,
        "output_file_SHA256":{name:hashlib.sha256(b).hexdigest() for name,b in assets.items()},
    }
    if missing_hash:
        del receipt["output_file_SHA256"]["location.csv"]
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for name,content in assets.items():
            z.writestr(name,content)
        z.writestr("manifest.json",json.dumps(receipt,sort_keys=True))


class TestFootprintRebuildSensitivities(unittest.TestCase):
    def test_three_tiv_scenarios_preserve_site_policy_coordinates_and_checksums(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_KREISE",2):
            root=Path(t)
            source=root/"source.zip"
            make_input(source)
            dst=root/"tiv.zip"
            receipt=m.build(source,dst)
            self.assertEqual(receipt["fictional_policy_count"],3)
            self.assertFalse(receipt["actual_RV_locations_observed"])
            self.assertFalse(receipt["floor_area_or_storeys_observed"])
            self.assertFalse(receipt["native_German_Oasis_GUL_IL_RI_OEP_AEP"])
            expected={
                "low_single_storey_1800_eur_per_m2":541350,
                "central_two_storeys_2200_eur_per_m2":1323300,
                "high_three_storeys_3000_eur_per_m2":2706750,
            }
            with zipfile.ZipFile(dst) as z,zipfile.ZipFile(source) as orig:
                self.assertIsNone(z.testzip())
                self.assertEqual(z.read("physical_candidate_evidence.csv"),orig.read("physical_candidate_evidence.csv"))
                accounts=set()
                locations=set()
                for key,total in expected.items():
                    self.assertEqual(receipt["scenario_case_results"][key]["synthetic_total_building_TIV_eur"],total)
                    manifest=json.loads(z.read(key+"/manifest.json"))
                    self.assertFalse(manifest["actual_insurer_building_TIV_or_policy_known"])
                    self.assertFalse(manifest["model_run_approved"])
                    for filename in ("location.csv","account.csv"):
                        self.assertEqual(hashlib.sha256(z.read(key+"/"+filename)).hexdigest(),
                                         manifest["output_SHA256"][filename])
                    rowlist=list(csv.DictReader(io.StringIO(z.read(key+"/location.csv").decode())))
                    account=z.read(key+"/account.csv")
                    self.assertEqual(len(rowlist),3)
                    self.assertEqual(sum(int(r["BuildingTIV"]) for r in rowlist),total)
                    locations.add(tuple((r["LocNumber"],r["Latitude"],r["Longitude"],r["LocGroup"]) for r in rowlist))
                    accounts.add(account)
                self.assertEqual(len(locations),1)
                self.assertEqual(len(accounts),1)

    def test_fail_closed_on_bad_residential_class_or_company_admission(self):
        for kw in ({"tamper_gfk":True},{"admit":True}):
            with tempfile.TemporaryDirectory() as t,patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_KREISE",2):
                source=Path(t)/"source.zip"
                make_input(source,**kw)
                out=Path(t)/"out.zip"
                with self.assertRaises(ValueError):
                    m.build(source,out)
                self.assertFalse(out.exists())

    def test_well_formed_but_unpinned_original_archive_is_rejected(self):
        # A self-consistent fake ZIP and hashes cannot replace the actual
        # pinned public HU2022 whole-archive identity.
        with tempfile.TemporaryDirectory() as t,patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_KREISE",2):
            source=Path(t)/"other-source.zip"
            make_input(source,source_sha="a"*64)
            output=Path(t)/"must_not_exist.zip"
            with self.assertRaisesRegex(ValueError,"source original full SHA/CRC"):
                m.build(source,output)
            self.assertFalse(output.exists())

    def test_missing_csv_hash_is_rejected_even_when_others_match(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_KREISE",2):
            source=Path(t)/"incomplete-receipt.zip"
            make_input(source,missing_hash=True)
            output=Path(t)/"must_not_exist.zip"
            with self.assertRaisesRegex(ValueError,"all three source OED CSV"):
                m.build(source,output)
            self.assertFalse(output.exists())

    def test_symlink_source_zip_is_rejected(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_KREISE",2):
            root=Path(t)
            source=root/"real.zip"
            make_input(source)
            link=root/"alias.zip"
            link.symlink_to(source)
            output=root/"must_not_exist.zip"
            with self.assertRaisesRegex(ValueError,"bounded existing file"):
                m.build(link,output)
            self.assertFalse(output.exists())

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t,patch.object(m,"EXPECTED_N",3),patch.object(m,"EXPECTED_KREISE",2):
            source=Path(t)/"source.zip"
            make_input(source)
            out=Path(t)/"existing.zip"
            out.write_bytes(b"unchanged")
            with self.assertRaises(ValueError):
                m.build(source,out)
            self.assertEqual(out.read_bytes(),b"unchanged")


if __name__=="__main__":
    unittest.main()
