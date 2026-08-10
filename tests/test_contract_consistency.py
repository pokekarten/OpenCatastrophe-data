# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts import query_source_landscape as landscape
from scripts import validate_manifest as manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_REFERENCE_RE = re.compile(r"`(manifests/[A-Za-z0-9._-]+\.json)`")
REVIEW_FILENAME_RE = re.compile(r"`([A-Za-z0-9._-]+\.md)`")


class ContractConsistencyTests(unittest.TestCase):
    def test_manifest_schema_matches_dependency_free_validator_surface(self) -> None:
        schema = json.loads((ROOT / "schemas/dataset-manifest.schema.json").read_text(encoding="utf-8"))
        properties = schema["properties"]

        self.assertEqual(set(properties), manifest.TOP_KEYS)
        self.assertEqual(set(schema["required"]), manifest.REQUIRED_TOP)
        self.assertEqual(set(properties["access_class"]["enum"]), manifest.ACCESS)
        self.assertEqual(set(properties["modelling_layer"]["enum"]), manifest.LAYERS)

        artifact = schema["$defs"]["artifact"]
        self.assertEqual(set(artifact["properties"]), manifest.ARTIFACT_KEYS)
        self.assertEqual(set(artifact["required"]), manifest.ARTIFACT_KEYS)

        licensing = properties["licensing"]
        self.assertEqual(set(licensing["properties"]), manifest.LICENSING_KEYS)
        self.assertEqual(set(licensing["properties"]["status"]["enum"]), manifest.LICENCE_STATUS)
        self.assertEqual(
            set(licensing["properties"]["commercial_use_status"]["enum"]),
            manifest.COMMERCIAL,
        )

        redistribution = properties["redistribution"]
        self.assertEqual(set(redistribution["properties"]), manifest.REDISTRIBUTION_KEYS)
        self.assertEqual(set(redistribution["properties"]["status"]["enum"]), manifest.REDIST_STATUS)
        self.assertEqual(set(redistribution["properties"]["scope"]["enum"]), manifest.REDIST_SCOPE)

        privacy = properties["privacy"]
        self.assertEqual(set(privacy["properties"]), manifest.PRIVACY_KEYS)
        self.assertEqual(set(privacy["properties"]["personal_data_status"]["enum"]), manifest.PERSONAL)
        self.assertEqual(
            set(privacy["properties"]["confidential_or_proprietary_status"]["enum"]),
            manifest.PERSONAL,
        )

        review = properties["review"]
        self.assertEqual(set(review["properties"]), manifest.REVIEW_KEYS)
        self.assertEqual(set(review["properties"]["status"]["enum"]), manifest.REVIEW_STATUS)

        transformation = properties["transformation"]
        self.assertEqual(set(transformation["properties"]), manifest.TRANSFORMATION_KEYS)
        self.assertEqual(set(transformation["required"]), manifest.TRANSFORMATION_KEYS)
        self.assertEqual(set(properties["spatial"]["properties"]), manifest.SPATIAL_KEYS)
        self.assertEqual(set(properties["temporal"]["properties"]), manifest.TEMPORAL_KEYS)
        self.assertEqual(
            set(properties["variables_and_units"]["items"]["properties"]),
            manifest.VARIABLE_KEYS,
        )

    def test_public_url_security_boundaries_do_not_drift(self) -> None:
        self.assertEqual(landscape.SENSITIVE_QUERY_KEYS, manifest.SENSITIVE_QUERY)
        self.assertEqual(landscape.LOCAL_HOST_SUFFIXES, manifest.LOCAL_HOST_SUFFIXES)

        unsafe_urls = (
            "https://user:secret@example.invalid/source",
            "https://service.internal/source",
            "https://192.0.2.10/source",
            "https://example.invalid:not-a-port/source",
            "https://example.invalid/source?access_token=synthetic",
            "https://example.invalid/source?authorization=synthetic",
            "https://example.invalid/source?X-Goog-Signature=synthetic",
            "https://example.invalid/source path",
        )
        for url in unsafe_urls:
            with self.subTest(url=url), self.assertRaises(manifest.ManifestError):
                manifest._public_url(url, "synthetic_url")
            with self.subTest(url=url), self.assertRaises(landscape.LandscapeQueryError):
                landscape._validate_authoritative_url(url, path=Path("synthetic.json"))

        safe_url = "https://example.invalid/source?dataset=public"
        self.assertEqual(manifest._public_url(safe_url, "synthetic_url"), safe_url)
        landscape._validate_authoritative_url(safe_url, path=Path("synthetic.json"))

    def test_every_admitted_manifest_has_exact_source_review_reference(self) -> None:
        manifest_paths = {
            f"manifests/{path.name}" for path in (ROOT / "manifests").glob("*.json")
        }
        self.assertTrue(manifest_paths)

        references_by_review: dict[str, set[str]] = {}
        for path in sorted((ROOT / "docs/source-reviews").glob("*.md")):
            if path.name == "README.md":
                continue
            references = set(MANIFEST_REFERENCE_RE.findall(path.read_text(encoding="utf-8")))
            self.assertTrue(references, f"{path} must reference at least one admitted manifest")
            references_by_review[path.name] = references

        referenced_paths = {
            reference
            for references in references_by_review.values()
            for reference in references
        }
        self.assertEqual(referenced_paths, manifest_paths)

        owners: dict[str, list[str]] = {}
        for review_name, references in references_by_review.items():
            for reference in references:
                owners.setdefault(reference, []).append(review_name)
        duplicates = {reference: names for reference, names in owners.items() if len(names) != 1}
        self.assertEqual(duplicates, {}, "each admitted manifest must have exactly one canonical source review")

    def test_source_reviews_echo_canonical_manifest_identity(self) -> None:
        for review_path in sorted((ROOT / "docs/source-reviews").glob("*.md")):
            if review_path.name == "README.md":
                continue
            review_text = review_path.read_text(encoding="utf-8")
            references = set(MANIFEST_REFERENCE_RE.findall(review_text))
            self.assertTrue(references, f"{review_path} must reference an admitted manifest")
            for reference in references:
                manifest_path = ROOT / reference
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                for field in ("provider", "product_name"):
                    value = payload[field]
                    with self.subTest(review=review_path.name, manifest=reference, field=field):
                        self.assertIn(
                            value,
                            review_text,
                            f"{review_path} must echo canonical manifest {field} without inventing a second identity",
                        )

    def test_source_review_readme_index_matches_review_files(self) -> None:
        review_dir = ROOT / "docs/source-reviews"
        expected = {path.name for path in review_dir.glob("*.md") if path.name != "README.md"}
        self.assertTrue(expected)
        readme = (review_dir / "README.md").read_text(encoding="utf-8")
        listed = {name for name in REVIEW_FILENAME_RE.findall(readme) if name != "README.md"}
        self.assertEqual(
            listed,
            expected,
            "docs/source-reviews/README.md must list every canonical source review exactly through its filename",
        )


if __name__ == "__main__":
    unittest.main()
