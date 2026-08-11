# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Regression tests for canonical HTTPS scheme parity in dataset manifests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts import validate_manifest as vm

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/dataset-manifest.schema.json"


class ManifestHttpsSchemeParityTests(unittest.TestCase):
    def test_validator_requires_canonical_lowercase_https_scheme(self) -> None:
        self.assertEqual(
            vm._public_url("https://example.org/source", "canonical_source"),
            "https://example.org/source",
        )
        for value in (
            "HTTPS://example.org/source",
            "Https://example.org/source",
            "hTtPs://example.org/source",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(
                vm.ManifestError,
                "absolute HTTPS URL",
            ):
                vm._public_url(value, "canonical_source")

    def test_schema_and_validator_share_lowercase_https_boundary(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        patterns = (
            schema["properties"]["canonical_source"]["pattern"],
            schema["properties"]["licensing"]["properties"]["terms_reference"]["pattern"],
        )
        for pattern in patterns:
            self.assertIsNotNone(re.match(pattern, "https://example.org/source"))
            for value in (
                "http://example.org/source",
                "HTTPS://example.org/source",
                "Https://example.org/source",
            ):
                with self.subTest(pattern=pattern, value=value):
                    self.assertIsNone(re.match(pattern, value))


if __name__ == "__main__":
    unittest.main()
