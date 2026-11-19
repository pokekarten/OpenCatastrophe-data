# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic safety tests for first original station-00348 device layout report."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.dwd_station00348_instrument_layout_v0 import (
    SecondStationLayoutBlocked, inspect, main,
)
from scripts.probe_dwd_station00348_original_v0 import METADATA_FILE

EQ_HEADER = (
    "Stations_ID;Stationsname;Geo. Laenge [Grad];Geo. Breite [Grad];"
    "Stationshoehe [m];Geberhoehe ueber Grund [m];Von_Datum;Bis_Datum;"
    "Geraetetyp Name;Messverfahren;eor;\n"
)
PAR_HEADER = (
    "Stations_ID;Von_Datum;Bis_Datum;Stationsname;Parameter;"
    "Parameterbeschreibung;Einheit;Datenquelle (Strukturversion_SV);"
    "Zusatz-Info;Besonderheiten;Literaturhinweis;eor;\n"
)
DEVICE_NAMES = (
    "Metadaten_Geraete_Windgeschwindigkeit_Maxwind_00348.txt",
    "Metadaten_Geraete_Windrichtung_Maxwind_00348.txt",
)
PARAM_NAME = "Metadaten_Parameter_00348.txt"


def original(folder, *, no_param=False, no_device=False, no_html=False,
             unexpected_member=None, broken_eq=False, station="00348"):
    path = folder / METADATA_FILE
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Metadaten_Geographie_00348.txt",
                         b"Stations_id;von_datum;bis_datum\n348;20000101;20200101\n")
        if not no_device:
            for name in DEVICE_NAMES:
                header = (b"WRONG\n" if broken_eq else EQ_HEADER.encode())
                content = (header +
                           b"348;SECRET;11;48;500;10;20100101;20110901;"
                           b"PRIVATE_DEVICE;METHOD;eor;\n" +
                           b"copyright source footer\n")
                member = name.replace("00348", station)
                archive.writestr(member, content)
                if not no_html:
                    archive.writestr(member[:-4] + ".html",
                                     b"<table><tr><th>PRIVATE</th></tr></table>")
        if not no_param:
            archive.writestr(PARAM_NAME, PAR_HEADER.encode() +
                             b"348;20100101;20110901;PRIVATE;FX_10;"
                             b"SECRET;m/sec;V24;-;-;-;eor;\n"
                             b"Original source footer\n")
            if not no_html:
                archive.writestr(PARAM_NAME[:-4] + ".html",
                                 b"<table><tr><th>FX</th></tr></table>")
        if unexpected_member:
            archive.writestr(unexpected_member, b"public member")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class Original00348MetadataLayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_original_station_families_source_header_only(self):
        path, sha = original(self.root)
        report = inspect(path, expected_sha256=sha)
        self.assertEqual(report["equipment_txt_family_count"], 2)
        self.assertEqual(report["txt_families_with_unrecognized_headers"], 0)
        self.assertEqual(report["parameter_txt"]["date_candidate_tokens"], 2)
        self.assertIn("Geberhoehe ueber Grund [m]",
                      next(iter(report["equipment_txt"].values()))["native_source_header_only"])
        self.assertTrue(report["parameter_txt"]["provider_html_companion_present"])
        self.assertFalse(report["fx10_to_maxwind_foreign_key_proven"])
        self.assertFalse(report["model_input_approved"])
        self.assertNotIn("SECRET", str(report))
        self.assertNotIn("PRIVATE_DEVICE", str(report))

    def test_original_sha_gate_blocks_changed_bytes(self):
        path, sha = original(self.root)
        with self.assertRaises(SecondStationLayoutBlocked):
            inspect(path, expected_sha256="0" * 64)
        self.assertEqual(len(sha), 64)

    def test_no_parameter_txt_blocks_source(self):
        path, sha = original(self.root, no_param=True)
        with self.assertRaises(SecondStationLayoutBlocked):
            inspect(path, expected_sha256=sha)

    def test_no_equipment_txt_blocks_source(self):
        path, sha = original(self.root, no_device=True)
        with self.assertRaises(SecondStationLayoutBlocked):
            inspect(path, expected_sha256=sha)

    def test_other_station_equipment_txt_not_accepted(self):
        path, sha = original(self.root, station="00349")
        with self.assertRaises(SecondStationLayoutBlocked):
            inspect(path, expected_sha256=sha)

    def test_missing_html_companion_is_explicit_not_fake(self):
        path, sha = original(self.root, no_html=True)
        report = inspect(path, expected_sha256=sha)
        self.assertFalse(report["parameter_txt"]["provider_html_companion_present"])
        self.assertIsNone(report["parameter_txt"]["provider_html_sha256"])
        self.assertFalse(report["sensor_history_temporal_join_verified"])

    def test_unrecognized_source_header_not_assumed_semantically_valid(self):
        path, sha = original(self.root, broken_eq=True)
        result = inspect(path, expected_sha256=sha)
        self.assertEqual(result["txt_families_with_unrecognized_headers"], 2)
        for info in result["equipment_txt"].values():
            self.assertEqual(info["native_source_header_only"], [])
            self.assertFalse(info["native_header_candidate_recognized"])

    def test_zip_path_traversal_disallowed(self):
        path, sha = original(self.root, unexpected_member="../unreviewed")
        with self.assertRaises(SecondStationLayoutBlocked):
            inspect(path, expected_sha256=sha)

    def test_default_cli_must_reject_synthetic_original_sha(self):
        path, _ = original(self.root)
        self.assertEqual(main(["--metadata-zip", str(path)]), 1)

    def test_original_filename_and_regular_file_required(self):
        path, sha = original(self.root)
        link = self.root / "alias.zip"
        link.symlink_to(path)
        with self.assertRaises(SecondStationLayoutBlocked):
            inspect(link, expected_sha256=sha)


if __name__ == "__main__":
    unittest.main()
