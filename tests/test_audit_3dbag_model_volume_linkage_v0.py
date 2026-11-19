# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Invented BAG IDs and 3DBAG CityJSON objects, never real property details."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_3dbag_model_volume_linkage_v0 import (
    ModelledVolumeError, audit, main,
)

URL = (
    "https://service.pdok.nl/kadaster/bag/wfs/v2_0"
    "?service=WFS&version=2.0.0&request=GetFeature"
    "&typeNames=bag:verblijfsobject&count=50"
    "&outputFormat=application/json"
    "&propertyName=identificatie,oppervlakte,pandidentificatie,status,gebruiksdoel"
    "&bbox=136701.28,455804.71,136728.86,455849.32,EPSG:28992"
)


def bid(index):
    return f"{index:016d}"


def wfs():
    features = []
    for i in range(8):
        features.append({
            "type": "Feature",
            "properties": {
                "identificatie": f"UNIT-{i}",
                "oppervlakte": 70+i,
                "pandidentificatie": bid((i % 5) + 1),
                "status": "Verblijfsobject in gebruik",
                "gebruiksdoel": "woonfunctie",
            },
            "geometry": {"type": "Point",
                         "coordinates": [136705 + i, 455820.0]},
        })
    return {"type": "FeatureCollection", "name": "verblijfsobject",
            "crs": {"type": "name", "properties": {
                "name": "urn:ogc:def:crs:EPSG::28992"}},
            "numberMatched": len(features), "features": features,
            "bbox": [136701.28, 455804.71, 136728.86, 455849.32]}


def model(index):
    key = "NL.IMBAG.Pand." + bid(index)
    return {
        "metadata": {
            "type": "CityJSON", "version": "2.0",
            "metadata": {"referenceSystem":
                         "https://www.opengis.net/def/crs/EPSG/0/7415"},
        },
        "feature": {
            "id": key,
            "type": "CityJSONFeature",
            "CityObjects": {
                key: {
                    "type": "Building",
                    "attributes": {
                        "b3_kwaliteitsindicator": True,
                        "b3_volume_lod12": 100 + index,
                        "b3_volume_lod13": 90 + index,
                        "b3_volume_lod22": 80 + index,
                        "b3_val3dity_lod12": "[]",
                        "b3_val3dity_lod13": "[]",
                        "b3_val3dity_lod22": "[]",
                    },
                },
                key + ".part": {"type": "BuildingPart", "parents": [key]},
            },
            "vertices": [[100.0, 200.0, 300.0]],
        },
    }


class BagTo3dBagVolumeTests(unittest.TestCase):
    def test_exact_5_ids_and_valid_modelled_volumes(self):
        r = audit(wfs(), [model(i) for i in range(1, 6)], wfs_source_url=URL)
        self.assertEqual(r["wfs_sample_active_units"], 8)
        self.assertEqual(r["distinct_expected_bag_pand_refs"], 5)
        self.assertEqual(r["distinct_3dbag_building_id_matches"], 5)
        self.assertEqual(r["expected_buildings_without_supplied_3dbag_model"], 0)
        self.assertEqual(r["volumes_by_lod"]["lod12"]["sum_modelled_volume_m3"], 515)
        self.assertEqual(r["volumes_by_lod"]["lod13"]["sum_modelled_volume_m3"], 465)
        self.assertEqual(r["volumes_by_lod"]["lod22"]["sum_modelled_volume_m3"], 415)
        self.assertTrue(r["no_raw_ids_or_geometries_in_output"])
        for k in ("exact_3dbag_release_verified", "complete_multi_pand_relation_verified",
                  "source_rights_reviewed", "source_admitted", "replacement_cost_estimated",
                  "real_insured_tiv_or_policy_verified"):
            self.assertFalse(r[k])
        out = json.dumps(r)
        self.assertNotIn("NL.IMBAG.Pand.", out)
        self.assertNotIn("UNIT-", out)
        self.assertNotIn("000000", out)
        self.assertNotIn("vertices", out)

    def test_missing_model_never_false_coverage_or_volume(self):
        r = audit(wfs(), [model(i) for i in range(1, 5)], wfs_source_url=URL)
        self.assertEqual(r["expected_buildings_without_supplied_3dbag_model"], 1)
        for lod in ("lod12", "lod13", "lod22"):
            self.assertTrue(r["volumes_by_lod"][lod]["volume_suppressed_below_five"])
            self.assertIsNone(r["volumes_by_lod"][lod]["sum_modelled_volume_m3"])

    def test_invalid_geometry_code_and_quality_flag_exclude_volume(self):
        docs = [model(i) for i in range(1, 6)]
        docs[0]["feature"]["CityObjects"]["NL.IMBAG.Pand."+bid(1)]["attributes"]["b3_val3dity_lod12"] = "[601]"
        r = audit(wfs(), docs, wfs_source_url=URL)
        self.assertEqual(r["volumes_by_lod"]["lod12"]["invalid_3d_geometry_code_count"], 1)
        self.assertIsNone(r["volumes_by_lod"]["lod12"]["sum_modelled_volume_m3"])
        self.assertEqual(r["volumes_by_lod"]["lod13"]["sum_modelled_volume_m3"], 465)

        docs = [model(i) for i in range(1, 6)]
        docs[1]["feature"]["CityObjects"]["NL.IMBAG.Pand."+bid(2)]["attributes"]["b3_kwaliteitsindicator"] = False
        r = audit(wfs(), docs, wfs_source_url=URL)
        self.assertEqual(r["models_with_quality_marker_false"], 1)
        self.assertIsNone(r["volumes_by_lod"]["lod22"]["sum_modelled_volume_m3"])

    def test_invalid_volume_does_not_get_claimed_as_measured(self):
        for bad in (0, -100, True, float("nan"), "1000", None, 100_000_001):
            with self.subTest(bad=bad):
                docs = [model(i) for i in range(1, 6)]
                docs[0]["feature"]["CityObjects"]["NL.IMBAG.Pand."+bid(1)]["attributes"]["b3_volume_lod12"] = bad
                r = audit(wfs(), docs, wfs_source_url=URL)
                self.assertIsNone(r["volumes_by_lod"]["lod12"]["sum_modelled_volume_m3"])

    def test_rejects_extra_building_id_and_duplicate_model(self):
        docs = [model(i) for i in range(1, 5)] + [model(6)]
        with self.assertRaisesRegex(ModelledVolumeError, "unexpected or duplicate"):
            audit(wfs(), docs, wfs_source_url=URL)
        docs = [model(1), model(1)]
        with self.assertRaisesRegex(ModelledVolumeError, "unexpected or duplicate"):
            audit(wfs(), docs, wfs_source_url=URL)

    def test_rejects_bad_crs_wrong_cityjson_version_and_missing_building(self):
        for kind in ("crs", "version", "missing_building"):
            docs = [model(i) for i in range(1, 6)]
            if kind == "crs":
                docs[0]["metadata"]["metadata"]["referenceSystem"] = "EPSG:4326"
            elif kind == "version":
                docs[0]["metadata"]["version"] = "1.0"
            else:
                docs[0]["feature"]["CityObjects"] = {}
            with self.subTest(kind=kind), self.assertRaises(ModelledVolumeError):
                audit(wfs(), docs, wfs_source_url=URL)

    def test_blocks_wrong_or_address_bearing_bag_wfs(self):
        data = wfs()
        data["features"][0]["properties"]["postcode"] = "not allowed"
        with self.assertRaises(ValueError):
            audit(data, [model(i) for i in range(1, 6)], wfs_source_url=URL)
        data = wfs()
        with self.assertRaises(ValueError):
            audit(data, [model(i) for i in range(1, 6)],
                  wfs_source_url=URL.replace("service.pdok.nl", "evil.example"))

    def test_cli_private_files_only(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            wa = p / "wfs.json"
            wa.write_text(json.dumps(wfs()), encoding="utf-8")
            files = []
            for i in range(1, 6):
                filepath = p / f"model-{i}.json"
                filepath.write_text(json.dumps(model(i)), encoding="utf-8")
                files.append(str(filepath))
            self.assertEqual(main(["--wfs", str(wa), "--wfs-source-url", URL,
                                   "--models", *files]), 0)


if __name__ == "__main__":
    unittest.main()
