# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic tests for one original Kyrill cell shared by 24 invented assets."""

from __future__ import annotations
import copy
import csv
import hashlib
import io
import math
import unittest

from research_runners.climk_kyrill_24_assets_native_peril_crosswalk_v0 import (
    AREA_PERIL, CrosswalkError, PINNED_SHA256, SITES, crosswalk,
)
from research_runners.climk_era5_original_oasis_tile_v0 import build_tile
from research_runners.wisc_netcdf_oasis_tile_v0 import bins_from_text

GUST = 35.21054044063598


def fixture():
    files, receipt = build_tile(
        original_sha256=PINNED_SHA256,
        source_storm_index=0, storm_name="KYRILL", storm_date_label="20070118",
        latitudes=[-45 + 0.5*i for i in range(181)],
        longitudes=[-30 + 0.5*i for i in range(269)],
        gust_tile=[[GUST]], row_start=78, col_start=112,
        edges=bins_from_text("0,10,20,30,40,50,60,80,120,200"),
    )
    sample = {
        "source_sha256": PINNED_SHA256, "source_sha_pinned": True,
        "source_storm_name": "KYRILL", "source_storm_date_label": "20070118",
        "storm_index_zero_based": 0, "event_identity_cross_model_matched": False,
        "source_event_frequency_inferred": False, "scientifically_admitted": False,
        "site_count": 2,
        "site_samples": [
            {
                "site_id": site_id,
                "native_cell_x": 112, "native_cell_y": 78,
                "absolute_max_gust_m_s": GUST,
            }
            for site_id,_,_ in SITES
        ],
    }
    return sample, files, receipt


class KyrillFictionalCrosswalkOfflineTests(unittest.TestCase):
    def test_24_assets_really_share_one_original_native_area_peril(self):
        sample,files,receipt=fixture()
        csv_body, result = crosswalk(sample,files,receipt)
        self.assertEqual(AREA_PERIL,21095)
        self.assertEqual(result["oasis_areaperil_id"],21095)
        self.assertEqual(result["distinct_physical_hazard_cells"],1)
        self.assertEqual(result["fictional_site_markers"],2)
        self.assertEqual(result["fictional_asset_count"],24)
        self.assertEqual(result["fictional_tiv_eur"],240_000_000)
        self.assertEqual(result["source_gust_m_s"],GUST)
        self.assertEqual(result["oasis_intensity_bin_id"],4)
        self.assertFalse(result["annual_oep_aep_authorized"])
        self.assertFalse(result["native_full_oasis_gul_il_ri_verified"])
        self.assertFalse(result["real_insurer_locations_verified"])
        self.assertFalse(result["original_provider_bytes_independently_verified_by_pure_function"])
        rows=list(csv.DictReader(io.StringIO(csv_body.decode())))
        self.assertEqual(len(rows),24)
        self.assertEqual({r["areaperil_id"] for r in rows},{"21095"})
        self.assertEqual({r["replacement_cost_eur"] for r in rows},{"10000000"})
        self.assertEqual({r["source_storm_index_zero_based"] for r in rows},{"0"})
        self.assertEqual(sum(r["synthetic_site_id"]==SITES[0][0] for r in rows),12)
        self.assertEqual(sum(r["synthetic_site_id"]==SITES[1][0] for r in rows),12)
        self.assertEqual(result["crosswalk_csv_sha256"],hashlib.sha256(csv_body).hexdigest())

    def test_deterministic_output_bytes(self):
        a=fixture();b=fixture()
        self.assertEqual(crosswalk(*a),crosswalk(*b))

    def test_wrong_original_source_sha_for_site_sample_rejected(self):
        a,b,c=fixture();a["source_sha256"]="a"*64
        with self.assertRaisesRegex(CrosswalkError,"source storm"):
            crosswalk(a,b,c)

    def test_wrong_source_sha_for_wind_tile_rejected(self):
        a,b,c=fixture();c["original_sha256_verified"]="b"*64
        with self.assertRaisesRegex(CrosswalkError,"source tile"):
            crosswalk(a,b,c)

    def test_wrong_storm_name_date_or_event_index_rejected(self):
        for key,value in (("source_storm_name","EMMA"),("source_storm_date_label","20070119"),("storm_index_zero_based",1)):
            with self.subTest(key=key):
                a,b,c=fixture();a[key]=value
                with self.assertRaisesRegex(CrosswalkError,"source storm"):
                    crosswalk(a,b,c)

    def test_two_fictional_sites_in_distinct_physical_cells_must_block(self):
        a,b,c=fixture();a["site_samples"][1]["native_cell_x"]=113
        with self.assertRaisesRegex(CrosswalkError,"same cell"):
            crosswalk(a,b,c)

    def test_duplicate_site_metadata_blocks(self):
        a,b,c=fixture();a["site_samples"][1]["site_id"]=a["site_samples"][0]["site_id"]
        with self.assertRaisesRegex(CrosswalkError,"duplicated"):
            crosswalk(a,b,c)

    def test_drift_in_sampled_original_gust_blocks(self):
        a,b,c=fixture();a["site_samples"][1]["absolute_max_gust_m_s"]=GUST+0.01
        with self.assertRaisesRegex(CrosswalkError,"different"):
            crosswalk(a,b,c)

    def test_nonfinite_original_gust_blocks(self):
        for v in (float("nan"),float("inf"),-1,0,45,True,"35.2"):
            with self.subTest(v=str(v)):
                a,b,c=fixture();a["site_samples"][0]["absolute_max_gust_m_s"]=v
                with self.assertRaisesRegex(CrosswalkError,"source gust"):
                    crosswalk(a,b,c)

    def test_source_native_cell_shift_blocks(self):
        a,b,c=fixture();c["tile"]["col_start"]=113
        with self.assertRaisesRegex(CrosswalkError,"source tile"):
            crosswalk(a,b,c)

    def test_source_hash_binding_for_modified_footprint_bytes(self):
        a,b,c=fixture()
        b["footprint.csv"]=b["footprint.csv"].replace(b",4,1.0",b",5,1.0")
        with self.assertRaisesRegex(CrosswalkError,"not bound"):
            crosswalk(a,b,c)

    def test_invalid_footprint_bin_even_with_recomputed_hash_rejected(self):
        a,b,c=fixture()
        b["footprint.csv"]=b["footprint.csv"].replace(b",4,1.0",b",5,1.0")
        c["output_files"]["footprint.csv"]={
            "bytes":len(b["footprint.csv"]),
            "sha256":hashlib.sha256(b["footprint.csv"]).hexdigest(),
        }
        with self.assertRaisesRegex(CrosswalkError,"not identical"):
            crosswalk(a,b,c)

    def test_inconsistent_area_peril_lookup_block(self):
        a,b,c=fixture()
        b["areaperil_dict.csv"]=b["areaperil_dict.csv"].replace(b"78,112",b"78,113")
        c["output_files"]["areaperil_dict.csv"]={
            "bytes":len(b["areaperil_dict.csv"]),
            "sha256":hashlib.sha256(b["areaperil_dict.csv"]).hexdigest(),
        }
        with self.assertRaisesRegex(CrosswalkError,"geogrid index"):
            crosswalk(a,b,c)

    def test_annual_or_financial_promotion_block(self):
        a,b,c=fixture();c["annual_oep_aep_authorized"]=True
        with self.assertRaisesRegex(CrosswalkError,"source tile"):
            crosswalk(a,b,c)
        a,b,c=fixture();a["source_event_frequency_inferred"]=True
        with self.assertRaisesRegex(CrosswalkError,"source storm"):
            crosswalk(a,b,c)


if __name__=="__main__":
    unittest.main()
