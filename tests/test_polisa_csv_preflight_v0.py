# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic fixtures; neither Polisa raw rows nor provider traffic."""
from __future__ import annotations

import csv
from io import StringIO
import unittest

from scripts.polisa_csv_preflight_v0 import COLUMNS, VERSION, Blocked, inspect, valid_lei


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
                         line_property_eur_m="0", lei="TEST0000000000000075")],
                         markets={"Poland", "Estonia"}, count=2)
        self.assertEqual(result["market_count"], 2)
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["missing_property_premium_cells_not_zeros"], 1)
        self.assertEqual(result["lei_present_rows"], 1)
        self.assertEqual(result["lei_missing_rows"], 1)
        self.assertEqual(result["distinct_upstream_source_links"], 1)
        self.assertEqual(result["rows_requiring_original_source_rights_review"], 2)
        self.assertEqual(result["priority_rights_review_rows_by_market"], {"Estonia": 1})
        self.assertTrue(result["priority_rights_market_flags_are_not_row_licences"])
        self.assertFalse(result["gleif_original_identity_crosswalk_completed"])
        self.assertFalse(result["provider_original_bytes_authenticated"])
        self.assertFalse(result["commercial_reuse_approved"])
        self.assertFalse(result["cat_model_input_approved"])

    def test_country_flags_prioritize_review_not_commercial_approval(self):
        result = self.check([
            sample("Hungary", "A"), sample("Slovenia", "B"),
            sample("Poland", "C"),
        ], markets={"Hungary", "Slovenia", "Poland"}, count=3)
        self.assertEqual(
            result["priority_rights_review_rows_by_market"],
            {"Hungary": 1, "Slovenia": 1},
        )
        self.assertEqual(result["rows_requiring_original_source_rights_review"], 3)
        self.assertFalse(result["row_level_upstream_rights_reviewed"])
        self.assertFalse(result["commercial_reuse_approved"])
        self.assertFalse(result["cat_model_input_approved"])

    def test_upstream_link_count_is_aggregate_only(self):
        result = self.check([
            sample("Poland", "A"),
            sample("Poland", "B", source="https://example.org/second-report"),
        ], count=2)
        self.assertEqual(result["distinct_upstream_source_links"], 2)
        self.assertNotIn("https://", str(result))
        self.assertNotIn("Imaginary Insurer", str(result))

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
        for url in ("", "http://example.org/report", "https://" + "local" + "host/report"):
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

    def test_lei_checksum_not_just_twenty_character_shape(self):
        # Purely synthetic, valid arithmetic; does NOT assert registered legal identity.
        valid = "TEST0000000000000075"
        self.assertTrue(valid_lei(valid))
        self.assertFalse(valid_lei("TEST0000000000000076"))
        self.assertFalse(valid_lei("TEST000000000000007A"))
        self.assertFalse(valid_lei("BAD"))
        for candidate in ("BAD", "TEST0000000000000076", "TEST000000000000007A"):
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(Blocked, "LEI"):
                    self.check([sample(lei=candidate)])

    def test_non_public_literal_ip_source_blocked(self):
        # Construct the negative fixture without embedding a real-looking endpoint.
        ip = ".".join(("127", "0", "0", "1"))
        for address in (ip, "::1"):
            with self.subTest(address=address):
                url = "https://" + ("[" + address + "]" if ":" in address else address) + "/report"
                with self.assertRaisesRegex(Blocked, "source"):
                    self.check([sample(source=url)])

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
