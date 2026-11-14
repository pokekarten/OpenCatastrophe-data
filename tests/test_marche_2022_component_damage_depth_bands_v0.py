# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only tests for sample-conditional component damage summaries."""

from __future__ import annotations

import io
import json
import unittest
import zipfile
from decimal import Decimal

from research_runners.marche_2022_survey_original_preflight_v0 import SourceStructureError
from research_runners.marche_2022_component_damage_depth_bands_v0 import (
    DEPTH_BINS, _bin, _binary, _depth, _dictionary_outcome_contract,
    _summarize, _wilson,
)

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def make_dict(sector: str = "industrial", *, valid: bool = True) -> bytes:
    if sector == "industrial":
        aspect, field, values = "Observed damage", "Building structure and plants", '"0" false; "1" true'
    else:
        aspect, field, values = "Damage to external coating/perimeter", "Damage", '"yes"; "no"'
    if not valid:
        values = "not binary"
    def col(name: str, text: str) -> str:
        return f'<c r="{name}61" t="inlineStr"><is><t>{text}</t></is></c>'
    xml = f'<worksheet xmlns="{NS}"><sheetData><row r="61">'
    xml += col("B", aspect) + col("C", field) + col("D", "boolean") + col("E", values)
    xml += '</row></sheetData></worksheet>'
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/worksheets/sheet1.xml", xml)
    return output.getvalue()


class ComponentFrequencyTests(unittest.TestCase):
    def test_depth_metres_is_not_water_surface_elevation(self) -> None:
        self.assertEqual(_depth("0"), Decimal(0))
        self.assertEqual(_depth("1.25"), Decimal("1.25"))
        self.assertIsNone(_depth("-"))
        self.assertIsNone(_depth(""))

    def test_bad_depth_is_fail_closed(self) -> None:
        for s in ("-1", "NaN", "Infinity", "200", "1,4", "bad"):
            with self.subTest(value=s), self.assertRaises(SourceStructureError):
                _depth(s)

    def test_source_specific_binary_codes(self) -> None:
        self.assertEqual(_binary("1", "industrial"), 1)
        self.assertEqual(_binary("0", "industrial"), 0)
        self.assertEqual(_binary("yes", "residential"), 1)
        self.assertEqual(_binary("no", "residential"), 0)
        self.assertIsNone(_binary("-", "industrial"))
        self.assertIsNone(_binary("", "residential"))

    def test_cross_sector_binary_coding_rejected(self) -> None:
        with self.assertRaises(SourceStructureError):
            _binary("yes", "industrial")
        with self.assertRaises(SourceStructureError):
            _binary("1", "residential")

    def test_depth_bin_half_open_edges(self) -> None:
        cases = [("0", 0), ("0.499", 0), ("0.5", 1), ("0.999", 1),
                 ("1", 2), ("1.999", 2), ("2", 3)]
        for value, index in cases:
            with self.subTest(value=value):
                self.assertEqual(_bin(Decimal(value)), DEPTH_BINS[index])

    def test_wilson_is_bounded_and_includes_estimate(self) -> None:
        for pos, count in [(0, 20), (10, 20), (20, 20), (3, 11)]:
            with self.subTest(pos=pos):
                lower, upper = _wilson(pos, count)
                self.assertTrue(0 <= lower <= pos / count <= upper <= 1)

    def test_aggregate_no_original_rows_leaked(self) -> None:
        sample = [(Decimal("0.2"), int(i < 10)) for i in range(20)]
        result = _summarize(sample, sector="residential")
        item = result["published_depth_bins"][0]
        self.assertEqual(item["surveyed_properties_with_both_values"], 20)
        self.assertEqual(item["reported_damage_yes"], 10)
        self.assertEqual(item["observed_sample_fraction"], 0.5)
        self.assertFalse(item["suppressed"])
        self.assertFalse(result["raw_rows_or_coordinates_exported"])
        self.assertNotIn("identifier", json.dumps(result))

    def test_small_n_is_suppressed_without_counts(self) -> None:
        result = _summarize([(Decimal("2.5"), 1)] * 4, sector="industrial")
        entry = result["published_depth_bins"][-1]
        self.assertTrue(entry["suppressed"])
        self.assertNotIn("reported_damage_yes", entry)
        self.assertNotIn("surveyed_properties_with_both_values", entry)

    def test_rare_positive_suppressed(self) -> None:
        sample = [(Decimal("0.2"), int(i == 0)) for i in range(20)]
        entry = _summarize(sample, sector="residential")["published_depth_bins"][0]
        self.assertTrue(entry["suppressed"])

    def test_rare_negative_suppressed(self) -> None:
        sample = [(Decimal("0.2"), int(i != 0)) for i in range(20)]
        entry = _summarize(sample, sector="industrial")["published_depth_bins"][0]
        self.assertTrue(entry["suppressed"])

    def test_correct_publisher_dictionary_outcome_contracts(self) -> None:
        _dictionary_outcome_contract(make_dict("industrial"), "industrial")
        _dictionary_outcome_contract(make_dict("residential"), "residential")

    def test_wrong_outcome_dictionary_cannot_pass(self) -> None:
        with self.assertRaisesRegex(SourceStructureError, "coding"):
            _dictionary_outcome_contract(make_dict("industrial", valid=False), "industrial")

    def test_summary_rejects_malformed_direct_research_inputs(self) -> None:
        # Do not rely on an upstream source parser when this aggregator is
        # imported directly; otherwise invalid binary values could make a
        # published sample fraction exceed one or throw a math domain error.
        invalid = [
            ([(Decimal("NaN"), 1)], "outside-depth"),
            ([(Decimal("-0.1"), 0)], "outside-depth"),
            ([(Decimal("10.1"), 0)], "outside-depth"),
            ([("0.3", 1)], "outside-depth"),
            ([(Decimal("0.3"), True)], "binary"),
            ([(Decimal("0.3"), 2)], "binary"),
            ([(Decimal("0.3"), -1)], "binary"),
            ([(Decimal("0.3"), 1, 0)], "structure"),
            ([["0.3", 1]], "structure"),
        ]
        for sample, expected in invalid:
            with self.subTest(sample=sample), self.assertRaisesRegex(
                    SourceStructureError, expected):
                _summarize(sample, sector="residential")
        with self.assertRaisesRegex(SourceStructureError, "sector"):
            _summarize([(Decimal("0.5"), 1)], sector="unverified")
        valid = [(Decimal("0.2"), 1)] * 10 + [(Decimal("0.2"), 0)] * 10
        self.assertEqual(_summarize(valid, sector="industrial")[
                         "published_depth_bins"][0]["observed_sample_fraction"], 0.5)

    def test_bin_values_not_monotonicity_forced(self) -> None:
        pairs = ([(Decimal("0.3"), 1)] * 15 + [(Decimal("0.3"), 0)] * 5
               + [(Decimal("0.8"), 1)] * 5 + [(Decimal("0.8"), 0)] * 15)
        a, b = _summarize(pairs, sector="industrial")["published_depth_bins"][:2]
        self.assertGreater(a["observed_sample_fraction"], b["observed_sample_fraction"])


if __name__ == "__main__":
    unittest.main()
