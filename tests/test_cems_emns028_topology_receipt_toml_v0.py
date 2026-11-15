# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Metadata-only original CEMS FileGDB research receipt: no feature input."""
import tomllib
import unittest
from pathlib import Path

PATH = (Path(__file__).resolve().parents[1] /
        "docs/research/cems-emns028-filegdb-topology-receipt-20261101.toml")


class CemsOriginalFileGdbTopologyReceiptTests(unittest.TestCase):
    def test_original_identity_and_layer_counts(self):
        d = tomllib.loads(PATH.read_text(encoding="utf-8"))
        self.assertEqual(d["activation_id"], "EMSN028")
        self.assertEqual(d["original_archive_size_bytes"], 155898548)
        self.assertEqual(d["full_original_archive_sha256"],
                         "7ef43d0637447abae705728723c06d2f05415a21667fdee1f10e8fc25b5bf3c2")
        self.assertEqual(d["total_layers"], 18)
        self.assertEqual(d["opened_layers"], 18)
        layers = {x["layer"]: x for x in d["selected_layers"]}
        self.assertEqual(layers["Buildings"]["source_features"], 647276)
        self.assertEqual(layers["Estimated_Max_Flood_Extent"]["source_features"], 1237)
        self.assertEqual(layers["Flooded_area"]["source_features"], 1)

    def test_invalid_original_polygon_not_reclassified_as_valid_or_observed(self):
        d = tomllib.loads(PATH.read_text(encoding="utf-8"))
        flooded = next(x for x in d["selected_layers"] if x["layer"] == "Flooded_area")
        estimated = next(x for x in d["selected_layers"]
                         if x["layer"] == "Estimated_Max_Flood_Extent")
        self.assertIs(flooded["source_geometry_valid"], False)
        self.assertIn("Self-intersection", flooded["source_geometry_topology_reason"])
        self.assertIs(flooded["full_spatial_overlay_authorized"], False)
        self.assertIs(flooded["exact_aoi04_flood_extent_verified"], False)
        self.assertIs(estimated["modelled_maximum_not_observed"], True)
        self.assertIs(estimated["full_layer_geometry_validity_tested"], False)
        for key in (
            "precise_aoi04_observed_polygon_proven",
            "original_flooded_area_geometry_valid",
            "overlay_approved",
            "historical_building_2016_vintage_verified",
            "insurer_tiv_and_claims_verified",
            "cat_model_input_approved",
        ):
            self.assertIs(d["scientific_and_rights_gates"][key], False)


if __name__ == "__main__":
    unittest.main()
