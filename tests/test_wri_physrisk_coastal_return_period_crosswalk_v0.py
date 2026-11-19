# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only source/derivative period identity and missing-source tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.wri_physrisk_coastal_return_period_crosswalk_v0 import (
    SourceMismatch, REQUIRED_WRI_RP, REQUIRED_PHYSRISK_RP, inspect_crosswalk,
)

ROOT = Path(__file__).resolve().parents[1]


def fname(rp):
    parts = (rp + ".0").split(".")[:2]
    return "inuncoast_historical_nosub_hist_rp" + parts[0].zfill(4) + "_" + parts[1] + ".tif"


def provider_html(rps=None):
    rps = REQUIRED_WRI_RP if rps is None else rps
    return (
        "<html><head><title>Aqueduct Floods Hazard Maps Version 2</title></head>"
        "<body>October 20, 2020<h3>Coastal - Historical/Baseline Scenario - No subsidence</h3>"
        + "".join('<a href="' + fname(rp) + '">' + fname(rp) + '</a>' for rp in rps)
        + "</body></html>"
    ).encode("utf-8")


def attrs(index=None):
    return json.dumps({
        "crs": "+init=epsg:4326", "index_name": "return period (years)",
        "index_values": list(REQUIRED_PHYSRISK_RP if index is None else index),
        "dimensions": ["index", "latitude", "longitude"],
    }).encode("utf-8")


def inspect(a=None, b=None):
    a = provider_html() if a is None else a
    b = attrs() if b is None else b
    return inspect_crosswalk(a, b, hashlib.sha256(a).hexdigest(),
                             hashlib.sha256(b).hexdigest())


class WRIPhysriskCrosswalkTests(unittest.TestCase):
    def test_exact_10_provider_vs_9_derived_without_loss_admission(self):
        result = inspect()
        self.assertEqual(result["wri_only_return_period_years"], ["1.5"])
        self.assertEqual(result["wri_return_period_years"], list(REQUIRED_WRI_RP))
        self.assertEqual(result["physrisk_return_period_years"], list(REQUIRED_PHYSRISK_RP))
        self.assertEqual(len(result["matching_provider_file_urls"]), 9)
        self.assertTrue(result["matching_provider_file_urls"][0].endswith("rp0002_0.tif"))
        self.assertTrue(result["matching_provider_file_urls"][-1].endswith("rp1000_0.tif"))
        self.assertFalse(result["wri_geotiffs_downloaded"])
        self.assertFalse(result["original_geotiff_pixel_comparison_completed"])
        self.assertFalse(result["return_period_maps_are_event_occurrences"])
        self.assertFalse(result["model_input_admitted"])

    def test_source_missing_period_is_blocked(self):
        without_1p5 = [x for x in REQUIRED_WRI_RP if x != "1.5"]
        with self.assertRaisesRegex(SourceMismatch, "incomplete"):
            inspect(provider_html(without_1p5))
        without_100 = [x for x in REQUIRED_WRI_RP if x != "100"]
        with self.assertRaises(SourceMismatch):
            inspect(provider_html(without_100))

    def test_duplicate_source_hrefs_are_not_silently_deduplicated(self):
        with self.assertRaisesRegex(SourceMismatch, "duplicate"):
            inspect(provider_html(list(REQUIRED_WRI_RP) + ["100"]))
        broken = provider_html().replace(b'rp0100_0.tif', b'rp0100_0.tif?token=secret')
        with self.assertRaises(SourceMismatch):
            inspect(broken)

    def test_protected_or_wrong_scenario_cannot_satisfy_source_contract(self):
        bad = provider_html().replace(b'inuncoast_historical_nosub_hist_', b'inuncoast_historical_wtsub_hist_')
        with self.assertRaises(SourceMismatch):
            inspect(bad)
        bad_title = provider_html().replace(b'Version 2', b'Version 1')
        with self.assertRaisesRegex(SourceMismatch, "product/release"):
            inspect(bad_title)

    def test_derived_period_order_additions_and_unit_types_blocked(self):
        for wrong in (list(REQUIRED_PHYSRISK_RP[:-1]),
                      [5, 2] + list(REQUIRED_PHYSRISK_RP[2:]),
                      [1.5] + list(REQUIRED_PHYSRISK_RP),
                      [True] + list(REQUIRED_PHYSRISK_RP[1:]),
                      [float(x) for x in REQUIRED_PHYSRISK_RP]):
            with self.subTest(index=wrong):
                with self.assertRaises(SourceMismatch):
                    inspect(b=attrs(wrong))

    def test_exact_source_hash_duplicate_json_size_and_nonfinite_block(self):
        a, b = provider_html(), attrs()
        with self.assertRaisesRegex(SourceMismatch, "SHA-256 mismatch"):
            inspect_crosswalk(a, b, "0" * 64, hashlib.sha256(b).hexdigest())
        malformed = b'{"index_name":"return period (years)","index_values":[],"index_values":[]}'
        with self.assertRaisesRegex(SourceMismatch, "duplicate"):
            inspect(b=malformed)
        for bad in (b'\xff', b'NaN', b'x' * 4097):
            with self.subTest(bad=bad[:10]):
                with self.assertRaises(SourceMismatch):
                    inspect(b=bad)
        with self.assertRaises(SourceMismatch):
            inspect(a=b"x" * 100001)

    def test_cli_synthetic_receipt_and_source_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            d = Path(temp)
            a, b, out = d / "index.html", d / "zattrs", d / "receipt.json"
            a.write_bytes(provider_html())
            b.write_bytes(attrs())
            cmd = [sys.executable,
                   str(ROOT / "research_runners/wri_physrisk_coastal_return_period_crosswalk_v0.py"),
                   str(a), str(b),
                   "--expected-wri-sha256", hashlib.sha256(a.read_bytes()).hexdigest(),
                   "--expected-zattrs-sha256", hashlib.sha256(b.read_bytes()).hexdigest(),
                   "--out", str(out)]
            valid = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertEqual(json.loads(out.read_text())["wri_only_return_period_years"], ["1.5"])
            invalid = subprocess.run(cmd[:-1] + [str(a)], capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertEqual(a.read_bytes(), provider_html())


if __name__ == "__main__":
    unittest.main()
