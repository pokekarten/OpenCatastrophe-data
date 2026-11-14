# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic SQLite/ZIP structure only; no ACT source address values."""
from __future__ import annotations

import contextlib
import hashlib
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

from research_runners.lu_geobase_addresses_20260401_original_v0 import (
    GeoBaseAddressError, inspect, _id_summary, main,
)


def make_zip(folder: Path, *, epsg=2169, add_id_fields=True):
    dbpath = folder / "fictional-address.gpkg"
    with contextlib.closing(sqlite3.connect(dbpath)) as conn:
        conn.execute("PRAGMA application_id=1196444487")
        conn.execute("CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,srs_id INTEGER)")
        conn.execute("CREATE TABLE gpkg_geometry_columns(table_name TEXT,geometry_type_name TEXT,column_name TEXT,srs_id INTEGER)")
        conn.execute("CREATE TABLE gpkg_spatial_ref_sys(srs_name TEXT)")
        conn.execute("INSERT INTO gpkg_contents VALUES('Addresses_AD_Address','features',?)",(epsg,))
        conn.execute("INSERT INTO gpkg_geometry_columns VALUES('Addresses_AD_Address','POINT','geom',?)",(epsg,))
        if add_id_fields:
            conn.execute('CREATE TABLE "Addresses_AD_Address" (geom BLOB, AD_AddressID TEXT, AlternativeIdentifier TEXT)')
            conn.executemany('INSERT INTO "Addresses_AD_Address" VALUES(?,?,?)',[
                (b"P", "SYN-1", "123"),(b"P","SYN-2","123"),(b"P","SYN-3","456"),
            ])
        else:
            conn.execute('CREATE TABLE "Addresses_AD_Address" (geom BLOB, OtherField TEXT)')
            conn.execute('INSERT INTO "Addresses_AD_Address" VALUES(?,?)', (b"P","fictional"))
        conn.commit()
    output = folder / "synthetic-original.zip"
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(dbpath,arcname="Addresses.gpkg")
    return output


def synthetic_pins(source: Path):
    data = source.read_bytes()
    with zipfile.ZipFile(source) as archive:
        gpkg = [p for p in archive.infolist() if p.filename.lower().endswith(".gpkg")]
        inner_sha = hashlib.sha256(archive.read(gpkg[0])).hexdigest() if len(gpkg) == 1 else "0" * 64
    return {
        "expected_md5": hashlib.md5(data).hexdigest(),
        "expected_zip_sha256": hashlib.sha256(data).hexdigest(),
        "expected_gpkg_sha256": inner_sha,
    }


class OriginalAddressTests(unittest.TestCase):
    def test_fake_original_zip_schema_and_id_aggregate(self):
        with tempfile.TemporaryDirectory() as d:
            p=make_zip(Path(d))
            r=inspect(p,**synthetic_pins(p))
            entry=r["gpkg_original_address_layers"][0]
            self.assertEqual(entry["original_feature_rows"],3)
            self.assertEqual(entry["aggregate_id_quality"]["AD_AddressID"]["distinct_nonblank_ids"],3)
            self.assertEqual(entry["aggregate_id_quality"]["AlternativeIdentifier"]["duplicate_excess_nonblank_rows"],1)
            self.assertFalse(r["address_to_building_crosswalk_proven"])
            self.assertFalse(r["cat_model_input_admitted"])
            self.assertNotIn("SYN-1",str(r))
            self.assertNotIn("\"123\"",str(r))

    def test_broken_original_zip_md5_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=make_zip(Path(d))
            with self.assertRaisesRegex(GeoBaseAddressError,"MD5"):
                inspect(p)

    def test_wrong_crs_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=make_zip(Path(d),epsg=4326)
            with self.assertRaisesRegex(GeoBaseAddressError,"EPSG"):
                inspect(p,**synthetic_pins(p))

    def test_missing_expected_fields_is_explicit_not_silent_match(self):
        with tempfile.TemporaryDirectory() as d:
            p=make_zip(Path(d),add_id_fields=False)
            r=inspect(p,**synthetic_pins(p))
            entry=r["gpkg_original_address_layers"][0]
            self.assertFalse(entry["expected_address_keys_present"]["AD_AddressID"])
            self.assertFalse(entry["expected_address_keys_present"]["AlternativeIdentifier"])
            self.assertEqual(entry["aggregate_id_quality"],{})

    def test_counts_and_blank_ids(self):
        r=_id_summary(["A","A","B",""," "," B "],"SYN")
        self.assertEqual(r["rows"],6)
        self.assertEqual(r["blank_rows"],2)
        self.assertEqual(r["duplicate_excess_nonblank_rows"],1)
        self.assertEqual(r["whitespace_padded_rows"],1)

    def test_reject_control_and_untyped_source_values(self):
        for val in (True,1.5,"\nprivate","a"*257):
            with self.subTest(type=str(type(val))),self.assertRaises(GeoBaseAddressError):
                _id_summary([val],"SYN")

    def test_invalid_member_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"evil.zip"
            with zipfile.ZipFile(p,"w") as archive:
                archive.writestr("../evil.gpkg",b"data")
            with self.assertRaises(GeoBaseAddressError):
                inspect(p,**synthetic_pins(p))

    def test_no_gpkg_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"empty.zip"
            with zipfile.ZipFile(p,"w") as archive:
                archive.writestr("original.txt","synthetic")
            with self.assertRaises(GeoBaseAddressError):
                inspect(p,**synthetic_pins(p))

    def test_full_original_sha256_pins_are_required(self):
        with tempfile.TemporaryDirectory() as d:
            p=make_zip(Path(d))
            good=synthetic_pins(p)
            zip_bad=dict(good,expected_zip_sha256="0"*64)
            with self.assertRaisesRegex(GeoBaseAddressError,"ZIP SHA-256"):
                inspect(p,**zip_bad)
            gpkg_bad=dict(good,expected_gpkg_sha256="0"*64)
            with self.assertRaisesRegex(GeoBaseAddressError,"GeoPackage SHA-256"):
                inspect(p,**gpkg_bad)

    def test_cli_rejects_invalid_original_without_leaking_name(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"private-name-address.gpkg.zip"
            p.write_bytes(b"invalid")
            with contextlib.redirect_stderr(io.StringIO()) as e:
                result=main(["--source-zip",str(p)])
            self.assertEqual(result,2)
            self.assertNotIn("private-name",e.getvalue())


if __name__=="__main__":
    unittest.main()
