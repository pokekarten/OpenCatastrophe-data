# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Three public physical coordinates, *fictional* OED contracts: offline guards."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from export_rva_nrw_hu_2022_geocoded_oed_smoke_v0 import (
    export_coordinates_audited,SITE_COUNT,FICTITIOUS_BUILDING_VALUE_EUR,
)


def synthetic_source():
    """Deliberately invented physical points; not source downloaded or actual insurer."""
    return {
        "schema":"NRW_HU_2022_ORIGINAL_FIRST_PHYSICAL_POLYGON_SMOKE_V0",
        "actual_source_geometry_reprojected_to_wgs84":True,
        "source_original_zip_sha256_verified":False,
        "actual_RV_insured_site_location_verified":False,
        "model_input_approved":False,
        "observed_original_example_physical_polygons_count":3,
        "bounded_original_prefix_audit":{"shp_records_inspected":250},
        "original_example_county_codes":["05362","05974","05774"],
        "physical_source_only_sample_wgs84_coordinates":[
            {"lat":50.804382,"lon":7.020381},
            {"lat":51.453377,"lon":8.378007},
            {"lat":51.519438,"lon":8.658974},
        ],
    }


class TestPhysicalSourceToFictionalOED(unittest.TestCase):
    def test_three_geocoded_public_points_never_actual_insurer_sites(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp)/"oed"
            receipt=export_coordinates_audited(synthetic_source(),directory)
            with (directory/"location.csv").open(encoding="utf-8",newline="") as file:
                loc=list(csv.DictReader(file))
            with (directory/"account.csv").open(encoding="utf-8",newline="") as file:
                account=list(csv.DictReader(file))
            self.assertEqual((len(loc),len(account)),(SITE_COUNT,SITE_COUNT))
            self.assertEqual({r["LocNumber"] for r in loc},{r["AccNumber"] for r in account})
            self.assertEqual(len({r["AccNumber"] for r in account}),3)
            self.assertEqual({r["LocPerilsCovered"] for r in loc},{"WW2"})
            self.assertEqual({r["OEDVersion"] for r in loc},{"5.0.0"})
            self.assertEqual({r["Latitude"] for r in loc},{"50.804382","51.453377","51.519438"})
            self.assertEqual({r["LocGroup"] for r in loc},{"KREIS-05362","KREIS-05974","KREIS-05774"})
            self.assertEqual(sum(int(x["BuildingTIV"]) for x in loc),SITE_COUNT*FICTITIOUS_BUILDING_VALUE_EUR)
            self.assertEqual(receipt["fictitious_total_tiv_eur"],1_350_000)
            self.assertIs(receipt["source_original_zip_full_sha256_verified"],False)
            self.assertIs(receipt["actual_RV_insured_buildings_verified"],False)
            self.assertIs(receipt["native_oasis_GUL_IL_RI_OEP_AEP_verified"],False)
            self.assertIs(receipt["germany_CAT_model_input_approved"],False)
            self.assertEqual(json.loads((directory/"manifest.json").read_text())["fictitious_insurance_contracts"],3)
            for name,sha in receipt["output_sha256"].items():
                self.assertEqual(hashlib.sha256((directory/name).read_bytes()).hexdigest(),sha)

    def test_false_company_or_full_source_authentication_blocks(self):
        base=synthetic_source()
        for key in ("actual_RV_insured_site_location_verified","source_original_zip_sha256_verified","model_input_approved"):
            tampered=dict(base,**{key:True})
            with tempfile.TemporaryDirectory() as t:
                with self.assertRaises(ValueError):
                    export_coordinates_audited(tampered,Path(t)/"out")
                self.assertFalse((Path(t)/"out").exists())

    def test_unknown_or_malformed_coordinates_fail_before_writing(self):
        base=synthetic_source()
        for pts in (
            [],
            [{"lat":50.8,"lon":7.0}],
            [{"lat":None,"lon":7.0}]*3,
            [{"lat":48.1,"lon":7.0}]*3,
            [{"lat":50.1,"lon":22.0}]*3,
        ):
            tampered=dict(base,physical_source_only_sample_wgs84_coordinates=pts)
            with tempfile.TemporaryDirectory() as t:
                with self.assertRaises(ValueError):
                    export_coordinates_audited(tampered,Path(t)/"out")
                self.assertFalse((Path(t)/"out").exists())

    def test_fresh_directory_required_and_original_source_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            t=Path(temp)
            d=t/"already_created"
            d.mkdir()
            with self.assertRaises(ValueError):
                export_coordinates_audited(synthetic_source(),d)
            modified=dict(synthetic_source())
            modified["bounded_original_prefix_audit"]={"shp_records_inspected":249}
            with self.assertRaises(ValueError):
                export_coordinates_audited(modified,t/"no")
            self.assertFalse((t/"no").exists())


if __name__=="__main__":
    unittest.main()
