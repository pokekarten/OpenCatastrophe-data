# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic-only structural tests for pinned Natural Earth GeoJSON preflight."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest

from scripts.naturalearth_admin0_geojson_preflight import (
    GeojsonBlocked, ORIGINAL_SHA256, inspect_original_geojson,
)

RING = [[0.0, 0.0], [2.0, 0.0], [2.0, 3.0], [0.0, 0.0]]


def synthetic_collection() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"ADM0_A3": "AAA", "ISO_A2": "AA"},
             "geometry": {"type": "Polygon", "coordinates": [copy.deepcopy(RING)]}},
            {"type": "Feature", "properties": {"ADM0_A3": "BBB", "ISO_A2": "-99"},
             "geometry": {"type": "MultiPolygon", "coordinates": [[copy.deepcopy(RING)]]}},
        ],
    }


def encode(obj: object) -> bytes:
    return json.dumps(obj, separators=(",", ":"), allow_nan=True).encode("utf-8")


class NaturalEarthGeojsonPreflightTests(unittest.TestCase):
    def test_synthetic_valid_and_original_byte_sha(self) -> None:
        raw = encode(synthetic_collection())
        got = inspect_original_geojson(raw, require_pinned_identity=False)
        self.assertEqual(got["original_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(got["feature_count"], 2)
        self.assertEqual(got["unique_adm0_a3"], 2)
        self.assertEqual(got["coordinate_pair_count"], 8)
        self.assertEqual(got["missing_iso2_sentinel_count"], 1)
        self.assertEqual(got["nonstandard_iso_a2_count"], 0)
        self.assertEqual(got["geometry_type_counts"], {"Polygon": 1, "MultiPolygon": 1})
        self.assertFalse(got["model_input_admitted"])
        self.assertFalse(got["original_bytes_persisted"])

    def test_synthetic_cannot_claim_pinned_provider_identity(self) -> None:
        self.assertEqual(len(ORIGINAL_SHA256), 64)
        with self.assertRaisesRegex(GeojsonBlocked, "byte identity"):
            inspect_original_geojson(encode(synthetic_collection()))

    def test_duplicate_admin0_identifier_fails_closed(self) -> None:
        obj = synthetic_collection()
        obj["features"][1]["properties"]["ADM0_A3"] = "AAA"
        with self.assertRaisesRegex(GeojsonBlocked, "duplicate ADM0"):
            inspect_original_geojson(encode(obj), require_pinned_identity=False)

    def test_missing_and_invalid_country_codes_are_not_imputed(self) -> None:
        for value in (None, "LONG", "Aa", "-99"):
            with self.subTest(code=value):
                obj = synthetic_collection()
                obj["features"][0]["properties"]["ADM0_A3"] = value
                with self.assertRaises(GeojsonBlocked):
                    inspect_original_geojson(encode(obj), require_pinned_identity=False)
        obj = synthetic_collection()
        obj["features"][0]["properties"]["ISO_A2"] = 1
        with self.assertRaises(GeojsonBlocked):
            inspect_original_geojson(encode(obj), require_pinned_identity=False)

    def test_publisher_cn_tw_is_flagged_not_silently_normalized(self) -> None:
        obj = synthetic_collection()
        obj["features"][1]["properties"]["ISO_A2"] = "CN-TW"
        got = inspect_original_geojson(encode(obj), require_pinned_identity=False)
        self.assertEqual(got["nonstandard_iso_a2_count"], 1)
        self.assertEqual(got["missing_iso2_sentinel_count"], 0)
        obj["features"][1]["properties"]["ISO_A2"] = "TW-X"
        with self.assertRaises(GeojsonBlocked):
            inspect_original_geojson(encode(obj), require_pinned_identity=False)

    def test_unclosed_ring_and_invalid_coordinates_are_rejected(self) -> None:
        for point in ([0.0, 91.0], [181.0, 0.0], [float("nan"), 0.0], [True, 0.0]):
            with self.subTest(point=point):
                obj = synthetic_collection()
                obj["features"][0]["geometry"]["coordinates"][0][1] = point
                with self.assertRaises(GeojsonBlocked):
                    inspect_original_geojson(encode(obj), require_pinned_identity=False)
        obj = synthetic_collection()
        obj["features"][0]["geometry"]["coordinates"][0].pop()
        with self.assertRaises(GeojsonBlocked):
            inspect_original_geojson(encode(obj), require_pinned_identity=False)

    def test_duplicate_json_keys_and_nan_are_rejected(self) -> None:
        for raw in (
            b'{"type":"FeatureCollection","type":"FeatureCollection","features":[]}',
            b'{"type":"FeatureCollection","features":[NaN]}',
        ):
            with self.subTest(raw=raw), self.assertRaises(GeojsonBlocked):
                inspect_original_geojson(raw, require_pinned_identity=False)

    def test_bad_feature_type_and_nonpolygon_fail_closed(self) -> None:
        obj = synthetic_collection()
        obj["features"][0]["geometry"] = {"type": "Point", "coordinates": [1, 2]}
        with self.assertRaises(GeojsonBlocked):
            inspect_original_geojson(encode(obj), require_pinned_identity=False)
        obj = synthetic_collection()
        obj["features"][0]["type"] = "NotAFeature"
        with self.assertRaises(GeojsonBlocked):
            inspect_original_geojson(encode(obj), require_pinned_identity=False)

    def test_max_byte_budget_and_input_type(self) -> None:
        for raw in (None, b"", b" " * (1024 * 1024 + 1)):
            with self.subTest(length=len(raw) if isinstance(raw, bytes) else None), self.assertRaises(GeojsonBlocked):
                inspect_original_geojson(raw, require_pinned_identity=False)


if __name__ == "__main__":
    unittest.main()
