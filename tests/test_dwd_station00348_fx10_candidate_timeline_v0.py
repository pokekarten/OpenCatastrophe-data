# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only interval and original-source tests for second DWD FX_10 pilot."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.dwd_original_instrument_intervals_v0 import EQ_HEADERS, PAR_HEADERS
from scripts.dwd_station00348_fx10_candidate_timeline_v0 import (
    DEVICE_FILE, PARAMETER_FILE, Station00348JoinBlocked, inspect, main,
)
from scripts.probe_dwd_station00348_original_v0 import METADATA_FILE


def equipment(start="20000101", end="20201231", height="10",
              station="348", model="PRIVATE_INSTRUMENT"):
    return [station, "PRIVATE_PLACE", "11", "48", "500", height,
            start, end, model, "METHOD", "eor", ""]


def parameter(code, start="20000101", end="20201231", unit="m/sec",
              station="348"):
    return [station, start, end, "PRIVATE_PLACE", code, "PRIVATE_DESCRIPTION",
            unit, "V24", "-", "-", "-", "eor", ""]


def source(root, *, device=None, params=None, omit=None, filename=METADATA_FILE):
    defaults = [
        parameter("FX_10", "20000101", "20091231"),
        parameter("FX_10", "20100101", "20101231"),
        parameter("FX_10", "20110101", "20201231", unit="m/s"),
        parameter("FNX_10"),
        parameter("FMX_10"),
        parameter("DX_10", "20000101", "20091231"),
        parameter("DX_10", "20100101", "20101231"),
        parameter("DX_10", "20110101", "20201231"),
    ]
    src = root / filename
    with zipfile.ZipFile(src, "w", zipfile.ZIP_DEFLATED) as z:
        members = (
            (DEVICE_FILE, EQ_HEADERS, [device if device is not None else equipment()]),
            (PARAMETER_FILE, PAR_HEADERS, params if params is not None else defaults),
        )
        for name, header, rows in members:
            if name == omit:
                continue
            payload = (";".join(header) + "\n" +
                       "\n".join(";".join(x) for x in rows) +
                       "\nCopyright dummy footer\n")
            z.writestr(name, payload)
        z.writestr("Metadaten_Geographie_00348.txt",
                   "Stations_id;Von_Datum;Bis_Datum\n348;20000101;20201231\n")
    return src, hashlib.sha256(src.read_bytes()).hexdigest()


class Station00348FX10CandidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_exact_synthetic_history_over_609_days(self):
        path, digest = source(self.root)
        report = inspect(path, expected_sha256=digest)
        self.assertEqual(report["observed_measurement_calendar_days"], 609)
        self.assertEqual(report["unique_fx10_maxwind_candidate_days"], 609)
        self.assertEqual(report["missing_candidate_days"], 0)
        self.assertEqual(report["multiply_assigned_candidate_days"], 0)
        self.assertEqual(report["plausible_unverified_sensor_height_days"], 609)
        self.assertEqual(report["original_parameter_records"], 8)
        self.assertEqual(report["original_fx10_parameter_records"], 3)
        self.assertEqual(len(report["monthly_candidate_days"]), 21)
        self.assertFalse(report["model_input_approved"])
        self.assertFalse(report["device_fx10_foreign_key_verified"])
        self.assertFalse(report["original_metadata_matches_live_frozen_sha"])
        self.assertNotIn("PRIVATE_INSTRUMENT", str(report))

    def test_gap_is_retained_not_interpolated(self):
        path, digest = source(self.root, device=equipment(end="20101231"))
        report = inspect(path, expected_sha256=digest)
        self.assertEqual(report["missing_candidate_days"], 244)
        self.assertEqual(report["unique_fx10_maxwind_candidate_days"], 365)

    def test_fx10_overlap_not_silently_resolved(self):
        params = [
            parameter("FX_10", "20100101", "20111231"),
            parameter("FX_10", "20100101", "20111231"),
            parameter("FX_10", "20000101", "20091231"),
            parameter("FNX_10"), parameter("FMX_10"),
            parameter("DX_10"), parameter("DX_10"), parameter("DX_10"),
        ]
        path, digest = source(self.root, params=params)
        report = inspect(path, expected_sha256=digest)
        self.assertEqual(report["multiply_assigned_candidate_days"], 609)
        self.assertEqual(report["unique_fx10_maxwind_candidate_days"], 0)

    def test_meters_per_second_alias_and_unit_mismatch_separate(self):
        path, digest = source(self.root)
        report = inspect(path, expected_sha256=digest)
        self.assertEqual(report["source_unit_candidate_days"],
                         {"source_meters_per_second_candidate": 609})
        params = [
            parameter("FX_10", "20000101", "20091231"),
            parameter("FX_10", "20100101", "20101231", unit="knots"),
            parameter("FX_10", "20110101", "20201231", unit="m/sec"),
            parameter("FNX_10"), parameter("FMX_10"),
            parameter("DX_10"), parameter("DX_10"), parameter("DX_10"),
        ]
        path, digest = source(self.root, params=params)
        report = inspect(path, expected_sha256=digest)
        self.assertEqual(report["source_unit_candidate_days"]["source_meters_per_second_candidate"], 244)
        self.assertTrue(any(k.startswith("unrecognized_unit_sha256_")
                            for k in report["source_unit_candidate_days"]))

    def test_bad_or_unknown_sensor_height_not_admitted(self):
        path, digest = source(self.root, device=equipment(height="-999"))
        report = inspect(path, expected_sha256=digest)
        self.assertEqual(report["plausible_unverified_sensor_height_days"], 0)
        self.assertFalse(report["model_input_approved"])

    def test_station_identity_mismatch_fails(self):
        path, digest = source(self.root, device=equipment(station="349"))
        with self.assertRaises(Station00348JoinBlocked):
            inspect(path, expected_sha256=digest)

    def test_missing_maxwind_or_parameter_member_fails(self):
        for missing in (DEVICE_FILE, PARAMETER_FILE):
            with self.subTest(missing=missing):
                path, digest = source(self.root, omit=missing)
                with self.assertRaises(Station00348JoinBlocked):
                    inspect(path, expected_sha256=digest)

    def test_new_source_sha_not_silently_accepted(self):
        path, digest = source(self.root)
        with self.assertRaises(Station00348JoinBlocked):
            inspect(path, expected_sha256="0" * 64)
        self.assertEqual(len(digest), 64)

    def test_wrong_filename_and_symlink_rejected(self):
        path, digest = source(self.root, filename="Meta_Daten_zehn_min_fx_00349.zip")
        with self.assertRaises(Station00348JoinBlocked):
            inspect(path, expected_sha256=digest)
        correct, digest = source(self.root)
        link = self.root / "alias.zip"
        link.symlink_to(correct)
        with self.assertRaises(Station00348JoinBlocked):
            inspect(link, expected_sha256=digest)

    def test_reject_unexpected_original_parameter_vocabulary(self):
        params = [
            parameter("FX_10"), parameter("FX_10"), parameter("FX_10"),
            parameter("FNX_10"), parameter("FMX_10"),
            parameter("DX_10"), parameter("DX_10"), parameter("UNKNOWN"),
        ]
        path, digest = source(self.root, params=params)
        with self.assertRaises(Station00348JoinBlocked):
            inspect(path, expected_sha256=digest)

    def test_main_cli_is_frozen_to_real_original_sha(self):
        path, digest = source(self.root)
        self.assertEqual(main(["--metadata-zip", str(path)]), 1)
        self.assertFalse(inspect(path, expected_sha256=digest)["model_input_approved"])


if __name__ == "__main__":
    unittest.main()
