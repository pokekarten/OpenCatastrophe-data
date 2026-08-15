# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import csv
import hashlib
import io
import unittest
from unittest.mock import patch

from scripts import extract_efehr_kosovo_taxonomy as taxonomy
from scripts import profile_efehr_kosovo_exposure as exposure


def csv_bytes(taxonomies: list[str], *, header: tuple[str, ...] = taxonomy.EXPECTED_HEADER) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, delimiter=",", lineterminator="\n")
    writer.writerow(header)
    for index, value in enumerate(taxonomies):
        row = [f"v{index}-{column}" for column in range(len(header))]
        if taxonomy.TAXONOMY_FIELD in header:
            row[header.index(taxonomy.TAXONOMY_FIELD)] = value
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


class KosovoTaxonomyExtractorTests(unittest.TestCase):
    def test_fingerprint_matches_profiler_contract(self):
        values = {"A", "B/C", " value with spaces "}
        self.assertEqual(taxonomy._value_set_sha256(values), exposure._value_set_sha256(values))

    def test_internal_parser_preserves_exact_values_without_normalization(self):
        raw = csv_bytes([" Z ", "A", "A"])
        text = raw.decode("utf-8")
        expected = {" Z ", "A"}
        result = taxonomy._extract_taxonomy_values(
            text,
            expected_distinct_count=2,
            expected_value_set_sha256=taxonomy._value_set_sha256(expected),
        )
        self.assertEqual(result, [" Z ", "A"])

    def test_internal_parser_requires_exact_trusted_header(self):
        header = list(taxonomy.EXPECTED_HEADER)
        header[2] = "MACRO_TAXONOMY"
        raw = csv_bytes(["A"], header=tuple(header))
        with self.assertRaisesRegex(taxonomy.KosovoTaxonomyError, "header does not match"):
            taxonomy._extract_taxonomy_values(
                raw.decode("utf-8"),
                expected_distinct_count=1,
                expected_value_set_sha256=taxonomy._value_set_sha256({"A"}),
            )

    def test_internal_parser_rejects_empty_taxonomy(self):
        raw = csv_bytes([""])
        with self.assertRaisesRegex(taxonomy.KosovoTaxonomyError, "empty taxonomy"):
            taxonomy._extract_taxonomy_values(
                raw.decode("utf-8"),
                expected_distinct_count=1,
                expected_value_set_sha256=taxonomy._value_set_sha256({"A"}),
            )

    def test_internal_parser_rejects_distinct_count_drift(self):
        raw = csv_bytes(["A", "B"])
        with self.assertRaisesRegex(taxonomy.KosovoTaxonomyError, "distinct count"):
            taxonomy._extract_taxonomy_values(
                raw.decode("utf-8"),
                expected_distinct_count=1,
                expected_value_set_sha256=taxonomy._value_set_sha256({"A", "B"}),
            )

    def test_internal_parser_rejects_fingerprint_drift(self):
        raw = csv_bytes(["A", "B"])
        with self.assertRaisesRegex(taxonomy.KosovoTaxonomyError, "fingerprint"):
            taxonomy._extract_taxonomy_values(
                raw.decode("utf-8"),
                expected_distinct_count=2,
                expected_value_set_sha256="0" * 64,
            )

    def test_internal_parser_rejects_ragged_rows(self):
        text = ",".join(taxonomy.EXPECTED_HEADER) + "\nA,B\n"
        with self.assertRaisesRegex(taxonomy.KosovoTaxonomyError, "ragged row"):
            taxonomy._extract_taxonomy_values(
                text,
                expected_distinct_count=1,
                expected_value_set_sha256=taxonomy._value_set_sha256({"A"}),
            )

    def test_public_worker_rejects_non_bytes_before_parse(self):
        with patch.object(taxonomy, "_extract_taxonomy_values", side_effect=AssertionError("parser ran")):
            with self.assertRaisesRegex(taxonomy.KosovoTaxonomyError, "immutable bytes"):
                taxonomy.extract_verified_kosovo_taxonomy("not bytes")  # type: ignore[arg-type]

    def test_public_worker_rejects_byte_count_before_parse(self):
        with patch.object(taxonomy, "_extract_taxonomy_values", side_effect=AssertionError("parser ran")):
            with self.assertRaisesRegex(taxonomy.KosovoTaxonomyError, "byte count"):
                taxonomy.extract_verified_kosovo_taxonomy(b"not-the-receipted-object")

    def test_public_worker_rejects_digest_before_parse(self):
        wrong = b"x" * exposure.EXPECTED_BYTE_COUNT
        with patch.object(taxonomy, "_extract_taxonomy_values", side_effect=AssertionError("parser ran")):
            with self.assertRaisesRegex(taxonomy.KosovoTaxonomyError, "SHA-256"):
                taxonomy.extract_verified_kosovo_taxonomy(wrong)

    def test_public_worker_success_is_closed_and_exact(self):
        values = [f"TAX-{index:03d}" for index in range(85)] + [" TAX-085 "]
        raw = csv_bytes(values + [values[0]])
        digest = hashlib.sha256(raw).hexdigest()
        value_set = set(values)
        fingerprint = taxonomy._value_set_sha256(value_set)

        with (
            patch.object(exposure, "EXPECTED_BYTE_COUNT", len(raw)),
            patch.object(exposure, "EXPECTED_SHA256", digest),
            patch.object(taxonomy, "EXPECTED_DISTINCT_COUNT", len(value_set)),
            patch.object(taxonomy, "EXPECTED_VALUE_SET_SHA256", fingerprint),
        ):
            result = taxonomy.extract_verified_kosovo_taxonomy(raw)

        self.assertEqual(result["taxonomy_field"], "TAXONOMY")
        self.assertEqual(result["taxonomy_count"], 86)
        self.assertEqual(result["taxonomy_value_set_sha256"], fingerprint)
        self.assertEqual(result["taxonomies"], sorted(value_set))
        self.assertIn(" TAX-085 ", result["taxonomies"])
        self.assertIs(result["normalization_applied"], False)
        self.assertIs(result["raw_rows_returned"], False)
        self.assertIs(result["external_bytes_persisted"], False)
        self.assertIs(result["publication_authorized"], False)

    def test_public_worker_rejects_bom_even_after_receipt_identity(self):
        raw = b"\xef\xbb\xbf" + csv_bytes(["A"])
        with (
            patch.object(exposure, "EXPECTED_BYTE_COUNT", len(raw)),
            patch.object(exposure, "EXPECTED_SHA256", hashlib.sha256(raw).hexdigest()),
            patch.object(taxonomy, "EXPECTED_DISTINCT_COUNT", 1),
            patch.object(taxonomy, "EXPECTED_VALUE_SET_SHA256", taxonomy._value_set_sha256({"A"})),
        ):
            with self.assertRaisesRegex(taxonomy.KosovoTaxonomyError, "BOM"):
                taxonomy.extract_verified_kosovo_taxonomy(raw)


if __name__ == "__main__":
    unittest.main()
