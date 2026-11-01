# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline negative-source tests: strict original FX_10 ↔ Maxwind candidate only."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.dwd_equipment_layout_evidence_v0 import PAIRS
from scripts.dwd_original_instrument_intervals_v0 import EQ_HEADERS, PAR_HEADERS
from scripts.dwd_fx10_maxwind_candidate_join_v0 import (
    CandidateJoinBlocked, CANDIDATE_DEVICE_FAMILY, PARAMETERS,
    _daily_pair_count, inspect,
)


def _text(columns, records):
    return (";".join(columns) + chr(10)
            + chr(10).join(";".join(row) for row in records) + chr(10)
            + "Original synthetic source footer" + chr(10)).encode("utf-8")


def eq(start="20100101", end="20191231", height="10", name="PRIVATEDEVICE"):
    return ["3", "Private station", "11.5", "48.2", "500", height,
            start, end, name, "PrivateMethod", "eor", ""]


def par(code="FX_10", start="20100101", end="20191231", unit="m/s"):
    return ["3", start, end, "Private station", code, "PRIVATE DESCRIPTION",
            unit, "V24", "-", "-", "-", "eor", ""]


def default_parameters():
    return [
        par("FX_10", "19900101", "20091231"),
        par("FX_10", "20100101", "20101231"),
        par("FX_10", "20110101", "20191231"),
        par("FNX_10"),
        par("FMX_10"),
        par("DX_10", "19900101", "20091231"),
        par("DX_10", "20100101", "20101231"),
        par("DX_10", "20110101", "20191231"),
    ]


def source(root, *, eq_rows=None, parameter_rows=None, wrong_station=False):
    path = root / "Meta_Daten_zehn_min_fx_00003.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as a:
        a.writestr("Metadaten_Geographie_00003.txt",
                   "Stations_id;von_datum;bis_datum\n3;20000101;20191231\n")
        for stem in PAIRS:
            for ext in (".txt", ".html"):
                name = stem + ext
                if ext == ".html":
                    payload = b"<table><tr><th>DATA</th></tr></table>"
                elif stem == PARAMETERS:
                    payload = _text(PAR_HEADERS,
                                    parameter_rows if parameter_rows is not None
                                    else default_parameters())
                elif stem == CANDIDATE_DEVICE_FAMILY:
                    payload = _text(EQ_HEADERS,
                                    eq_rows if eq_rows is not None
                                    else [eq("19900101", "20091231", name="old"),
                                          eq("20100101", "20191231")])
                else:
                    if stem in (PAIRS[0], PAIRS[2]):
                        payload = _text(EQ_HEADERS, [eq()])
                    else:
                        payload = _text(EQ_HEADERS, [eq("19900101", "20091231"),
                                                    eq("20100101", "20191231")])
                a.writestr(name, payload)
    if wrong_station:
        # Fingerprint drift while retaining a parseable archive.
        b = path.read_bytes()
        path.write_bytes(b + b"modified")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


class FX10CandidateJoinTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_original_candidate_pair_has_full_455_day_coverage(self):
        path, digest = source(self.root)
        report = inspect(path, expected_sha256=digest)
        self.assertEqual(report["window_days"], 455)
        self.assertEqual(report["one_candidate_pair_days"], 455)
        self.assertEqual(report["missing_candidate_pair_days"], 0)
        self.assertEqual(report["multiple_candidate_pair_days"], 0)
        self.assertEqual(report["one_pair_days_with_non_matching_unit"], 0)
        self.assertEqual(report["one_pair_days_with_plausible_unverified_sensor_height"], 455)
        self.assertFalse(report["original_device_parameter_foreign_key_proven"])
        self.assertFalse(report["model_input_approved"])
        self.assertEqual(report["fx10_original_parameter_records"], 3)
        self.assertEqual(len(report["monthly_candidate_pair_counts"]), 15)
        self.assertNotIn("PRIVATE", str(report))

    def test_missing_device_window_is_not_interpolated(self):
        path, sha = source(self.root, eq_rows=[
            eq("19900101", "20091231"), eq("20100101", "20101231")])
        report = inspect(path, expected_sha256=sha)
        self.assertEqual(report["missing_candidate_pair_days"], 90)
        self.assertEqual(report["one_candidate_pair_days"], 365)

    def test_multiple_fx10_intervals_cannot_be_silently_selected(self):
        rows = default_parameters()
        rows[1] = par("FX_10", "20100101", "20191231")
        path, sha = source(self.root, parameter_rows=rows)
        report = inspect(path, expected_sha256=sha)
        self.assertEqual(report["multiple_candidate_pair_days"], 90)
        self.assertEqual(report["one_candidate_pair_days"], 365)

    def test_mismatch_of_official_gust_unit_remains_explicit(self):
        rows = default_parameters()
        rows[1] = par("FX_10", "20100101", "20101231", unit="knots")
        path, sha = source(self.root, parameter_rows=rows)
        report = inspect(path, expected_sha256=sha)
        self.assertEqual(report["one_pair_days_with_non_matching_unit"], 365)

    def test_invalid_candidate_mast_height_is_never_promoted(self):
        path, sha = source(self.root, eq_rows=[
            eq("19900101", "20091231"), eq("20100101", "20191231", height="-999")])
        report = inspect(path, expected_sha256=sha)
        self.assertEqual(report["one_pair_days_with_plausible_unverified_sensor_height"], 0)
        self.assertFalse(report["scientific_instrument_join_approved"])

    def test_changed_original_bytes_fail_sha_gate(self):
        path, _ = source(self.root)
        with self.assertRaises(CandidateJoinBlocked):
            inspect(path, expected_sha256="f" * 64)

    def test_symlink_original_source_is_rejected(self):
        path, sha = source(self.root)
        link = self.root / "alias.zip"
        link.symlink_to(path)
        with self.assertRaises(CandidateJoinBlocked):
            inspect(link, expected_sha256=sha)

    def test_forged_fx10_cardinality_fails(self):
        rows = default_parameters()
        rows[0] = par("DX_10", "19900101", "20091231")
        path, sha = source(self.root, parameter_rows=rows)
        with self.assertRaisesRegex(CandidateJoinBlocked, "cardinality"):
            inspect(path, expected_sha256=sha)

    def test_unrecognized_parameter_vocabulary_fails(self):
        rows = default_parameters()
        rows[3] = par("OTHER")
        path, sha = source(self.root, parameter_rows=rows)
        with self.assertRaisesRegex(CandidateJoinBlocked, "vocabulary"):
            inspect(path, expected_sha256=sha)

    def test_malformed_native_header_fails(self):
        data = _text(["INVALID", *EQ_HEADERS[1:]], [eq()])
        from scripts.dwd_original_instrument_intervals_v0 import _rows, InstrumentAuditBlocked
        with self.assertRaises(InstrumentAuditBlocked):
            _rows(data, EQ_HEADERS)

    def test_daily_counts_without_source_rows_never_leak(self):
        from datetime import date
        rows = [
            {"__begin": date(2010,1,1), "__end": date(2011,3,31),
             "Geraetetyp Name": "SENSITIVE", "Messverfahren": "PRIVATE",
             "Geberhoehe ueber Grund [m]": "10"},
        ]
        params = [{"__begin": date(2010,1,1), "__end": date(2011,3,31),
                   "Einheit": "m/s"}]
        report = _daily_pair_count(rows, params)
        self.assertEqual(report["one_candidate_pair_days"], 455)
        self.assertNotIn("SENSITIVE", str(report))
        self.assertNotIn("PRIVATE", str(report))


if __name__ == "__main__":
    unittest.main()
