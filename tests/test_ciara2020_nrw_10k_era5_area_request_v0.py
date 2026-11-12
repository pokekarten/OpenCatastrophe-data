# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline source-identity and exact 0.25-degree ERA5 NRW coverage challenges."""
from __future__ import annotations

from copy import deepcopy
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_runners"))
import ciara2020_nrw_10k_era5_area_request_v0 as area


def three():
    sites = [
        ("SYN-NRW-05111-01", "05111", "51.11", "6.62", 100000),
        ("SYN-NRW-05111-02", "05111", "51.22", "6.81", 200000),
        ("SYN-NRW-05974-01", "05974", "51.14", "6.68", 300000),
    ]
    location = [
        dict(LocNumber=ident, AccNumber=ident, LocGroup="KREIS-"+county,
             CountryCode="DE", OEDVersion="5.0.0", LocCurrency="EUR",
             LocPerilsCovered="WW2", BuildingTIV=str(tiv),
             Latitude=lat, Longitude=lon)
        for ident,county,lat,lon,tiv in sites
    ]
    account = [dict(AccNumber=ident,PolNumber=ident,OEDVersion="5.0.0")
               for ident,*_ in sites]
    evidence = [
        dict(LocNumber=ident, KreisAGS2022=county,
             SourcePhysicalCandidateNotInsuredSite="true",
             SourceGFK="31001_1010",
             SourceOiSHA256=f"{i+1:064x}")
        for i,(ident,county,*_) in enumerate(sites)
    ]
    return location, account, evidence


def small(rows):
    return area.build_area_plan(*rows,expected_sites=3,
                                expected_counties=2,expected_tiv=600000)


def csvbytes(rows):
    f = io.StringIO(newline="")
    writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return f.getvalue().encode()


class CiaraNRWAreaTests(unittest.TestCase):
    def test_exact_3_site_grid_bounds_and_clear_scientific_nonadmission(self):
        study = small(three())
        self.assertEqual(study["request"], {
            "variable": ["10m_wind_gust_since_previous_post_processing"],
            "date": ["2020-02-08", "2020-02-11"],
            "area": [51.25, 6.5, 51.0, 7.0],
            "data_format": "netcdf",
        })
        self.assertEqual(study["public_building_candidates"],3)
        self.assertEqual(study["source_2022_NRW_counties"],2)
        self.assertEqual(study["requested_atmospheric_grid_nodes_0p25deg"],6)
        self.assertEqual(study["occupied_grid_nodes_by_public_building_candidates"],2)
        self.assertEqual(study["maximum_requested_gridpoint_hours_if_all_nodes_returned"],576)
        self.assertFalse(study["original_CDS_source_data_acquired_or_attested"])
        self.assertFalse(study["CDS_data_licence_accepted_by_operator_verified"])
        self.assertFalse(study["German_wind_vulnerability_or_gross_net_EP_model_admitted"])
        self.assertFalse(study["request_executed"])
        self.assertNotIn("SYN-NRW-05111-01",json.dumps(study))
        self.assertEqual(len(study["occupied_nodes_count_sha256"]),64)

    def test_duplicate_and_crosswalk_drift_rejected(self):
        edits = (
            (0, "LocNumber", "SYN-NRW-05111-01"),
            (1, "AccNumber", "SYN-NRW-05111-01"),
            (2, "LocNumber", "SYN-NRW-05111-01"),
            (0, "AccNumber", "NONEXISTENT"),
            (1, "PolNumber", "OTHER-POLICY"),
            (2, "SourceOiSHA256", f"{1:064x}"),
        )
        for layer,field,value in edits:
            with self.subTest(layer=layer,field=field):
                docs=list(deepcopy(three()))
                docs[layer][1][field]=value
                with self.assertRaises(area.CiaraAreaBlocked):
                    small(docs)

    def test_spatial_midpoint_outside_or_malformed_block(self):
        for field,value in (("Latitude","51.125"),("Longitude","6.625"),
                            ("Latitude","NaN"),("Latitude","Infinity"),
                            ("Latitude","49.0"),("Longitude","11"),
                            ("Longitude","broken")):
            with self.subTest(field=field,value=value):
                docs=list(deepcopy(three()))
                docs[0][0][field]=value
                with self.assertRaises(area.CiaraAreaBlocked):
                    small(docs)

    def test_insurer_identity_nonresidential_or_source_tiv_drift_block(self):
        cases = (
            (0,"LocGroup","KREIS-05112"),
            (0,"CountryCode","FR"),
            (0,"LocCurrency","GBP"),
            (0,"LocPerilsCovered","FL"),
            (0,"BuildingTIV","NaN"),
            (0,"BuildingTIV","9999"),
            (2,"SourceGFK","31001_2463"),
            (2,"SourcePhysicalCandidateNotInsuredSite","false"),
            (2,"SourceOiSHA256","not-a-hash"),
        )
        for layer,field,value in cases:
            with self.subTest(layer=layer,field=field,value=value):
                docs=list(deepcopy(three()))
                docs[layer][0][field]=value
                with self.assertRaises(area.CiaraAreaBlocked):
                    small(docs)

    def test_fake_original_zip_not_accepted_under_real_source_sha(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"fake.zip"
            with zipfile.ZipFile(p,"w") as z:
                z.writestr("location.csv", csvbytes(three()[0]))
                z.writestr("account.csv", csvbytes(three()[1]))
                z.writestr("physical_candidate_evidence.csv",csvbytes(three()[2]))
                z.writestr("manifest.json","{}")
            with self.assertRaisesRegex(area.CiaraAreaBlocked,"exact pinned"):
                area.plan_from_archived_source(p)
            link=Path(td)/"link.zip"
            link.symlink_to(p)
            with self.assertRaisesRegex(area.CiaraAreaBlocked,"exact pinned"):
                area.plan_from_archived_source(link)

    def test_exact_archive_bytes_required_before_manifest_can_be_trusted(self):
        # Deliberately generate 10k fake sites in a temporary ZIP to exercise
        # the entire byte-pinned source handoff. Only the test monkeypatches pins.
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"fully_synthetic.zip"
            location,accounts,evidence=[],[],[]
            for i in range(10000):
                cid=f"05{i%53:03d}"
                ident=f"FAKE-PUBLIC-{i:05d}"
                tiv=482602+(9500 if i==9999 else 0)
                location.append(dict(
                    LocNumber=ident,AccNumber=ident,LocGroup="KREIS-"+cid,
                    CountryCode="DE",OEDVersion="5.0.0",LocCurrency="EUR",
                    LocPerilsCovered="WW2",BuildingTIV=str(tiv),
                    Latitude=f"{50.401+(i%33)*0.013:.6f}",
                    Longitude=f"{6.201+(i%37)*0.017:.6f}"))
                accounts.append(dict(AccNumber=ident,PolNumber=ident,OEDVersion="5.0.0"))
                evidence.append(dict(
                    LocNumber=ident,KreisAGS2022=cid,
                    SourcePhysicalCandidateNotInsuredSite="true",
                    SourceGFK="31001_1010",SourceOiSHA256=f"{i+1:064x}"))
            blobs={"location.csv":csvbytes(location),
                   "account.csv":csvbytes(accounts),
                   "physical_candidate_evidence.csv":csvbytes(evidence)}
            pins={name:hashlib.sha256(blob).hexdigest() for name,blob in blobs.items()}
            manifest={
                "schema":area.SOURCE_SCHEMA,
                "status":"GEOCODED_FICTIONAL_INSURANCE_NOT_MODEL_ADMITTED",
                "source_original_2022_HU_complete_archive_SHA256":area.SOURCE_SHA,
                "source_original_2022_HU_full_CRCs_verified":True,
                "output_file_SHA256":pins,
                "physical_building_candidates_selected":10000,
                "real_source_counties_represented":53,
                "fictional_policy_count":10000,
                "model_input_approved":False,
                "insurer_building_TIV_observed":False,
                "physical_building_footprints_are_actual_RV_insured_sites":False,
            }
            with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as z:
                for name,blob in blobs.items():
                    z.writestr(name,blob)
                z.writestr("manifest.json",json.dumps(manifest,sort_keys=True))
            file_sha=hashlib.sha256(p.read_bytes()).hexdigest()
            with patch.object(area,"SOURCE_ARTIFACT_SHA256",file_sha),patch.dict(
                    area.SOURCE_CSV_SHA256,pins,clear=True):
                result=area.plan_from_archived_source(p)
                self.assertEqual(result["public_building_candidates"],10000)
                self.assertEqual(result["source_2022_NRW_counties"],53)
                self.assertEqual(result["historical_source_fictional_building_TIV_EUR"],4826029500)
                self.assertFalse(result["request_executed"])


if __name__ == "__main__":
    unittest.main()
