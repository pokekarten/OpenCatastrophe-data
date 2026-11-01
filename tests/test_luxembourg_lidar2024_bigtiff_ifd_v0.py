# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fully synthetic 4KiB byte-range and BigTIFF IFD fixture tests."""
from __future__ import annotations

import hashlib
import struct
import unittest

from research_runners import luxembourg_lidar2024_bigtiff_ifd_v0 as mod


def synthetic_tiff(*, width=10000, height=10000, tile_width=512,
                   geo_epsg=2169, first_ifd=16, is_tiled=True):
    raw=bytearray(max(8192,first_ifd+512))
    raw[:16]=struct.pack('<2sHHHQ',b'II',43,8,0,first_ifd)
    tiles=((width+tile_width-1)//tile_width)*((height+tile_width-1)//tile_width)
    tags=[
        (256,16,1,width),(257,16,1,height),(258,3,1,32),
        (259,3,1,8),(322,4,1,tile_width),(323,4,1,tile_width),
        (33550,12,3,720),(33922,12,6,760),
        (34735,3,8,820),
    ]
    if is_tiled:
        tags += [(324,16,tiles,1200),(325,16,tiles,2400)]
    raw[first_ifd:first_ifd+8]=struct.pack('<Q',len(tags))
    for i,(tag,typ,count,value) in enumerate(tags):
        start=first_ifd+8+i*20
        raw[start:start+20]=struct.pack('<HHQQ',tag,typ,count,value)
    raw[720:744]=struct.pack('<ddd',.5,.5,0.)
    raw[760:808]=struct.pack('<dddddd',0.,0.,0.,74000.,75000.,0.)
    raw[820:836]=struct.pack('<HHHHHHHH',1,1,0,1,3072,0,1,geo_epsg)
    return bytes(raw)


class FakeResponse:
    def __init__(self,body,status,headers):
        self.body,self.status,self.headers=body,status,headers
        self.read_calls=0
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def getcode(self):return self.status
    def info(self):return self.headers
    def read(self,n):
        self.read_calls+=1
        return self.body[:n]


class FakeOpener:
    def __init__(self,raw,*,status=206,range_mismatch=False):
        self.raw,self.status,self.range_mismatch=raw,status,range_mismatch
        self.requests,self.responses=[],[]
    def open(self,req,timeout=20):
        value=req.headers['Range'].removeprefix('bytes=')
        a,b=map(int,value.split('-'))
        headers={'Content-Range':f'bytes {a}-{b}/{40*1024**3}',
                 'Content-Length':'4096'}
        if self.range_mismatch:
            headers['Content-Range']=f'bytes {a+1}-{b}/{40*1024**3}'
        result=FakeResponse(self.raw[a:b+1],self.status,headers)
        self.requests.append(req)
        self.responses.append(result)
        return result


class OriginalBigTIFFMetadataTests(unittest.TestCase):
    def run_fixture(self,raw=None,**opts):
        original=raw if raw is not None else synthetic_tiff()
        opener=FakeOpener(original,**opts)
        digest=hashlib.sha256(original[:4096]).hexdigest()
        return mod.inspect('MNT',opener=opener,expected_first_sha=digest),opener

    def test_valid_source_bigtiff_internal_tiles_and_epsg(self):
        report,opener=self.run_fixture()
        self.assertEqual(report['declared_projected_epsg'],2169)
        self.assertEqual(report['raster_width_pixels'],10000)
        self.assertEqual(report['internal_tile_width_pixels'],512)
        self.assertEqual(report['internal_tile_count'],400)
        self.assertEqual(report['pixel_size_x_units'],0.5)
        self.assertEqual(report['source_metadata_range_requests'],1)
        self.assertEqual(report['source_metadata_bytes_read'],4096)
        self.assertFalse(report['CAT_model_input_admitted'])
        self.assertFalse(report['raster_pixel_values_read'])
        self.assertEqual(len(opener.requests),1)
        self.assertEqual(opener.requests[0].headers['Range'],'bytes=0-4095')

    def test_second_page_exact_range_only(self):
        raw=synthetic_tiff(first_ifd=4120)
        report,opener=self.run_fixture(raw)
        self.assertEqual(report['source_metadata_range_requests'],2)
        self.assertEqual(opener.requests[1].headers['Range'],'bytes=4096-8191')

    def test_no_full_body_read_on_status_200(self):
        op=FakeOpener(synthetic_tiff(),status=200)
        with self.assertRaisesRegex(mod.MetadataBlockError,'ignored HTTP range'):
            mod.inspect('MNT',opener=op,expected_first_sha=None)
        self.assertEqual(op.responses[0].read_calls,0)

    def test_bad_content_range_rejected_before_body(self):
        op=FakeOpener(synthetic_tiff(),range_mismatch=True)
        with self.assertRaisesRegex(mod.MetadataBlockError,'byte position'):
            mod.inspect('MNT',opener=op,expected_first_sha=None)
        self.assertEqual(op.responses[0].read_calls,0)

    def test_wrong_previously_observed_source_fragment_rejected(self):
        with self.assertRaisesRegex(mod.MetadataBlockError,'SHA-256 drift'):
            mod.inspect('MNS',opener=FakeOpener(synthetic_tiff()),expected_first_sha='0'*64)

    def test_wrong_epsg_fails_closed(self):
        with self.assertRaisesRegex(mod.MetadataBlockError,'EPSG:2169'):
            self.run_fixture(synthetic_tiff(geo_epsg=3857))

    def test_non_tiled_source_rejected(self):
        with self.assertRaisesRegex(mod.MetadataBlockError,'not a tiled'):
            self.run_fixture(synthetic_tiff(is_tiled=False))

    def test_ifd_outside_bounded_metadata_rejected(self):
        with self.assertRaisesRegex(mod.MetadataBlockError,'IFD pointer'):
            self.run_fixture(synthetic_tiff(first_ifd=1048576))

    def test_bad_first_ifd_count_rejected(self):
        raw=bytearray(synthetic_tiff())
        raw[16:24]=struct.pack('<Q',10000)
        with self.assertRaisesRegex(mod.MetadataBlockError,'tag count'):
            self.run_fixture(bytes(raw))

    def test_oversized_native_pixel_scale_rejected(self):
        raw=bytearray(synthetic_tiff())
        raw[720:728]=struct.pack('<d',100.)
        with self.assertRaisesRegex(mod.MetadataBlockError,'pixel scale'):
            self.run_fixture(bytes(raw))

    def test_unknown_asset_blocked_before_network(self):
        op=FakeOpener(synthetic_tiff())
        with self.assertRaisesRegex(mod.MetadataBlockError,'Unreviewed official asset'):
            mod.inspect('UNREVIEWED',opener=op)
        self.assertEqual(len(op.requests),0)


if __name__=='__main__':
    unittest.main()
