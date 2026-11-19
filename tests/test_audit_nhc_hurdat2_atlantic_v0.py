# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent synthetic-only HURDAT2 Atlantic strict preflight regression."""
from __future__ import annotations

import unittest

from scripts.audit_nhc_hurdat2_atlantic_v0 import audit_bytes, HURDAT2PreflightError


def record(date="20210829", hhmm="1200", marker="", status="HU", lat="29.2N", lon="90.4W",
           wind="90", pressure="950", radii=None, rmw="-999"):
    if radii is None:
        radii = ["-999"] * 12
    return ", ".join([date, hhmm, marker, status, lat, lon, wind, pressure, *radii, rmw])


def document(rows=None, header="AL092021, TEST, 2,", next_storm=False):
    if rows is None:
        rows = [record(), record(hhmm="1655", marker="L", wind="-99", pressure="-999")]
    entries = [header, *rows]
    if next_storm:
        entries += ["AL102021, OTHER, 1,", record("20210905", "0000", "", "TD", "0.0N", "0.0E")]
    return ("\n".join(entries) + "\n").encode("ascii")


class NHCAtlanticPreflightTests(unittest.TestCase):
    def test_valid_synthetic_with_missing_not_zero_and_asynoptic(self):
        receipt = audit_bytes(document(next_storm=True))
        self.assertEqual((receipt["storms"], receipt["tracks"]), (2, 3))
        self.assertEqual(receipt["asynoptic_tracks"], 1)
        self.assertEqual(receipt["missing_wind"], 1)
        self.assertEqual(receipt["missing_pressure"], 1)
        self.assertEqual(receipt["missing_wind_radii"], 36)
        self.assertEqual(receipt["missing_rmw"], 3)
        self.assertEqual(receipt["model_admission"], "not_admitted")
        self.assertEqual(receipt["input_provider_provenance"], "not_verified")
        self.assertEqual(len(receipt["input_sha256"]), 64)

    def test_real_zero_is_not_marked_missing(self):
        s = audit_bytes(document([record(radii=["0"] * 12, rmw="0")], "AL092021, TEST, 1,"))
        self.assertEqual(s["missing_wind_radii"], 0)
        self.assertEqual(s["missing_rmw"], 0)

    def test_missing_rare_1967_wind_is_not_zero(self):
        s = audit_bytes(document([record(wind="-99")], "AL011967, TEST, 1,"))
        self.assertEqual(s["missing_wind"], 1)

    def test_reject_invalid_files(self):
        examples = [
            b"", b"\0", b"\xff", b"bad\n", document(header="EP092021, TEST, 2,"),
            document(header="AL092021, TEST, 3,"),
            document(header="AL092021, TEST, 0,"),
            document(header="AL092021, TEST, 2"),
            document(rows=[record(), record(hhmm="1200")]),
            document(rows=[record(hhmm="1655"), record(hhmm="1200")]),
            document(rows=[record(lat="91.0N"), record(hhmm="1655")]),
            document(rows=[record(lon="190.0W"), record(hhmm="1655")]),
            document(rows=[record(status="XX"), record(hhmm="1655")]),
            document(rows=[record(marker="X"), record(hhmm="1655")]),
            document(rows=[record(date="20210230"), record(hhmm="1655")]),
            document(rows=[record(hhmm="2460"), record(hhmm="1655")]),
            document(rows=[record(wind="-999"), record(hhmm="1655")]),
            document(rows=[record(pressure="-99"), record(hhmm="1655")]),
            document(rows=[record(radii=["-99"] * 12), record(hhmm="1655")]),
            document(rows=[record(rmw="-99"), record(hhmm="1655")]),
            document(rows=[record().rsplit(",", 1)[0], record(hhmm="1655")]),
            document(rows=[record(), record(hhmm="1655")], next_storm=True).replace(b"AL102021", b"AL092021"),
            document().replace(b"\n", b"\n\n", 1),
            b"a" * (16 * 1024 * 1024 + 1),
        ]
        for pos, data in enumerate(examples):
            with self.subTest(pos=pos), self.assertRaises(HURDAT2PreflightError):
                audit_bytes(data)


if __name__ == "__main__":
    unittest.main()
