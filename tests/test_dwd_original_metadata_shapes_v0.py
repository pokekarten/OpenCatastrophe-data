# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only regression tests: source hash, no-follow, field shape, no data values."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.dwd_original_metadata_shapes_v0 import (
    MetadataShapeBlocked, _table_shape, profile,
)


def _original(base: Path, geography=None, equipment=None, parameter=None):
    path = base / "Meta_Daten_zehn_min_fx_00003.zip"
    geo = geography if geography is not None else (
        b"Stations_id;Von_Datum;Bis_Datum;Geogr_Breite;Geogr_Laenge\r\n"
        b"00003;20100101;20110331;51.23;7.55\r\n")
    eq = equipment if equipment is not None else (
        b"Stations_id;Von_Datum;Bis_Datum;Geraetetyp\r\n"
        b"00003;20100101;20110331;Synthetic Sensor\r\n")
    par = parameter if parameter is not None else (
        b"Stations_id;Von_Datum;Bis_Datum;Parameter\r\n"
        b"00003;20100101;20110331;FX_10\r\n")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Metadaten_Geographie_00003.txt", geo)
        z.writestr("Metadaten_Geraete_00003.txt", eq)
        z.writestr("Metadaten_Parameter_00003.txt", par)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class MetadataShapesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_valid_synthetic_triplet_only_schema_logged(self):
        path, digest = _original(self.root)
        result = profile(path, expected_sha256=digest)
        self.assertEqual(result["members_examined"], 3)
        self.assertEqual(result["recognized_delimited_headers"], 3)
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["valid_geography_for_measurement_window"])
        self.assertFalse(result["raw_metadata_rows_persisted"])
        self.assertNotIn("51.23", str(result))
        self.assertNotIn("Synthetic Sensor", str(result))
        self.assertEqual(
            result["required_families"]["geography"][0]["columns"],
            ["Stations_id", "Von_Datum", "Bis_Datum", "Geogr_Breite", "Geogr_Laenge"])
        self.assertEqual(result["required_families"]["geography"][0]["nonempty_data_lines"], 1)

    def test_wrong_original_source_sha_is_blocked(self):
        path, digest = _original(self.root)
        with self.assertRaisesRegex(MetadataShapeBlocked, "evidence gate"):
            profile(path, expected_sha256="0" * 64)

    def test_symlink_rejected(self):
        path, digest = _original(self.root)
        link = self.root / "link.zip"
        link.symlink_to(path)
        with self.assertRaises(MetadataShapeBlocked):
            profile(link, expected_sha256=digest)

    def test_missing_family_rejected(self):
        path = self.root / "Meta_Daten_zehn_min_fx_00003.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("Metadaten_Geographie_00003.txt", "Station;Date\n3;2020")
        with self.assertRaises(MetadataShapeBlocked):
            profile(path, expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def test_duplicate_column_headers_are_not_schema(self):
        result = _table_shape(b"Station;Station;Von_Datum\n3;3;2020\n")
        self.assertFalse(result["header_recognized"])
        self.assertEqual(result["shape_status"], "blocked_unrecognized_header")

    def test_bad_row_shape_is_not_promoted(self):
        result = _table_shape(b"Station;Von_Datum\n3;2020\n3\n")
        self.assertTrue(result["header_recognized"])
        self.assertFalse(result["same_field_count_on_data_lines"])
        self.assertEqual(result["shape_status"], "blocked_csv_row_field_count")

    def test_cp1252_fallback_label_is_heuristic(self):
        result = _table_shape("Höhe;Stationsname\n12;Test\n".encode("cp1252"))
        self.assertEqual(result["encoding_hint"], "cp1252_heuristic")
        self.assertTrue(result["header_recognized"])

    def test_unknown_delimiter_is_held_not_guessed(self):
        result = _table_shape(b"Station Date Height\n3 2020 101\n")
        self.assertEqual(result["shape_status"], "blocked_delimiter_not_verified")
        self.assertEqual(result["columns"], [])

    def test_oversized_or_blank_member_is_rejected(self):
        for data in (b"", b"x" * 512001):
            with self.subTest(size=len(data)), self.assertRaises(MetadataShapeBlocked):
                _table_shape(data)

    def test_untrusted_station_not_validated_by_syntax_alone(self):
        path, digest = _original(self.root, geography=(
            b"Stations_id;Von_Datum;Bis_Datum;Geogr_Breite;Geogr_Laenge\n"
            b"99999;19000101;19000102;0;0\n"))
        result = profile(path, expected_sha256=digest)
        self.assertEqual(result["recognized_delimited_headers"], 3)
        self.assertFalse(result["valid_geography_for_measurement_window"])
        self.assertFalse(result["valid_instrument_for_measurement_window"])

    def test_bad_header_bytes_not_printed(self):
        result = _table_shape(b"Station;Value\n3;1\n")
        self.assertNotIn("3;1", str(result))
        self.assertEqual(result["member_bytes"], len(b"Station;Value\n3;1\n"))


if __name__ == "__main__":
    unittest.main()
