# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Keep acquisition-history prose distinct from current admission/publication state."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "manifests"

_NEGATED_ACQUISITION = re.compile(
    r"(?:"
    r"\bno\b[^.]{0,180}\b(?:selected|acquired|hashed)\b"
    r"|\b(?:bytes?|files?|artifacts?|assets?|workbooks?|downloads?|responses?|requests?|snapshots?|tiles?|scenes?)\b"
    r"[^.]{0,100}\b(?:was|were|has|have|had)\s+not\b[^.]{0,60}\b(?:selected|acquired|hashed)\b"
    r")",
    re.IGNORECASE,
)
_REVIEW_TIME_ANCHOR = re.compile(
    r"\b(?:at (?:the|this) (?:manifest |source )?review time|as of (?:the|this) review|during (?:the|this) review|by (?:the|this) review|for (?:the|this) review|review-time)\b",
    re.IGNORECASE,
)
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])(?:\s+|$)|\n+")


def _strings(value: object, path: str = "") -> list[tuple[str, str]]:
    if isinstance(value, dict):
        out: list[tuple[str, str]] = []
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            out.extend(_strings(child, child_path))
        return out
    if isinstance(value, list):
        out = []
        for index, child in enumerate(value):
            out.extend(_strings(child, f"{path}[{index}]"))
        return out
    return [(path, value)] if isinstance(value, str) else []


def _unanchored_negated_acquisition(text: str) -> list[str]:
    """Return negated acquisition sentences that lack their own review-time anchor."""

    failures: list[str] = []
    for sentence in _SENTENCE_BOUNDARY.split(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        if _NEGATED_ACQUISITION.search(sentence) and not _REVIEW_TIME_ANCHOR.search(sentence):
            failures.append(sentence)
    return failures


class ManifestTemporalNarrativeTests(unittest.TestCase):
    def test_review_time_anchor_must_scope_the_same_sentence(self) -> None:
        """An unrelated historical sentence must not sanitize a live acquisition claim."""

        stale_examples = (
            "At the manifest review time, metadata was checked. No bytes have been acquired.",
            "No bytes have been acquired. At the manifest review time, metadata was checked.",
        )
        for text in stale_examples:
            with self.subTest(text=text):
                self.assertEqual(_unanchored_negated_acquisition(text), ["No bytes have been acquired."])

        self.assertEqual(
            _unanchored_negated_acquisition(
                "At the manifest review time, no exact provider bytes had been acquired."
            ),
            [],
        )

    def test_durable_admission_narrative_time_qualifies_negated_acquisition_state(self) -> None:
        """Current publication state must not be conflated with historical byte acquisition state."""

        failures: list[str] = []
        for manifest_path in sorted(MANIFESTS.glob("*.json")):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            # retrieval_query_or_filters is inherently a record of the retrieval/review operation.
            # The drift risk is durable admission/review prose that reads like a live dashboard.
            for path, text in _strings({
                "redistribution": manifest.get("redistribution", {}),
                "review": manifest.get("review", {}),
            }):
                for statement in _unanchored_negated_acquisition(text):
                    failures.append(f"{manifest_path.name}:{path}: {statement}")

        self.assertEqual(
            failures,
            [],
            "Negated acquisition/selection/hash statements in durable manifest narrative must be explicitly review-time scoped:\n"
            + "\n".join(failures),
        )

    def test_source_review_acquisition_history_is_time_qualified(self) -> None:
        failures: list[str] = []
        for review_path in sorted((ROOT / "docs" / "source-reviews").glob("*.md")):
            for line_number, line in enumerate(review_path.read_text(encoding="utf-8").splitlines(), 1):
                for statement in _unanchored_negated_acquisition(line):
                    failures.append(f"{review_path.name}:{line_number}: {statement}")
        self.assertEqual(
            failures,
            [],
            "Negated acquisition/selection/hash statements in source reviews must be explicitly review-time scoped:\n"
            + "\n".join(failures),
        )


if __name__ == "__main__":
    unittest.main()
