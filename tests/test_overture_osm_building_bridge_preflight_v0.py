# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline synthetic tests; no actual Overture/source records are asserted."""
import copy
import tempfile
import unittest
from pathlib import Path

from scripts.overture_osm_building_bridge_preflight_v0 import (
    BridgeError, SCHEMA, _read, bridge_osm_buildings,
)

RELEASE = "2026-10-21.0"
GERS_1 = "fea28f69-7afa-460c-b270-61ef74cd340c"
GERS_2 = "fae28f69-7afa-460c-b270-61ef74cd340c"


def example():
    return {
        "schema": SCHEMA,
        "release": RELEASE,
        "bridge_provider": "osm",
        "bridge_dataset": "OpenStreetMap",
        "local_records": [{"local_id": "SYNTH-1", "record_id": "w123@5"}],
        "bridge_rows": [{
            "id": GERS_1, "record_id": "w123@5", "dataset": "OpenStreetMap",
            "provider": "osm", "theme": "buildings", "type": "building",
        }],
    }


class OSMBridgePreflightTests(unittest.TestCase):
    def test_exact_join_is_only_candidate(self):
        r = bridge_osm_buildings(example(), expected_release=RELEASE)
        self.assertEqual(r["version_exact_bridge_candidates"], [{
            "local_id": "SYNTH-1", "source_record_id": "w123@5",
            "overture_feature_id": GERS_1,
        }])
        for field in ("source_file_original_bytes_verified", "gers_registry_membership_verified",
                      "physical_geometry_crosschecked", "independent_model_input_approved",
                      "raw_data_import_authorized", "insured_value_inferred",
                      "bridge_slice_proves_global_absence"):
            self.assertIs(r[field], False)

    def test_osm_version_is_not_silently_stripped(self):
        v = example()
        v["local_records"][0]["record_id"] = "w123@4"
        r = bridge_osm_buildings(v, expected_release=RELEASE)
        self.assertEqual(r["unmatched_in_provided_slice"], ["SYNTH-1"])
        self.assertFalse(r["version_exact_bridge_candidates"])

    def test_missing_version_rejected(self):
        v = example()
        v["local_records"][0]["record_id"] = "w123"
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_invalid_osm_version_rejected(self):
        v = example()
        v["bridge_rows"][0]["record_id"] = "w123@0"
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_mixed_release_rejected(self):
        v = example()
        v["release"] = "2026-09-23.1"
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_dynamic_release_rejected(self):
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(example(), expected_release="latest")

    def test_wrong_theme_rejected(self):
        v = example()
        v["bridge_rows"][0]["theme"] = "base"
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_building_part_rejected(self):
        v = example()
        v["bridge_rows"][0]["type"] = "building_part"
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_different_provider_rejected(self):
        v = example()
        v["bridge_rows"][0]["provider"] = "microsoft"
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_mislabeled_dataset_rejected(self):
        v = example()
        v["bridge_rows"][0]["dataset"] = "OtherData"
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_duplicate_pair_rejected(self):
        v = example()
        v["bridge_rows"].append(copy.deepcopy(v["bridge_rows"][0]))
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_one_source_two_gers_ambiguous(self):
        v = example()
        second = copy.deepcopy(v["bridge_rows"][0])
        second["id"] = GERS_2
        v["bridge_rows"].append(second)
        r = bridge_osm_buildings(v, expected_release=RELEASE)
        self.assertEqual(r["ambiguous_local_ids"], ["SYNTH-1"])
        self.assertFalse(r["version_exact_bridge_candidates"])

    def test_two_local_ids_same_gers_ambiguous(self):
        v = example()
        v["local_records"].append({"local_id": "SYNTH-2", "record_id": "w456@7"})
        second = copy.deepcopy(v["bridge_rows"][0])
        second["record_id"] = "w456@7"
        v["bridge_rows"].append(second)
        r = bridge_osm_buildings(v, expected_release=RELEASE)
        self.assertEqual(r["ambiguous_local_ids"], ["SYNTH-1", "SYNTH-2"])
        self.assertFalse(r["version_exact_bridge_candidates"])

    def test_duplicate_local_id_rejected(self):
        v = example()
        v["local_records"].append(copy.deepcopy(v["local_records"][0]))
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_missing_source_in_slice_is_not_global_absence(self):
        v = example()
        v["local_records"].append({"local_id": "SYNTH-2", "record_id": "w999@1"})
        r = bridge_osm_buildings(v, expected_release=RELEASE)
        self.assertEqual(r["unmatched_in_provided_slice"], ["SYNTH-2"])
        self.assertIs(r["bridge_slice_proves_global_absence"], False)

    def test_invalid_uuid_rejected(self):
        v = example()
        v["bridge_rows"][0]["id"] = "not-a-uuid"
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_metadata_cannot_promote_model(self):
        v = example()
        v["model_input_approved"] = True
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_extra_private_insurer_value_rejected(self):
        v = example()
        v["local_records"][0]["insured_value"] = 1000000
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_duplicate_json_key_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text('{"provider":"osm","provider":"other"}')
            with self.assertRaises(BridgeError):
                _read(path)

    def test_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text('{"value":NaN}')
            with self.assertRaises(BridgeError):
                _read(path)

    def test_invalid_array_cardinality_rejected(self):
        v = example()
        v["bridge_rows"] = []
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)

    def test_unexpected_bridge_field_rejected(self):
        v = example()
        v["bridge_rows"][0]["all_source_data_is_admitted"] = True
        with self.assertRaises(BridgeError):
            bridge_osm_buildings(v, expected_release=RELEASE)


if __name__ == "__main__":
    unittest.main()
