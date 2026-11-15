# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests for exact-original two-station zero-lag DWD pairing."""
from __future__ import annotations

from datetime import timedelta
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.dwd_two_station_paired_gust_v0 import (
    START, END, FIRST_FILE, SECOND_FILE, PairedWindBlocked,
    _extract, _paired_stats, compare, main,
)

HEADER = "STATIONS_ID;MESS_DATUM;QN;FX_10;FNX_10;FMX_10;DX_10;eor\n"


def source(folder: Path, name: str, station: str, *,
           stamps=None, gusts=None, extra_member=None):
    stamps = stamps or ("201001010000", "201001010010", "201001010020")
    gusts = gusts or ("11.0", "16.0", "22.0")
    path = folder / name
    data = HEADER + "".join(
        f"{int(station)};{timestamp};3;{gust};1;1;90;eor\n"
        for timestamp, gust in zip(stamps, gusts)
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"produkt_zehn_min_fx_20100101_20110901_{station}.txt", data)
        if extra_member:
            z.writestr(extra_member, b"bad")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_full_samples(transform=lambda i: (float(i % 51) + 1, float(i % 51) + 1)):
    a = {}
    b = {}
    t = START
    count = 0
    while t <= END:
        x, y = transform(count)
        a[t] = (x, 3)
        b[t] = (y, 3)
        t += timedelta(minutes=10)
        count += 1
    return (
        {"shared_samples": a, "shared_missing": 0,
         "shared_qn_counts": {"3": count}},
        {"shared_samples": b, "shared_missing": 0,
         "shared_qn_counts": {"3": count}},
    )


class TwoStationPairedResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_original_two_sources_are_separately_sha_guarded(self):
        for name, station in ((FIRST_FILE, "00003"), (SECOND_FILE, "00348")):
            with self.subTest(station=station):
                path, digest = source(self.root, name, station)
                result = _extract(path, station=station, filename=name,
                                  digest=digest, expected_full_count=3)
                self.assertEqual(result["full_source_rows"], 3)
                self.assertEqual(len(result["shared_samples"]), 3)
                self.assertEqual(result["shared_missing"], 0)
                with self.assertRaises(PairedWindBlocked):
                    _extract(path, station=station, filename=name,
                             digest="0" * 64, expected_full_count=3)

    def test_one_to_one_zero_lag_positive_correlation(self):
        first, second = synthetic_full_samples(
            lambda i: (float(i % 51) + 1, 2 * (float(i % 51) + 1)))
        result = _paired_stats(first, second)
        self.assertEqual(result["paired_10min_samples"], 65520)
        self.assertEqual(result["pearson_r_zero_lag_unadjusted"], 1.0)
        self.assertFalse(result["serial_dependence_adjusted"])
        self.assertFalse(result["meteorological_event_dependence_derived"])
        self.assertEqual(len(result["cooccurrence_counts_by_gust_threshold"]), 3)
        self.assertNotIn("shared_samples", str(result))

    def test_negative_pearson_correlation_is_not_forced_positive(self):
        first, second = synthetic_full_samples(
            lambda i: (float(i % 51) + 1, 60 - (float(i % 51) + 1)))
        result = _paired_stats(first, second)
        self.assertEqual(result["pearson_r_zero_lag_unadjusted"], -1.0)

    def test_missing_source_observation_blocks_admission(self):
        first, second = synthetic_full_samples()
        second["shared_missing"] = 1
        with self.assertRaises(PairedWindBlocked):
            _paired_stats(first, second)

    def test_missing_timestamp_blocks_even_if_other_values_exist(self):
        first, second = synthetic_full_samples()
        second["shared_samples"].pop(START)
        with self.assertRaises(PairedWindBlocked):
            _paired_stats(first, second)

    def test_no_variance_blocks_pearson(self):
        first, second = synthetic_full_samples(lambda i: (5.0, float(i % 20)))
        with self.assertRaises(PairedWindBlocked):
            _paired_stats(first, second)

    def test_wrong_station_in_source_content_is_blocked(self):
        path, digest = source(self.root, SECOND_FILE, "00349")
        with self.assertRaises(PairedWindBlocked):
            _extract(path, station="00348", filename=SECOND_FILE,
                     digest=digest, expected_full_count=3)

    def test_offgrid_or_missing_original_timestamps_block(self):
        for stamps in (("201001010000", "201001010020", "201001010030"),
                       ("201001010000", "201001010015", "201001010020"),
                       ("201001010000", "201001010000", "201001010010")):
            with self.subTest(stamps=stamps):
                path, digest = source(self.root, FIRST_FILE, "00003", stamps=stamps)
                with self.assertRaises(PairedWindBlocked):
                    _extract(path, station="00003", filename=FIRST_FILE,
                             digest=digest, expected_full_count=3)

    def test_negative_outside_missing_sentinel_and_nan_block(self):
        for speed in ("-10.0", "NaN", "Infinity"):
            with self.subTest(speed=speed):
                path, digest = source(self.root, FIRST_FILE, "00003",
                                      gusts=("11", speed, "22"))
                with self.assertRaises(PairedWindBlocked):
                    _extract(path, station="00003", filename=FIRST_FILE,
                             digest=digest, expected_full_count=3)

    def test_zip_traversal_member_blocks_data(self):
        path, digest = source(self.root, FIRST_FILE, "00003", extra_member="../unsafe")
        with self.assertRaises(PairedWindBlocked):
            _extract(path, station="00003", filename=FIRST_FILE,
                     digest=digest, expected_full_count=3)

    def test_actual_cli_rejects_unpinned_synthetic_archives(self):
        first, _ = source(self.root, FIRST_FILE, "00003")
        second, _ = source(self.root, SECOND_FILE, "00348")
        self.assertEqual(main(["--first-zip", str(first),
                               "--second-zip", str(second)]), 1)

    def test_synthetic_full_compare_requires_65520_paired_rows(self):
        first, a = source(self.root, FIRST_FILE, "00003")
        second, b = source(self.root, SECOND_FILE, "00348")
        with self.assertRaises(PairedWindBlocked):
            compare(first, second, first_digest=a, second_digest=b,
                    first_count=3, second_count=3)


if __name__ == "__main__":
    unittest.main()
