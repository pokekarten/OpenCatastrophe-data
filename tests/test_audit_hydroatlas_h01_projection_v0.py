# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only H01 negative and positive tests. No source data or network."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from scripts.audit_hydroatlas_h01_projection_v0 import (
    H01Blocked, MAX_BYTES, MAX_ROWS, inspect, main,
)


def row(ident=1000000001, mean=5., minimum=1., maximum=10.):
    return {"HYBAS_ID": ident, "dis_m3_pyr": mean,
            "dis_m3_pmn": minimum, "dis_m3_pmx": maximum}


def data(*rows):
    return b"\n".join(json.dumps(r, sort_keys=True).encode() for r in rows) + b"\n"


class H01ProjectedQualityTests(unittest.TestCase):
    def test_bounded_valid_native_columns_without_false_admission(self):
        r = inspect(data(row(), row(1000000002, 0., 0., 0.)),
                    layer="BasinATLAS_v10_lev02")
        self.assertEqual(r["records"], 2)
        self.assertEqual(r["complete_triplets"], 2)
        self.assertEqual(r["unresolved_null_triplets"], 0)
        self.assertEqual(r["all_zero_triplets"], 1)
        self.assertEqual(r["unit"], "m3/s")
        self.assertEqual(r["climate_reference"], "1971-2000")
        self.assertTrue(r["hydrological_context_preflight_pass"])
        self.assertTrue(r["min_max_from_twelve_long_term_monthly_means"])
        for key in ("original_archive_sha256_verified", "independent_gauge_validation",
                    "CAT_model_input_approved", "event_flood_hazard_or_return_period_approved"):
            self.assertFalse(r[key])
        self.assertEqual(len(r["projection_sha256"]), 64)
        self.assertNotIn("1000000001", json.dumps(r))

    def test_null_does_not_become_zero_or_model_approval(self):
        r = inspect(data(row(minimum=None), row(1000000002)),
                    layer="BasinATLAS_v10_lev01")
        self.assertEqual(r["unresolved_null_triplets"], 1)
        self.assertEqual(r["complete_triplets"], 1)
        self.assertFalse(r["hydrological_context_preflight_pass"])
        self.assertFalse(r["CAT_model_input_approved"])

    def test_only_exact_version_and_basin_levels(self):
        for layer in ("BasinATLAS_v11_lev02", "RiverATLAS_v10",
                      "BasinATLAS_v10_lev00", "BasinATLAS_v10_lev13",
                      "BasinATLAS_v10_lev2", "BasinATLAS_v10_lev02/../../",
                      "", None):
            with self.subTest(layer=layer), self.assertRaises(H01Blocked):
                inspect(data(row()), layer=layer)
        self.assertEqual(inspect(data(row()), layer="BasinATLAS_v10_lev12")["records"], 1)

    def test_missing_extra_and_renamed_columns_rejected(self):
        for modifications in (
            {"dis_m3_pmn": None, "drop": "dis_m3_pmn"},
            {"flood_rp100": 100.},
            {"dis_m3_syr": 5., "drop": "dis_m3_pyr"},
        ):
            item = row()
            if "drop" in modifications:
                item.pop(modifications["drop"])
            item.update({k: v for k, v in modifications.items() if k != "drop"})
            with self.subTest(columns=tuple(item)), self.assertRaises(H01Blocked):
                inspect(data(item), layer="BasinATLAS_v10_lev02")

    def test_duplicate_basin_and_invalid_identity_rejected(self):
        with self.assertRaises(H01Blocked):
            inspect(data(row(), row()), layer="BasinATLAS_v10_lev02")
        for value in (None, 0, -1, True, 1., "1000000001"):
            with self.subTest(value=value), self.assertRaises(H01Blocked):
                inspect(data(row(ident=value)), layer="BasinATLAS_v10_lev02")

    def test_no_unreviewed_negative_sentinels_and_malformed_numeric(self):
        for value in (-9999, -1, float("nan"), float("inf"),
                      -float("inf"), True, "5", [], {}):
            with self.subTest(value=str(value)), self.assertRaises(H01Blocked):
                inspect(data(row(mean=value)), layer="BasinATLAS_v10_lev02")
        for raw in (b'{"HYBAS_ID":1,"dis_m3_pyr":NaN}',
                    b'{"HYBAS_ID":1,"dis_m3_pyr":Infinity}'):
            with self.assertRaises(H01Blocked):
                inspect(raw, layer="BasinATLAS_v10_lev02")

    def test_reject_climatology_mean_outside_min_max(self):
        for mean, minimum, maximum in ((5., 6., 10.), (5., 1., 4.), (5., 10., 1.)):
            with self.subTest(mean=mean, minimum=minimum), self.assertRaises(H01Blocked):
                inspect(data(row(mean=mean, minimum=minimum, maximum=maximum)),
                        layer="BasinATLAS_v10_lev02")

    def test_invalid_json_and_duplicate_keys_rejected(self):
        for raw in (b'{"HYBAS_ID":1,"HYBAS_ID":2}\n', b'[]\n',
                    b'{}\n', b'not json\n', b'\xff\n', b'\n'):
            with self.subTest(raw=raw[:15]), self.assertRaises(H01Blocked):
                inspect(raw, layer="BasinATLAS_v10_lev02")

    def test_byte_and_row_limits_rejected(self):
        for raw in (b"", b"x" * (MAX_BYTES + 1),
                    data(*(row(i + 1) for i in range(MAX_ROWS + 1)))):
            with self.assertRaises(H01Blocked):
                inspect(raw, layer="BasinATLAS_v10_lev02")

    def test_cli_no_sensitive_value_or_path_in_output(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "fake-hidden-1000000001.jsonl"
            p.write_bytes(data(row()))
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = main(["--projected-jsonl", str(p),
                           "--layer", "BasinATLAS_v10_lev02"])
            self.assertEqual(rc, 0)
            self.assertFalse(json.loads(out.getvalue())["CAT_model_input_approved"])
            self.assertNotIn("1000000001", out.getvalue())
            p.write_bytes(b"broken provider projection")
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = main(["--projected-jsonl", str(p),
                           "--layer", "BasinATLAS_v10_lev02"])
            self.assertEqual(rc, 2)
            self.assertNotIn(str(p), err.getvalue())
            self.assertEqual(out.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
