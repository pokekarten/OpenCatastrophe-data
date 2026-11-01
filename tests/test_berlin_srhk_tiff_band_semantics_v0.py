# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic TIFF IFD band semantics, NoData and GDAL XML adversarial tests."""
from __future__ import annotations

import struct
import unittest

from research_runners.berlin_srhk_tiff_band_semantics_v0 import (
    TiffBandError, inspect_tiff_band_declarations,
)


def original_like(*, nodata="-9999", unit="m", scale="0.01",
                  offset="0", with_gdal=True, with_nodata=True):
    rows = [
        (258, 3, 1, struct.pack("<H", 32)),
        (259, 3, 1, struct.pack("<H", 8)),
        (277, 3, 1, struct.pack("<H", 1)),
        (339, 3, 1, struct.pack("<H", 3)),
    ]
    if with_nodata:
        rows.append((42113, 2, len(nodata)+1, nodata.encode("ascii")+b"\0"))
    if with_gdal:
        xml = ('<GDALMetadata><Item name="UNITTYPE" sample="0">' + unit +
               '</Item><Item name="SCALE" sample="0">' + scale +
               '</Item><Item name="OFFSET" sample="0">' + offset +
               '</Item></GDALMetadata>').encode("ascii")+b"\0"
        rows.append((42112, 2, len(xml), xml))
    rows.sort(key=lambda x: x[0])
    base = bytearray(b"II" + struct.pack("<HI", 42, 8))
    base += struct.pack("<H", len(rows))
    payload = bytearray()
    start_data = 8 + 2 + len(rows)*12 + 4
    for tag, kind, count, value in rows:
        if len(value) <= 4:
            packed = value.ljust(4, b"\0")
        else:
            packed = struct.pack("<I", start_data + len(payload))
            payload += value
        base += struct.pack("<HHI", tag, kind, count) + packed
    base += struct.pack("<I", 0)
    base += payload
    return bytes(base)


class BerlinTiffBandSemanticsTests(unittest.TestCase):
    def test_declared_but_not_scientifically_admitted(self):
        r = inspect_tiff_band_declarations(original_like())
        self.assertTrue(r["band_metadata_ifd_accessible"])
        self.assertEqual(r["bits_per_sample"], 32)
        self.assertEqual(r["sample_format_code"], 3)
        self.assertEqual(r["samples_per_pixel"], 1)
        self.assertEqual(r["tiff_compression_code"], 8)
        self.assertTrue(r["gdal_nodata_tag_present"])
        self.assertEqual(r["gdal_nodata_declared"], {"type": "finite_number", "value": -9999.0})
        self.assertTrue(r["gdal_band_unit_label_reviewed"])
        self.assertEqual(r["gdal_band_unit_label_declared"], "m")
        self.assertEqual(r["gdal_band_scale_claim"], 0.01)
        self.assertEqual(r["gdal_band_offset_claim"], 0.0)
        self.assertFalse(r["nodata_mask_or_pixels_validated"])
        self.assertFalse(r["water_depth_units_or_scale_scientifically_validated"])
        self.assertFalse(r["original_tiff_pixels_accessed"])
        self.assertFalse(r["building_hazard_or_cat_loss_admitted"])

    def test_no_gdal_tags_is_unknown_not_zero_or_metres(self):
        r = inspect_tiff_band_declarations(original_like(with_gdal=False, with_nodata=False))
        self.assertIsNone(r["gdal_nodata_declared"])
        self.assertFalse(r["gdal_nodata_tag_present"])
        self.assertIsNone(r["gdal_band_unit_label_declared"])
        self.assertFalse(r["gdal_metadata_tag_present"])
        self.assertIsNone(r["gdal_band_scale_claim"])
        self.assertTrue(r["missing_gdal_metadata_does_not_imply_meters_or_no_nodata"])

    def test_unknown_or_centimetre_units_do_not_become_metres(self):
        for src, expected in (("cm", "cm"), ("mm", "mm"),
                              ("m", "m"), ("ft", None)):
            with self.subTest(unit=src):
                r = inspect_tiff_band_declarations(original_like(unit=src))
                self.assertEqual(r["gdal_band_unit_label_declared"], expected)
                self.assertEqual(r["gdal_band_unit_label_reviewed"], expected is not None)
                self.assertFalse(r["water_depth_units_or_scale_scientifically_validated"])

    def test_nan_nodata_sentinel_not_replaced_by_dry_zero(self):
        r = inspect_tiff_band_declarations(original_like(nodata="nan"))
        self.assertEqual(r["gdal_nodata_declared"],
                         {"type": "nan_sentinel", "value": None})
        self.assertFalse(r["nodata_mask_or_pixels_validated"])

    def test_xml_entity_and_malformed_document_fail_closed(self):
        for bad in ('<!DOCTYPE GDALMetadata [<!ENTITY x "bad">]><GDALMetadata/>',
                    "<bad/>", "<GDALMetadata><Item name='UNITTYPE'>m</GDALMetadata>",
                    "<GDALMetadata><NonItem /></GDALMetadata>"):
            with self.subTest(bad=bad[:32]), self.assertRaises(TiffBandError):
                inspect_tiff_band_declarations(_replace_xml(original_like(), bad))

    def test_ambiguous_duplicate_unit_fail_closed(self):
        xml = ('<GDALMetadata><Item name="UNITTYPE" sample="0">m</Item>'
               '<Item name="UNITTYPE" sample="0">mm</Item></GDALMetadata>')
        with self.assertRaisesRegex(TiffBandError, "ambiguous"):
            inspect_tiff_band_declarations(_replace_xml(original_like(), xml))

    def test_nonfinite_scale_or_nodata_rejected(self):
        for value in ("inf", "-inf", "not-number"):
            with self.subTest(value=value):
                with self.assertRaises(TiffBandError):
                    inspect_tiff_band_declarations(original_like(scale=value))
        for value in ("inf", "banana"):
            with self.subTest(nodata=value):
                with self.assertRaises(TiffBandError):
                    inspect_tiff_band_declarations(original_like(nodata=value))

    def test_bad_magic_large_ifd_and_no_partial_claim(self):
        for raw in (b"", b"BAD" * 25, original_like() + b"\0"*1_048_576):
            with self.subTest(size=len(raw)), self.assertRaises(TiffBandError):
                inspect_tiff_band_declarations(raw)
        head = b"II" + struct.pack("<HI", 42, 900000) + b"\0"*80
        r = inspect_tiff_band_declarations(head)
        self.assertFalse(r["band_metadata_ifd_accessible"])
        self.assertIsNone(r["gdal_nodata_tag_present"])
        too_many = bytearray(original_like())
        struct.pack_into("<H", too_many, 8, 513)
        with self.assertRaisesRegex(TiffBandError, "unbounded"):
            inspect_tiff_band_declarations(bytes(too_many))

    def test_duplicate_ifd_tag_rejected(self):
        raw = bytearray(original_like())
        n = struct.unpack_from("<H", raw, 8)[0]
        # Duplicate existing BitsPerSample as TIFF compression tag.
        struct.pack_into("<H", raw, 10+12*1, 258)
        with self.assertRaisesRegex(TiffBandError, "duplicate"):
            inspect_tiff_band_declarations(bytes(raw))

    def test_bad_out_of_bounds_gdal_metadata_does_not_infer_units(self):
        raw = bytearray(original_like())
        n = struct.unpack_from("<H", raw, 8)[0]
        for i in range(n):
            tag = struct.unpack_from("<H", raw, 10+i*12)[0]
            if tag == 42112:
                struct.pack_into("<I", raw, 10+i*12+8, 900000)
        r = inspect_tiff_band_declarations(bytes(raw))
        self.assertIsNone(r["gdal_metadata_tag_present"])
        self.assertIsNone(r["gdal_band_unit_label_declared"])
        self.assertFalse(r["water_depth_units_or_scale_scientifically_validated"])


def _replace_xml(original: bytes, xml: str) -> bytes:
    # Rebuild only a fresh synthetic IFD with controlled XML payload.
    # The tagged bytes are intentionally NOT genuine provider content.
    marker = b"<GDALMetadata>"
    i = original.find(marker)
    assert i >= 0
    old_length = len(original)-i
    new = bytearray(original[:i] + xml.encode("ascii") + b"\0")
    count = struct.unpack_from("<H", new, 8)[0]
    for n in range(count):
        at = 10+n*12
        if struct.unpack_from("<H", new, at)[0] == 42112:
            struct.pack_into("<I", new, at+4, len(xml)+1)
    return bytes(new)


if __name__ == "__main__":
    unittest.main()
