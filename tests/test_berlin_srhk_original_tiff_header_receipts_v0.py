# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline immutable original TIFF-header receipts, not a source pixel validation.

The provider-bound evidence is in named original GitHub Actions logs. This
test validates only the locally recorded *metadata* and explicit nonadmission
constraints. It deliberately performs no HTTP or ZIP/TIFF data retrieval.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs/research/berlin-srhk-original-tiff-header-receipts-20261101.json"
PREFIX_HASHES = {
    "extreme": "9b86b039e4c0915b76f4ea64bc13c201f43483a2585dcdd8f6650d6e1a70579f",
    "extraordinary": "ba22dae2169f3ffab268f9411099e98c5fc3a15cfd8094d6b486b6e9a0c32149",
}
ORIGINAL_URLS = {
    "extreme": "https://gdi.berlin.de/data/ua_srhk/atom/wasserstand_extrem2022.zip",
    "extraordinary": "https://gdi.berlin.de/data/ua_srhk/atom/wasserstand_aussergewoehnliches_ereignis2022.zip",
}
BBOX = [360768.970463454, 5789616.562878486, 424650.970463454, 5844372.562878486]
PILOT_BBOX = [391700, 5819950, 391900, 5820150]
PINNED_CODE_SHA = "4f162912e975ca16818dc7389ea39bf010b858c742ccb482e0624946897dc5cb"


def _unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate key in source receipt: " + key)
        out[key] = value
    return out


def _nonfinite(value):
    raise ValueError("nonfinite JSON in source receipt: " + value)


def _load(path=PATH):
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=_nonfinite,
    )


class BerlinVerifiedHeaderReceiptsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = _load()

    def test_evidence_run_provenance_is_two_distinct_successful_main_runs(self):
        rows = self.data["independent_github_actions_evidence"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            {r["evidence_kind"]: (r["run_id"], r["main_commit"]) for r in rows},
            {
                "original_affine_header": (
                    41334867841, "e6b0831bf7f64b72e109fa111bf8af9664d88fd6"
                ),
                "original_band_nodata_header": (
                    41335440273, "383ab39fb6f7612660476b7b5992b9df76c012c3"
                ),
            },
        )
        for row in rows:
            self.assertIs(row["completed_successfully"], True)
            self.assertEqual(
                row["run_url"],
                "https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/"
                + str(row["run_id"]),
            )

    def test_two_original_source_identities_and_partial_hashes_frozen(self):
        observations = self.data["observations"]
        self.assertEqual(len(observations), 2)
        self.assertEqual({x["scenario"] for x in observations}, set(PREFIX_HASHES))
        for row in observations:
            self.assertEqual(row["source_url"], ORIGINAL_URLS[row["scenario"]])
            self.assertEqual(
                row["original_prefix_65536_sha256"],
                PREFIX_HASHES[row["scenario"]],
            )
            self.assertRegex(row["original_prefix_65536_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(row["nodata_reader_code_sha256"], PINNED_CODE_SHA)
            for key in ("affine_read_utc", "nodata_read_utc"):
                t = datetime.fromisoformat(row[key])
                self.assertIsNotNone(t.tzinfo)
                self.assertEqual(t.utcoffset().total_seconds(), 0)

    def test_exact_projected_pixel_grid_arithmetic_and_header_bbox_coverage(self):
        self.assertEqual(self.data["crs"], "EPSG:25833")
        self.assertEqual(self.data["pilot_bbox_epsg25833_m"], PILOT_BBOX)
        for row in self.data["observations"]:
            self.assertEqual(row["header_declared_projected_epsg"], 25833)
            self.assertEqual(row["header_dimensions_pixels"], [63882, 54756])
            self.assertEqual(row["header_pixel_scale_metres"], [1, 1])
            ext = row["header_projected_bounds_epsg25833_m"]
            for measured, known in zip(ext, BBOX):
                self.assertTrue(math.isclose(measured, known, abs_tol=1e-7))
            self.assertTrue(
                math.isclose(ext[2]-ext[0], row["header_dimensions_pixels"][0],
                             abs_tol=1e-7)
            )
            self.assertTrue(
                math.isclose(ext[3]-ext[1], row["header_dimensions_pixels"][1],
                             abs_tol=1e-7)
            )
            a, b, c, d = PILOT_BBOX
            self.assertTrue(ext[0] <= a and ext[1] <= b)
            self.assertTrue(ext[2] >= c and ext[3] >= d)
            self.assertIs(row["pilot_bbox_intersects_header_extent"], True)
            self.assertIs(row["pilot_bbox_fully_within_header_extent"], True)

    def test_nodata_is_not_zero_and_units_remain_scientifically_unknown(self):
        for row in self.data["observations"]:
            self.assertEqual(
                row["declared_gdal_nodata"],
                {"tag_present": True, "type": "finite_number", "value": -9999},
            )
            self.assertNotEqual(row["declared_gdal_nodata"]["value"], 0)
            info = row["tiff_band_metadata"]
            self.assertEqual(
                [info["bits_per_sample"], info["sample_format_code"],
                 info["samples_per_pixel"], info["compression_code"]],
                [32, 3, 1, 5],
            )
            self.assertIs(info["gdal_metadata_tag_present"], False)
            for key in ("gdal_unit_declared", "gdal_scale_declared",
                        "gdal_offset_declared"):
                self.assertIsNone(info[key])
            for key in (
                "original_pixel_values_read", "nodata_mask_validated",
                "scientific_water_depth_units_validated",
                "actual_building_hazard_join_verified", "admitted_as_cat_model_input",
            ):
                self.assertIs(row[key], False)

    def test_receipt_is_not_a_full_archive_or_model_admission(self):
        self.assertTrue(self.data["research_only"])
        self.assertEqual(self.data["provenance_status"], "verified_original_header_only")
        access = self.data["original_source_access"]
        self.assertIs(access["source_url_pinned"], True)
        self.assertEqual(access["source_bytes_per_scenario_and_run"], 65536)
        self.assertEqual(access["source_range"], "bytes 0-65535")
        self.assertEqual(access["decompressed_tiff_prefix_max_bytes"], 1048576)
        for key in (
            "full_source_zip_sha256_verified", "full_tiff_crc_verified",
            "original_provider_bytes_saved", "pixel_blocks_read",
        ):
            self.assertIs(access[key], False)

    def test_invalid_json_duplicate_keys_and_nan_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            json.loads('{"source":1,"source":2}', object_pairs_hook=_unique_pairs)
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            json.loads('{"depth":NaN}', parse_constant=_nonfinite)


if __name__ == "__main__":
    unittest.main()
