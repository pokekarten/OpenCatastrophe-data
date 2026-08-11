# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_manifest", ROOT / "scripts/validate_manifest.py")
assert SPEC and SPEC.loader
vm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vm)
MANIFEST = ROOT / "manifests/dwd.cdc.obsgermany-climate-10min-extreme-wind.v24.03.json"


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = vm.load_manifest(MANIFEST)

    def test_real_metadata_manifest_is_valid(self) -> None:
        vm.validate_structure(self.payload)
        vm.assert_public_asset_allowed(self.payload, "metadata")

    def test_registry_manifest_identity_is_path_stable_and_unique(self) -> None:
        manifests = sorted((ROOT / "manifests").glob("*.json"))
        self.assertTrue(manifests)
        dataset_ids: list[str] = []
        for path in manifests:
            payload = vm.load_manifest(path)
            dataset_id = payload["dataset_id"]
            with self.subTest(manifest=path.name):
                self.assertEqual(
                    path.stem,
                    dataset_id,
                    "registry manifest filename must equal its dataset_id",
                )
            dataset_ids.append(dataset_id)
        self.assertEqual(
            len(dataset_ids),
            len(set(dataset_ids)),
            "registry dataset_id values must be unique",
        )

    def test_narrow_review_blocks_source_permitted_raw_and_derived(self) -> None:
        with self.assertRaises(vm.ManifestError):
            vm.assert_public_asset_allowed(self.payload, "raw")
        with self.assertRaises(vm.ManifestError):
            vm.assert_public_asset_allowed(self.payload, "derived")

    def test_restricted_access_still_allows_public_metadata_when_other_gates_pass(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["access_class"] = "restricted"
        vm.assert_public_asset_allowed(payload, "metadata")

    def test_restricted_access_blocks_raw_even_when_other_gates_pass(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["access_class"] = "restricted"
        payload["review"]["status"] = "approved_raw"
        payload["raw_artifact"] = {
            "byte_size": 12,
            "sha256": "0" * 64,
            "storage_reference": "external://synthetic/restricted/raw.bin",
        }
        with self.assertRaisesRegex(
            vm.ManifestError,
            "restricted source access blocks raw source-byte publication",
        ):
            vm.assert_public_asset_allowed(payload, "raw")

    def test_restricted_access_preserves_explicit_derived_publication_gates(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["access_class"] = "restricted"
        payload["review"]["status"] = "approved_derived"
        payload["derived_artifact"] = {
            "byte_size": 12,
            "sha256": "1" * 64,
            "storage_reference": "external://synthetic/restricted/derived.bin",
        }
        payload["transformation"] = {
            "code_reference": "scripts/example_transform.py@0123456789abcdef",
            "config_identity": "sha256:" + "2" * 64,
        }
        vm.assert_public_asset_allowed(payload, "derived")

    def test_unknown_field_is_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["surprise"] = True
        with self.assertRaises(vm.ManifestError):
            vm.validate_structure(payload)

    def test_bool_is_not_artifact_byte_count(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["raw_artifact"] = {
            "byte_size": True,
            "sha256": "0" * 64,
            "storage_reference": "external://synthetic/example",
        }
        with self.assertRaises(vm.ManifestError):
            vm.validate_structure(payload)

    def test_storage_reference_rejects_noncanonical_segments(self) -> None:
        for reference in (
            "external://synthetic//example",
            "external://synthetic/./example",
            "external://synthetic/../example",
            "external://synthetic/.",
            "external://synthetic/..",
            "external://synthetic/",
        ):
            payload = copy.deepcopy(self.payload)
            payload["raw_artifact"] = {
                "byte_size": 1,
                "sha256": "0" * 64,
                "storage_reference": reference,
            }
            with self.subTest(reference=reference), self.assertRaises(vm.ManifestError):
                vm.validate_structure(payload)

    def test_storage_reference_schema_matches_validator_boundary(self) -> None:
        schema = json.loads((ROOT / "schemas/dataset-manifest.schema.json").read_text(encoding="utf-8"))
        pattern = schema["$defs"]["artifact"]["properties"]["storage_reference"]["pattern"]
        self.assertIsNotNone(re.fullmatch(pattern, "external://synthetic/example"))
        for reference in (
            "external://synthetic//example",
            "external://synthetic/./example",
            "external://synthetic/../example",
            "external://synthetic/.",
            "external://synthetic/..",
            "external://synthetic/",
        ):
            with self.subTest(reference=reference):
                self.assertIsNone(re.fullmatch(pattern, reference))

    def test_private_and_signed_urls_are_rejected(self) -> None:
        for url in (
            "http://example.org/source",
            "http://" + "127.0.0.1" + "/source",
            "https://example.org/source?token=" + "a" * 30,
            "https://user:pass@example.org/source",
        ):
            payload = copy.deepcopy(self.payload)
            payload["canonical_source"] = url
            with self.subTest(url=url), self.assertRaises(vm.ManifestError):
                vm.validate_structure(payload)

    def test_manifest_url_schema_matches_https_validator_boundary(self) -> None:
        schema = json.loads((ROOT / "schemas/dataset-manifest.schema.json").read_text(encoding="utf-8"))
        canonical_pattern = schema["properties"]["canonical_source"]["pattern"]
        terms_pattern = schema["properties"]["licensing"]["properties"]["terms_reference"]["pattern"]
        for pattern in (canonical_pattern, terms_pattern):
            self.assertIsNotNone(re.match(pattern, "https://example.org/source"))
            self.assertIsNone(re.match(pattern, "http://example.org/source"))

        payload = copy.deepcopy(self.payload)
        payload["licensing"]["terms_reference"] = "http://example.org/terms"
        with self.assertRaisesRegex(vm.ManifestError, "absolute HTTPS URL"):
            vm.validate_structure(payload)

    def test_unknown_rights_fail_closed(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["licensing"]["status"] = "unknown"
        with self.assertRaises(vm.ManifestError):
            vm.assert_public_asset_allowed(payload, "metadata")

    def test_privacy_uncertainty_fails_closed(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["privacy"]["personal_data_status"] = "unknown"
        with self.assertRaises(vm.ManifestError):
            vm.assert_public_asset_allowed(payload, "metadata")

    def test_derived_asset_requires_lineage(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["derived_artifact"] = {
            "byte_size": 1,
            "sha256": "1" * 64,
            "storage_reference": "external://synthetic/derived",
        }
        with self.assertRaises(vm.ManifestError):
            vm.validate_structure(payload)

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text('{"schema_version":"1.0.0","schema_version":"1.0.0"}', encoding="utf-8")
            with self.assertRaises(vm.ManifestError):
                vm.load_manifest(path)

    def test_nonfinite_json_number_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.json"
            path.write_text('{"x": NaN}', encoding="utf-8")
            with self.assertRaises(vm.ManifestError):
                vm.load_manifest(path)

    def test_validate_manifest_cli_fails_closed_with_stable_exit_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text('{"schema_version":"1.0.0","schema_version":"1.0.0"}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "scripts/validate_manifest.py", str(path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 1)
        self.assertTrue(result.stdout.startswith("BLOCKED:"), result.stdout)
        self.assertEqual(result.stderr, "")

    def test_manifest_identity_cli_matches_library_digest(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import manifest_identity as module
        finally:
            sys.path.pop(0)
        expected = module.manifest_sha256(self.payload)
        result = subprocess.run(
            [sys.executable, "scripts/manifest_identity.py", str(MANIFEST.relative_to(ROOT))],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), expected)
        self.assertEqual(result.stderr, "")

    def test_manifest_identity_is_deterministic(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import manifest_identity as module
        finally:
            sys.path.pop(0)
        first = module.manifest_sha256(self.payload)
        reordered = dict(reversed(list(self.payload.items())))
        self.assertEqual(first, module.manifest_sha256(reordered))
        self.assertRegex(first, r"^[a-f0-9]{64}$")


if __name__ == "__main__":
    unittest.main()
