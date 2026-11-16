# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Fully synthetic ZIP/SQLite for original BKG VG250 2025 archive gate."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock
from zipfile import ZipFile, ZIP_STORED

from research_runners.bkg_vg250_2025_original_archive_preflight_v0 import (
    BkgOriginalArchiveBlocked, EXPECTED_SRS, inspect_original_archive, main
)


def make_zip(root: Path, *, states: int = 16,
             water_states: int = 2,
             srs: int = EXPECTED_SRS,
             land_gf: int = 4,
             without_structure_land: int = 0,
             without_structure_water: int = 0,
             name: str = "DE_VG250.gpkg",
             no_ags: bool = False,
             with_second_gpkg: bool = False) -> Path:
    gpkg = root / "synthetic.gpkg"
    db = sqlite3.connect(str(gpkg))
    db.executescript("""
        CREATE TABLE gpkg_contents(table_name TEXT, data_type TEXT, srs_id INTEGER);
        CREATE TABLE gpkg_geometry_columns(
            table_name TEXT, geometry_type_name TEXT, srs_id INTEGER);
        CREATE TABLE vg250_sta(fid INTEGER PRIMARY KEY, GF INTEGER, AGS TEXT);
    """)
    if no_ags:
        db.execute("CREATE TABLE vg250_lan(fid INTEGER PRIMARY KEY, GF INTEGER, BAD_CODE TEXT)")
    else:
        db.execute("CREATE TABLE vg250_lan(fid INTEGER PRIMARY KEY, GF INTEGER, AGS TEXT)")
    for layer in ("vg250_sta", "vg250_lan"):
        db.execute("INSERT INTO gpkg_contents VALUES (?,?,?)",(layer,"features",srs))
        db.execute("INSERT INTO gpkg_geometry_columns VALUES (?,?,?)",
                   (layer,"MULTIPOLYGON",srs))
    db.execute("INSERT INTO vg250_sta(GF,AGS) VALUES (?,?)",(land_gf,"DEU"))
    for i in range(states):
        db.execute("INSERT INTO vg250_lan(GF,"+("BAD_CODE" if no_ags else "AGS")+") VALUES (?,?)",
                   (land_gf, f"{i+1:02d}"))
    for i in range(water_states):
        db.execute("INSERT INTO vg250_lan(GF,"+("BAD_CODE" if no_ags else "AGS")+") VALUES (?,?)",
                   (2, f"{i+1:02d}"))
    # Synthetic source GF=3 and GF=1 are separate provider records;
    # they never increase GF4 land key coverage or GF2 water counts.
    for i in range(without_structure_land):
        db.execute("INSERT INTO vg250_lan(GF,"+("BAD_CODE" if no_ags else "AGS")+") VALUES (?,?)",
                   (3, f"{i+1:02d}"))
    for i in range(without_structure_water):
        db.execute("INSERT INTO vg250_lan(GF,"+("BAD_CODE" if no_ags else "AGS")+") VALUES (?,?)",
                   (1, f"{i+1:02d}"))
    db.commit()
    db.close()
    archive = root / "synthetic.zip"
    with ZipFile(archive, "w", compression=ZIP_STORED) as z:
        z.write(gpkg, arcname=name)
        if with_second_gpkg:
            z.write(gpkg, arcname="second.gpkg")
    return archive


def check_fixture(archive: Path):
    md5 = hashlib.md5(archive.read_bytes(),usedforsecurity=False).hexdigest()
    return inspect_original_archive(archive,synthetic_expected_md5=md5)


class BkgOriginal2025ZipSyntheticTests(unittest.TestCase):
    def test_original_shaped_synthetic_state_country_cardinality(self):
        with tempfile.TemporaryDirectory() as d:
            r = check_fixture(make_zip(Path(d)))
            self.assertTrue(len(r["full_zip_sha256"])==64)
            self.assertTrue(len(r["gpkg_original_sha256"])==64)
            self.assertEqual(r["source_gpkg_layers"]["vg250_sta"]["distinct_ags_gf4_land"],1)
            self.assertEqual(r["source_gpkg_layers"]["vg250_lan"]["distinct_ags_gf4_land"],16)
            self.assertEqual(r["source_gpkg_layers"]["vg250_lan"]["gf2_water_records"],2)
            self.assertFalse(r["official_publisher_sidecar_md5_matches_full_zip"])
            self.assertFalse(r["source_original_file_identity_verified"])
            self.assertFalse(r["cat_model_input_approved"])
            self.assertFalse(r["insurance_geolocation_approved"])
            self.assertFalse(r["original_zip_or_gpkg_persisted_in_git_or_neon"])
            for prohibited in ("original_feature_coordinates", "source_polygon_wkt",
                               "raw_geometry", "geometry_json", "site_coordinates"):
                self.assertNotIn(prohibited, json.dumps(r))
            self.assertFalse(r["all_geom_coordinates_and_topology_validated"])

    def test_block_reason_is_author_controlled_and_leaks_no_source_path(self):
        with tempfile.TemporaryDirectory() as d:
            original = make_zip(Path(d))
            with mock.patch("sys.stderr", new_callable=io.StringIO) as err:
                rc = main(["--original-zip",str(original)])
                self.assertEqual(rc,2)
                msg = err.getvalue()
                self.assertIn("whole-source ZIP differs from publisher MD5 sidecar",msg)
                self.assertNotIn(str(original),msg)
                self.assertNotIn("DE_VG250",msg)

    def test_synthetic_can_never_be_mistaken_for_official_MD5(self):
        with tempfile.TemporaryDirectory() as d:
            archive=make_zip(Path(d))
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"MD5"):
                inspect_original_archive(archive)

    def test_water_components_never_count_as_16_land_state_keys(self):
        with tempfile.TemporaryDirectory() as d:
            r=check_fixture(make_zip(Path(d),water_states=5))
            self.assertEqual(r["source_gpkg_layers"]["vg250_lan"]["gf2_water_records"],5)
            self.assertEqual(r["source_gpkg_layers"]["vg250_lan"]["distinct_ags_gf4_land"],16)
            self.assertEqual(r["source_gpkg_layers"]["vg250_lan"]["original_feature_records"],21)

    def test_documented_official_GF1_and_GF3_are_distinct_source_records(self):
        with tempfile.TemporaryDirectory() as d:
            report=check_fixture(make_zip(Path(d),water_states=2,
                                          without_structure_land=2,
                                          without_structure_water=3))
            layer=report["source_gpkg_layers"]["vg250_lan"]
            self.assertEqual(layer["gf1_unstructured_water_records"],3)
            self.assertEqual(layer["gf2_structured_water_records"],2)
            self.assertEqual(layer["gf3_unstructured_land_records"],2)
            self.assertEqual(layer["gf4_structured_land_records"],16)
            self.assertEqual(layer["gf4_land_records"],16)
            self.assertEqual(layer["gf2_water_records"],2)
            self.assertEqual(layer["distinct_ags_gf4_land"],16)
            self.assertEqual(layer["original_feature_records"],23)
            self.assertFalse(report["cat_model_input_approved"])
            self.assertFalse(report["source_vintage_inside_zip_independently_verified"])

    def test_GF3_cannot_replace_GF4_land_key_for_an_official_state(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"16 official state"):
                check_fixture(make_zip(Path(d),states=15,
                                       without_structure_land=1))

    def test_GF1_unstructured_water_never_increases_GF2_water_count(self):
        with tempfile.TemporaryDirectory() as d:
            r=check_fixture(make_zip(Path(d),water_states=0,
                                     without_structure_water=5))
            layer=r["source_gpkg_layers"]["vg250_lan"]
            self.assertEqual(layer["gf1_unstructured_water_records"],5)
            self.assertEqual(layer["gf2_water_records"],0)
            self.assertEqual(layer["distinct_ags_gf4_land"],16)

    def test_missing_one_land_state_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"16 official state"):
                check_fixture(make_zip(Path(d),states=15))

    def test_unknown_GF_value_never_silently_maps_to_land_or_water(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"land/water GF"):
                check_fixture(make_zip(Path(d),land_gf=3))

    def test_wrong_crs_is_not_allowed_to_pass_native_projection(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"spatial reference"):
                check_fixture(make_zip(Path(d),srs=3857))

    def test_missing_original_AGS_schema_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"GF and AGS"):
                check_fixture(make_zip(Path(d),no_ags=True))

    def test_duplicate_gpkg_member_blocks_source_interpretation(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"exactly one"):
                check_fixture(make_zip(Path(d),with_second_gpkg=True))

    def test_zip_path_traversal_blocks_even_without_extracting_by_filename(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"unsafe original"):
                check_fixture(make_zip(Path(d),name="../evil.gpkg"))

    def test_original_zip_mutation_and_symlink_block(self):
        with tempfile.TemporaryDirectory() as d:
            archive=make_zip(Path(d))
            md5=hashlib.md5(archive.read_bytes(),usedforsecurity=False).hexdigest()
            with archive.open("ab") as f:
                f.write(b"mutated")
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"MD5"):
                inspect_original_archive(archive,synthetic_expected_md5=md5)
            link=Path(d)/"original-link.zip"
            link.symlink_to(archive)
            with self.assertRaisesRegex(BkgOriginalArchiveBlocked,"symlink"):
                inspect_original_archive(link,synthetic_expected_md5=md5)


if __name__ == "__main__":
    unittest.main()
