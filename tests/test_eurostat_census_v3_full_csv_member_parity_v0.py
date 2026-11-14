# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Pure synthetic, entirely offline Eurostat CSV member parity fixtures."""
from __future__ import annotations

import hashlib
import io
import struct
import zlib
import unittest

from research_runners.eurostat_census_v3_full_csv_member_parity_v0 import (
    BANDS, HEADER, TARGET_CNTR_ID, TARGET_GRID_ID,
    CSV_MEMBER, EXPECTED_COMPRESSED_BYTES, EXPECTED_UNCOMPRESSED_BYTES,
    EXPECTED_ZIP_MEMBER_CRC32, CSVParityBlocked, verify_csv_deflate_member,
    verify_original_zip_local_header,
)


def make_row(*, grid_id=TARGET_GRID_ID, country=TARGET_CNTR_ID, total="100",
             male="40", first_age="10"):
    fields = {
        "GRD_ID":grid_id, "T":total, "M":male, "F":"60",
        "Y_LT15":first_age,"Y_1564":"60","Y_GE65":"30","EMP":"70",
        "NAT":"90","EU_OTH":"5","OTH":"5","SAME":"90",
        "CHG_IN":"8","CHG_OUT":"2","LAND_SURFACE":"1.0",
        "POPULATED":"1","CNTR_ID":country
    }
    return ",".join(fields[x] for x in HEADER)


def fake_member(*, lines=None, header=None):
    if lines is None:
        lines = [make_row(grid_id="CRS3035RES1000mN1000000E1000000"),
                 make_row(),
                 make_row(grid_id="CRS3035RES1000mN1001000E1001000")]
    source = ("\n".join([",".join(header or HEADER),*lines]) + "\n").encode("ascii")
    compressor = zlib.compressobj(level=6,wbits=-15)
    compressed = compressor.compress(source) + compressor.flush()
    bands = dict(zip(HEADER,lines[1].split(",")))
    ordered = ",".join(str(int(bands[b])) for b in BANDS).encode("ascii")
    digest = hashlib.sha256(ordered).hexdigest()
    return source,compressed,digest


def run_fake(source,member,digest,*,crc=None,uncompressed_size=None,
             compressed_size=None):
    return verify_csv_deflate_member(
        io.BytesIO(member),
        expected_compressed_bytes=compressed_size if compressed_size is not None else len(member),
        expected_uncompressed_bytes=uncompressed_size if uncompressed_size is not None else len(source),
        expected_crc32=crc if crc is not None else zlib.crc32(source),
        expected_cell_sha256=digest,
    )


class OneCellCSVSourceParityTests(unittest.TestCase):
    def test_synthetic_multiple_rows_validated_without_source_exposure(self):
        source,member,digest=fake_member()
        receipt=run_fake(source,member,digest)
        self.assertTrue(receipt["source_same_release_csv_tiff_14_band_parity"])
        self.assertTrue(receipt["original_zip_member_crc32_matches"])
        self.assertEqual(receipt["original_csv_row_count"],3)
        self.assertEqual(receipt["target_row_match_count"],1)
        self.assertEqual(receipt["uncompressed_original_csv_sha256"],hashlib.sha256(source).hexdigest())
        self.assertFalse(receipt["cat_model_input_approved"])
        self.assertFalse(receipt["legal_automation_review_cleared_by_this_script"])
        self.assertNotIn(make_row(),str(receipt))
        self.assertNotIn('100,40,60',str(receipt))

    def test_nonmatching_source_raster_fingerprint_blocks(self):
        source,member,digest=fake_member()
        with self.assertRaisesRegex(CSVParityBlocked,"disagree"):
            run_fake(source,member,"0"*64)

    def test_wrong_full_csv_crc_and_size_block(self):
        source,member,digest=fake_member()
        with self.assertRaisesRegex(CSVParityBlocked,"CRC32"):
            run_fake(source,member,digest,crc=123)
        with self.assertRaisesRegex(CSVParityBlocked,"uncompressed source exceeded"):
            run_fake(source,member,digest,uncompressed_size=len(source)-1)
        with self.assertRaisesRegex(CSVParityBlocked,"incomplete"):
            run_fake(source,member[:-4],digest,
                     compressed_size=len(member))

    def test_duplicate_target_or_wrong_country_block(self):
        source,member,digest=fake_member(lines=[
            make_row(grid_id="CRS3035RES1000mN1000000E1000000"),
            make_row(),make_row()])
        with self.assertRaisesRegex(CSVParityBlocked,"duplicate"):
            run_fake(source,member,digest)
        source,member,digest=fake_member(lines=[
            make_row(grid_id="CRS3035RES1000mN1000000E1000000"),
            make_row(country="XY"),make_row()])
        with self.assertRaisesRegex(CSVParityBlocked,"country"):
            run_fake(source,member,digest)

    def test_nonexistent_target_does_not_get_false_parity(self):
        others=[
            make_row(grid_id="CRS3035RES1000mN1000000E1000000"),
            make_row(grid_id="CRS3035RES1000mN1010000E1000000"),
            make_row(grid_id="CRS3035RES1000mN1020000E1000000")]
        source,member,digest=fake_member(lines=others)
        with self.assertRaisesRegex(CSVParityBlocked,"not found"):
            run_fake(source,member,digest)

    def test_bad_header_and_disclosure_codes_fail_closed(self):
        source,member,digest=fake_member(header=HEADER[:-1]+["WRONG"])
        with self.assertRaisesRegex(CSVParityBlocked,"header"):
            run_fake(source,member,digest)
        source,member,digest=fake_member(lines=[
            make_row(grid_id="CRS3035RES1000mN1000000E1000000"),
            make_row(total="-3"),make_row()])
        with self.assertRaisesRegex(CSVParityBlocked,"unexpected census negative"):
            run_fake(source,member,digest)
        source,member,digest=fake_member(lines=[
            make_row(grid_id="CRS3035RES1000mN1000000E1000000"),
            make_row(male="-8888"),
            make_row(grid_id="CRS3035RES1000mN1001000E1001000")])
        # Sentinel values are preserved in the canonical fingerprint, not zeros.
        self.assertTrue(run_fake(source,member,digest)
                        ["source_same_release_csv_tiff_14_band_parity"])

    def test_highly_compressible_valid_full_member_is_streamed_safely(self):
        # Repeated non-target census rows are deliberately synthetic and very
        # compressible. Their single deflate input chunk expands to much more
        # than MAX_OUTPUT_PER_CHUNK; this must NOT cause a false science failure.
        ordinary = make_row(grid_id="CRS3035RES1000mN1000000E1000000")
        source, member, digest = fake_member(lines=[
            ordinary, make_row(), *([ordinary] * 35000)])
        self.assertGreater(len(source), 2_097_152)
        self.assertLess(len(member), 65_536)
        receipt = run_fake(source, member, digest)
        self.assertEqual(receipt["original_csv_row_count"], 35002)
        self.assertEqual(receipt["target_row_match_count"], 1)
        self.assertTrue(receipt["source_same_release_csv_tiff_14_band_parity"])
        self.assertTrue(receipt["original_zip_member_crc32_matches"])
        self.assertFalse(receipt["cat_model_input_approved"])

    def test_wrong_source_inflation_and_long_line_block(self):
        source,member,digest=fake_member()
        with self.assertRaises(CSVParityBlocked):
            run_fake(source,b"not a deflate stream",digest)
        source,member,digest=fake_member(lines=[
            make_row(grid_id="CRS3035RES1000mN1000000E1000000"),
            make_row(),make_row(grid_id="CRS3035RES1000mN1001000E1001000")
                       + (",OVERLONG"*180)])
        with self.assertRaises(CSVParityBlocked):
            run_fake(source,member,digest)


def synthetic_zip_member_header(*, filename=CSV_MEMBER, flags=0,
                                crc=EXPECTED_ZIP_MEMBER_CRC32,
                                compressed=EXPECTED_COMPRESSED_BYTES,
                                uncompressed=EXPECTED_UNCOMPRESSED_BYTES,
                                extra=b""):
    # Synthetic structure and fake timestamps; not original GISCO ZIP bytes.
    encoded = filename.encode("utf-8")
    return (
        struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, flags, 8,
                    0, 0, crc, compressed, uncompressed, len(encoded), len(extra))
        + encoded + extra
    )


class ZIPLocalHeaderIdentityTests(unittest.TestCase):
    def test_exact_member_name_sizes_crc_and_offset_required(self):
        raw = synthetic_zip_member_header()
        evidence = verify_original_zip_local_header(raw)
        self.assertEqual(evidence["local_header_bytes"], len(raw))
        self.assertEqual(evidence["original_member"], CSV_MEMBER)
        self.assertEqual(evidence["absolute_compressed_payload_offset"],
                         evidence["local_header_offset"] + len(raw))
        self.assertTrue(evidence["original_member_crc32_match"])
        self.assertFalse(evidence["model_input_approved"])

    def test_valid_descriptor_header_with_zero_local_crc_and_sizes(self):
        raw = synthetic_zip_member_header(
            flags=0x0008, crc=0, compressed=0, uncompressed=0
        )
        evidence = verify_original_zip_local_header(raw)
        self.assertTrue(evidence["uses_zip_data_descriptor"])

    def test_wrong_member_encryption_crc_sizes_and_truncation_rejected(self):
        cases = [
            synthetic_zip_member_header(filename="different.csv"),
            synthetic_zip_member_header(flags=1),
            synthetic_zip_member_header(crc=0),
            synthetic_zip_member_header(compressed=2),
            synthetic_zip_member_header(uncompressed=4),
            synthetic_zip_member_header()[:-2],
            synthetic_zip_member_header() + b"trailing",
            synthetic_zip_member_header(flags=8, crc=1, compressed=0, uncompressed=0),
            b"not-a-zip-file",
        ]
        for raw in cases:
            with self.subTest(length=len(raw), header_sha=hashlib.sha256(raw).hexdigest()):
                with self.assertRaises(CSVParityBlocked):
                    verify_original_zip_local_header(raw)


if __name__=="__main__":
    unittest.main()
