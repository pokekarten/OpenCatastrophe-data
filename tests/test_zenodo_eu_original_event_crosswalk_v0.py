# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only hazard-index identity, unit and event join regression tests."""

from __future__ import annotations

import csv
import io
import unittest

from scripts.zenodo_eu_original_event_crosswalk_v0 import (
    INDEX_HEADER, SOURCES, CrosswalkError, original_file_receipt,
    parse_index, reconcile,
)
from tests.test_zenodo_eu_wind_flood_pairs_preflight_v0 import rows


def index_bytes(peril: str, **changes: str) -> bytes:
    entries = {
        "ws": ["ws", "ws1687", "2017-01-08", "2017-01-10",
               "-24.99", "17.56", "50.75", "69.67", "19.33", "Mean wind speed (m/s)"],
        "fl": ["fl", "fl614", "2017-01-02", "2017-03-06",
               "13.33", "60.60", "52.84", "68.96", "38.59", "Mean flood depth (cm)"],
    }
    values = list(entries[peril])
    for k, v in changes.items():
        values[INDEX_HEADER.index(k)] = v
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(INDEX_HEADER)
    w.writerow(values)
    return b.getvalue().encode()


class TestZenodoEuOriginalEventCrosswalk(unittest.TestCase):
    def test_exact_synthetic_join(self) -> None:
        r = reconcile(index_bytes("ws"), index_bytes("fl"), rows())
        self.assertTrue(r["exact_event_id_crosswalk_complete"])
        self.assertEqual(r["original_wind_catalogue_events"], 1)
        self.assertEqual(r["original_flood_catalogue_events"], 1)
        self.assertEqual(r["pair_source_diagnostic"]["wind_flood_pair_rows"], 1)
        self.assertFalse(r["model_input_admitted"])
        self.assertFalse(r["pixel_overlap_proven"])
        self.assertFalse(r["insured_loss_generated"])

    def test_missing_index_id_is_reported_not_fabricated(self) -> None:
        r = reconcile(index_bytes("ws"), index_bytes("fl", groupname="fl615"), rows())
        self.assertEqual(r["unique_missing_index_ids"], 1)
        self.assertFalse(r["exact_event_id_crosswalk_complete"])

    def test_date_mismatch_flag(self) -> None:
        r = reconcile(index_bytes("ws", start_date="2017-01-07"), index_bytes("fl"), rows())
        self.assertEqual(r["unique_event_date_mismatches"], 1)
        self.assertFalse(r["exact_event_id_crosswalk_complete"])

    def test_bbox_mismatch_flag(self) -> None:
        r = reconcile(index_bytes("ws", minlon="-23.0"), index_bytes("fl"), rows())
        self.assertEqual(r["unique_event_bbox_mismatches"], 1)

    def test_intensity_mismatch_flag(self) -> None:
        r = reconcile(index_bytes("ws", intensity="20.33"), index_bytes("fl"), rows())
        self.assertEqual(r["unique_event_intensity_mismatches"], 1)

    def test_duplicate_original_id_rejected(self) -> None:
        b = index_bytes("ws")
        with self.assertRaisesRegex(CrosswalkError, "duplicate"):
            parse_index(b + b.splitlines(keepends=True)[-1], "ws")

    def test_incompatible_original_unit_rejected(self) -> None:
        with self.assertRaisesRegex(CrosswalkError, "unit"):
            parse_index(index_bytes("fl", **{"intensity unit": "Mean flood depth (m)"}), "fl")

    def test_wrong_hazard_code_rejected(self) -> None:
        with self.assertRaisesRegex(CrosswalkError, "peril/ID"):
            parse_index(index_bytes("ws", hazardtype="fl"), "ws")

    def test_bad_source_geometry_rejected(self) -> None:
        with self.assertRaisesRegex(CrosswalkError, "geometry"):
            parse_index(index_bytes("ws", maxlat="99"), "ws")

    def test_original_identity_requires_actual_publisher_bytes(self) -> None:
        with self.assertRaisesRegex(CrosswalkError, "original size/MD5"):
            original_file_receipt("flood", index_bytes("fl"))
        self.assertEqual(SOURCES["flood"][1], 477845)
        self.assertEqual(SOURCES["pairs"][1], 801138)


if __name__ == "__main__":
    unittest.main()
