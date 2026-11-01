# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for original DWD station 00003 geography timeline audit."""
from __future__ import annotations

from datetime import date
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.dwd_station_geography_interval_research_v0 import (
    GeographyBlocked, _day_audit, _date_label, _parse_geography, analyze,
)

HEADER = "Stations_id;Stationshoehe;Geogr.Breite;Geogr.Laenge;von_datum;bis_datum;Stationsname\r\n"


def row(begin, end, lat="48.2", lon="11.5", height="510", station="00003"):
    return f"{station};{height};{lat};{lon};{begin};{end};SyntheticPlace\r\n"


def original(base, geo_rows):
    p = base / "Meta_Daten_zehn_min_fx_00003.zip"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Metadaten_Geographie_00003.txt",
                   HEADER + "".join(geo_rows))
        z.writestr("Metadaten_Geraete_00003.txt", "synthetic unavailable instrument")
        z.writestr("Metadaten_Parameter_00003.txt", "synthetic unavailable parameter")
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


class GeographyIntervalResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_one_original_history_segment_covering_window(self):
        path, sha = original(self.root, [row("20000101", "20191231")])
        result = analyze(path, expected_sha256=sha)
        self.assertEqual(result["original_geography_history_rows"], 1)
        self.assertEqual(result["distinct_original_geographic_positions"], 1)
        self.assertEqual(result["provisional_inclusive_candidate_unique_days"], 455)
        self.assertEqual(result["provisional_inclusive_multiple_candidate_days"], 0)
        self.assertEqual(result["provisional_inclusive_zero_candidate_days"], 0)
        self.assertFalse(result["production_geographic_join_approved"])
        self.assertFalse(result["station_coordinates_emitted"])
        self.assertNotIn("48.2", str(result))
        self.assertNotIn("SyntheticPlace", str(result))

    def test_duplicate_periods_are_marked_ambiguous_not_silently_selected(self):
        source = (HEADER + row("20000101", "20191231")
                  + row("20100101", "20110331", lat="48.3")).encode()
        segments = _parse_geography(source)
        counts = _day_audit(segments)
        self.assertEqual(counts["provisional_inclusive_multiple_candidate_days"], 455)
        self.assertEqual(counts["provisional_inclusive_candidate_unique_days"], 0)

    def test_partial_coverage_reports_gaps_without_interpolation(self):
        source = (HEADER + row("20100101", "20101231")).encode()
        counts = _day_audit(_parse_geography(source))
        self.assertEqual(counts["provisional_inclusive_candidate_unique_days"], 365)
        self.assertEqual(counts["provisional_inclusive_zero_candidate_days"], 90)

    def test_geography_date_labels_must_be_exact_yyyymmdd(self):
        for value in ("2010-01-01", "201001", "20100230", "N/A", "201001010000"):
            with self.subTest(value=value), self.assertRaises(GeographyBlocked):
                _date_label(value)
        self.assertEqual(_date_label("20100101"), date(2010, 1, 1))

    def test_inverted_period_or_wrong_station_fails_closed(self):
        for rows in ([row("20120101", "20100101")],
                     [row("20100101", "20110331", station="00004")]):
            with self.subTest(rows=rows), self.assertRaises(GeographyBlocked):
                _parse_geography((HEADER + "".join(rows)).encode())

    def test_invalid_geography_numeric_and_nonfinite_fail(self):
        for lat, lon, height in (("NaN", "11", "500"), ("91", "11", "500"),
                                 ("48", "181", "500"), ("48", "11", "Infinity")):
            with self.subTest(lat=lat, lon=lon, height=height), self.assertRaises(GeographyBlocked):
                _parse_geography((HEADER + row("20100101", "20110331", lat, lon, height)).encode())

    def test_malformed_or_unexpected_provider_header_fails(self):
        raw = (HEADER.replace("Geogr.Breite", "Latitude")
               + row("20100101", "20110331")).encode()
        with self.assertRaises(GeographyBlocked):
            _parse_geography(raw)

    def test_wrong_pinned_sha_rejected(self):
        path, _ = original(self.root, [row("20000101", "20200101")])
        with self.assertRaises(GeographyBlocked):
            analyze(path, expected_sha256="f" * 64)

    def test_metadata_without_required_families_rejected(self):
        path = self.root / "Meta_Daten_zehn_min_fx_00003.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("Metadaten_Geographie_00003.txt", HEADER + row("20000101", "20191231"))
        with self.assertRaises(GeographyBlocked):
            analyze(path, expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def test_overlong_row_or_duplicate_columns_fails(self):
        raw = (HEADER + row("20100101", "20110331") + "X" * 600000).encode()
        with self.assertRaises(GeographyBlocked):
            _parse_geography(raw)
        raw = (HEADER.replace("Geogr.Laenge", "Geogr.Breite")
               + row("20100101", "20110331")).encode()
        with self.assertRaises(GeographyBlocked):
            _parse_geography(raw)


if __name__ == "__main__":
    unittest.main()
