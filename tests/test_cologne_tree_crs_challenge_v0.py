# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Offline tests: synthetic multi-offset tree CRS hypothesis and negative gates."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

RUNNERS = Path(__file__).resolve().parents[1] / "research_runners"
sys.path.insert(0, str(RUNNERS))
MODULE = RUNNERS / "cologne_tree_crs_challenge_v0.py"
spec = importlib.util.spec_from_file_location("cologne_tree_crs_challenge_v0", MODULE)
assert spec and spec.loader
challenge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(challenge)

# Synthetic points deliberately span a wide area inside the official Köln
# bounding envelope when passed through the *fake* mock transform below.
POINTS = (
    (350000., 5620000.),
    (353000., 5635000.),
    (360000., 5640000.),
    (370000., 5660000.),
    (365000., 5630000.),
)


def transform(x, y):
    """Artificial deterministic transform; NOT production projection maths."""
    return 6.9 + (x - 350000) / 150000, 50.86 + (y - 5600000) / 300000


def samples():
    return [
        {
            "tree_id_sha256": ("%064x" % (n + 1)),
            "coords_internal": point,
            "source_crs_declaration": "not_declared",
            "response_sha256": ("%064x" % (n + 11)),
        }
        for n, point in enumerate(POINTS)
    ]


def synthetic_raw(*, x=350000., y=5648000., ident="synthetic-only"):
    doc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [x, y]},
                "properties": {"Baumnummer": ident, "Kronendurchmesser_-_m": "7"},
            }
        ],
    }
    return json.dumps(doc).encode("utf-8")


class CologneTreeCrsChallengeTests(unittest.TestCase):
    def test_fixed_urls_have_no_unbounded_query(self):
        self.assertEqual(challenge.OFFSETS, (0, 750, 2500, 5000, 10000))
        for i in challenge.OFFSETS:
            url = challenge.sample_url(i)
            self.assertTrue(url.startswith("https://geoportal.stadt-koeln.de/"))
            self.assertIn("COUNT=1", url)
            self.assertIn("SORTBY=Baumnummer", url)
            self.assertIn("STARTINDEX=" + str(i), url)
        with self.assertRaises(challenge.ChallengeError):
            challenge.sample_url(1000000)

    def test_synthetic_projected_points_plausible_but_never_admitted(self):
        result = challenge.assess_crs_hypothesis(samples(), transform)
        self.assertEqual(result["sample_count"], 5)
        self.assertTrue(result["all_transformed_points_inside_kgg_bbox"])
        self.assertFalse(result["source_snapshot_pinned"])
        self.assertFalse(result["scientific_validation_complete"])
        self.assertFalse(result["model_admitted"])
        self.assertFalse(result["external_source_bytes_persisted"])
        self.assertEqual(len(result["source_response_sha256"]), 5)
        self.assertEqual(len(result["stable_id_hashes_sha256"]), 64)
        self.assertGreater(result["transformed_span_degrees_rounded"]["latitude"], 0.05)

    def test_exact_five_samples_required(self):
        with self.assertRaises(challenge.ChallengeError):
            challenge.assess_crs_hypothesis(samples()[:3], transform)

    def test_duplicate_source_id_blocked(self):
        arr = samples()
        arr[4]["tree_id_sha256"] = arr[0]["tree_id_sha256"]
        with self.assertRaises(challenge.ChallengeError):
            challenge.assess_crs_hypothesis(arr, transform)

    def test_crs_change_not_silently_accepted(self):
        arr = samples()
        arr[0]["source_crs_declaration"] = "EPSG:4326"
        with self.assertRaises(challenge.ChallengeError):
            challenge.assess_crs_hypothesis(arr, transform)

    def test_wrong_utm_magnitudes_blocked(self):
        arr = samples()
        arr[2]["coords_internal"] = (6.98, 50.94)
        with self.assertRaises(challenge.ChallengeError):
            challenge.assess_crs_hypothesis(arr, transform)

    def test_wrong_transformed_city_envelope_blocked(self):
        with self.assertRaises(challenge.ChallengeError):
            challenge.assess_crs_hypothesis(samples(), lambda x, y: (9.0, 52.0))

    def test_non_finite_output_blocked(self):
        with self.assertRaises(challenge.ChallengeError):
            challenge.assess_crs_hypothesis(samples(), lambda x, y: (float("nan"), 50.9))

    def test_insufficient_spatial_dispersion_blocked(self):
        with self.assertRaises(challenge.ChallengeError):
            challenge.assess_crs_hypothesis(samples(), lambda x, y: (7.0, 50.95))

    def test_original_one_feature_receipt_hides_tree_id_and_raw_coordinates(self):
        receipt = challenge.parse_source_sample(synthetic_raw())
        self.assertEqual(receipt["source_crs_declaration"], "not_declared")
        self.assertEqual(len(receipt["response_sha256"]), 64)
        self.assertEqual(len(receipt["tree_id_sha256"]), 64)
        self.assertEqual(len(receipt["coords_internal"]), 2)
        self.assertNotIn("synthetic-only", str(receipt))

    def test_original_geojson_with_declared_wrong_crs_rejected(self):
        body = json.loads(synthetic_raw())
        body["crs"] = {"type": "name", "properties": {"name": "EPSG:4326"}}
        with self.assertRaises(challenge.ChallengeError):
            challenge.parse_source_sample(json.dumps(body).encode("utf-8"))

    def test_original_geojson_without_source_identifier_rejected(self):
        body = json.loads(synthetic_raw())
        del body["features"][0]["properties"]["Baumnummer"]
        with self.assertRaises(challenge.ChallengeError):
            challenge.parse_source_sample(json.dumps(body).encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
