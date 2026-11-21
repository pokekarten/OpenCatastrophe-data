# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline ZIP64, pathname, source-CRS and bounded EOCD/central dir challenges."""
import io
from pathlib import Path
import struct
import sys
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"research_runners"))
from rva_nrw_hu_2022_original_zip_range_receipt_v0 import (
    eocd_from_last_bytes,parse_directory,OriginalZipBlocked,MAX_TAIL
)

SHIFT=850_000_000

def make_entries(*,include_prj=True,malicious=False):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        stem='../bad' if malicious else 'nrw_2022_hausumringe'
        for ext in ('.shp','.shx','.dbf')+ (('.prj',) if include_prj else ()):
            z.writestr(stem+ext,b"fake geometries never promoted to an insured site")
    return out.getvalue()

def fixture(data:bytes):
    eocd_pos=data.rfind(b"PK\x05\x06")
    assert eocd_pos>0
    orig_cd=struct.unpack_from('<I',data,eocd_pos+16)[0]
    cdsize=struct.unpack_from('<I',data,eocd_pos+12)[0]
    edited=bytearray(data)
    struct.pack_into('<I',edited,eocd_pos+16,orig_cd+SHIFT)
    buf=bytes(edited)
    total=len(buf)+SHIFT
    tail=buf[-MAX_TAIL:]
    record=eocd_from_last_bytes(tail,total-len(tail),total)
    assert record['central_offset']==orig_cd+SHIFT
    return record, data[orig_cd:orig_cd+cdsize]

class TestOriginalRangeReceipt(unittest.TestCase):
    def test_valid_original_style_zip_central_directory_metadata_only(self):
        receipt,directory=fixture(make_entries())
        self.assertEqual(receipt['member_count'],4)
        records=parse_directory(directory,receipt['member_count'])
        self.assertEqual({r['name'].rsplit('.',1)[-1] for r in records},{'shp','shx','dbf','prj'})
        self.assertTrue(all(r['compressed_bytes']>0 for r in records))

    def test_missing_prj_or_path_traversal_denied(self):
        for d in (make_entries(include_prj=False), make_entries(malicious=True)):
            record,directory=fixture(d)
            with self.assertRaises(OriginalZipBlocked):
                parse_directory(directory,record['member_count'])

    def test_invalid_eocd_bombs_and_duplicate_are_denied(self):
        record,central=fixture(make_entries())
        for modified in (central[:-1], b'not-a-central-directory'):
            with self.assertRaises(OriginalZipBlocked):
                parse_directory(modified,record['member_count'])
        with self.assertRaises(OriginalZipBlocked):
            eocd_from_last_bytes(b'bad',SHIFT,SHIFT+3)
        with self.assertRaises(OriginalZipBlocked):
            eocd_from_last_bytes(b'not-a-zip'*9000,SHIFT,SHIFT+81000)
        with self.assertRaises(OriginalZipBlocked):
            parse_directory(central,record['member_count']+1)

if __name__=='__main__':
    unittest.main()
