# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only source geometry, GeoTIFF window and cellwise privacy tests."""
from __future__ import annotations

import hashlib
import importlib.util
import struct
import unittest
from unittest.mock import patch

HAS_SHAPELY=importlib.util.find_spec("shapely") is not None
HAS_GEO=HAS_SHAPELY and importlib.util.find_spec("pyproj") is not None
if HAS_SHAPELY:
    from shapely.geometry import box
    from shapely.ops import unary_union

from research_runners import ghsl_bvv_original_1024_cell_pairwise_v0 as cells
from research_runners.bvv_oberbayern_full_shp_roi_stream_v0 import NativeSHPStream
from tests.test_bvv_oberbayern_full_shp_roi_stream_v0 import synthetic_source


class Original1024SyntheticTests(unittest.TestCase):
    @unittest.skipUnless(HAS_GEO,"optional pinned test requires Shapely and pyproj")
    def test_original_1024_native_projected_grid_is_exact_same_source_roi(self):
        roi,grid=cells.build_frozen_1024_cells()
        self.assertEqual(len(grid),1024)
        self.assertTrue(all(c.is_valid for c in grid))
        self.assertLess(roi.symmetric_difference(unary_union(grid)).area,0.01)
        self.assertAlmostEqual(sum(c.area for c in grid),roi.area,delta=0.01)
        self.assertAlmostEqual(roi.area,588514088.109,delta=0.01)
        self.assertNotEqual(grid[0].centroid.x,grid[32].centroid.x)
        self.assertGreater(grid[0].centroid.y,grid[32].centroid.y)

    def test_synthetic_uint32_window_is_north_to_south_west_to_east(self):
        blob=bytearray(cells.NATIVE_BYTES)
        start=(cells.WINDOW_LOCAL_Y*cells.TILE_SIDE+cells.WINDOW_LOCAL_X)*4
        second=start+4
        next_row=((cells.WINDOW_LOCAL_Y+1)*cells.TILE_SIDE+cells.WINDOW_LOCAL_X)*4
        struct.pack_into("<III",blob,start,17,18,19)
        struct.pack_into("<I",blob,next_row,20)
        values,window=cells.decode_native_1024_original_values(bytes(blob))
        self.assertEqual(len(values),1024)
        self.assertEqual(len(window),4096)
        self.assertEqual((values[0],values[1],values[2],values[32]),(17,18,19,20))
        self.assertEqual(hashlib.sha256(window).hexdigest(),
                         hashlib.sha256(b"".join(
                            bytes(blob[((cells.WINDOW_LOCAL_Y+r)*cells.TILE_SIDE+
                                         cells.WINDOW_LOCAL_X)*4:
                                       ((cells.WINDOW_LOCAL_Y+r)*cells.TILE_SIDE+
                                         cells.WINDOW_LOCAL_X)*4+128])
                            for r in range(32)
                         )).hexdigest())

    def test_native_uint32_nodata_and_bad_size_fail_closed(self):
        with self.assertRaises(cells.CellwiseBlocked):
            cells.decode_native_1024_original_values(b"bad")
        b=bytearray(cells.NATIVE_BYTES)
        idx=(cells.WINDOW_LOCAL_Y*cells.TILE_SIDE+cells.WINDOW_LOCAL_X)*4
        struct.pack_into("<I",b,idx,0xffffffff)
        with self.assertRaisesRegex(cells.CellwiseBlocked,"NoData"):
            cells.decode_native_1024_original_values(bytes(b))

    @unittest.skipUnless(HAS_GEO,"optional pinned test requires Shapely and pyproj")
    def test_paired_cell_areas_and_support_are_aggregated_without_raw_pixels(self):
        _,grid=cells.build_frozen_1024_cells()
        # two wholly invented projected footprints; never real buildings
        g=unary_union((grid[0].buffer(-15),grid[1].buffer(-20)))
        surf=(10,)+(0,)*1023
        volume=(20,)+(0,)*1023
        out=cells.area_by_paired_native_cells(g,grid,surf,volume)
        self.assertEqual(out["paired_native_original_cells"],1024)
        self.assertEqual(out["paired_both_source_footprint_cells_positive"],1)
        self.assertEqual(out["paired_ghsl_positive_bvv_zero_cells"],0)
        self.assertEqual(out["paired_ghsl_zero_bvv_positive_cells"],1)
        self.assertEqual(out["paired_both_zero_cells"],1022)
        self.assertEqual(out["paired_bvv_footprint_positive_cells"],2)
        self.assertAlmostEqual(out["paired_official_current_footprint_cell_areas_sum_m2"],
                               g.area,delta=0.005)
        self.assertRegex(out["paired_native_cell_tuple_sha256"],r"^[a-f0-9]{64}$")
        self.assertFalse(out["model_input_approved"])
        self.assertFalse(out["paired_native_cell_values_or_original_geometries_persisted"])
        self.assertTrue(all(type(v) in (str,int,float,bool) for v in out.values()))
        self.assertNotIn("geometry",out)

    @unittest.skipUnless(HAS_GEO,"optional pinned test requires Shapely and pyproj")
    def test_paired_source_row_order_and_volume_are_both_in_sha(self):
        _,grid=cells.build_frozen_1024_cells()
        geo=grid[0].buffer(-20)
        s=(10,)+(0,)*1023
        v=(20,)+(0,)*1023
        first=cells.area_by_paired_native_cells(geo,grid,s,v)
        changed_v=(21,)+(0,)*1023
        second=cells.area_by_paired_native_cells(geo,grid,s,changed_v)
        self.assertNotEqual(first["paired_native_cell_tuple_sha256"],
                            second["paired_native_cell_tuple_sha256"])
        changed_s=(0,10)+(0,)*1022
        third=cells.area_by_paired_native_cells(geo,grid,changed_s,v)
        self.assertNotEqual(first["paired_native_cell_tuple_sha256"],
                            third["paired_native_cell_tuple_sha256"])

    @unittest.skipUnless(HAS_GEO,"optional pinned test requires Shapely and pyproj")
    def test_unsupported_original_values_and_constant_geometries_fail(self):
        _,grid=cells.build_frozen_1024_cells()
        geo=grid[0].buffer(-20)
        with self.assertRaises(cells.CellwiseBlocked):
            cells.area_by_paired_native_cells(geo,grid,(0xffffffff,)+(0,)*1023,(20,)+(0,)*1023)
        with self.assertRaisesRegex(cells.CellwiseBlocked,"variances"):
            cells.area_by_paired_native_cells(geo,grid,(0,)*1024,(20,)+(0,)*1023)
        with self.assertRaises(cells.CellwiseBlocked):
            cells.area_by_paired_native_cells(geo,grid,(0,)*1023,(20,)+(0,)*1023)

    @unittest.skipUnless(HAS_SHAPELY,"optional pinned test requires GEOS")
    def test_full_original_source_optional_union_callback_scalar_only(self):
        raw=synthetic_source(count=2)
        roi=box(649900,5349900,650030,5350030)
        calls=[]
        def callback(g,receipt):
            calls.append((receipt["roi_original_polygon_records_intersecting"],
                          round(g.area,3)))
            return {"research_only_callback_count":2,
                    "research_only_callback_no_coords":True}
        parser=NativeSHPStream(expected_records=2,expected_bytes=len(raw),
                               expected_header_sha=None,roi=roi,
                               original_roi_union_analysis=callback)
        for offset in range(0,len(raw),29):
            parser.feed(raw[offset:offset+29])
        out=parser.finish()
        self.assertEqual(calls,[(2,200.)])
        self.assertEqual(out["research_only_callback_count"],2)
        self.assertTrue(out["research_only_callback_no_coords"])
        self.assertNotIn("650000",str(out))
        self.assertFalse(out["model_input_approved"])

    @unittest.skipUnless(HAS_SHAPELY,"optional pinned test requires GEOS")
    def test_original_source_callback_cannot_return_geometry_or_change_provenance(self):
        raw=synthetic_source(count=2)
        roi=box(649900,5349900,650030,5350030)
        for callback in (lambda g,r:{"raw_original_geometries":[g]},
                         lambda g,r:{"source_id":"wrong"}):
            parser=NativeSHPStream(expected_records=2,expected_bytes=len(raw),
                                   expected_header_sha=None,roi=roi,
                                   original_roi_union_analysis=callback)
            parser.feed(raw)
            with self.assertRaisesRegex(Exception,"research data|overwrite"):
                parser.finish()

    def test_no_external_source_without_trusted_main_live_flag(self):
        with self.assertRaises(SystemExit) as cm:
            cells.main([])
        self.assertNotEqual(cm.exception.code,0)
        with self.assertRaisesRegex(cells.CellwiseBlocked,"unreviewed"):
            cells.fetch_frozen_ghsl_cells("future-unknown-source")


if __name__=="__main__":
    unittest.main()
