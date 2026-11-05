# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only offline tests for NZ public property-building join cardinality."""

from __future__ import annotations

import contextlib
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.nz_linz_property_building_join_preflight_v0 import (
    NZJoinPreflightError,
    _read_bounded_csv,
    evaluate,
    main,
)


def _fixture() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    return (
        [{"unit_of_property_id": "SYNPROP_A"}, {"unit_of_property_id": "SYNPROP_B"}],
        [{"source": "NZ Unit of Property", "unit_of_property_id": "SYNPROP_A"},
         {"source": "NZ Property Titles", "unit_of_property_id": ""}],
        [{"unit_of_property_id": "SYNPROP_A", "building_id": "SYNROOF_1"},
         {"unit_of_property_id": "SYNPROP_A", "building_id": "SYNROOF_2"},
         {"unit_of_property_id": "SYNPROP_B", "building_id": "SYNROOF_3"}],
        [{"building_id": "SYNROOF_1"}, {"building_id": "SYNROOF_2"}],
    )


def _write(path: Path, rows: list[dict[str, str]], columns: tuple[str, ...]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


class NZJoinPreflightTests(unittest.TestCase):
    def test_one_to_many_never_duplicates_valuation_asset_count(self) -> None:
        output = evaluate(*_fixture())
        counts = output["counts"]
        self.assertEqual(counts["valuation_distinct_nonnull_units"], 2)
        self.assertEqual(counts["valuation_units_with_boundary_in_sample"], 1)
        self.assertEqual(counts["valuation_units_with_building_reference_in_sample"], 2)
        self.assertEqual(counts["valuation_units_with_multiple_linked_buildings"], 1)
        self.assertEqual(counts["valuation_units_with_linked_current_outline_in_sample"], 1)
        self.assertEqual(counts["distinct_matched_current_outline_ids_in_sample"], 2)
        self.assertFalse(output["cautions"]["cat_model_input_admitted"])
        self.assertFalse(output["cautions"]["source_release_or_vintage_alignment_verified"])

    def test_duplicates_and_missing_keys_are_visible_not_silent(self) -> None:
        vals, bounds, refs, outlines = _fixture()
        vals.append({"unit_of_property_id": "SYNPROP_A"})
        vals.append({"unit_of_property_id": ""})
        refs.append(dict(refs[0]))
        refs.append({"unit_of_property_id": "", "building_id": "SYNROOF_9"})
        outlines.append({"building_id": "SYNROOF_1"})
        counts = evaluate(vals, bounds, refs, outlines)["counts"]
        self.assertEqual(counts["valuation_duplicate_id_rows"], 1)
        self.assertEqual(counts["valuation_missing_id_rows"], 1)
        self.assertEqual(counts["reference_duplicate_pairs"], 1)
        self.assertEqual(counts["reference_invalid_key_rows"], 1)
        self.assertEqual(counts["current_outline_duplicate_building_ids"], 1)

    def test_rated_boundary_only_and_shared_building_blocks_one_to_one(self) -> None:
        # Even if a fallback parcel carries a stray rating-unit key, it is
        # not an official rated-property boundary.
        vals = [{"unit_of_property_id": "P1"}, {"unit_of_property_id": "P2"},
                {"unit_of_property_id": "P3"}]
        bounds = [
            {"source": "NZ Unit of Property", "unit_of_property_id": "P1"},
            {"source": "NZ Property Titles", "unit_of_property_id": "P2"},
            {"source": "NZ Unit of Property", "unit_of_property_id": "P3"},
        ]
        refs = [
            {"unit_of_property_id": "P1", "building_id": "B1"},
            {"unit_of_property_id": "P2", "building_id": "B2"},
            {"unit_of_property_id": "P3", "building_id": "B1"},
        ]
        outlines = [{"building_id": "B1"}, {"building_id": "B2"}]
        out = evaluate(vals, bounds, refs, outlines)
        c = out["counts"]
        self.assertEqual(c["valuation_units_with_boundary_in_sample"], 2)
        self.assertEqual(c["non_rated_fallback_rows_with_unit_id"], 1)
        self.assertEqual(c["current_outline_ids_referenced_by_multiple_properties"], 1)
        self.assertEqual(c["conservative_one_to_one_join_candidates_in_sample"], 0)
        self.assertTrue(out["cautions"]["one_to_one_candidates_do_not_prove_physical_or_insured_assets"])

        # Distinct building references and exactly one dated source *candidate*
        # per unit become structurally unambiguous, not model-admitted.
        refs[-1] = {"unit_of_property_id": "P3", "building_id": "B3"}
        outlines.append({"building_id": "B3"})
        c = evaluate(vals, bounds, refs, outlines)["counts"]
        self.assertEqual(c["conservative_one_to_one_join_candidates_in_sample"], 2)
        self.assertEqual(c["current_outline_ids_referenced_by_multiple_properties"], 0)

        # Duplicate rated-property boundary or duplicate outline must block
        # the corresponding otherwise-unique candidate.
        bounds.append({"source": "NZ Unit of Property", "unit_of_property_id": "P1"})
        c = evaluate(vals, bounds, refs, outlines)["counts"]
        self.assertEqual(c["rated_boundary_duplicate_unit_id_rows"], 1)
        self.assertEqual(c["conservative_one_to_one_join_candidates_in_sample"], 1)
        outlines.append({"building_id": "B3"})
        c = evaluate(vals, bounds, refs, outlines)["counts"]
        self.assertEqual(c["conservative_one_to_one_join_candidates_in_sample"], 0)
        self.assertEqual(c["current_outline_duplicate_building_ids"], 1)

    def test_csv_header_and_row_bound_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.csv"
            path.write_text("other\nvalue\n", encoding="utf-8")
            with self.assertRaises(NZJoinPreflightError):
                _read_bounded_csv(path, ("unit_of_property_id",), 3)
            path.write_text("unit_of_property_id\nSYN_A\nSYN_B\n", encoding="utf-8")
            with self.assertRaises(NZJoinPreflightError):
                _read_bounded_csv(path, ("unit_of_property_id",), 1)
            with self.assertRaises(NZJoinPreflightError):
                _read_bounded_csv(path, ("unit_of_property_id",), 100_001)

    def test_cli_reports_aggregate_only_no_source_identifiers(self) -> None:
        vals, bounds, refs, outlines = _fixture()
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            sources = (
                ("v.csv", vals, ("unit_of_property_id",)),
                ("b.csv", bounds, ("source", "unit_of_property_id")),
                ("r.csv", refs, ("unit_of_property_id", "building_id")),
                ("o.csv", outlines, ("building_id",)),
            )
            for name, rows, fields in sources:
                _write(d / name, rows, fields)
            command = [
                "--valuations", str(d / "v.csv"),
                "--boundaries", str(d / "b.csv"),
                "--property-building-refs", str(d / "r.csv"),
                "--outlines", str(d / "o.csv"),
            ]
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(command), 0)
            report = output.getvalue()
            self.assertNotIn("SYNPROP", report)
            self.assertNotIn("SYNROOF", report)
            self.assertNotIn(str(d), report)
            self.assertEqual(json.loads(report)["counts"]["valuation_rows"], 2)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(command + ["--max-rows", "1"]), 2)


if __name__ == "__main__":
    unittest.main()
