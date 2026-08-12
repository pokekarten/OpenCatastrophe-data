# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import validate_model_input as validator

ROOT = Path(__file__).resolve().parents[1]
SHA_A = "a" * 64
SHA_B = "b" * 64
STORAGE = "external://synthetic/hazard"


def valid_manifest() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "dataset_id": "synthetic.hazard",
        "provider": "Synthetic Provider",
        "product_name": "Synthetic Hazard",
        "version_or_release": "1.0",
        "canonical_source": "https://example.com/data",
        "retrieved_at": "2026-08-12T00:00:00Z",
        "retrieval_query_or_filters": None,
        "access_class": "open",
        "modelling_layer": "hazard",
        "intended_use": "Independent synthetic model-input validation.",
        "raw_artifact": {
            "byte_size": 3,
            "sha256": SHA_A,
            "storage_reference": STORAGE,
        },
        "derived_artifact": None,
        "licensing": {
            "status": "verified",
            "spdx_expression": "CC0-1.0",
            "licence_name": None,
            "terms_reference": "https://example.com/terms",
            "terms_reviewed_at": "2026-08-12T00:00:00Z",
            "terms_version_or_date": "2026-08-12",
            "terms_content_sha256": None,
            "commercial_use_status": "allowed",
            "attribution_requirements": None,
            "share_alike_or_derivative_requirements": None,
            "notes": None,
        },
        "redistribution": {"status": "allowed", "scope": "raw", "conditions": None},
        "privacy": {
            "personal_data_status": "none",
            "confidential_or_proprietary_status": "none",
            "notes": None,
        },
        "spatial": {"crs": "EPSG:4326", "extent": "synthetic"},
        "temporal": {"extent": "2020-01-01/2020-01-03"},
        "variables_and_units": [
            {"name": "wind_speed", "unit": "m/s", "description": "Synthetic."}
        ],
        "transformation": None,
        "review": {
            "status": "approved_raw",
            "reviewed_at": "2026-08-12T00:00:00Z",
            "reviewer": "synthetic-reviewer",
            "notes": None,
        },
    }


def valid_model_input() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "manifest": "manifests/synthetic.hazard.json",
        "dataset_id": "synthetic.hazard",
        "artifact": "raw",
        "storage_reference": STORAGE,
        "sha256": SHA_A,
        "modelling_layer": "hazard",
        "scientific_role": "validation",
        "peril": {"id": "windstorm", "subperil": "extreme_wind"},
        "measure": {
            "quantity": "wind_speed",
            "unit": "m/s",
            "aggregation": "maximum",
        },
        "spatial": {
            "crs": "EPSG:4326",
            "support": "point",
            "resolution": None,
        },
        "temporal": {
            "support": "interval_series",
            "start": "2020-01-01T00:00:00Z",
            "end": "2020-01-03T00:00:00Z",
            "step_seconds": 600,
            "aggregation_window_seconds": 600,
        },
        "quality": {
            "missing_value_policy": "explicit",
            "quality_flag_policy": "preserved",
        },
    }


class ModelInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "manifests").mkdir()
        self.manifest_path = self.root / "manifests/synthetic.hazard.json"
        self.write_manifest(valid_manifest())

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_manifest(self, payload: dict[str, object]) -> None:
        self.manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    def test_schema_is_closed_versioned_json(self) -> None:
        schema = validator.load_strict_json(ROOT / "schemas/model-input-v1.schema.json")
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], validator.SCHEMA_VERSION)

    def test_valid_binding_resolves_exact_admitted_artifact(self) -> None:
        validator.validate_model_input(valid_model_input(), root=self.root)

    def test_manifest_binding_must_match_path_dataset_artifact_and_layer(self) -> None:
        payload = valid_model_input()
        payload["manifest"] = "manifests/other.json"
        with self.assertRaisesRegex(validator.ModelInputError, "manifest path must match dataset_id"):
            validator.validate_model_input(payload, root=self.root)

        payload = valid_model_input()
        payload["sha256"] = SHA_B
        with self.assertRaisesRegex(validator.ModelInputError, "sha256 does not match"):
            validator.validate_model_input(payload, root=self.root)

        payload = valid_model_input()
        payload["storage_reference"] = "external://synthetic/wrong"
        with self.assertRaisesRegex(validator.ModelInputError, "storage_reference does not match"):
            validator.validate_model_input(payload, root=self.root)

        payload = valid_model_input()
        payload["modelling_layer"] = "exposure"
        with self.assertRaisesRegex(validator.ModelInputError, "modelling_layer does not match"):
            validator.validate_model_input(payload, root=self.root)

    def test_metadata_only_manifest_cannot_pose_as_model_input(self) -> None:
        manifest = valid_manifest()
        manifest["raw_artifact"] = None
        manifest["review"]["status"] = "approved_metadata_only"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(validator.ModelInputError, "raw artifact is not identified"):
            validator.validate_model_input(valid_model_input(), root=self.root)

    def test_mutable_latest_manifest_is_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["version_or_release"] = "latest"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(validator.ModelInputError, "mutable version label latest"):
            validator.validate_model_input(valid_model_input(), root=self.root)

    def test_semantic_objects_are_closed_and_type_strict(self) -> None:
        payload = valid_model_input()
        payload["measure"]["extra"] = "no"
        with self.assertRaisesRegex(validator.ModelInputError, "measure contains unexpected fields"):
            validator.validate_model_input(payload, root=self.root)

        payload = valid_model_input()
        payload["spatial"]["resolution"] = {"value": True, "unit": "km"}
        with self.assertRaisesRegex(validator.ModelInputError, "positive finite number"):
            validator.validate_model_input(payload, root=self.root)

        payload = valid_model_input()
        payload["temporal"]["step_seconds"] = True
        with self.assertRaisesRegex(validator.ModelInputError, "positive integer"):
            validator.validate_model_input(payload, root=self.root)

    def test_temporal_bounds_and_static_semantics_fail_closed(self) -> None:
        payload = valid_model_input()
        payload["temporal"]["end"] = payload["temporal"]["start"]
        with self.assertRaisesRegex(validator.ModelInputError, "later than temporal.start"):
            validator.validate_model_input(payload, root=self.root)

        payload = valid_model_input()
        payload["temporal"] = {
            "support": "static",
            "start": "2020-01-01T00:00:00Z",
            "end": None,
            "step_seconds": None,
            "aggregation_window_seconds": None,
        }
        with self.assertRaisesRegex(validator.ModelInputError, "static temporal support"):
            validator.validate_model_input(payload, root=self.root)

    def test_duplicate_keys_and_nonfinite_json_fail_closed(self) -> None:
        duplicate = self.root / "duplicate.json"
        duplicate.write_text('{"schema_version":"1.0.0","schema_version":"1.0.0"}', encoding="utf-8")
        with self.assertRaisesRegex(validator.ModelInputError, "duplicate JSON key"):
            validator.load_strict_json(duplicate)

        nonfinite = self.root / "nonfinite.json"
        nonfinite.write_text('{"value":NaN}', encoding="utf-8")
        with self.assertRaisesRegex(validator.ModelInputError, "non-finite JSON number"):
            validator.load_strict_json(nonfinite)

    def test_unsafe_manifest_and_storage_paths_are_rejected(self) -> None:
        payload = valid_model_input()
        payload["manifest"] = "../manifests/synthetic.hazard.json"
        with self.assertRaisesRegex(validator.ModelInputError, "canonical manifests"):
            validator.validate_model_input(payload, root=self.root)

        payload = valid_model_input()
        payload["storage_reference"] = "external://synthetic/../hazard"
        with self.assertRaisesRegex(validator.ModelInputError, "noncanonical path segments"):
            validator.validate_model_input(payload, root=self.root)

    def test_cli_executes_against_explicit_root(self) -> None:
        model_input_path = self.root / "model-input.json"
        model_input_path.write_text(json.dumps(valid_model_input()), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "scripts/validate_model_input.py",
                str(model_input_path),
                "--root",
                str(self.root),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "PASS\n")


if __name__ == "__main__":
    unittest.main()
