# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic-only instrument/parameter layout and provenance tests."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.dwd_equipment_layout_evidence_v0 import (
    EquipmentBlocked, PAIRS, _html_layout, _txt_layout, analyze,
)


def synthetic_zip(folder, *, drop=None, content_override=None):
    path = folder / "Meta_Daten_zehn_min_fx_00003.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Metadaten_Geographie_00003.txt",
                   "Stations_id;von_datum;bis_datum\n00003;20000101;20191231\n")
        for stem in PAIRS:
            for ext in (".txt", ".html"):
                name = stem + ext
                if name == drop:
                    continue
                raw = (b"<html><table><tr><th>Heading</th><td>secret</td></tr>"
                       b"<tr><td>secret instrument</td></tr></table></html>"
                       if ext == ".html" else
                       b"Device date columns unknown\n00003 20100101 20110331 PrivateDevice\n")
                z.writestr(name, content_override if name == drop else raw)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class EquipmentLayoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_original_member_pairs_are_synthetically_verified(self):
        path, sha = synthetic_zip(self.root)
        result = analyze(path, expected_sha256=sha)
        self.assertEqual(result["member_pairs_verified"], 5)
        self.assertEqual(set(result["pair_layouts"]), set(PAIRS))
        self.assertFalse(result["model_input_approved"])
        self.assertFalse(result["instrument_timeline_verified"])
        self.assertFalse(result["instrument_values_emitted"])
        self.assertNotIn("PrivateDevice", str(result))
        self.assertNotIn("secret instrument", str(result))
        for value in result["pair_layouts"].values():
            self.assertEqual(value["txt"]["valid_calendar_tokens"], 2)
            self.assertEqual(value["html"]["tables"], 1)

    def test_wrong_original_sha_rejected(self):
        path, _ = synthetic_zip(self.root)
        with self.assertRaises(EquipmentBlocked):
            analyze(path, expected_sha256="0" * 64)

    def test_missing_original_pair_rejected(self):
        path, sha = synthetic_zip(self.root, drop=PAIRS[0] + ".html")
        with self.assertRaisesRegex(EquipmentBlocked, "set drifted"):
            analyze(path, expected_sha256=sha)

    def test_date_strings_do_not_become_approved_intervals(self):
        r = _txt_layout(b"Device unknown\n00003 20100101 20110331 OBSERVATION\n")
        self.assertEqual(r["valid_calendar_tokens"], 2)
        self.assertFalse(r["authoritative_column_mapping_proven"])
        self.assertFalse(r["instrument_change_proven"])
        self.assertEqual(r["first_three_line_signatures"][1]["candidate_date_offsets"], [6, 15])

    def test_bad_calendar_tokens_are_only_candidates(self):
        r = _txt_layout(b"Device 20100230 20101231\n")
        self.assertEqual(r["candidate_date_tokens"], 2)
        self.assertEqual(r["valid_calendar_tokens"], 1)

    def test_provider_header_field_names_only_without_rows(self):
        names = ["Stations_id", "von_datum", "bis_datum", "Gerat", "Parameter",
                 "Hohe", "Einheit", "Methode"]
        data = (";".join(names) + chr(10) + "PRIVATE;20000101;20201231;SECRET;OTHER;A;B;C" + chr(10)).encode()
        result = _txt_layout(data)
        self.assertTrue(result["header_candidate_recognized"])
        self.assertEqual(result["source_column_names"], names)
        self.assertNotIn("PRIVATE", str(result))
        self.assertNotIn("SECRET", str(result))
        self.assertFalse(result["authoritative_column_mapping_proven"])

    def test_cp1252_legacy_hint(self):
        r = _html_layout("<html>Geräte</html>".encode("cp1252"))
        self.assertEqual(r["encoding_hint"], "cp1252_heuristic")
        self.assertFalse(r["provider_html_semantics_interpreted"])

    def test_no_html_or_txt_data_content_disclosure(self):
        t = _txt_layout(b"SN PRIVATE_FIRST_LAST\n00003 20100101 20101231 SECRET\n")
        h = _html_layout(b"<table><tr><th>SecretName</th><td>secretvalue</td></tr></table>")
        self.assertNotIn("PRIVATE_FIRST_LAST", str(t))
        self.assertNotIn("SecretName", str(h))
        self.assertNotIn("secretvalue", str(h))
        self.assertEqual(h["header_cells"], 1)
        self.assertEqual(h["value_cells"], 1)

    def test_oversized_text_and_html_blocked(self):
        with self.assertRaises(EquipmentBlocked):
            _txt_layout(b"x" * 512001)
        with self.assertRaises(EquipmentBlocked):
            _html_layout(b"x" * 512001)
        with self.assertRaises(EquipmentBlocked):
            _txt_layout(b"")
        with self.assertRaises(EquipmentBlocked):
            _html_layout(b"")

    def test_too_many_rows_or_long_line_blocked(self):
        with self.assertRaises(EquipmentBlocked):
            _txt_layout(b"x\n" * 513)
        with self.assertRaises(EquipmentBlocked):
            _txt_layout(b"x" * 8193)

    def test_date_offset_never_exposes_date_values(self):
        r = _txt_layout(b"A 20100101 20110331 Secret\n")
        self.assertNotIn("20100101", str(r))
        self.assertNotIn("Secret", str(r))
        self.assertEqual(r["valid_calendar_tokens"], 2)

    def test_no_symlinks_into_external_source(self):
        path, sha = synthetic_zip(self.root)
        alias = self.root / "alias.zip"
        alias.symlink_to(path)
        with self.assertRaises(EquipmentBlocked):
            analyze(alias, expected_sha256=sha)


if __name__ == "__main__":
    unittest.main()
