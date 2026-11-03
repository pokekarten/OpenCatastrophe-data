# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Entirely invented one-parish ZIP; NEVER provider-supplied geodata."""
import hashlib
import io
import struct
import unittest
import zipfile

from research_runners.us_census_2026_county_zip_audit_v0 import (
    CensusZipError, STEM, MAX_ZIP_BYTES, _dbf_summary, audit_original_zip,
)


def shape_header(length):
    header = bytearray(100)
    struct.pack_into(">I", header, 0, 9994)
    struct.pack_into(">I", header, 24, length//2)
    struct.pack_into("<II", header, 28, 1000, 5)
    return bytes(header)


def fake_members():
    coords = ((-90.2, 29.8), (-90.0, 29.8), (-90.0, 30.0),
              (-90.2, 30.0), (-90.2, 29.8))
    body = (struct.pack("<i4dii", 5, -90.2, 29.8, -90.0, 30.0, 1, 5)
            + struct.pack("<i", 0)
            + b"".join(struct.pack("<dd", *point) for point in coords))
    assert len(body) == 128
    shp = shape_header(100+8+len(body))+struct.pack(">II", 1, len(body)//2)+body
    shx = shape_header(108) + struct.pack(">II", 50, len(body)//2)

    fields = (("STATEFP", 2), ("COUNTYFP", 3),
              ("GEOID", 5), ("NAME", 20))
    header_len = 32 + len(fields)*32 + 1
    record_len = 1 + sum(n for _,n in fields)
    dbf = bytearray(header_len)
    dbf[0] = 3
    struct.pack_into("<IHH", dbf, 4, 1, header_len, record_len)
    for index, (name, width) in enumerate(fields):
        off = 32 + 32*index
        dbf[off:off+len(name)] = name.encode("ascii")
        dbf[off+11] = ord("C")
        dbf[off+16] = width
    dbf[header_len-1] = 13
    dbf += b" " + b"22" + b"071" + b"22071" + b"Orleans".ljust(20, b" ")
    return {
        f"{STEM}.shp":shp,
        f"{STEM}.shx":shx,
        f"{STEM}.dbf":bytes(dbf),
        f"{STEM}.prj":b'GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983"],UNIT["Degree",0.0174533]]',
    }


def zipped(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zipobj:
        for name, raw in members.items():
            zipobj.writestr(name, raw)
    return buf.getvalue()


class CountyOriginalZipTests(unittest.TestCase):
    def test_synthetic_one_parish_archive_passes_structure_not_admission(self):
        raw = zipped(fake_members())
        o = audit_original_zip(raw)
        self.assertEqual(o["dbf_feature_count"], 1)
        self.assertEqual(o["shx_index_feature_count"], 1)
        self.assertTrue(o["orleans_parish_geoid_22071_verified"])
        self.assertFalse(o["sha256_matched_independent_pin"])
        self.assertFalse(o["model_input_admitted"])
        self.assertFalse(o["complete_polygon_topology_verified"])
        self.assertFalse(o["insurance_exposure_verified"])

    def test_explicit_external_digest_works_and_wrong_digest_rejected(self):
        raw = zipped(fake_members())
        o = audit_original_zip(raw, independently_pinned_sha256=hashlib.sha256(raw).hexdigest())
        self.assertTrue(o["sha256_matched_independent_pin"])
        for digest in ("f"*64, "A"*64, "0"):
            with self.subTest(digest=digest), self.assertRaises(CensusZipError):
                audit_original_zip(raw, independently_pinned_sha256=digest)

    def test_zip_path_traversal_rejected(self):
        x = fake_members()
        x["../private.csv"] = b"no"
        with self.assertRaises(CensusZipError):
            audit_original_zip(zipped(x))

    def test_duplicate_zip_members_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for name, raw in fake_members().items():
                z.writestr(name, raw)
            z.writestr(f"{STEM}.prj", b"duplicate")
        with self.assertRaises(CensusZipError):
            audit_original_zip(buf.getvalue())

    def test_archive_missing_component_rejected(self):
        x = fake_members()
        x.pop(f"{STEM}.dbf")
        with self.assertRaises(CensusZipError):
            audit_original_zip(zipped(x))

    def test_forged_shapefile_file_length_rejected(self):
        x = fake_members()
        shp = bytearray(x[f"{STEM}.shp"])
        struct.pack_into(">I", shp, 24, 500)
        x[f"{STEM}.shp"] = bytes(shp)
        with self.assertRaises(CensusZipError):
            audit_original_zip(zipped(x))

    def test_shx_mismatched_polygon_pointer_rejected(self):
        x = fake_members()
        shx = bytearray(x[f"{STEM}.shx"])
        struct.pack_into(">I", shx, 100, 51)
        x[f"{STEM}.shx"] = bytes(shx)
        with self.assertRaises(CensusZipError):
            audit_original_zip(zipped(x))

    def test_missing_polygon_body_rejected_despite_index(self):
        x = fake_members()
        shp = shape_header(100)
        x[f"{STEM}.shp"] = shp
        with self.assertRaises(CensusZipError):
            audit_original_zip(zipped(x))

    def test_original_nonascii_county_names_do_not_change_numeric_geoids(self):
        dbf = bytearray(fake_members()[f"{STEM}.dbf"])
        header_len = struct.unpack("<H", dbf[8:10])[0]
        record_len = struct.unpack("<H", dbf[10:12])[0]
        struct.pack_into("<I", dbf, 4, 2)
        # Fictional second county with Unicode source label; its exact
        # bytes stay untouched and numeric GEOID must still validate.
        invented_name = b"Do\xc3\xb1a Ana"
        dbf.extend(b" " + b"35" + b"013" + b"35013" +
                   invented_name.ljust(20, b" "))
        self.assertEqual(len(dbf), header_len + 2*record_len)
        self.assertEqual(_dbf_summary(bytes(dbf))[0], 2)
        # But non-ASCII in an official fixed-digit GEOID is never okay.
        bad = bytearray(dbf)
        bad[header_len + record_len + 1 + 2 + 3] = 0xc3
        with self.assertRaises(CensusZipError):
            _dbf_summary(bytes(bad))

    def test_invalid_or_duplicate_official_parish_geoids_rejected(self):
        for value in (b"22072", b"00000"):
            x = fake_members()
            raw = bytearray(x[f"{STEM}.dbf"])
            header = struct.unpack("<H", raw[8:10])[0]
            raw[header+1+2+3:header+1+2+3+5] = value
            x[f"{STEM}.dbf"] = bytes(raw)
            with self.subTest(value=value), self.assertRaises(CensusZipError):
                audit_original_zip(zipped(x))

    def test_wrong_crs_or_shape_type_rejected(self):
        x = fake_members()
        x[f"{STEM}.prj"] = b'PROJCS["Web_Mercator"]'
        with self.assertRaises(CensusZipError):
            audit_original_zip(zipped(x))
        x = fake_members()
        shp = bytearray(x[f"{STEM}.shp"])
        struct.pack_into("<i", shp, 32, 3)
        x[f"{STEM}.shp"] = bytes(shp)
        with self.assertRaises(CensusZipError):
            audit_original_zip(zipped(x))

    def test_invalid_original_payload_or_bomb_budget_rejected(self):
        for original in (b"not-zip", b"", b"\0"*(MAX_ZIP_BYTES+1)):
            with self.subTest(length=len(original)), self.assertRaises(CensusZipError):
                audit_original_zip(original)


if __name__ == "__main__":
    unittest.main()
