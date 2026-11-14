# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic short DBF/ZIP fixture; no real Bavarian identifiers or geometry."""
from __future__ import annotations

from unittest import TestCase, main
from unittest.mock import patch
import hashlib
import struct
import zlib

from research_runners import by_hausumringe_oberbayern_dbf_v0 as dbf


def synthetic_original(*, deleted=False):
    body=bytearray(65)
    body[0]=3
    body[1:4]=bytes((126,11,12))
    struct.pack_into("<IHH",body,4,3,65,10)
    body[32:38]=b"TESTID"
    body[43]=ord("C")
    body[48]=9
    body[49]=0
    body[64]=0x0d
    for i in range(3):
        flag=b"*" if deleted and i==1 else b" "
        body.extend(flag+(f"fake{i:04d}x".encode("ascii")))
    assert len(body)==95
    z=zlib.compressobj(level=6,wbits=-15)
    comp=z.compress(body)+z.flush()
    crc=zlib.crc32(body)
    result=bytearray(45+len(comp))
    struct.pack_into(
        "<4sHHHHHIIIHH",result,0,b"PK\x03\x04",20,0,8,0,0,
        crc,len(comp),len(body),15,0
    )
    result[30:45]=b"hausumringe.dbf"
    result[45:]=comp
    return bytes(result),bytes(body),comp,crc


def transport(length):
    return {
        "Content-Range":f"bytes 0-{length-1}/{dbf.TOTAL}",
        "Content-Length":str(length),
        "Content-Type":"application/zip",
        "Content-Encoding":"identity",
    }


class DBFFakeSourceTests(TestCase):
    def _fixture(self,*,deleted=False):
        packet,body,compressed,crc=synthetic_original(deleted=deleted)
        patches={
            "MAX_READ":len(packet),
            "END":len(packet)-1,
            "COMPRESSED_BYTES":len(compressed),
            "UNCOMPRESSED_BYTES":len(body),
            "ORIGINAL_CRC32":crc,
            "EXPECTED_DBF_RECORDS":3,
            "EXPECTED_SHX_RECORDS_FROM_DIRECTORY":3,
            "FROZEN":{"hausumringe.prj":(len(packet),0,0)},
        }
        return packet,body,patches

    def test_synthetic_three_records_crcs_sha_and_no_identity_leak(self):
        packet,body,params=self._fixture(deleted=True)
        with patch.multiple(dbf,**params):
            proof=dbf.inspect_original_dbf(
                packet,status=206,response_url=dbf.URL,headers=transport(len(packet))
            )
        self.assertEqual(proof["dbf_original_record_count_verified"],3)
        self.assertEqual(proof["dbf_original_active_records"],2)
        self.assertEqual(proof["dbf_original_deleted_records"],1)
        self.assertEqual(proof["dbf_original_uncompressed_sha256"],hashlib.sha256(body).hexdigest())
        self.assertEqual(proof["dbf_original_header_update_date_file_metadata_only"],"2026-11-12")
        self.assertEqual(proof["dbf_attribute_field_count"],1)
        self.assertFalse(proof["shp_original_polygons_downloaded"])
        self.assertFalse(proof["original_provider_bytes_persisted"])
        self.assertFalse(proof["model_input_approved"])
        self.assertNotIn("TESTID",str(proof))
        self.assertNotIn("fake0",str(proof))

    def test_wrong_url_status_range_mime_and_encoding_block(self):
        packet,body,params=self._fixture()
        with patch.multiple(dbf,**params):
            cases=[
                (200,dbf.URL,transport(len(packet))),
                (206,"https://wrong.example/archive",transport(len(packet))),
                (206,dbf.URL,{**transport(len(packet)),"Content-Range":"bytes 0-999/174299765"}),
                (206,dbf.URL,{**transport(len(packet)),"Content-Length":"174299765"}),
                (206,dbf.URL,{**transport(len(packet)),"Content-Type":"text/html"}),
                (206,dbf.URL,{**transport(len(packet)),"Content-Encoding":"gzip"}),
            ]
            for status,url,h in cases:
                with self.subTest(status=status,url=url,h=h),self.assertRaises(dbf.DBFBlocked):
                    dbf.inspect_original_dbf(packet,status=status,response_url=url,headers=h)

    def test_wrong_zip_signature_or_entry_name_blocks(self):
        packet,body,params=self._fixture()
        with patch.multiple(dbf,**params):
            for pos in (0,8,30):
                wrong=bytearray(packet);wrong[pos]^=1
                with self.subTest(pos=pos),self.assertRaises(dbf.DBFBlocked):
                    dbf.inspect_original_dbf(bytes(wrong),status=206,response_url=dbf.URL,headers=transport(len(packet)))

    def test_bad_crc_and_invalid_compressed_payload_block(self):
        packet,body,params=self._fixture()
        with patch.multiple(dbf,**params):
            for pos in (14,len(packet)-3):
                wrong=bytearray(packet);wrong[pos]^=1
                with self.subTest(pos=pos),self.assertRaises(dbf.DBFBlocked):
                    dbf.inspect_original_dbf(bytes(wrong),status=206,response_url=dbf.URL,headers=transport(len(packet)))

    def test_deleted_flag_wrong_record_count_and_wrong_field_block(self):
        packet,body,params=self._fixture()
        for kind in ("record_count","field_type","delete_flag","terminator","date"):
            modified=bytearray(body)
            if kind=="record_count":
                struct.pack_into("<I",modified,4,4)
            elif kind=="field_type":
                modified[43]=ord("D")
            elif kind=="delete_flag":
                modified[65]=ord("?")
            elif kind=="terminator":
                modified[64]=0
            else:
                modified[2]=13
            z=zlib.compressobj(wbits=-15)
            compressed=z.compress(modified)+z.flush()
            crc=zlib.crc32(modified)
            blob=bytearray(45+len(compressed))
            struct.pack_into("<4sHHHHHIIIHH",blob,0,b"PK\x03\x04",20,0,8,0,0,
                             crc,len(compressed),len(modified),15,0)
            blob[30:45]=b"hausumringe.dbf";blob[45:]=compressed
            changed_params={
                **params,"MAX_READ":len(blob),"END":len(blob)-1,
                "COMPRESSED_BYTES":len(compressed),"UNCOMPRESSED_BYTES":len(modified),
                "ORIGINAL_CRC32":crc,
                "FROZEN":{"hausumringe.prj":(len(blob),0,0)},
            }
            with self.subTest(kind=kind),patch.multiple(dbf,**changed_params),self.assertRaises(dbf.DBFBlocked):
                dbf.inspect_original_dbf(bytes(blob),status=206,response_url=dbf.URL,headers=transport(len(blob)))

    def test_truncated_and_extended_response_fail_closed(self):
        packet,body,params=self._fixture()
        with patch.multiple(dbf,**params):
            for bad in (packet[:-1],packet+b"\0"):
                with self.assertRaises(dbf.DBFBlocked):
                    dbf.inspect_original_dbf(bad,status=206,response_url=dbf.URL,headers=transport(len(packet)))

    def test_original_full_zip_and_shx_not_approved(self):
        self.assertEqual(dbf.RANGE,"bytes=0-275601")
        self.assertEqual(dbf.MAX_READ,275602)
        self.assertEqual(dbf.EXPECTED_SHX_RECORDS_FROM_DIRECTORY,2703736)
        self.assertEqual(dbf.EXPECTED_DBF_RECORDS,2703736)


if __name__=="__main__":
    main()
