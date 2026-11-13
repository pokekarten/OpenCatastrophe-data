# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely synthetic native Shapefile stream and ROI geometry gate tests."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import struct
import unittest
from unittest.mock import patch
import zlib
from research_runners import bvv_oberbayern_full_shp_roi_stream_v0 as p

HAS_GEOMETRY = (importlib.util.find_spec("shapely") is not None and
                importlib.util.find_spec("pyproj") is not None)


def synthetic_source(*, clockwise=True, count=2):
    # No source or private buildings: two identical fake 20x10m polygons.
    points=[(650000.,5350000.),(650000.,5350010.),
            (650020.,5350010.),(650020.,5350000.),(650000.,5350000.)]
    if not clockwise:
        points=list(reversed(points))
    raw=bytearray(100)
    length=100+count*(8+128)
    struct.pack_into(">I",raw,0,9994)
    struct.pack_into(">I",raw,24,length//2)
    struct.pack_into("<II",raw,28,1000,5)
    struct.pack_into("<4d",raw,36,500000.,5200000.,800000.,5500000.)
    for number in range(1,count+1):
        body=bytearray(128)
        struct.pack_into("<I",body,0,5)
        struct.pack_into("<4d",body,4,650000.,5350000.,650020.,5350010.)
        struct.pack_into("<II",body,36,1,5)
        struct.pack_into("<I",body,44,0)
        for j,(x,y) in enumerate(points):
            struct.pack_into("<2d",body,48+j*16,x,y)
        raw.extend(struct.pack(">II",number,64))
        raw.extend(body)
    return bytes(raw)


class BavarianFullOriginalSyntheticTests(unittest.TestCase):
    def new_parser(self,raw,roi=None):
        return p.NativeSHPStream(expected_records=2,
                                 expected_bytes=len(raw),expected_header_sha=None,
                                 roi=roi)

    def test_all_original_file_records_stream_without_disk(self):
        raw=synthetic_source()
        q=self.new_parser(raw)
        for offset in range(0,len(raw),17):
            q.feed(raw[offset:offset+17])
        result=q.finish()
        self.assertEqual(result["original_full_native_records_checked"],2)
        self.assertEqual(result["original_full_decoded_shape_sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["original_full_decoded_shape_crc32"],f"{zlib.crc32(raw):08x}")
        self.assertEqual(result["original_max_content_bytes"],128)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["source_coordinates_geometries_or_bytes_persisted"])
        self.assertNotIn("650000",str(result))

    @unittest.skipUnless(HAS_GEOMETRY,"optional pinned source job GEOS/PROJ unavailable")
    def test_projected_frozen_native_ghsl_grid_not_100m_equivalent(self):
        q, bbox=p.frozen_roi_geometries()
        self.assertTrue(q.is_valid)
        self.assertGreater(q.area,100_000_000)
        self.assertLess(q.area,2_000_000_000)
        expected=(11.440416643747994,48.007916676356096,
                  11.707083309358438,48.27458334194954)
        for got, want in zip(bbox,expected):
            self.assertAlmostEqual(got,want,places=9)

    @unittest.skipUnless(HAS_GEOMETRY,"optional pinned source job GEOS/PROJ unavailable")
    def test_polygon_union_eliminates_double_counting(self):
        from shapely.geometry import box
        raw=synthetic_source()
        q=self.new_parser(raw,roi=box(649900,5349900,650030,5350030))
        for offset in range(0,len(raw),29):
            q.feed(raw[offset:offset+29])
        x=q.finish()
        self.assertEqual(x["roi_bbox_candidates"],2)
        self.assertEqual(x["roi_original_polygon_records_intersecting"],2)
        self.assertEqual(x["roi_original_polygon_areas_sum_pre_union_m2"],400.)
        self.assertEqual(x["roi_original_polygon_areas_union_m2"],200.)
        self.assertEqual(x["roi_original_polygon_overlap_area_m2"],200.)
        self.assertFalse(x["ghsl_actual_accuracy_or_tiv_validated"])

    @unittest.skipUnless(HAS_GEOMETRY,"optional pinned source job GEOS/PROJ unavailable")
    def test_counterclockwise_native_shell_blocks_unreviewed_hole_topology(self):
        from shapely.geometry import box
        raw=synthetic_source(clockwise=False)
        q=self.new_parser(raw,roi=box(649900,5349900,650030,5350030))
        with self.assertRaisesRegex(p.FullSHPBlocked,"clockwise"):
            q.feed(raw)

    @unittest.skipUnless(HAS_GEOMETRY,"optional pinned source job GEOS/PROJ unavailable")
    def test_hierarchical_union_batches_bound_memory_beyond_first_two_shapes(self):
        from shapely.geometry import box
        raw=synthetic_source(count=6)
        q=p.NativeSHPStream(expected_records=6,expected_bytes=len(raw),
                            expected_header_sha=None,
                            roi=box(649900,5349900,650030,5350030))
        # Force tiny 2-shape batches to exercise multiple binary-carry
        # merge levels using solely synthetic repeated overlapping shapes.
        with patch.object(p,"MAX_PENDING_ROI_FEATURES",2):
            for i in range(0,len(raw),37):
                q.feed(raw[i:i+37])
            self.assertLessEqual(len(q.roi_clipped_geometries),1)
            result=q.finish()
        self.assertEqual(result["roi_original_polygon_records_intersecting"],6)
        self.assertEqual(result["roi_original_polygon_areas_sum_pre_union_m2"],1200.)
        self.assertEqual(result["roi_original_polygon_areas_union_m2"],200.)
        self.assertEqual(result["roi_original_polygon_overlap_area_m2"],1000.)
        self.assertEqual(result["roi_geos_union_batches_completed"],3)
        self.assertLessEqual(result["roi_geos_union_active_levels"],2)
        self.assertFalse(result["model_input_approved"])

    def test_malformed_header_record_numbers_truncation_and_extra_bytes_block(self):
        raw=synthetic_source()
        for offset,format_,value in ((0,">I",11),(24,">I",3),
                                      (32,"<I",1),(100,">I",3),
                                      (104,">I",9000)):
            with self.subTest(offset=offset):
                corrupted=bytearray(raw)
                struct.pack_into(format_,corrupted,offset,value)
                q=self.new_parser(bytes(corrupted))
                with self.assertRaises(p.FullSHPBlocked):
                    q.feed(bytes(corrupted))
        q=self.new_parser(raw)
        q.feed(raw[:-12])
        with self.assertRaises(p.FullSHPBlocked):
            q.finish()
        with self.assertRaises(p.FullSHPBlocked):
            self.new_parser(raw).feed(raw+b"EXTRA")

    def test_network_rejects_http_200_wrong_origin_and_missing_range(self):
        for code,url in ((200,p.URL),(206,"https://malicious.invalid/path")):
            with self.assertRaises(p.FullSHPBlocked):
                p.inspect_original_stream(io.BytesIO(),status=code,
                                          response_url=url,headers={},roi=None)
        with self.assertRaises(p.FullSHPBlocked):
            p.inspect_original_stream(io.BytesIO(),status=206,
                                     response_url=p.URL,headers={},roi=None)

    def test_verified_original_range_segments_are_exactly_contiguous(self):
        from unittest.mock import patch
        chunks = []
        original = b"abcdefghijklmnopqrstuvwxyz0123456789"
        reader = p.VerifiedOriginalSegmentStream()
        def fake_get(start, end):
            chunks.append((start, end))
            return original[start-100:end-99], ('"same-source"', "Fri, 13 Nov 2026 11:00:00 GMT")
        reader._get_segment = fake_get
        with (patch.object(p, "START", 100),
              patch.object(p, "END", 135),
              patch.object(p, "READ_BYTES", 36),
              patch.object(p, "MAX_ORIGINAL_SEGMENT_BYTES", 9)):
            pieces=[]
            while True:
                block=reader.read(7)
                if not block:
                    break
                pieces.append(block)
            self.assertEqual(b"".join(pieces), original)
            self.assertEqual(chunks, [(100,108),(109,117),(118,126),(127,135)])
            self.assertEqual(reader.requests_verified,4)
            self.assertTrue(reader.complete())
            self.assertEqual(reader.http_bytes_verified,36)
            self.assertEqual(reader.read(1),b"")

    def test_segment_truncation_and_source_mutation_fail_closed(self):
        reader=p.VerifiedOriginalSegmentStream()
        reader._get_segment=lambda start,end: (b"bad",("etag","date"))
        with (patch.object(p,"START",100),patch.object(p,"END",125),
              patch.object(p,"MAX_ORIGINAL_SEGMENT_BYTES",8)):
            with self.assertRaisesRegex(p.FullSHPBlocked,"size"):
                reader.read(5)
        reader=p.VerifiedOriginalSegmentStream()
        def changed_validator(start,end):
            etag='"source-v1"' if start==100 else '"source-v2"'
            return b"x"*(end-start+1),(etag,"date")
        reader._get_segment=changed_validator
        with (patch.object(p,"START",100),patch.object(p,"END",115),
              patch.object(p,"MAX_ORIGINAL_SEGMENT_BYTES",8)):
            self.assertEqual(reader.read(8),b"x"*8)
            with self.assertRaisesRegex(p.FullSHPBlocked,"ETag"):
                reader.read(8)

    def test_segment_trust_cannot_be_asserted_by_unvalidated_file_reader(self):
        import io
        with self.assertRaisesRegex(p.FullSHPBlocked, "exact verified source reader"):
            p.inspect_original_stream(io.BytesIO(b"X"*100),status=206,
                response_url=p.URL,headers={},roi=None,verified_segments=True)

    def test_explicit_live_main_opt_in_required(self):
        with self.assertRaises(SystemExit) as ctx:
            p.main([])
        self.assertNotEqual(ctx.exception.code,0)


if __name__=="__main__":
    unittest.main()
