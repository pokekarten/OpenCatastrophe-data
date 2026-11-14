# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only tests: never use real owners, addresses, parcels or sales."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_hmlr_inspire_sale_linkage_v0 import (
    FAMILY, CadastralLinkageError, audit, load, main,
)


def fixture():
    return {
        "source_family": FAMILY,
        "snapshot_date": "2026-09-30",
        "transactions": [
            {"transaction_uid": "sale-a", "sale_date": "2026-08-12", "price_gbp": 400000},
            {"transaction_uid": "sale-b", "sale_date": "2026-08-20", "price_gbp": 300000},
            {"transaction_uid": "sale-c", "sale_date": "2026-09-01", "price_gbp": 200000},
        ],
        "polygons": [{"inspire_id": "poly-1"}, {"inspire_id": "poly-2"}],
        "lookup": [
            {"transaction_uid": "sale-a", "inspire_id": "poly-1"},
            {"transaction_uid": "sale-a", "inspire_id": "poly-2"},
            {"transaction_uid": "sale-b", "inspire_id": "poly-2"},
            {"transaction_uid": "sale-b", "inspire_id": "poly-2"},
            {"transaction_uid": "sale-c", "inspire_id": "nonexistent-polygon"},
            {"transaction_uid": "unknown-sale", "inspire_id": "poly-1"},
        ],
    }


class HmlrFreeholdLinkageTests(unittest.TestCase):
    def test_joins_do_not_duplicate_sold_value_across_polygons(self):
        result = audit(fixture())
        self.assertEqual(result["distinct_transaction_count"], 3)
        self.assertEqual(result["matched_transaction_count"], 2)
        self.assertEqual(result["unmatched_transaction_count"], 1)
        self.assertEqual(result["validated_lookup_link_count"], 3)
        self.assertEqual(result["multi_polygon_transaction_count"], 1)
        self.assertEqual(result["duplicate_lookup_rows_suppressed"], 1)
        self.assertEqual(result["lookup_rows_without_sale"], 1)
        self.assertEqual(result["lookup_rows_without_polygon"], 1)
        self.assertEqual(result["matched_sale_price_once_gbp"], 700000)
        self.assertEqual(result["incorrect_sale_price_if_allocated_to_all_polygons_gbp"], 1100000)
        self.assertEqual(result["potential_overcount_from_naive_polygon_join_gbp"], 400000)
        for key in ("source_admitted", "may_feed_cat_model", "value_is_insured_tiv",
                    "value_is_rebuilding_cost", "ready_for_ownership_or_policy_inference"):
            self.assertFalse(result[key])
        self.assertNotIn("sale-a", json.dumps(result))

    def test_no_link_is_not_a_building_or_insured_asset(self):
        inp = fixture()
        inp["lookup"] = []
        result = audit(inp)
        self.assertEqual(result["matched_transaction_count"], 0)
        self.assertEqual(result["matched_sale_price_once_gbp"], 0)
        self.assertFalse(result["may_feed_cat_model"])

    def test_reject_ownership_address_and_restricted_tax_register_fields(self):
        for field, value in (("owner_name", "Jane Test"),
                             ("Grundbuchblattnummer", "secret"),
                             ("property_address", "fake"),
                             ("title_number", "abc")):
            with self.subTest(field=field):
                inp = fixture()
                inp["polygons"][0][field] = value
                with self.assertRaises(CadastralLinkageError):
                    audit(inp)

    def test_reject_missing_or_duplicate_sale_identity(self):
        inp = fixture()
        inp["transactions"].append(inp["transactions"][0].copy())
        with self.assertRaisesRegex(CadastralLinkageError, "duplicate transaction"):
            audit(inp)

    def test_reject_future_sales_and_noninteger_or_nonfinite_values(self):
        for sale_date, price in (("2026-10-01", 1000), ("2026-08-01", True),
                                 ("2026-08-01", -5), ("2026-08-01", float("nan"))):
            with self.subTest(date=sale_date, price=price):
                inp = fixture()
                inp["transactions"][0].update(sale_date=sale_date, price_gbp=price)
                with self.assertRaises(CadastralLinkageError):
                    audit(inp)

    def test_reject_wrong_source_and_oversize(self):
        inp = fixture()
        inp["source_family"] = "de.nrw.grundbuch"
        with self.assertRaises(CadastralLinkageError):
            audit(inp)
        inp = fixture()
        inp["lookup"] = inp["lookup"] * 1000
        with self.assertRaises(CadastralLinkageError):
            audit(inp)

    def test_fail_closed_exact_fields_and_bad_dates(self):
        inp = fixture()
        inp["lookup"][0]["address"] = "not allowed"
        with self.assertRaises(CadastralLinkageError):
            audit(inp)
        inp = fixture()
        inp["snapshot_date"] = "2026-02-30"
        with self.assertRaises(CadastralLinkageError):
            audit(inp)

    def test_cli_synthetic_and_json_duplicate_key_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "toy.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            self.assertEqual(main(["--input", str(path)]), 0)
            path.write_text('{"snapshot_date":"2026-09-30","snapshot_date":"2026-10-01"}', encoding="utf-8")
            with self.assertRaises(CadastralLinkageError):
                load(path)
            self.assertEqual(main(["--input", str(path)]), 1)


if __name__ == "__main__":
    unittest.main()
