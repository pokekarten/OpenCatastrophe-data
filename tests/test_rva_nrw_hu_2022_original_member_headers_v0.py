# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline genuine ZIP layout and invented header semantic challenges only."""
import io
import struct
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
import rva_nrw_hu_2022_original_member_headers_v0 as m
from rva_nrw_hu_2022_original_zip_range_receipt_v0 import parse_directory,OriginalZipBlocked


def small_zip():
    z=io.BytesIO()
    with zipfile.ZipFile(z,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        for suffix in ("shp","shx","dbf","prj"):
            archive.writestr("2022_hu_shp."+suffix, b"ETRS UTM test bytes only "+suffix.encode()*8)
    return z.getvalue()


def original_styled_records():
    n=11_232_755
    prj=("PROJCS[\"ETRS89 / UTM Zone 32N\",GEOGCS[\"ETRS89\",DATUM[\"ETRS_1989\"]]]").encode()*2
    header_length=65
    rec_length=46
    dbf=bytearray(header_length)
    dbf[0]=3
    struct.pack_into("<I",dbf,4,n)
    struct.pack_into("<H",dbf,8,header_length)
    struct.pack_into("<H",dbf,10,rec_length)
    dbf[32:35]=b"AGS"
    dbf[43]=ord("C")
    dbf[48]=8
    dbf[64]=13
    shp=bytearray(100)
    struct.pack_into(">I",shp,0,9994)
    struct.pack_into(">I",shp,24,500)
    struct.pack_into("<I",shp,28,1000)
    struct.pack_into("<I",shp,32,5)
    struct.pack_into("<dddd",shp,36,6.3,50.6,8.3,52.2)
    records=[
        {"name":"2022_hu_shp."+suffix,
         "uncompressed_bytes":value,
         "compressed_bytes":20, "local_header_offset":0,"method":8,"crc32_hex":"00000000"}
        for suffix,value in (
            ("prj",len(prj)),("dbf",header_length+rec_length*n+1),
            ("shp",1000),("shx",100+8*n))
    ]
    return records,{".prj":(prj,True),".dbf":(bytes(dbf),False),".shp":(bytes(shp),False)}


class TestHUHeader(unittest.TestCase):
    def test_local_zip_member_prefix_checks_original_compressed_bytes(self):
        data=small_zip()
        eocd=data.rfind(b"PK\x05\x06")
        cd=struct.unpack_from("<I",data,eocd+16)[0]
        size=struct.unpack_from("<I",data,eocd+12)[0]
        count=struct.unpack_from("<H",data,eocd+10)[0]
        members=parse_directory(data[cd:cd+size],count)
        for item in members:
            prefix,complete=m.read_member_prefix(item,len(data),
                 range_fn=lambda start,end,total:data[start:end+1])
            self.assertTrue(complete)
            self.assertIn(b"ETRS UTM test bytes",prefix)

    def test_dbf_shx_count_and_projected_bbox_cross_check(self):
        members,data=original_styled_records()
        def fake(member,total,range_fn=None):
            suffix="."+member["name"].rsplit(".",1)[1]
            return data[suffix]
        with patch.object(m,"read_member_prefix",side_effect=fake):
            result=m.verify_headers(members,901092946)
        self.assertEqual(result["original_2022_HU_DBF_row_count"],11232755)
        self.assertEqual(result["original_2022_HU_SHX_index_record_count"],11232755)
        self.assertEqual(result["original_DBF_fields"][0]["name"],"AGS")
        self.assertFalse(result["actual_original_ZIP_full_sha256_verified"])
        self.assertFalse(result["individual_OED_sites_geocoded"])

    def test_bad_index_count_or_crs_blocks(self):
        members,data=original_styled_records()
        for typ in ("wrong_count","wrong_prj","wrong_stem"):
            corrupted=[dict(x) for x in members]
            payload=dict(data)
            if typ=="wrong_count":
                corrupted[-1]["uncompressed_bytes"]-=8
            elif typ=="wrong_prj":
                payload[".prj"]=(b"UNKNOWN REFERENCE STUFF"*8,True)
            else:
                corrupted[-1]["name"]="2030_hu_shp.shx"
            def fake(member,total,range_fn=None):
                return payload["."+member["name"].rsplit(".",1)[1]]
            with self.subTest(typ=typ),patch.object(m,"read_member_prefix",side_effect=fake):
                with self.assertRaises(OriginalZipBlocked):
                    m.verify_headers(corrupted,901092946)


if __name__=="__main__":
    unittest.main()
