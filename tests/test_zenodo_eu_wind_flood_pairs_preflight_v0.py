# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only regression for fail-closed original event-pair CSV proof."""

from __future__ import annotations

import csv
import io
import unittest

from scripts.zenodo_eu_wind_flood_pairs_preflight_v0 import (
    EXPECTED_BYTES, HEADER, ORIGINAL_URL, OriginalPairError, original_receipt,
    parse_pair_csv,
)


def rows(*changes: dict[str, str]) -> bytes:
    exemplar = {
        "groupname_1": "ws1687", "groupname_2": "fl614",
        "start_date_1": "2017-01-08", "end_date_1": "2017-01-10",
        "start_date_2": "2017-01-02", "end_date_2": "2017-03-06",
        "hazardtype_1": "ws",
        "minlon_1": "-24.99", "maxlon_1": "17.56",
        "minlat_1": "50.75", "maxlat_1": "69.67",
        "intensity_1": "19.33", "intensity unit_1": "Mean wind speed (m/s)",
        "hazardtype_2": "fl",
        "minlon_2": "13.33", "maxlon_2": "60.60",
        "minlat_2": "52.84", "maxlat_2": "68.96",
        "intensity_2": "38.59", "intensity unit_2": "Mean flood depth (cm)",
    }
    buf = io.StringIO(newline="")
    out = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n")
    out.writeheader()
    for item in changes or ({},):
        out.writerow({**exemplar, **item})
    return buf.getvalue().encode("utf-8")


class TestWindFloodPairPreflight(unittest.TestCase):
    def test_valid_synthetic_cross_peril_pair(self) -> None:
        report = parse_pair_csv(rows())
        self.assertEqual(report["wind_flood_pair_rows"], 1)
        self.assertEqual(report["pair_rows_without_calendar_overlap"], 0)
        self.assertEqual(report["pair_rows_without_bbox_overlap"], 0)
        self.assertTrue(report["bbox_overlap_not_sparse_pixel_overlap"])

    def test_counts_same_peril_rows_without_loss_claim(self) -> None:
        same = {
            "groupname_1": "ws1690", "groupname_2": "ws1691",
            "hazardtype_2": "ws", "intensity unit_2": "Mean wind speed (m/s)",
        }
        report = parse_pair_csv(rows({}, same))
        self.assertEqual(report["other_pair_rows_requires_scientific_review"], 1)
        self.assertEqual(report["wind_flood_pair_rows"], 1)
        self.assertTrue(report["original_event_ids_not_insured_losses"])

    def test_nonoverlap_is_flagged_without_fabricating_match(self) -> None:
        report = parse_pair_csv(rows({
            "start_date_2": "2017-02-01", "end_date_2": "2017-02-20",
            "minlon_2": "30", "maxlon_2": "40",
        }))
        self.assertEqual(report["pair_rows_without_calendar_overlap"], 1)
        self.assertEqual(report["pair_rows_without_bbox_overlap"], 1)

    def test_no_cross_peril_pair_blocked(self) -> None:
        same = {
            "groupname_1": "ws1690", "groupname_2": "ws1691",
            "hazardtype_2": "ws", "intensity unit_2": "Mean wind speed (m/s)",
        }
        with self.assertRaisesRegex(OriginalPairError, "no valid wind/flood"):
            parse_pair_csv(rows(same))

    def test_duplicate_pair_blocked(self) -> None:
        with self.assertRaisesRegex(OriginalPairError, "duplicate"):
            parse_pair_csv(rows({}, {}))

    def test_bad_id_hazard_blocked(self) -> None:
        with self.assertRaisesRegex(OriginalPairError, "hazard/event"):
            parse_pair_csv(rows({"groupname_1": "fl1"}))

    def test_bad_speed_unit_blocked(self) -> None:
        with self.assertRaisesRegex(OriginalPairError, "unit"):
            parse_pair_csv(rows({"intensity unit_1": "Peak gust (m/s)"}))

    def test_flood_depth_not_meters(self) -> None:
        with self.assertRaisesRegex(OriginalPairError, "unit"):
            parse_pair_csv(rows({"intensity unit_2": "Mean flood depth (m)"}))

    def test_end_before_start_blocked(self) -> None:
        with self.assertRaisesRegex(OriginalPairError, "precedes"):
            parse_pair_csv(rows({"end_date_1": "2017-01-01"}))

    def test_bad_calendar_day_blocked(self) -> None:
        with self.assertRaisesRegex(OriginalPairError, "impossible"):
            parse_pair_csv(rows({"start_date_1": "2017-02-30"}))

    def test_out_of_bounds_coordinates_blocked(self) -> None:
        with self.assertRaisesRegex(OriginalPairError, "bounding box"):
            parse_pair_csv(rows({"maxlat_1": "91"}))

    def test_nan_intensity_blocked(self) -> None:
        with self.assertRaisesRegex(OriginalPairError, "non-finite"):
            parse_pair_csv(rows({"intensity_2": "nan"}))

    def test_unexpected_column_blocked(self) -> None:
        raw = rows().replace(b"hazardtype_1", b"hazardtype_x")
        with self.assertRaisesRegex(OriginalPairError, "header"):
            parse_pair_csv(raw)

    def test_untrusted_bytes_blocked(self) -> None:
        with self.assertRaisesRegex(OriginalPairError, "truncated"):
            original_receipt(rows())
        self.assertGreater(EXPECTED_BYTES, 800000)
        self.assertEqual(ORIGINAL_URL, "https://zenodo.org/api/records/22080546/files/fl_ws.csv/content")


if __name__ == "__main__":
    unittest.main()
