# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only Bavarian polygon vs DLR WSF source grid tests; no original bytes."""
from __future__ import annotations

import copy
import importlib.util
import unittest

from research_runners.by_hausumringe_wsf2019_spatial_gate_v0 import (
    AlignmentBlocked, ORIGINAL_COMPRESSED_TILE_SHA,
    verify_neon_mask, verify_local_reference, compare_area_weighted, inspect,
)

HAS_GEOS=importlib.util.find_spec("shapely") is not None
HAS_PROJ=importlib.util.find_spec("pyproj") is not None
BBOX=(11.549459944867865,48.12571421072036,11.552334553777047,48.12858881962954)


def synthetic_rows():
    return ["1"*8+"0"*24 for _ in range(32)]


def fake_neon():
    # Every mask here is SYNTHETIC: the immutable original hash must reject it.
    return {
        "sample_id":29, "source_id":"dlr.wsf.2019",
        "sample_kind":"geospatial_preview","model_input_approved":False,
        "provider_response_sha256":ORIGINAL_COMPRESSED_TILE_SHA,
        "sample_json":{
            "source_id":"dlr.wsf.2019","epsg":4326,
            "model_input_approved":False,
            "original_compressed_tile_sha256":ORIGINAL_COMPRESSED_TILE_SHA,
            "sample_subtype":"native_geotiff_lzw_window_mixed",
            "window_width":32,"window_height":32,
            "window_bbox_lonlat":list(BBOX),
            "window_class_counts":{"0":768,"255":256},
            "window_raster_rows_binary_1_is_255":synthetic_rows(),
        },
    }


def make_box(a,b,c,d):
    from pyproj import Transformer
    to_utm=Transformer.from_crs("EPSG:4326","EPSG:25832",always_xy=True)
    w,s,e,n=BBOX
    step=(e-w)/32
    coords=[(w+a*step,n-b*step),(w+c*step,n-b*step),
            (w+c*step,n-d*step),(w+a*step,n-d*step)]
    ring=[list(to_utm.transform(x,y)) for x,y in coords]
    ring.append(ring[0])
    return {"type":"Polygon","coordinates":[ring]}


def fake_bvv(geometry):
    return {
        "source_id":"de.bayern.hausumringe","type":"FeatureCollection",
        "original_format":"Shapefile","source_crs":"EPSG:25832",
        "license":"CC-BY-4.0","source_is_official_open_data":True,
        "independently_verified_source_asset":False,
        "roi_complete_for_frozen_bbox":False,
        "source_snapshot_date":"2026-11-01",
        "original_archive_sha256":"b"*64,
        "features":[{"type":"Feature","geometry":geometry,"properties":{}}],
    }


class FailClosedSyntheticTests(unittest.TestCase):
    def test_fabricated_mask_rejected_even_if_source_hash_claimed(self):
        with self.assertRaisesRegex(AlignmentBlocked,"digest mismatch"):
            verify_neon_mask(fake_neon())

    def test_wrong_source_or_approval_rejected(self):
        x=fake_neon();x["source_id"]="de.bkg.hu-de"
        with self.assertRaises(AlignmentBlocked):verify_neon_mask(x)
        x=fake_neon();x["model_input_approved"]=True
        with self.assertRaises(AlignmentBlocked):verify_neon_mask(x)

    def test_unproven_complete_archive_refused(self):
        g={"type":"Point","coordinates":[0,0]}
        x=fake_bvv(g);x["independently_verified_source_asset"]=True
        with self.assertRaises(AlignmentBlocked):verify_local_reference(x)
        x=fake_bvv(g);x["roi_complete_for_frozen_bbox"]=True
        with self.assertRaises(AlignmentBlocked):verify_local_reference(x)

    def test_license_and_projection_fail_closed(self):
        g={"type":"Point","coordinates":[0,0]}
        x=fake_bvv(g);x["license"]="unknown"
        with self.assertRaises(AlignmentBlocked):verify_local_reference(x)
        x=fake_bvv(g);x["source_crs"]="EPSG:4326"
        with self.assertRaises(AlignmentBlocked):verify_local_reference(x)

    def test_bad_snapshot_and_fake_source_hash_fail_closed(self):
        g={"type":"Point","coordinates":[0,0]}
        x=fake_bvv(g);x["source_snapshot_date"]="2026-02-31"
        with self.assertRaises(AlignmentBlocked):verify_local_reference(x)
        x=fake_bvv(g);x["original_archive_sha256"]="invalid"
        with self.assertRaises(AlignmentBlocked):verify_local_reference(x)


@unittest.skipUnless(HAS_GEOS and HAS_PROJ,"dedicated pinned GEOS/pyproj job tests geometry")
class SyntheticGeometryTests(unittest.TestCase):
    def test_exact_area_weighted_perfect_overlap(self):
        gs,_=verify_local_reference(fake_bvv(make_box(0,0,8,32)))
        r=compare_area_weighted(synthetic_rows(),BBOX,gs)
        self.assertAlmostEqual(r["reference_area_in_native_cell_equivalents"],256,delta=0.2)
        self.assertAlmostEqual(r["area_weighted_iou_on_partial_reference"],1,delta=0.001)
        self.assertAlmostEqual(r["area_weighted_reference_recall_partial_only"],1,delta=0.001)

    def test_shift_four_pixels_yields_half_overlap(self):
        gs,_=verify_local_reference(fake_bvv(make_box(4,0,12,32)))
        r=compare_area_weighted(synthetic_rows(),BBOX,gs)
        self.assertAlmostEqual(r["intersection_area_in_native_cell_equivalents"],128,delta=0.2)
        self.assertAlmostEqual(r["area_weighted_predicted_precision_partial_only"],0.5,delta=0.001)
        self.assertAlmostEqual(r["area_weighted_iou_on_partial_reference"],1/3,delta=0.001)

    def test_disjoint_polygon_has_zero_overlap(self):
        gs,_=verify_local_reference(fake_bvv(make_box(16,0,20,16)))
        r=compare_area_weighted(synthetic_rows(),BBOX,gs)
        self.assertEqual(r["intersection_area_in_native_cell_equivalents"],0)
        self.assertEqual(r["area_weighted_iou_on_partial_reference"],0)

    def test_duplicate_polygons_not_double_counted(self):
        x=fake_bvv(make_box(0,0,8,32))
        x["features"].append(copy.deepcopy(x["features"][0]))
        gs,_=verify_local_reference(x)
        r=compare_area_weighted(synthetic_rows(),BBOX,gs)
        self.assertAlmostEqual(r["reference_area_in_native_cell_equivalents"],256,delta=0.2)

    def test_bowtie_topology_and_nonpolygon_block(self):
        g=make_box(0,0,8,32);p=g["coordinates"][0]
        x=fake_bvv({"type":"Polygon","coordinates":[[p[0],p[2],p[1],p[3],p[0]]]})
        with self.assertRaises(AlignmentBlocked):verify_local_reference(x)
        x=fake_bvv({"type":"Point","coordinates":[690000,5330000]})
        with self.assertRaises(AlignmentBlocked):verify_local_reference(x)

    def test_polygon_without_raster_intersection_blocks(self):
        from shapely.affinity import translate
        from shapely.geometry import shape
        shifted=translate(shape(make_box(0,0,8,32)),xoff=10000,yoff=10000)
        with self.assertRaisesRegex(AlignmentBlocked,"no common footprint"):
            compare_area_weighted(synthetic_rows(),BBOX,[shifted])


if __name__=="__main__":
    unittest.main()
