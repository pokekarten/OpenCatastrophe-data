# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only JRC 1.5 Occurrence TIFF prefix and percent/NoData gates."""
from __future__ import annotations

import hashlib
import json
import struct
import unittest

from scripts import preflight_jrc_gsw_v15_occurrence_header_v0 as jrc


def classic(*, width=40000, height=40000, compression=50000) -> bytes:
    raw = bytearray(jrc.PREFIX_BYTES)
    raw[:4] = b"II*\x00"
    struct.pack_into("<I", raw, 4, 8)
    entries = [
        (256,4,1,width), (257,4,1,height),
        (258,3,1,8), (259,3,1,compression),
        (277,3,1,1), (322,4,1,1024), (323,4,1,1024),
        (34735,3,4,1500),  # external GeoKey, not parsed/verified
    ]
    struct.pack_into("<H", raw, 8, len(entries))
    for index, tag in enumerate(entries):
        struct.pack_into("<HHII", raw, 10 + index * 12, *tag)
    return bytes(raw)


def big_tiff() -> bytes:
    raw = bytearray(jrc.PREFIX_BYTES)
    raw[:4] = b"MM\x00+"
    struct.pack_into(">HHQ",raw,4,8,0,16)
    struct.pack_into(">Q",raw,16,3)
    for i,entry in enumerate(((256,16,1,40000),(257,16,1,40000),
                              (277,3,1,1))):
        struct.pack_into(">HHQQ",raw,24+20*i,*entry)
    # Big-endian SHORT must occupy the first two bytes of its BigTIFF
    # value field, with six zero padding bytes in this synthetic fixture.
    struct.pack_into(">Q",raw,24+20*2+12,1 << 48)
    return bytes(raw)


class JRCGSWOccurrenceHeaderTests(unittest.TestCase):
    def test_classic_little_endian_exact_native_shape_without_admission(self):
        data=classic()
        rec=jrc.inspect_tiff_prefix(data)
        self.assertEqual(rec["source_id"],jrc.SOURCE_ID)
        self.assertEqual(rec["fixed_candidate_original_url"],jrc.SOURCE_URL)
        self.assertEqual(rec["external_prefix_sha256"],hashlib.sha256(data).hexdigest())
        self.assertEqual(rec["original_prefix_bytes"],4096)
        self.assertTrue(rec["first_ifd_fully_within_prefix"])
        self.assertTrue(rec["expected_10_degree_tile_40000x40000_if_inline"])
        self.assertTrue(rec["single_8bit_band_if_inline"])
        self.assertEqual(rec["compression_if_inline"],50000)
        self.assertEqual(rec["geotiff_tag_ids_if_visible"],[34735])
        for key in ("original_provider_source_identity_verified",
                    "whole_original_tiff_sha256_verified",
                    "post_2026_11_10_correction_verified",
                    "geospatial_crs_and_affine_verified",
                    "decoded_original_pixels_verified",
                    "source_downloaded_by_preflight",
                    "external_source_bytes_persisted_by_preflight",
                    "model_input_approved"):
            with self.subTest(flag=key):
                self.assertFalse(rec[key])
        self.assertNotIn("provider_body", json.dumps(rec))

    def test_big_endian_bigtiff_inline_long8_shape_supported(self):
        rec=jrc.inspect_tiff_prefix(big_tiff())
        self.assertEqual(rec["tiff_flavour"],"BigTIFF")
        self.assertEqual(rec["byte_order"],"big")
        self.assertEqual(rec["width_if_inline"],40000)
        self.assertEqual(rec["height_if_inline"],40000)
        self.assertEqual(rec["samples_per_pixel_if_inline"],1)
        self.assertTrue(rec["expected_10_degree_tile_40000x40000_if_inline"])
        self.assertFalse(rec["single_8bit_band_if_inline"])

    def test_incomplete_first_ifd_does_not_claim_dimensions(self):
        raw=bytearray(classic())
        struct.pack_into("<I",raw,4,8000)
        rec=jrc.inspect_tiff_prefix(bytes(raw))
        self.assertFalse(rec["first_ifd_fully_within_prefix"])
        self.assertIsNone(rec["first_ifd_entry_count_if_visible"])
        self.assertIsNone(rec["width_if_inline"])
        self.assertFalse(rec["expected_10_degree_tile_40000x40000_if_inline"])

    def test_truncated_first_ifd_stays_inconclusive(self):
        raw=bytearray(classic())
        struct.pack_into("<I",raw,4,4080)
        struct.pack_into("<H",raw,4080,100)  # Declared directory cannot fit.
        rec=jrc.inspect_tiff_prefix(bytes(raw))
        self.assertFalse(rec["first_ifd_fully_within_prefix"])
        self.assertEqual(rec["first_ifd_entry_count_if_visible"],100)

    def test_bigtiff_requires_eight_byte_aligned_first_directory(self):
        raw = bytearray(big_tiff())
        # 18 is classic word-aligned but invalid as a BigTIFF IFD offset.
        struct.pack_into(">Q", raw, 8, 18)
        with self.assertRaisesRegex(jrc.JRCHeaderBlocked, "unaligned"):
            jrc.inspect_tiff_prefix(bytes(raw))
        self.assertTrue(jrc.inspect_tiff_prefix(big_tiff())[
            "first_ifd_fully_within_prefix"
        ])

    def test_first_ifd_requires_terminal_next_pointer_inside_prefix(self):
        # The count and all IFD entries can fit, yet the 4/8 byte next-IFD
        # pointer is outside the exact 4096-byte original prefix.
        # In that case the word 'fully' would be a false-positive.
        classic_raw = bytearray(classic())
        struct.pack_into("<I", classic_raw, 4, 4092)
        struct.pack_into("<H", classic_raw, 4092, 0)
        rec = jrc.inspect_tiff_prefix(bytes(classic_raw))
        self.assertEqual(rec["first_ifd_entry_count_if_visible"], 0)
        self.assertFalse(rec["first_ifd_fully_within_prefix"])
        self.assertFalse(rec["expected_10_degree_tile_40000x40000_if_inline"])

        big_raw = bytearray(big_tiff())
        struct.pack_into(">Q", big_raw, 8, 4088)
        struct.pack_into(">Q", big_raw, 4088, 0)
        rec = jrc.inspect_tiff_prefix(bytes(big_raw))
        self.assertEqual(rec["first_ifd_entry_count_if_visible"], 0)
        self.assertFalse(rec["first_ifd_fully_within_prefix"])
        self.assertIsNone(rec["width_if_inline"])

        # Exact-end boundaries with the terminal pointer should pass.
        classical_end = bytearray(classic())
        struct.pack_into("<I", classical_end, 4, 4090)
        struct.pack_into("<H", classical_end, 4090, 0)
        self.assertTrue(
            jrc.inspect_tiff_prefix(bytes(classical_end))[
                "first_ifd_fully_within_prefix"
            ]
        )
        big_end = bytearray(big_tiff())
        struct.pack_into(">Q", big_end, 8, 4080)
        struct.pack_into(">Q", big_end, 4080, 0)
        self.assertTrue(
            jrc.inspect_tiff_prefix(bytes(big_end))[
                "first_ifd_fully_within_prefix"
            ]
        )

    def test_invalid_bytes_and_tiff_word_sizes_are_blocked(self):
        for raw in (b"",b"hello",bytes(jrc.PREFIX_BYTES),
                    classic()[:4095],classic()+b"x"):
            with self.subTest(n=len(raw)),self.assertRaises(jrc.JRCHeaderBlocked):
                jrc.inspect_tiff_prefix(raw)
        raw=bytearray(big_tiff())
        struct.pack_into(">H",raw,4,4)
        with self.assertRaisesRegex(jrc.JRCHeaderBlocked,"BigTIFF"):
            jrc.inspect_tiff_prefix(bytes(raw))

    def test_invalid_ifd_duplicate_overflow_and_zero_width_blocked(self):
        raw=bytearray(classic())
        struct.pack_into("<I",raw,4,0)
        with self.assertRaisesRegex(jrc.JRCHeaderBlocked,"IFD pointer"):
            jrc.inspect_tiff_prefix(bytes(raw))
        raw=bytearray(classic())
        struct.pack_into("<H",raw,8,257)
        with self.assertRaisesRegex(jrc.JRCHeaderBlocked,"entry count"):
            jrc.inspect_tiff_prefix(bytes(raw))
        raw=bytearray(classic())
        struct.pack_into("<HHII",raw,22,256,4,1,40000)
        with self.assertRaisesRegex(jrc.JRCHeaderBlocked,"duplicate"):
            jrc.inspect_tiff_prefix(bytes(raw))
        with self.assertRaisesRegex(jrc.JRCHeaderBlocked,"zero-valued"):
            jrc.inspect_tiff_prefix(classic(width=0))
        with self.assertRaisesRegex(jrc.JRCHeaderBlocked,"implausible"):
            jrc.inspect_tiff_prefix(classic(width=400000))

    def test_tiff_sample_architecture_requires_short_tag_types(self):
        # The byte value '8' or '1' is NOT a valid typed assertion of
        # BitsPerSample / SamplesPerPixel if the IFD tag declares LONG.
        # Previously either malformed field created a false positive.
        for entry_index, tag, val, missing in (
            (2, 258, 8, "bits_per_sample_if_inline"),
            (4, 277, 1, "samples_per_pixel_if_inline"),
        ):
            with self.subTest(tag=tag):
                raw = bytearray(classic())
                struct.pack_into("<HHII", raw, 10 + entry_index * 12,
                                 tag, 4, 1, val)
                parsed = jrc.inspect_tiff_prefix(bytes(raw))
                self.assertIsNone(parsed[missing])
                self.assertFalse(parsed["single_8bit_band_if_inline"])
                self.assertFalse(parsed["model_input_approved"])
        valid = jrc.inspect_tiff_prefix(classic())
        self.assertTrue(valid["single_8bit_band_if_inline"])

    def test_unexpected_shape_only_signals_not_actual_asset_rejection(self):
        rec=jrc.inspect_tiff_prefix(classic(width=35000,height=40000))
        self.assertFalse(rec["expected_10_degree_tile_40000x40000_if_inline"])
        self.assertFalse(rec["whole_original_tiff_sha256_verified"])

    def test_value_semantics_0_is_observed_not_water_255_is_nodata(self):
        sample=bytes([0,1,20,99,100,255,255])
        result=jrc.validate_decoded_occurrence_values(sample)
        self.assertEqual(result["decoded_pixel_count"],7)
        self.assertEqual(result["nodata_255_count"],2)
        self.assertEqual(result["observed_zero_not_water_count"],1)
        self.assertEqual(result["observed_percent_min"],0)
        self.assertEqual(result["observed_percent_max"],100)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["original_provider_source_identity_verified"])
        self.assertFalse(result["post_2026_11_10_correction_verified"])

    def test_unbounded_values_101_through_254_fail_closed(self):
        for value in (101,125,254):
            with self.subTest(value=value),self.assertRaisesRegex(
                    jrc.JRCHeaderBlocked,"out-of-range"):
                jrc.validate_decoded_occurrence_values(bytes((0,value,255)))
        self.assertIsNone(jrc.validate_decoded_occurrence_values(
            bytes([255,255]))["observed_percent_max"])

    def test_non_bytes_oversized_or_empty_values_rejected(self):
        for vals in (b"",None, [0,10,255], bytes(65537), memoryview(b"\x00")):
            with self.subTest(v=str(type(vals))),self.assertRaises(
                    jrc.JRCHeaderBlocked):
                jrc.validate_decoded_occurrence_values(vals)

    def test_no_network_or_full_file_by_default(self):
        code=(jrc.Path(jrc.__file__)).read_text(encoding="utf-8")
        for forbidden in ("urllib.request", "requests.get", "http.client",
                          "boto3", "urlopen", ".getresponse(", "Range:"):
            self.assertNotIn(forbidden,code)
        with self.assertRaises(SystemExit) as e:
            jrc.main([])
        self.assertNotEqual(e.exception.code,0)


if __name__=="__main__":
    unittest.main()
