# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only ArcGIS native schema and published field crosswalk regression."""
from __future__ import annotations

import hashlib
import json
import unittest
from research_runners import us_wildfire_original_arcgis_metadata_v0 as g


def metadata(profile, **changes):
    expected = g.PROFILES[profile]
    p = {
        "id": expected["id"], "name": expected["name"],
        "type": "Feature Layer", "geometryType": expected["geometry"],
        "spatialReference": {"wkid": 4269},
        "fields": [{"name": name, "type": kind} for name, kind in expected["fields"].items()],
    }
    p.update(changes)
    return p


def parse(profile, data=None):
    blob = json.dumps(
        metadata(profile) if data is None else data, separators=(",", ":")
    ).encode("utf-8")
    return g.inspect_layer(blob, hashlib.sha256(blob).hexdigest(), profile)


class WildfireOriginalMetadataTests(unittest.TestCase):
    def test_fpa_fields_are_native_not_research_header(self):
        value = parse("fpa_fod_7")
        self.assertEqual(value["source_to_research_projection_field_map"], {
            "fpa_record_id": "fod_id", "mtbs_id": "mtbs_id", "fire_year": "fire_year"
        })
        self.assertFalse(value["original_source_file_sha256_pinned"])
        self.assertFalse(value["native_row_values_examined"])
        self.assertFalse(value["individual_event_join_proven"])
        self.assertFalse(value["authenticated_original_publisher_bytes"])

    def test_mtbs_polygons_map_source_id_year_and_event_type(self):
        value = parse("mtbs_perimeters_2024")
        self.assertEqual(value["source_to_research_projection_field_map"], {
            "mtbs_component_id": None, "mtbs_id": "fire_id",
            "fire_year": "year", "event_kind": "fire_type",
        })
        self.assertEqual(value["geometry"], "esriGeometryPolygon")
        self.assertFalse(value["polygon_component_key_from_perim_id_authorized"])

    def test_publisher_fire_type_mapping_is_explicit_and_never_guesses_wildfire(self):
        cases = (
            ("Wildfire", ("wildfire", True)),
            ("Prescribed Fire", ("prescribed", True)),
            ("Wildland Fire Use", ("unknown", True)),
            ("Unknown", ("unknown", True)),
            ("new publisher category", ("unknown", False)),
            ("wildfire", ("unknown", False)),
            (" Wildfire ", ("unknown", False)),
            ("", ("unknown", False)),
            (None, ("unknown", False)),
        )
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(g.classify_mtbs_fire_type(raw), expected)

    def test_perim_id_is_satellite_scene_not_polygon_key(self):
        value = parse("mtbs_perimeters_2024")
        self.assertFalse(value["polygon_component_key_from_perim_id_authorized"])
        self.assertIsNone(value["source_to_research_projection_field_map"]["mtbs_component_id"])
        self.assertIn("satellite scene", value["perim_id_publisher_semantics"])

    def test_valid_pair_remains_research_only(self):
        f = json.dumps(metadata("fpa_fod_7")).encode()
        m = json.dumps(metadata("mtbs_perimeters_2024")).encode()
        result = g.inspect_pair(f, hashlib.sha256(f).hexdigest(),
                                m, hashlib.sha256(m).hexdigest())
        self.assertEqual(result["state"], "PROVIDED_LAYER_SCHEMA_COMPATIBLE_RESEARCH_ONLY")
        self.assertFalse(result["point_polygon_join_approved"])
        self.assertFalse(result["value_and_geometric_support_verified"])

    def test_wrong_perimeter_year_and_wrong_layer_blocked(self):
        for patch in ({"id": 84}, {"name": "2025 Burned Area Boundaries"}, {"id": 0}):
            with self.subTest(patch=patch), self.assertRaises(g.OriginalLayerBlocked):
                parse("mtbs_perimeters_2024", metadata("mtbs_perimeters_2024", **patch))

    def test_geometry_reversal_and_coordinate_reference_blocked(self):
        for profile, geometry in (("fpa_fod_7", "esriGeometryPolygon"),
                                  ("mtbs_perimeters_2024", "esriGeometryPoint")):
            with self.subTest(profile=profile), self.assertRaisesRegex(
                g.OriginalLayerBlocked, "geometry"
            ):
                parse(profile, metadata(profile, geometryType=geometry))
        with self.assertRaisesRegex(g.OriginalLayerBlocked, "4269"):
            parse("fpa_fod_7", metadata("fpa_fod_7", spatialReference={"wkid": 4326}))

    def test_missing_key_and_changed_type_fail_closed(self):
        for profile, required in (("fpa_fod_7", "mtbs_id"),
                                  ("mtbs_perimeters_2024", "fire_id")):
            data = metadata(profile)
            data["fields"] = [x for x in data["fields"] if x["name"] != required]
            with self.subTest(profile=profile), self.assertRaisesRegex(
                g.OriginalLayerBlocked, "required original field"
            ):
                parse(profile, data)
        data = metadata("fpa_fod_7")
        next(x for x in data["fields"] if x["name"] == "fod_id")["type"] = "esriFieldTypeString"
        with self.assertRaisesRegex(g.OriginalLayerBlocked, "type changed"):
            parse("fpa_fod_7", data)

    def test_duplicate_casefold_field_names_blocked(self):
        data = metadata("mtbs_perimeters_2024")
        data["fields"].append({"name": "FIRE_ID", "type": "esriFieldTypeString"})
        with self.assertRaisesRegex(g.OriginalLayerBlocked, "duplicate"):
            parse("mtbs_perimeters_2024", data)

    def test_strict_json_duplicate_keys_and_nonfinite(self):
        for raw in (b'{"id":82,"id":82}', b'{"foo":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(g.OriginalLayerBlocked):
                g.inspect_layer(raw, hashlib.sha256(raw).hexdigest(), "mtbs_perimeters_2024")

    def test_original_metadata_hash_mismatch_blocks(self):
        raw = json.dumps(metadata("fpa_fod_7")).encode()
        with self.assertRaisesRegex(g.OriginalLayerBlocked, "SHA-256"):
            g.inspect_layer(raw, "0"*64, "fpa_fod_7")

    def test_missing_fields_or_arcgis_error_blocks(self):
        for d in ({"error":{"code":404}}, metadata("fpa_fod_7", fields=[]),
                  metadata("fpa_fod_7", fields="not a list")):
            with self.subTest(d=d), self.assertRaises(g.OriginalLayerBlocked):
                parse("fpa_fod_7", d)

    def test_bad_typed_id_and_empty_or_oversize_blob_rejected(self):
        for p in (metadata("mtbs_perimeters_2024", id=True),
                  metadata("mtbs_perimeters_2024", id="82")):
            with self.subTest(p=p), self.assertRaises(g.OriginalLayerBlocked):
                parse("mtbs_perimeters_2024", p)
        for blob in (b"", b"0" * (g.MAX_SNAPSHOT_BYTES+1)):
            with self.assertRaises(g.OriginalLayerBlocked):
                g.inspect_layer(blob, "0"*64, "fpa_fod_7")

    def test_legal_additional_fields_and_source_case_preserved(self):
        p = metadata("fpa_fod_7")
        p["fields"].append({"name": "new_field", "type": "esriFieldTypeString"})
        p["fields"][0]["name"] = "FOD_ID"
        out = parse("fpa_fod_7", p)
        self.assertEqual(out["source_to_research_projection_field_map"]["fpa_record_id"], "FOD_ID")
