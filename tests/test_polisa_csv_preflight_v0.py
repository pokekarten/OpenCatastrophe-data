# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic fixtures; neither Polisa raw rows nor provider traffic."""
from __future__ import annotations

import csv
from io import StringIO
import unittest

from scripts.polisa_csv_preflight_v0 import COLUMNS, VERSION, Blocked, inspect


def sample(market="Poland", ident="TEST_A", **overrides):
    row = {name: "" for name in COLUMNS}
    row.update({
        "market": market, "year": "2025", "insurer": "Imaginary Insurer",
        "insurer_id": ident, "premium_eur_m": "12.5",
        "source": "https://example.org/imaginary-official-report",
        "data_version": VERSION,
    })
    row.update(overrides)
    return row


def payload(rows, columns=COLUMNS):
    out = StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row.get(c, "") for c in columns])
    return ("\ufeff" + out.getvalue()).encode("utf-8")


class PolisaPreflightTests(unittest.TestCase):
    def check(self, rows, *, markets=None, count=1):
        return inspect(payload(rows), expected_rows=count,
                       expected_markets=frozenset(markets or {"Poland"}))

    def test_valid_synthetic_slice_remains_unapproved(self):
        result = self.check([sample(), sample("Estonia", "TEST_B",
                         line_property_eur_m="0")],
                         markets={"Poland", "Estonia"}, count=2)
        self.assertEqual(result["market_count"], 2)
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["missing_property_premium_cells_not_zeros"], 1)
        self.assertFalse(result["provider_original_bytes_authenticated"])
        self.assertFalse(result["commercial_reuse_approved"])
        self.assertFalse(result["cat_model_input_approved"])

    def test_duplicate_market_year_insurer_key_blocked(self):
        with self.assertRaisesRegex(Blocked, "duplicate"):
            self.check([sample(), sample()], count=2)

    def test_old_version_is_rejected_even_when_other_rows_new(self):
        with self.assertRaisesRegex(Blocked, "version"):
            self.check([sample(), sample("Poland", "TEST_B",
                       data_version="2026-11-09.d5ad62")], count=2)

    def test_older_ratio_schema_is_rejected(self):
        old = tuple("combined_ratio_gross_pct"
                    if c == "claims_ratio_gross_pct" else c for c in COLUMNS)
        with self.assertRaisesRegex(Blocked, "schema/order"):
            inspect(payload([sample()], columns=old),
                    expected_rows=1, expected_markets=frozenset({"Poland"}))

    def test_missing_or_unsafe_source_is_rejected(self):
        for url in ("", "http://example.org/report", "https://localhost/report"):
            with self.subTest(url=url), self.assertRaisesRegex(Blocked, "source"):
                self.check([sample(source=url)])

    def test_negative_nonfinite_and_garbled_premium_rejected(self):
        for value in ("NaN", "Infinity", "-0.1", "x"):
            with self.subTest(value=value), self.assertRaises(Blocked):
                self.check([sample(premium_eur_m=value)])

    def test_missing_market_and_unknown_market_fail_closed(self):
        with self.assertRaisesRegex(Blocked, "coverage"):
            self.check([sample()], markets={"Poland", "Estonia"})
        with self.assertRaisesRegex(Blocked, "market/year"):
            self.check([sample(market="Atlantis")])

    def test_invalid_lei_fails_closed(self):
        with self.assertRaisesRegex(Blocked, "LEI"):
            self.check([sample(lei="BAD")])

    def test_csv_header_and_row_length_must_match(self):
        with self.assertRaisesRegex(Blocked, "schema/order"):
            inspect(payload([sample()], columns=COLUMNS + ("extra",)),
                    expected_rows=1, expected_markets=frozenset({"Poland"}))
        raw = payload([sample()]).replace(
            b"\nPoland,", b"\nPoland,", 1
        ) + b"EXTRA\n"
        with self.assertRaisesRegex(Blocked, "column count"):
            inspect(raw, expected_rows=2,
                    expected_markets=frozenset({"Poland"}))


if __name__ == "__main__":
    unittest.main()
