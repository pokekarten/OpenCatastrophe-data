# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Purely synthetic/offline tests; never collect original NOAA CSV bytes."""

import hashlib
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research_runners.noaa_ibtracs_v04r01_csv_source_audit_v0 import (
    IBTrACSAuditError, audit_original_file, audit_rows, REQUIRED,
)


def synthetic_csv(*, lon="266.9", units=True, malformed=False, duplicate=False):
    header = list(REQUIRED) + [f"FILL_{i}" for i in range(174 - len(REQUIRED))]
    if duplicate:
        header[-1] = header[0]
    unit_fields = ["" for _ in header]
    unit_fields[header.index("LAT")] = "degrees_north"
    unit_fields[header.index("LON")] = "degrees_east"
    row = ["" for _ in header]
    for name, value in {
        "SID": "2001011N22345", "ISO_TIME": "2001-01-01 00:00:00",
        "LAT": "-16.2", "LON": lon, "SEASON": "2001", "BASIN": "SP",
        "TRACK_TYPE": "main", "WMO_WIND": "", "USA_WIND": "34",
    }.items():
        row[header.index(name)] = value
    if malformed:
        row.pop()
    return ",".join(header) + "\n" + (",".join(unit_fields) + "\n" if units else "") + ",".join(row) + "\n"


class IBTrACSOriginalSourceAuditTests(unittest.TestCase):
    def test_native_longitude_over_180_not_invalid(self):
        self.assertEqual(audit_rows(io.StringIO(synthetic_csv())), {
            "data_rows": 1, "distinct_storm_ids": 1,
            "longitude_gt_180_rows": 1, "column_count": 174,
        })

    def test_units_duplicate_header_and_ragged_rows_fail_closed(self):
        for payload in (
            synthetic_csv(units=False),
            synthetic_csv(malformed=True),
            synthetic_csv(duplicate=True),
        ):
            with self.subTest(payload=payload[:40]), self.assertRaises(IBTrACSAuditError):
                audit_rows(io.StringIO(payload))

    def test_bad_coordinates_and_nan_fail_closed(self):
        for lon in ("401", "NaN", "inf", "abc"):
            with self.subTest(lon=lon), self.assertRaises(IBTrACSAuditError):
                audit_rows(io.StringIO(synthetic_csv(lon=lon)))

    def test_bounded_row_limit(self):
        with self.assertRaises(IBTrACSAuditError):
            audit_rows(io.StringIO(synthetic_csv()), max_records=0)

    def test_file_identity_and_frozen_metrics(self):
        data = synthetic_csv().encode()
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "ibtracs.ALL.list.v04r01.csv"
            path.write_bytes(data)
            result = audit_original_file(
                path, expected_bytes=len(data),
                expected_sha256=hashlib.sha256(data).hexdigest(),
                expected_metrics=(1, 1, 1),
            )
            self.assertFalse(result["model_input_approved"])
            self.assertFalse(result["rights_approved_for_commercial_model"])
            with self.assertRaises(IBTrACSAuditError):
                audit_original_file(path, expected_bytes=len(data),
                                    expected_sha256="0" * 64, expected_metrics=(1, 1, 1))
            with self.assertRaises(IBTrACSAuditError):
                audit_original_file(path, expected_bytes=len(data),
                                    expected_sha256=hashlib.sha256(data).hexdigest(),
                                    expected_metrics=(1, 2, 1))


if __name__ == "__main__":
    unittest.main()
