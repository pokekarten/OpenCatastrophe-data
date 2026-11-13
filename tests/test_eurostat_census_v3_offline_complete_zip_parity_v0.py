# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No Eurostat original provider bytes: tiny synthetic local ZIP files only."""
from __future__ import annotations

import hashlib
import struct
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from research_runners.eurostat_census_v3_full_csv_member_parity_v0 import (
    BANDS, CSV_MEMBER, HEADER, CSVParityBlocked, TARGET_GRID_ID,
)
from research_runners.eurostat_census_v3_offline_complete_zip_parity_v0 import (
    verify_complete_local_v3_zip,
)


def row(grid=TARGET_GRID_ID, country="NO", total=100):
    values = {
        "GRD_ID":grid, "T":str(total), "M":"40", "F":"60",
        "Y_LT15":"10", "Y_1564":"60", "Y_GE65":"30", "EMP":"70",
        "NAT":"90", "EU_OTH":"5", "OTH":"5", "SAME":"90",
        "CHG_IN":"8", "CHG_OUT":"2", "LAND_SURFACE":"1.0",
        "POPULATED":"1", "CNTR_ID":country,
    }
    return values, ",".join(values[x] for x in HEADER)


def write_source(path, *, target=True, country="NO", wrong_filename=False,
                 duplicate=False, comment=False):
    values, actual = row(country=country)
    other = row(grid="CRS3035RES1000mN1000000E1000000")[1]
    content = ("\n".join([",".join(HEADER), other] +
                         ([actual] if target else []) + [other]) + "\n").encode()
    with ZipFile(path,"w",compression=ZIP_DEFLATED) as z:
        name = "other.csv" if wrong_filename else CSV_MEMBER
        z.writestr(name,content)
        if duplicate:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                z.writestr(name,content)
        if comment:
            z.comment=b"not-an-original-eocd-comment"
    digest = hashlib.sha256(",".join(values[b] for b in BANDS).encode()).hexdigest()
    with ZipFile(path) as z:
        info=z.infolist()[0]
    return digest,info


def frozen_directory(path):
    with ZipFile(path, "r") as z:
        return {
            i.filename: (i.header_offset,i.compress_size,i.file_size,
                         i.CRC,i.compress_type)
            for i in z.infolist()
        }


def synthetic_eocd_reference(path):
    # Synthetic ZIP's original tail directory, not real Eurostat bytes.
    data=Path(path).read_bytes()
    pos=data.rfind(b"PK\\x05\\x06".replace(b"\\x05",b"\x05").replace(b"\\x06",b"\x06"))
    assert pos>=0
    fields=struct.unpack("<IHHHHIIH",data[pos:pos+22])
    return fields[6],fields[5]


def verify_fixture(path, digest, info, *, expected_names=(CSV_MEMBER,), **override):
    return verify_complete_local_v3_zip(
        Path(path),
        expected_zip_bytes=Path(path).stat().st_size,
        expected_member_names=expected_names,
        expected_member_directory=frozen_directory(Path(path)),
        expected_central_directory_offset=synthetic_eocd_reference(path)[0],
        expected_central_directory_size=synthetic_eocd_reference(path)[1],
        expected_csv_header_offset=info.header_offset,
        expected_csv_compressed_bytes=info.compress_size,
        expected_csv_uncompressed_bytes=info.file_size,
        expected_csv_crc32=info.CRC,
        expected_pixel_sha256=digest,
        **override,
    )


class V3CompleteOfflineZipTests(unittest.TestCase):
    def test_full_local_zip_rechecks_central_directory_local_header_and_stream(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"synthetic-v3.zip"
            digest,info=write_source(p)
            receipt=verify_fixture(p,digest,info)
            self.assertEqual(receipt["entire_local_zip_sha256_computed"],
                             hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(receipt["member_compressed_bytes"],info.compress_size)
            self.assertEqual(receipt["member_uncompressed_bytes"],info.file_size)
            self.assertEqual(receipt["target_row_match_count"],1)
            self.assertTrue(receipt["source_same_release_csv_tiff_14_band_parity"])
            self.assertTrue(receipt["original_zip_member_crc32_matches"])
            self.assertFalse(receipt["provider_origin_independently_authenticated"])
            self.assertFalse(receipt["provider_acquisition_rights_verified"])
            self.assertFalse(receipt["commercial_insurance_model_input_admitted"])
            self.assertNotIn(row()[1],str(receipt))

    def test_wrong_zip_source_name_and_comment_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"other.zip"
            digest,info=write_source(p,wrong_filename=True)
            with self.assertRaisesRegex(CSVParityBlocked,"directory"):
                verify_fixture(p,digest,info)
            digest,info=write_source(p,comment=True)
            with self.assertRaisesRegex(CSVParityBlocked,"EOCD|comment"):
                verify_fixture(p,digest,info)

    def test_missing_target_row_and_wrong_country_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.zip"
            digest,info=write_source(p,target=False)
            with self.assertRaisesRegex(CSVParityBlocked,"not found"):
                verify_fixture(p,digest,info)
            digest,info=write_source(p,country="XX")
            with self.assertRaisesRegex(CSVParityBlocked,"different official reporting country"):
                verify_fixture(p,digest,info)

    def test_modified_local_header_byte_and_wrong_crc_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.zip"
            digest,info=write_source(p)
            with self.assertRaisesRegex(CSVParityBlocked,"central directory CSV"):
                verify_complete_local_v3_zip(
                    p, expected_zip_bytes=p.stat().st_size,
                    expected_member_names=(CSV_MEMBER,),
                    expected_member_directory=frozen_directory(p),
                    expected_central_directory_offset=synthetic_eocd_reference(p)[0],
                    expected_central_directory_size=synthetic_eocd_reference(p)[1],
                    expected_csv_header_offset=info.header_offset,
                    expected_csv_compressed_bytes=info.compress_size,
                    expected_csv_uncompressed_bytes=info.file_size,
                    expected_csv_crc32=info.CRC^0x01,
                    expected_pixel_sha256=digest,
                )
            data=bytearray(p.read_bytes());data[0]^=0x01;p.write_bytes(data)
            with self.assertRaisesRegex(CSVParityBlocked,"ZIP CSV local signature"):
                verify_fixture(p,digest,info)

    def test_duplicate_zip_source_names_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"duplicates.zip"
            digest,info=write_source(p,duplicate=True)
            with self.assertRaisesRegex(CSVParityBlocked,"EOCD|central directory member"):
                verify_fixture(p,digest,info)

    def test_changed_non_csv_member_must_not_pass_frozen_directory(self):
        # A complete V3 archive cannot claim original identity when a second
        # member's central CRC changed while the population CSV stayed intact.
        # The ZIP and cell are synthetic; no original Eurostat source bytes.
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"synthetic-source.zip"
            digest,csv_info=write_source(p)
            with ZipFile(p,"r") as z:
                original_synthetic_csv=z.read(CSV_MEMBER)
            readme="Eurostat_Census-GRID_2021_V3/read.me"
            with ZipFile(p,"w",compression=ZIP_DEFLATED) as z:
                z.writestr(CSV_MEMBER,original_synthetic_csv)
                z.writestr(readme,b"alpha")
            pinned=frozen_directory(p)
            with ZipFile(p,"w",compression=ZIP_DEFLATED) as z:
                z.writestr(CSV_MEMBER,original_synthetic_csv)
                z.writestr(readme,b"bravo")
            with ZipFile(p,"r") as z:
                info=z.getinfo(CSV_MEMBER)
            self.assertNotEqual(pinned[readme][3],
                                frozen_directory(p)[readme][3])
            with self.assertRaisesRegex(CSVParityBlocked,"per-member metadata changed"):
                verify_complete_local_v3_zip(
                    p,
                    expected_zip_bytes=p.stat().st_size,
                    expected_member_names=(CSV_MEMBER,readme),
                    expected_member_directory=pinned,
                    expected_central_directory_offset=synthetic_eocd_reference(p)[0],
                    expected_central_directory_size=synthetic_eocd_reference(p)[1],
                    expected_csv_header_offset=info.header_offset,
                    expected_csv_compressed_bytes=info.compress_size,
                    expected_csv_uncompressed_bytes=info.file_size,
                    expected_csv_crc32=info.CRC,
                    expected_pixel_sha256=digest,
                )

    def test_eocd_trailer_and_central_directory_tamper_blocked(self):
        # Original V3 must end at the exact classic EOCD, not at hidden data.
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"bounded.zip"
            digest,info=write_source(p)
            initial=p.read_bytes()
            offset,size=synthetic_eocd_reference(p)
            receipt=verify_fixture(p,digest,info)
            self.assertEqual(receipt["eocd_central_directory_offset"],offset)
            self.assertEqual(receipt["eocd_central_directory_bytes"],size)
            self.assertTrue(receipt["eocd_exact_archive_termination_verified"])
            metadata={CSV_MEMBER:(info.header_offset,info.compress_size,
                                  info.file_size,info.CRC,info.compress_type)}
            corrupted=bytearray(initial)
            # Classic EOCD 4-byte directory offset begins at position -6.
            corrupted[-6]^=0x01
            p.write_bytes(corrupted)
            with self.assertRaisesRegex(CSVParityBlocked,"EOCD central directory"):
                verify_complete_local_v3_zip(
                    p,
                    expected_zip_bytes=len(corrupted),
                    expected_member_names=(CSV_MEMBER,),
                    expected_member_directory=metadata,
                    expected_central_directory_offset=offset,
                    expected_central_directory_size=size,
                    expected_csv_header_offset=info.header_offset,
                    expected_csv_compressed_bytes=info.compress_size,
                    expected_csv_uncompressed_bytes=info.file_size,
                    expected_csv_crc32=info.CRC,
                    expected_pixel_sha256=digest,
                )
            p.write_bytes(initial+b"X")
            with self.assertRaisesRegex(CSVParityBlocked,"size mismatch"):
                verify_complete_local_v3_zip(
                    p,
                    expected_zip_bytes=len(initial),
                    expected_member_names=(CSV_MEMBER,),
                    expected_member_directory=metadata,
                    expected_central_directory_offset=offset,
                    expected_central_directory_size=size,
                    expected_csv_header_offset=info.header_offset,
                    expected_csv_compressed_bytes=info.compress_size,
                    expected_csv_uncompressed_bytes=info.file_size,
                    expected_csv_crc32=info.CRC,
                    expected_pixel_sha256=digest,
                )

    def test_extra_bytes_or_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"source.zip"
            digest,info=write_source(p)
            with self.assertRaisesRegex(CSVParityBlocked,"size mismatch"):
                verify_complete_local_v3_zip(
                    p, expected_zip_bytes=p.stat().st_size+1,
                    expected_member_names=(CSV_MEMBER,),
                    expected_member_directory=frozen_directory(p),
                    expected_central_directory_offset=synthetic_eocd_reference(p)[0],
                    expected_central_directory_size=synthetic_eocd_reference(p)[1],
                    expected_csv_header_offset=info.header_offset,
                    expected_csv_compressed_bytes=info.compress_size,
                    expected_csv_uncompressed_bytes=info.file_size,
                    expected_csv_crc32=info.CRC,
                    expected_pixel_sha256=digest,
                )
            link=Path(tmp)/"symlink.zip"
            link.symlink_to(p)
            with self.assertRaisesRegex(CSVParityBlocked,"non-symlink"):
                verify_fixture(link,digest,info)


if __name__=="__main__":
    unittest.main()
