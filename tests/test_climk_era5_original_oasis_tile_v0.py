# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Pure fictional CLIMK/Oasis adapter tests; original publisher tested separately."""

from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from decimal import Decimal

from research_runners.climk_era5_original_oasis_tile_v0 import (
    ClimkOasisError, build_tile, BINS, PROFILE,
)
from research_runners.wisc_netcdf_oasis_tile_v0 import bins_from_text

SHA="92856dea4578ac556ff5598176ff33411b56baa7c2af0170150e288bd5581102"

def fake(*,gust=None,shift=0,source_sha=SHA,storm_index=0,edges=None):
    return build_tile(
        original_sha256=source_sha,source_storm_index=storm_index,
        storm_name="Entirely fictitious winter storm",
        storm_date_label="1998-fictitious",
        latitudes=[-45.0 + i * 0.5 for i in range(181)],
        longitudes=[-30.0 + i * 0.5 for i in range(269)],
        gust_tile=gust if gust is not None else [[0,10,None],[20,30,40]],
        row_start=90,col_start=130+shift,
        edges=edges if edges is not None else bins_from_text(BINS),
    )

class ClimkOasisSyntheticTests(unittest.TestCase):
    def test_native_oasis_footprint_schema_and_pinned_provenance(self):
        files,receipt=fake()
        self.assertEqual(receipt["profile"],PROFILE)
        self.assertEqual(set(files),{"events.csv","footprint.csv","intensity_bin_dict.csv","areaperil_dict.csv"})
        self.assertEqual(files["events.csv"],b"event_id\n1\n")
        self.assertEqual(files["footprint.csv"].splitlines()[0],
            b"event_id,areaperil_id,intensity_bin_id,probability")
        self.assertEqual(len(files["footprint.csv"].splitlines()),6)
        self.assertEqual(receipt["valid_gust_cells"],5)
        self.assertEqual(receipt["unknown_weather_cells"],1)
        self.assertFalse(receipt["annual_oep_aep_authorized"])
        self.assertFalse(receipt["native_oasis_full_model_run_verified"])
        self.assertFalse(receipt["real_insurer_exposure_or_damage_verified"])
        self.assertFalse(receipt["source_cross_model_independence_proven"])
    def test_global_stable_areaperil_ids(self):
        files,_=fake()
        lines=files["footprint.csv"].decode().splitlines()
        self.assertEqual(lines[1],"1,24341,1,1.0")
        self.assertEqual(lines[2],"1,24342,2,1.0")
        self.assertEqual(lines[3],"1,24610,3,1.0")
        files2,_=fake(gust=[[30]],shift=1)
        self.assertEqual(files2["footprint.csv"].decode().splitlines()[1],"1,24342,4,1.0")
    def test_missing_not_zero_and_last_edge_is_inclusive(self):
        files,receipt=fake(gust=[[None,math.nan,0],[200,20,40]])
        self.assertEqual(receipt["unknown_weather_cells"],2)
        self.assertEqual(receipt["valid_gust_cells"],4)
        self.assertIn(b"1,24610,9,1.0",files["footprint.csv"])
    def test_source_sha_not_replaceable(self):
        with self.assertRaisesRegex(ClimkOasisError,"pinned original"):
            fake(source_sha="f"*64)
    def test_out_of_bounds_gust_blocked(self):
        for gust in (-1,201,math.inf,10**1000,"15"):
            with self.subTest(gust=str(gust)[:15]),self.assertRaises((ClimkOasisError,ValueError)):
                fake(gust=[[gust]])
    def test_invalid_source_event_index_and_labels(self):
        for event in (-1,50,True):
            with self.subTest(event=event),self.assertRaisesRegex(ClimkOasisError,"storm index"):
                fake(storm_index=event)
        with self.assertRaisesRegex(ClimkOasisError,"Storm_Names"):
            build_tile(original_sha256=SHA,source_storm_index=0,storm_name=" ",storm_date_label="1979",
                latitudes=[-45+i*.5 for i in range(181)],
                longitudes=[-30+i*.5 for i in range(269)],
                gust_tile=[[10]],row_start=90,col_start=100,edges=bins_from_text(BINS))
    def test_ragged_empty_tiles_and_missing_all_block(self):
        for gust in ([],[[12],[13,14]]):
            with self.assertRaises(ClimkOasisError):
                fake(gust=gust)
        with self.assertRaisesRegex(ClimkOasisError,"no observed"):
            fake(gust=[[None,None]])
    def test_no_binned_overflow_clipping(self):
        with self.assertRaisesRegex(ClimkOasisError,"no clipping"):
            fake(gust=[[80]],edges=bins_from_text("0,10,70"))
    def test_nonsensical_geographic_grid_blocks(self):
        with self.assertRaisesRegex(ClimkOasisError,"native ERA5 grid"):
            build_tile(original_sha256=SHA,source_storm_index=0,storm_name="A",
                storm_date_label="B",latitudes=[50,49],longitudes=[10,11],
                gust_tile=[[10]],row_start=0,col_start=0,edges=bins_from_text(BINS))
    def test_stable_output_receipt_sha(self):
        a,b=fake();aa,bb=fake()
        self.assertEqual((a,b),(aa,bb))
        for k,value in a.items():
            self.assertEqual(b["output_files"][k]["sha256"],hashlib.sha256(value).hexdigest())
            self.assertEqual(b["output_files"][k]["bytes"],len(value))

if __name__ == "__main__":
    unittest.main()
