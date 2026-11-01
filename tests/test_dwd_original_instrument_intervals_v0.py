# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only fail-closed tests for DWD equipment interval research."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.dwd_equipment_layout_evidence_v0 import PAIRS
from scripts.dwd_original_instrument_intervals_v0 import (
    EQ_HEADERS, PAR_HEADERS, InstrumentAuditBlocked, _rows, _coverage,
    _summary, _parameter_summary, analyze,
)


def eq_row(begin="20000101", end="20191231", device="T1", height="10",
           station="00003", method="METHOD"):
    return ["3" if station == "00003" else station, "SYNTHETIC", "11.5", "48.2",
            "500", height, begin, end, device, method, "eor", ""]


def param_row(begin="20000101", end="20191231", code="FX_10", station="00003"):
    return ["3" if station == "00003" else station, begin, end, "SYNTHETIC",
            code, "description", "m/s", "SV1", "-", "-", "-", "eor", ""]


def table(header, rows, footer=True):
    title = ";".join(header[:-1]) + ";"
    data = [";".join(row) for row in rows]
    if footer:
        data.append("Synthetic official footer text")
    return ("\n".join([title, *data]) + "\n").encode()


def source(folder, *, eq_overrides=None, param_override=None, drop=None):
    asset = folder / "Meta_Daten_zehn_min_fx_00003.zip"
    with zipfile.ZipFile(asset, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Metadaten_Geographie_00003.txt",
                   "Stations_id;von_datum;bis_datum\n3;20000101;20191231\n")
        for stem in PAIRS:
            for ext in (".txt", ".html"):
                name = stem + ext
                if name == drop:
                    continue
                raw = b"<table><tr><th>Secret</th></tr></table>"
                if ext == ".txt":
                    if stem.startswith("Metadaten_Parameter"):
                        raw = param_override if param_override is not None else table(PAR_HEADERS, [param_row()])
                    else:
                        rows = (eq_overrides or {}).get(stem, [eq_row()])
                        raw = table(EQ_HEADERS, rows)
                z.writestr(name, raw)
    return asset, hashlib.sha256(asset.read_bytes()).hexdigest()


class InstrumentIntervalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_all_four_families_cover_455_days_in_synthetic_source(self):
        path, sha = source(self.root)
        result = analyze(path, expected_sha256=sha)
        self.assertEqual(len(result["equipment_families"]), 4)
        for family in result["equipment_families"].values():
            self.assertEqual(family["unique_candidate_days"], 455)
            self.assertEqual(family["no_candidate_days"], 0)
            self.assertEqual(family["multiple_candidate_days"], 0)
            self.assertEqual(family["finite_candidate_sensor_height_records"], 1)
            self.assertFalse(family["device_replacement_proven"])
        self.assertEqual(result["parameter_family"]["pinned_observation_parameter_candidates"]["FX_10"]["unique_candidate_days"], 455)
        self.assertFalse(result["model_input_approved"])
        self.assertNotIn("SYNTHETIC", str(result))
        self.assertNotIn("METHOD", str(result))

    def test_two_overlapping_device_records_are_not_silently_chosen(self):
        stem = PAIRS[1]
        path, sha = source(self.root, eq_overrides={
            stem: [eq_row("20100101", "20110331", device="A"),
                   eq_row("20100101", "20110331", device="B")]})
        result = analyze(path, expected_sha256=sha)["equipment_families"][stem]
        self.assertEqual(result["multiple_candidate_days"], 455)
        self.assertEqual(result["distinct_candidate_device_method_height_combinations_in_window"], 2)
        self.assertFalse(result["device_replacement_proven"])

    def test_device_history_gap_is_explicit_not_interpolated(self):
        rows = _rows(table(EQ_HEADERS, [eq_row("20100101", "20101231")]), EQ_HEADERS)[0]
        s = _summary(rows, 1)
        self.assertEqual(s["unique_candidate_days"], 365)
        self.assertEqual(s["no_candidate_days"], 90)

    def test_original_extra_parameter_not_assumed_fx10(self):
        rows, footers = _rows(table(PAR_HEADERS, [param_row(code="OTHER"),
                                               param_row(code="FX_10")]), PAR_HEADERS)
        s = _parameter_summary(rows, footers)
        self.assertEqual(s["rows_with_unmapped_parameter_codes"], 1)
        self.assertEqual(s["pinned_observation_parameter_candidates"]["FX_10"]["original_candidate_rows"], 1)
        self.assertFalse(s["measured_fx_10_equipment_family_verified"])

    def test_wrong_station_is_blocked(self):
        with self.assertRaises(InstrumentAuditBlocked):
            _rows(table(EQ_HEADERS, [eq_row(station="00004")]), EQ_HEADERS)

    def test_invalid_or_reversed_date_intervals_block(self):
        for b, e in (("20130230", "20191231"),
                     ("20140101", "20120101"),
                     ("2010-01-01", "20110331")):
            with self.subTest(begin=b, end=e), self.assertRaises(InstrumentAuditBlocked):
                _rows(table(EQ_HEADERS, [eq_row(b, e)]), EQ_HEADERS)

    def test_data_after_footer_is_blocked(self):
        blob = table(EQ_HEADERS, [eq_row()]) + (";".join(eq_row()) + "\n").encode()
        with self.assertRaises(InstrumentAuditBlocked):
            _rows(blob, EQ_HEADERS)

    def test_schema_and_field_count_drift_block(self):
        changed = list(EQ_HEADERS)
        changed[6] = "Beginn"
        with self.assertRaises(InstrumentAuditBlocked):
            _rows(table(changed, [eq_row()]), EQ_HEADERS)
        with self.assertRaises(InstrumentAuditBlocked):
            _rows(table(EQ_HEADERS, [eq_row()[:-2]]), EQ_HEADERS)

    def test_unparsed_height_never_emits_fake_10m(self):
        rows, n = _rows(table(EQ_HEADERS, [eq_row(height="UNKNOWN")]), EQ_HEADERS)
        s = _summary(rows, n)
        self.assertEqual(s["finite_candidate_sensor_height_records"], 0)
        self.assertEqual(s["unparsed_or_out_of_range_height_records"], 1)

    def test_quoted_embedded_semicolon_must_not_change_native_positions(self):
        row = eq_row(device='"DEVICE;UNREVIEWED"')
        with self.assertRaises(InstrumentAuditBlocked):
            _rows(table(EQ_HEADERS, [row]), EQ_HEADERS)

    def test_original_member_set_missing_fails(self):
        path, sha = source(self.root, drop=PAIRS[0] + ".html")
        with self.assertRaises(InstrumentAuditBlocked):
            analyze(path, expected_sha256=sha)

    def test_wrong_original_sha_fails(self):
        path, _ = source(self.root)
        with self.assertRaises(InstrumentAuditBlocked):
            analyze(path, expected_sha256="0" * 64)

    def test_no_automatic_production_or_hazard_approval(self):
        path, sha = source(self.root)
        output = analyze(path, expected_sha256=sha)
        self.assertFalse(output["device_provenance_fully_validated"])
        self.assertFalse(output["model_input_approved"])
        self.assertFalse(output["original_instrument_values_emitted"])
        self.assertEqual(output["interval_endpoint_assumption"], "PROVISIONAL_BOTH_DATES_INCLUSIVE")


if __name__ == "__main__":
    unittest.main()
