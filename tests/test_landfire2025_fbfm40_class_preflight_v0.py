# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Independent synthetic science regression tests for FBFM40 classes."""
from __future__ import annotations

import json
import unittest

from scripts.landfire2025_fbfm40_class_preflight_v0 import (
    ALLOWED, BURNABLE, MAX_JSON_BYTES, MAX_SAMPLES, NONBURNABLE,
    LandfireClassError, screen_lf2025_fbfm40_sample, screen_sample_json,
)


def payload(vals, dataset="LF2025_FBFM40_CONUS"):
    return json.dumps({"dataset": dataset, "values": vals}, separators=(",", ":")).encode()


class FBFM40ClassPreflightTests(unittest.TestCase):
    def test_official_codes_40_fuel_5_nonburnable_and_distinct_nodata(self):
        self.assertEqual(len(BURNABLE), 40)
        self.assertEqual(len(NONBURNABLE), 5)
        self.assertEqual(len(ALLOWED), 46)
        vals = [-9999, -9999, 91, 92, 93, 98, 99, 101, 109, 121, 124, 141,
                149, 161, 165, 181, 189, 201, 204]
        out = screen_sample_json(payload(vals))
        self.assertEqual(out["nodata_pixels"], 2)
        self.assertEqual(out["nonburnable_class_pixels"], 5)
        self.assertEqual(out["burnable_fuel_model_pixels"], 12)
        self.assertEqual(out["valid_class_pixels"], 17)
        self.assertEqual(out["total_sampled_pixel_values"], 19)
        self.assertEqual(out["nonburnable_by_class"]["91"], 1)
        self.assertEqual(out["nonburnable_by_class"]["98"], 1)
        self.assertTrue(out["fuel_model_is_nominal_categorical_not_continuous"])
        for key in ("raster_crs_resolution_and_georeferencing_verified",
                    "original_archive_md5_and_sha256_verified",
                    "sample_original_provider_provenance_verified",
                    "sampling_representativeness_verified",
                    "ignition_probability_or_event_frequency_derived",
                    "commercial_data_rights_verified", "model_source_admitted"):
            self.assertFalse(out[key], key)

    def test_every_supported_category_is_accounted_for(self):
        out = screen_lf2025_fbfm40_sample("LF2025_FBFM40_CONUS", sorted(ALLOWED))
        self.assertEqual(out["burnable_fuel_model_pixels"], 40)
        self.assertEqual(out["nonburnable_class_pixels"], 5)
        self.assertEqual(out["nodata_pixels"], 1)
        self.assertEqual(sum(out["burnable_by_family"].values()), 40)
        self.assertEqual(sum(out["nonburnable_by_class"].values()), 5)

    def test_rejects_invalid_codes_and_ambiguous_scientific_input(self):
        cases = [[0], [1], [90], [94], [95], [96], [97], [100], [110], [120],
                 [125], [140], [150], [160], [166], [180], [190], [200],
                 [205], [-9998], [9999], [True], [False], [101.0], [101.5],
                 ["101"], [None], [101, False], [-9999, -9999], []]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(LandfireClassError):
                screen_lf2025_fbfm40_sample("LF2025_FBFM40_CONUS", case)
        for dataset in ("LF2024_FBFM40_CONUS", "LF2025_FBFM40_AK",
                        "LF2025_SummerFBFM40_CONUS", "LF2025_FBFM13_CONUS", None):
            with self.subTest(dataset=dataset), self.assertRaises(LandfireClassError):
                screen_lf2025_fbfm40_sample(dataset, [101])
        for sample in (None, (101,), {"101": 1}, list(range(MAX_SAMPLES + 1))):
            with self.assertRaises(LandfireClassError):
                screen_lf2025_fbfm40_sample("LF2025_FBFM40_CONUS", sample)

    def test_rejects_broken_json_duplicate_keys_and_overlimit(self):
        for raw in (b"", b"not-json", b'{"dataset":"X","dataset":"Y","values":[101]}',
                    b'{"dataset":"LF2025_FBFM40_CONUS","values":[NaN]}',
                    b'\x80', b"x" * (MAX_JSON_BYTES + 1),
                    b'{"dataset":"LF2025_FBFM40_CONUS","values":[101],"url":"https://example.invalid"}',
                    b'{"dataset":"LF2025_FBFM40_CONUS"}', b'[]'):
            with self.subTest(raw=raw[:40]), self.assertRaises(LandfireClassError):
                screen_sample_json(raw)


if __name__ == "__main__":
    unittest.main()
