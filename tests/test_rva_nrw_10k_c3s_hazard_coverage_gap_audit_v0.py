# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent fake-input cell exposure and unknown wind taxonomy acceptance tests."""
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
from rva_nrw_10k_c3s_hazard_coverage_gap_audit_v0 import (
    audit,write_report,CoverageBlocked,INPUT_SCHEMA,EXPECTED_HU_SHA,EXPECTED_GRID
)


def fixture(path:Path,*,change_receipt=False,wrong_vlt=False,wrong_cell=False,duplicate=False):
    grid={"grid_id":EXPECTED_GRID,"west_lon_e6":5500000,"south_lat_e6":50000000,
          "width_e6":250000,"height_e6":250000,"num_lon":20,"num_lat":13,"crs":"EPSG:4326"}
    coords=((7020381,50804382,"05362"),(8378007,51453377,"05974"),
            (8658974,51519438,"05774"))
    assignments=[]
    valuations=[]
    cellcount={}
    countycount={}
    for i,(lon,lat,county) in enumerate(coords,1):
        col=(lon-5500000)//250000
        row=(lat-50000000)//250000
        aid=f"SYN-NRW-{county}-01-{i:06d}"
        cell=f"{EXPECTED_GRID}:x{col:05d}:y{row:05d}"
        item={"asset_id":aid,
              "cedant_id":"FICTITIOUS_RVA_LIKE_NRW_NOT_OBSERVED",
              "country_iso2":"DE","taxonomy":"UNMAPPED_HU22_GFK_31001_1010",
              "lon_e6":lon,"lat_e6":lat,"col":col,"row":row,"cell_id":cell}
        if wrong_cell and i==1:item["col"]+=1
        if wrong_vlt and i==1:item["taxonomy"]="MASONRY"
        assignments.append(item)
        valuations.append({"asset_id":aid,"replacement_cost_eur":(100000,200000,300000)[i-1]})
        cellcount[cell]=cellcount.get(cell,0)+1
        countycount[county]=countycount.get(county,0)+1
    if duplicate:valuations[2]["asset_id"]=valuations[0]["asset_id"]
    payload=json.dumps({"grid":grid,"crosswalk_assignments":assignments,
                        "insured_asset_values":valuations},sort_keys=True,separators=(",",":")).encode()
    receipt={
        "schema":INPUT_SCHEMA,
        "status":"SPATIAL_CROSSWALK_SHAPE_ONLY_NO_ADMITTED_C3S_MODEL",
        "source_original_HU_2022_full_SHA256":EXPECTED_HU_SHA if not change_receipt else "f"*64,
        "source_physical_synthetic_OED_count":3,"original_NRW_counties":3,
        "synthetic_source_building_TIV_eur":600000,
        "handoff_json_sha256":hashlib.sha256(payload).hexdigest(),
        "grid_is_fictional_not_C3S_NetCDF":True,
        "actual_C3S_NetCDF_original_bytes_authenticated":False,
        "source_specific_wind_vulnerability_taxonomy_mapped":False,
        "wind_damage_probability_law_supplied":False,
        "gross_insured_net_reinsurance_or_EP_executed":False,
        "counts_by_demo_grid_cell":cellcount,
        "counts_by_real_source_Kreis":countycount,
    }
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("nextgen_c3s_spatial_handoff.json",payload)
        z.writestr("source_boundary_receipt.json",json.dumps(receipt))


class TestWindCoverGapAudit(unittest.TestCase):
    def test_exact_three_site_handoff_cell_and_unmapped_gfk_conservation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/"s.zip";out=root/"audit.zip"
            fixture(source)
            report=audit(source,expected_count=3,expected_kreise=3,expected_tiv=600000)
            summary=report["summary"]
            self.assertEqual(summary["fictional_total_building_TIV_eur"],600000)
            self.assertEqual(summary["number_of_official_NRW_Kreis"],3)
            self.assertEqual(sum(r["SyntheticAssetCount"] for r in report["cell_rows"]),3)
            self.assertEqual(sum(r["SyntheticBuildingTIVEUR"] for r in report["cell_rows"]),600000)
            self.assertEqual(sum(r["SyntheticAssetCount"] for r in report["gfk_rows"]),3)
            self.assertEqual(sum(r["SyntheticAssetCount"] for r in report["kreis_rows"]),3)
            self.assertEqual(sum(r["SyntheticBuildingTIVEUR"] for r in report["kreis_rows"]),600000)
            self.assertEqual(summary["sites_with_wind_material_roof_vulnerability_mapped"],0)
            self.assertEqual(summary["sites_with_actual_C3S_footprint_guessed_gust_values"],0)
            self.assertFalse(summary["native_Germany_GUL_IL_RI_OEP_AEP_executed"])
            receipt=write_report(out,report)
            with zipfile.ZipFile(out) as z:
                self.assertIsNone(z.testzip())
                for name,digest in receipt["output_sha256"].items():
                    self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest)
                rows=list(csv.DictReader(io.StringIO(z.read("invented_grid_cell_exposure.csv").decode())))
                self.assertEqual(sum(int(r["SyntheticAssetCount"]) for r in rows),3)
                self.assertTrue(all(x["WindHazardMeasured"]=="false" for x in rows))
            with self.assertRaises(CoverageBlocked):write_report(out,report)

    def test_fail_closed_corporate_or_hazard_promotion_wrong_cell_and_duplicates(self):
        for kwargs in ({"change_receipt":True},{"wrong_vlt":True},
                       {"wrong_cell":True},{"duplicate":True}):
            with self.subTest(kwargs=kwargs),tempfile.TemporaryDirectory() as td:
                source=Path(td)/"s.zip";fixture(source,**kwargs)
                with self.assertRaises(CoverageBlocked):
                    audit(source,expected_count=3,expected_kreise=3,expected_tiv=600000)


    def test_known_nonresidential_hu_function_not_a_wind_taxonomy(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/"s.zip";fixture(source)
            with zipfile.ZipFile(source) as z:
                data=json.loads(z.read("nextgen_c3s_spatial_handoff.json"))
                meta=json.loads(z.read("source_boundary_receipt.json"))
            data["crosswalk_assignments"][0]["taxonomy"]="UNMAPPED_HU22_GFK_31001_2463"
            blob=json.dumps(data,sort_keys=True,separators=(",",":")).encode()
            meta["handoff_json_sha256"]=hashlib.sha256(blob).hexdigest()
            with zipfile.ZipFile(source,"w",compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("nextgen_c3s_spatial_handoff.json",blob)
                z.writestr("source_boundary_receipt.json",json.dumps(meta))
            with self.assertRaises(CoverageBlocked):
                audit(source,expected_count=3,expected_kreise=3,expected_tiv=600000)

    def test_fail_closed_count_and_tiv_change(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/"s.zip";fixture(source)
            for kwargs in ({"expected_count":4,"expected_kreise":3,"expected_tiv":600000},
                           {"expected_count":3,"expected_kreise":3,"expected_tiv":600001},
                           {"expected_count":3,"expected_kreise":0,"expected_tiv":600000}):
                with self.subTest(kwargs=kwargs),self.assertRaises(CoverageBlocked):
                    audit(source,**kwargs)


if __name__=="__main__":
    unittest.main()
