# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fully synthetic original-archive streamed TIFF tail metadata / source guard."""
import io
import json
from hashlib import sha256
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from research_runners import berlin_srgk_rare_original_ifd_stream_v0 as m
from research_runners import berlin_srgk_depth_zip_central_range_v0 as zip_index


def synthetic_tiff():
    length=300000
    offset=length-200
    b=bytearray(length)
    struct.pack_into("<2sHI",b,0,b"II",42,offset)
    tags=[
        (256,4,1,4321),
        (257,4,1,8765),
        (33550,12,3,offset+82),
        (34735,3,8,offset+110),
        (42113,2,6,offset+130),
        (339,3,1,1),
    ]
    struct.pack_into("<H",b,offset,len(tags))
    for i,(tag,kind,count,value) in enumerate(tags):
        struct.pack_into("<HHII",b,offset+2+i*12,tag,kind,count,value)
    struct.pack_into("<I",b,offset+2+len(tags)*12,0)
    struct.pack_into("<ddd",b,offset+82,1.5,1.5,0.0)
    struct.pack_into("<8H",b,offset+110,1,1,0,1,3072,0,1,25833)
    b[offset+130:offset+136]=b"-9999\0"
    return bytes(b),offset


def source_zip():
    source,_=synthetic_tiff()
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("rare-example.tif",source)
        z.comment=b"Q"*65535
    return buffer.getvalue()


def set_source_constants(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        info=z.infolist()[0]
    index_offset,index_size,_=zip_index.locate_eocd(
        raw[-zip_index.TAIL:],len(raw)
    )
    central=raw[index_offset:index_offset+index_size]
    _,offset=synthetic_tiff()
    return [
      patch.object(m,"ZIP_BYTES",len(raw)),
      patch.object(m,"ZIP_CENTRAL_SHA256",sha256(central).hexdigest()),
      patch.object(m,"TIFF_NAME","rare-example.tif"),
      patch.object(m,"TIFF_BYTES",info.file_size),
      patch.object(m,"TIFF_COMPRESSED",info.compress_size),
      patch.object(m,"TIFF_IFD_OFFSET",offset),
    ]


class SourceResponse:
    status=200
    def __init__(self,req,raw,*,bad_length=False,bad_media=False):
        self.req=req
        self.stream=io.BytesIO(raw)
        self.reads=0
        self.headers={
            "Content-Length":str(len(raw)+1 if bad_length else len(raw)),
            "Content-Type":"text/html" if bad_media else "application/zip",
            "Content-Encoding":"identity",
        }
    def geturl(self):
        return self.req.full_url
    def read(self,count):
        self.reads+=1
        return self.stream.read(count)
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False


class OriginalRareSourceTests(unittest.TestCase):
    def test_exact_source_original_url_and_scientific_identity(self):
        self.assertEqual(m.ZIP_URL,
          "https://gdi.berlin.de/data/ua_srgk/atom/wasserstand_seltenes_ereignis.zip")
        self.assertEqual(m.ZIP_BYTES,132689382)
        self.assertEqual(m.TIFF_IFD_OFFSET,167112958)

    def test_tail_extracts_tiff_dimensions_projected_key_and_nodata_candidate(self):
        raw,offset=synthetic_tiff()
        with patch.object(m,"TIFF_IFD_OFFSET",offset):
            out=m.extract_tiff_tail_metadata(raw[-m.TAIL_LIMIT:],raw[:8],len(raw))
        self.assertEqual(out["raster_width_px"],4321)
        self.assertEqual(out["raster_height_px"],8765)
        self.assertEqual(out["geokey_direct_numeric_ids"]["3072"],25833)
        self.assertEqual(out["horizontal_pixel_scale_candidate"],[1.5,1.5,0.0])
        self.assertEqual(out["source_nodata_ascii_candidate"],"-9999")
        self.assertFalse(out["insured_model_input_admitted"])
        self.assertFalse(out["physical_flood_depth_unit_scale_authoritatively_verified"])

    def test_false_or_missing_metadata_rejected_not_imputed(self):
        raw,offset=synthetic_tiff()
        with patch.object(m,"TIFF_IFD_OFFSET",offset):
            with self.assertRaisesRegex(m.OriginalTiffBlocked,"outside"):
                m.extract_tiff_tail_metadata(raw[-100:],raw[:8],len(raw))
            with self.assertRaisesRegex(m.OriginalTiffBlocked,"offset drift"):
                m.extract_tiff_tail_metadata(raw[-m.TAIL_LIMIT:],
                    struct.pack("<2sHI",b"II",42,offset-2),len(raw))
            bad=bytearray(raw)
            struct.pack_into("<H",bad,offset,513)
            with self.assertRaisesRegex(m.OriginalTiffBlocked,"overlarge"):
                m.extract_tiff_tail_metadata(bytes(bad[-m.TAIL_LIMIT:]),
                    bytes(bad[:8]),len(bad))

    def test_complete_synthetic_archive_stream_has_crc_and_no_pixels_in_result(self):
        raw=source_zip()
        contexts=set_source_constants(raw)
        with tempfile.TemporaryDirectory() as temp:
            location=Path(temp)/"rare.zip"
            location.write_bytes(raw)
            for ctx in contexts:
                ctx.__enter__()
            try:
                result=m.inspect_archive(location)
                self.assertEqual(result["raster_width_px"],4321)
                self.assertEqual(result["raster_height_px"],8765)
                self.assertEqual(result["original_uncompressed_member_bytes_streamed"],300000)
                self.assertTrue(result["original_member_crc_read_to_end"])
                self.assertFalse(result["original_member_bytes_or_pixels_persisted"])
                self.assertFalse(result["insured_model_input_admitted"])
                self.assertNotIn("Q"*100,json.dumps(result))
            finally:
                for ctx in reversed(contexts):
                    ctx.__exit__(None,None,None)

    def test_revision_drift_blocks_before_decompression(self):
        raw=source_zip()
        contexts=set_source_constants(raw)
        with tempfile.TemporaryDirectory() as temp:
            location=Path(temp)/"rare.zip"
            location.write_bytes(raw)
            for ctx in contexts:
                ctx.__enter__()
            try:
                with patch.object(m,"ZIP_CENTRAL_SHA256","0"*64):
                    with self.assertRaisesRegex(m.OriginalTiffBlocked,"SHA"):
                        m.original_directory_check(location)
            finally:
                for ctx in reversed(contexts):
                    ctx.__exit__(None,None,None)

    def test_http_source_length_mismatch_rejected_before_read(self):
        raw=source_zip()
        record=[]
        def fake(req,timeout):
            r=SourceResponse(req,raw,bad_length=True)
            record.append(r)
            return r
        with tempfile.TemporaryDirectory() as temp,patch.object(m,"ZIP_BYTES",len(raw)):
            with self.assertRaisesRegex(m.OriginalTiffBlocked,"size changed"):
                m.download_ephemeral(Path(temp)/"source.zip",opener=fake)
        self.assertEqual(record[0].reads,0)

    def test_one_original_source_only_temp_deleted_and_model_closed(self):
        raw=source_zip()
        contexts=set_source_constants(raw)
        calls=[]
        def fake(req,timeout):
            calls.append((req.get_method(),req.full_url))
            return SourceResponse(req,raw)
        for ctx in contexts:
            ctx.__enter__()
        try:
            result=m.probe(opener=fake)
        finally:
            for ctx in reversed(contexts):
                ctx.__exit__(None,None,None)
        self.assertEqual(calls,[("GET",m.ZIP_URL)])
        self.assertEqual(result["original_zip_bytes_streamed"],len(raw))
        self.assertTrue(result["private_temp_source_archive_deleted"])
        self.assertFalse(result["cat_model_input_approved"])
        self.assertFalse(result["second_pilot_raster_extent_intersection_not_yet_proven"] is False)
        self.assertEqual(result["raster_height_px"],8765)
        self.assertNotIn("Q"*100,json.dumps(result))


if __name__=="__main__":
    unittest.main()
