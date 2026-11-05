# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strictly invented footprints and parishes, no Microsoft/Census bytes."""
from __future__ import annotations

import importlib.util
import json
import math
import struct
import unittest
import zlib

from research_runners.us_census_2026_microsoft_louisiana_building_parish_join_v0 import (
    SourceJoinError, MS_PREFIX_BYTES, MS_ZIP_MEMBER,
    _source_geojson_prefix, classify_footprints,
)

AVAILABLE = all(importlib.util.find_spec(n) is not None
                for n in ("shapely","pyproj"))


def invent_ms_prefix(*, features=None, wrong_filename=False,
                     no_features_array=False, wrong_magic=False):
    from shapely.geometry import mapping, box
    sample=features
    if sample is None:
        sample=[{"type":"Feature","properties":{},
                 "geometry":mapping(box(-90.18,29.94,-90.17,29.95))}
                 for _ in range(20)]
    obj={"type":"FeatureCollection",
         "features":sample if not no_features_array else None}
    raw=json.dumps(obj,separators=(",",":"),allow_nan=False).encode("utf8")
    enc=zlib.compressobj(6,zlib.DEFLATED,-15)
    compressed=enc.compress(raw)+enc.flush()
    name=(b"wrong.json" if wrong_filename
          else MS_ZIP_MEMBER.encode("ascii"))
    local=struct.pack(
        "<IHHHHHIIIHH",0x04034b50,20,8,8,0,0,0,0,0,len(name),0,
    )
    if wrong_magic:
        local=b"BAD!"+local[4:]
    output=local+name+compressed
    if len(output)>MS_PREFIX_BYTES:
        raise AssertionError("fictional ZIP prefix is too large")
    return output.ljust(MS_PREFIX_BYTES,b"\0")


@unittest.skipUnless(AVAILABLE,"Dedicated geospatial CI installs Shapely and pyproj")
class RealSourcesSyntheticChallenges(unittest.TestCase):
    @staticmethod
    def shapes():
        from shapely.geometry import box
        return {
            "22071":box(-90.2,29.9,-90.1,30.0),
            "22051":box(-90.1,29.9,-90.0,30.0),
        }

    @staticmethod
    def box(*bbox):
        from shapely.geometry import box
        return box(*bbox)

    def test_strictly_inside_source_roofprints_are_classified_not_admitted(self):
        buildings=[self.box(-90.18,29.94,-90.17,29.95),
                   self.box(-90.07,29.94,-90.06,29.95)]
        results,groups=classify_footprints(self.shapes(),buildings)
        self.assertEqual(results["strict_matched"],2)
        self.assertEqual(results["boundary_or_datum_uncertain"],0)
        self.assertEqual(groups,{"22071":1,"22051":1})

    def test_ten_meter_boundary_margin_holds_out_building(self):
        buildings=[self.box(-90.10004,29.94,-90.10001,29.95)]
        result,groups=classify_footprints(self.shapes(),buildings)
        self.assertEqual(result["boundary_or_datum_uncertain"],1)
        self.assertEqual(groups,{})

    def test_roofprint_spanning_two_parishes_never_selected_by_centroid(self):
        buildings=[self.box(-90.101,29.94,-90.099,29.95)]
        results,groups=classify_footprints(self.shapes(),buildings)
        self.assertEqual(results["multiple_parish_intersections"],1)
        self.assertEqual(groups,{})

    def test_outside_all_source_regions_is_explicit(self):
        buildings=[self.box(-91.1,29.94,-91.0,29.95)]
        results,groups=classify_footprints(self.shapes(),buildings)
        self.assertEqual(results["outside_all_parishes"],1)
        self.assertEqual(groups,{})

    def test_original_source_geometry_overlap_is_ambiguous(self):
        shapes=self.shapes()
        shapes["22051"]=self.box(-90.19,29.9,-90.09,30.0)
        results,groups=classify_footprints(
            shapes,[self.box(-90.18,29.94,-90.17,29.95)])
        self.assertEqual(results["multiple_parish_intersections"],1)
        self.assertEqual(groups,{})

    def test_geoids_are_exact_census_state_and_county_codes(self):
        shapes={"LA-Orleans":self.box(-90.2,29.9,-90.1,30)}
        with self.assertRaises(SourceJoinError):
            classify_footprints(
                shapes,[self.box(-90.18,29.94,-90.17,29.95)])

    def test_nans_and_nonpolygon_source_inputs_never_pass(self):
        shapes=self.shapes()
        for bad in (None,0,float("nan"),"Polygon",{}):
            with self.subTest(bad=str(bad)), self.assertRaises(SourceJoinError):
                classify_footprints(shapes,[bad])

    def test_margin_cannot_be_silently_zeroed_or_nonfinite(self):
        for value in (0,-1,float("nan"),float("inf"),True,1000):
            with self.subTest(v=str(value)),self.assertRaises(SourceJoinError):
                classify_footprints(
                    self.shapes(),[self.box(-90.18,29.94,-90.17,29.95)],
                    boundary_margin_m=value)

    def test_original_ms_zip_deflate_prefix_synthetic_20(self):
        result=_source_geojson_prefix(invent_ms_prefix())
        self.assertEqual(len(result),20)
        self.assertTrue(all(x.geom_type=="Polygon" for x in result))

    def test_changed_original_member_or_zip_signature_blocked(self):
        for args in ({"wrong_filename":True},{"wrong_magic":True}):
            with self.subTest(args=args),self.assertRaises(SourceJoinError):
                _source_geojson_prefix(invent_ms_prefix(**args))

    def test_shortened_or_wrong_source_prefix_blocked(self):
        with self.assertRaises(SourceJoinError):
            _source_geojson_prefix(invent_ms_prefix()[:100])
        with self.assertRaises(SourceJoinError):
            _source_geojson_prefix(b"\xff"*MS_PREFIX_BYTES)

    def test_source_with_fewer_than_20_features_is_not_extrapolated(self):
        from shapely.geometry import box,mapping
        one=[{"type":"Feature","properties":{},
              "geometry":mapping(box(-90.18,29.94,-90.17,29.95))}]
        with self.assertRaises(SourceJoinError):
            _source_geojson_prefix(invent_ms_prefix(features=one))

    def test_non_geojson_feature_collection_is_blocked(self):
        with self.assertRaises(SourceJoinError):
            _source_geojson_prefix(invent_ms_prefix(no_features_array=True))

    def test_wrong_source_feature_geometry_type_blocked(self):
        features=[{"type":"Feature","properties":{},
                   "geometry":{"type":"Point","coordinates":[-90.15,29.95]}}
                   for _ in range(20)]
        with self.assertRaises(SourceJoinError):
            _source_geojson_prefix(invent_ms_prefix(features=features))

    def test_polygon_crosswalk_categories_conserve_complete_sample(self):
        buildings=[self.box(-90.18,29.94,-90.17,29.95),
                   self.box(-90.10004,29.94,-90.10001,29.95),
                   self.box(-90.101,29.94,-90.099,29.95),
                   self.box(-91.1,29.94,-91.0,29.95)]
        summary,_=classify_footprints(self.shapes(),buildings)
        self.assertEqual(sum(summary.values()),len(buildings))
        self.assertEqual(summary, {
            "strict_matched":1,
            "boundary_or_datum_uncertain":1,
            "multiple_parish_intersections":1,
            "outside_all_parishes":1,
        })


if __name__=="__main__":
    unittest.main()
