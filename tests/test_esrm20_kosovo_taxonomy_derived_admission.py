# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
import unittest

from scripts import validate_manifest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifests/efehr.esrm20.european-exposure-model.v1.0.json"

EXPECTED_SOURCE_SHA256 = "4d562ad4925c527d518834b8dcd39a083cfd3b87b622031a84958ae7b4d8c5ea"
EXPECTED_TAXONOMY_SHA256 = "d5e6fe4e32489cdd2222b6b3facfd30937e2af61bbcf0ecead37ccf97202a945"
EXPECTED_EXECUTION_SHA = "f2fcfa1d94f1a44f738353ef0bae8d467351a2eb"
EXPECTED_REPRESENTATION = "oc-taxonomy-u64be-utf8-sorted-v1"


class Esrm20KosovoTaxonomyDerivedAdmissionTests(unittest.TestCase):
    def load_manifest(self) -> dict[str, object]:
        manifest = validate_manifest.load_manifest(MANIFEST_PATH)
        validate_manifest.validate_structure(manifest)
        return manifest

    def test_exact_taxonomy_derivative_is_publicly_admitted(self) -> None:
        manifest = self.load_manifest()

        self.assertEqual(manifest["review"]["status"], "approved_derived")
        self.assertIsNone(manifest["raw_artifact"])
        self.assertEqual(
            manifest["derived_artifact"],
            {
                "byte_size": 2666,
                "sha256": EXPECTED_TAXONOMY_SHA256,
                "storage_reference": (
                    "external://derived/efehr.esrm20.european-exposure-model.v1.0/"
                    "kosovo-residential/taxonomy/oc-taxonomy-u64be-utf8-sorted-v1"
                ),
            },
        )
        self.assertEqual(manifest["licensing"]["spdx_expression"], "CC-BY-4.0")
        self.assertEqual(manifest["redistribution"]["scope"], "raw")
        self.assertEqual(manifest["privacy"]["personal_data_status"], "none")
        self.assertEqual(
            manifest["privacy"]["confidential_or_proprietary_status"], "none"
        )

        validate_manifest.assert_public_asset_allowed(manifest, "derived")

    def test_raw_source_publication_remains_blocked(self) -> None:
        manifest = self.load_manifest()

        with self.assertRaisesRegex(
            validate_manifest.ManifestError,
            "asset kind exceeds repository review scope|raw publication requires raw_artifact identity",
        ):
            validate_manifest.assert_public_asset_allowed(manifest, "raw")

    def test_transformation_lineage_is_exact_and_does_not_claim_mapping_authority(self) -> None:
        manifest = self.load_manifest()
        transformation = manifest["transformation"]

        self.assertEqual(
            transformation["code_reference"],
            f"{EXPECTED_EXECUTION_SHA}:scripts/acquire_efehr_kosovo_taxonomy.py",
        )
        config_identity = transformation["config_identity"]
        self.assertIn("canonicalizer-_canonical_artifact_identity", config_identity)
        self.assertIn("upstream-extractor-scripts-extract_efehr_kosovo_taxonomy.py", config_identity)
        self.assertIn("issue-363-result-5303346187", config_identity)
        self.assertIn("source-receipt-5300981864", config_identity)
        self.assertIn("TAXONOMY", config_identity)
        self.assertIn("count-86", config_identity)
        self.assertIn(EXPECTED_REPRESENTATION, config_identity)
        self.assertIn("no-normalization", config_identity)

        review_notes = manifest["review"]["notes"]
        self.assertIn(EXPECTED_SOURCE_SHA256, manifest["retrieval_query_or_filters"])
        self.assertIn(EXPECTED_TAXONOMY_SHA256, review_notes)
        self.assertIn("acquire_efehr_kosovo_taxonomy.py::_canonical_artifact_identity", review_notes)
        self.assertIn("extract_efehr_kosovo_taxonomy.py", review_notes)
        self.assertIn("does not admit", review_notes)
        self.assertIn("mapping outcomes", review_notes)
        self.assertIn("vulnerability selections", review_notes)
        self.assertIn("model inputs", review_notes)


if __name__ == "__main__":
    unittest.main()
