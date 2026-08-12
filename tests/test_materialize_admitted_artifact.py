# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import materialize_admitted_artifact as materializer

ROOT = Path(__file__).resolve().parents[1]
BYTES = b"abc"
SHA = hashlib.sha256(BYTES).hexdigest()
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
        "intended_use": "Synthetic cache-materialization validation.",
        "raw_artifact": {
            "byte_size": len(BYTES),
            "sha256": SHA,
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
        "temporal": None,
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
        "sha256": SHA,
        "modelling_layer": "hazard",
        "scientific_role": "benchmark",
        "peril": {"id": "windstorm", "subperil": "extreme_wind"},
        "measure": {
            "quantity": "wind_speed",
            "unit": "m/s",
            "aggregation": "maximum",
        },
        "spatial": {"crs": "EPSG:4326", "support": "point", "resolution": None},
        "temporal": {
            "support": "static",
            "start": None,
            "end": None,
            "step_seconds": None,
            "aggregation_window_seconds": None,
        },
        "quality": {
            "missing_value_policy": "forbidden",
            "quality_flag_policy": "none",
        },
    }


class MaterializeAdmittedArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_tmp = tempfile.TemporaryDirectory()
        self.source_tmp = tempfile.TemporaryDirectory()
        self.cache_tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.repo_tmp.name)
        self.source_root = Path(self.source_tmp.name)
        self.cache_root = Path(self.cache_tmp.name)
        (self.root / "manifests").mkdir()
        (self.root / "inputs").mkdir()
        (self.root / "manifests/synthetic.hazard.json").write_text(
            json.dumps(valid_manifest()), encoding="utf-8"
        )
        self.model_input_path = self.root / "inputs/model-input.json"
        self.model_input_path.write_text(json.dumps(valid_model_input()), encoding="utf-8")
        self.source_path = self.source_root / "provider.bin"
        self.source_path.write_bytes(BYTES)

    def tearDown(self) -> None:
        self.cache_tmp.cleanup()
        self.source_tmp.cleanup()
        self.repo_tmp.cleanup()

    def materialize(self) -> dict[str, object]:
        return materializer.materialize(
            self.model_input_path,
            self.source_path,
            self.cache_root,
            root=self.root,
        )

    def test_materializes_exact_bytes_under_content_addressed_key(self) -> None:
        receipt = self.materialize()
        expected_key = f"synthetic.hazard/raw/{SHA}"
        self.assertEqual(receipt["cache_key"], expected_key)
        self.assertEqual(receipt["sha256"], SHA)
        self.assertEqual(receipt["byte_size"], len(BYTES))
        self.assertFalse(receipt["reused"])
        self.assertFalse(receipt["repository_bytes_persisted"])
        self.assertNotIn(str(self.cache_root), json.dumps(receipt))
        self.assertEqual((self.cache_root / expected_key).read_bytes(), BYTES)

    def test_same_exact_artifact_is_idempotently_reused(self) -> None:
        first = self.materialize()
        second = self.materialize()
        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])
        self.assertEqual(first["cache_key"], second["cache_key"])

    def test_hash_or_size_mismatch_fails_closed_without_cache_file(self) -> None:
        self.source_path.write_bytes(b"abd")
        with self.assertRaisesRegex(materializer.MaterializationError, "SHA-256"):
            self.materialize()
        self.assertFalse((self.cache_root / f"synthetic.hazard/raw/{SHA}").exists())

        self.source_path.write_bytes(b"ab")
        with self.assertRaisesRegex(materializer.MaterializationError, "byte size mismatch"):
            self.materialize()

    def test_metadata_only_manifest_cannot_materialize(self) -> None:
        manifest = valid_manifest()
        manifest["raw_artifact"] = None
        manifest["review"]["status"] = "approved_metadata_only"
        (self.root / "manifests/synthetic.hazard.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        with self.assertRaisesRegex(materializer.MaterializationError, "review/admission scope"):
            self.materialize()

    def test_source_and_cache_must_stay_outside_repository(self) -> None:
        internal_source = self.root / "provider.bin"
        internal_source.write_bytes(BYTES)
        with self.assertRaisesRegex(materializer.MaterializationError, "source file must be outside"):
            materializer.materialize(
                self.model_input_path,
                internal_source,
                self.cache_root,
                root=self.root,
            )

        with self.assertRaisesRegex(materializer.MaterializationError, "cache root must be outside"):
            materializer.materialize(
                self.model_input_path,
                self.source_path,
                self.root / "cache",
                root=self.root,
            )

    def test_symlink_source_and_cache_root_are_rejected(self) -> None:
        source_link = self.source_root / "source-link.bin"
        cache_link = self.source_root / "cache-link"
        try:
            source_link.symlink_to(self.source_path)
            cache_link.symlink_to(self.cache_root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")

        with self.assertRaisesRegex(materializer.MaterializationError, "source file must not be a symlink"):
            materializer.materialize(
                self.model_input_path,
                source_link,
                self.cache_root,
                root=self.root,
            )
        with self.assertRaisesRegex(materializer.MaterializationError, "cache root must not be a symlink"):
            materializer.materialize(
                self.model_input_path,
                self.source_path,
                cache_link,
                root=self.root,
            )

    def test_existing_wrong_cache_content_is_rejected(self) -> None:
        destination = self.cache_root / f"synthetic.hazard/raw/{SHA}"
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"wrong")
        with self.assertRaisesRegex(materializer.MaterializationError, "does not match admitted artifact"):
            self.materialize()
        self.assertEqual(destination.read_bytes(), b"wrong")

    def test_cli_emits_portable_receipt_without_private_paths(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/materialize_admitted_artifact.py"),
                str(self.model_input_path),
                str(self.source_path),
                str(self.cache_root),
                "--root",
                str(self.root),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["sha256"], SHA)
        self.assertNotIn(str(self.source_root), result.stdout)
        self.assertNotIn(str(self.cache_root), result.stdout)
        self.assertNotIn(str(self.root), result.stdout)


if __name__ == "__main__":
    unittest.main()
