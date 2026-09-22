# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import csv
import hashlib
import io
import json
import unittest
from decimal import Decimal

from research_runners import esrm20_kosovo_aalr_denominator as subject


def _country_bytes(*, aal: str = "2.0", aalr: str = "1.0") -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        [
            subject.NAME_HEADER,
            subject.AAL_HEADER,
            subject.AALR_HEADER,
        ]
    )
    writer.writerow(["Albania", "1.0", "0.5"])
    writer.writerow([subject.KOSOVO_LITERAL, aal, aalr])
    return stream.getvalue().encode("utf-8")


class KosovoAalrDenominatorTests(unittest.TestCase):
    def test_exact_residential_denominator_is_compatible(self) -> None:
        result = subject.build_result(
            aal_m_eur=Decimal("2.0"),
            aalr_per_mille=Decimal("1.0"),
            residential_replacement_cost_eur=Decimal("2000000000"),
        )
        self.assertTrue(
            result["nearest_decimal_display_rounding_hypothesis"][
                "compatible_with_residential_replacement_cost"
            ]
        )
        self.assertEqual(
            result["conclusion"],
            "RESIDENTIAL_DENOMINATOR_NUMERICALLY_COMPATIBLE_UNDER_DISPLAY_ROUNDING_HYPOTHESIS",
        )
        self.assertEqual(result["implied_denominator_relative_difference_ppm"], "0")
        self.assertFalse(result["denominator_semantics_verified"])
        self.assertFalse(result["reference_loss_agreement_verified"])

    def test_wrong_residential_denominator_is_incompatible(self) -> None:
        result = subject.build_result(
            aal_m_eur=Decimal("2.0"),
            aalr_per_mille=Decimal("1.0"),
            residential_replacement_cost_eur=Decimal("1000000000"),
        )
        self.assertFalse(
            result["nearest_decimal_display_rounding_hypothesis"][
                "compatible_with_residential_replacement_cost"
            ]
        )
        self.assertEqual(
            result["conclusion"],
            "RESIDENTIAL_DENOMINATOR_NUMERICALLY_INCOMPATIBLE_UNDER_DISPLAY_ROUNDING_HYPOTHESIS",
        )

    def test_extract_reads_only_unique_kosovo_residential_literals(self) -> None:
        raw = _country_bytes(aal="3.25", aalr="0.75")
        aal, aalr = subject._extract_kosovo_residential_literals(
            raw,
            expected_byte_count=len(raw),
            expected_sha256=hashlib.sha256(raw).hexdigest(),
        )
        self.assertEqual(aal, Decimal("3.25"))
        self.assertEqual(aalr, Decimal("0.75"))

    def test_ambiguous_kosovo_fails_closed(self) -> None:
        raw = _country_bytes()
        text = raw.decode("utf-8")
        raw = (text + text.splitlines()[-1] + "\n").encode("utf-8")
        with self.assertRaisesRegex(
            subject.DenominatorDiagnosticError,
            "Kosovo row is not unique",
        ):
            subject._extract_kosovo_residential_literals(
                raw,
                expected_byte_count=len(raw),
                expected_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_result_does_not_return_provider_literals_or_denominator(self) -> None:
        result = subject.build_result(
            aal_m_eur=Decimal("7.123456"),
            aalr_per_mille=Decimal("0.987654"),
            residential_replacement_cost_eur=Decimal("7654321098"),
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("7.123456", encoded)
        self.assertNotIn("0.987654", encoded)
        self.assertNotIn("7654321098", encoded)
        self.assertNotIn("aal_m_eur", result)
        self.assertNotIn("aalr_per_mille", result)
        self.assertNotIn("residential_replacement_cost_eur", result)
        self.assertTrue(result["published_numeric_values_interpreted"])
        self.assertFalse(result["published_numeric_values_returned"])
        self.assertFalse(result["external_bytes_persisted"])

    def test_nonpositive_values_fail_closed(self) -> None:
        with self.assertRaises(subject.DenominatorDiagnosticError):
            subject.build_result(
                aal_m_eur=Decimal("2"),
                aalr_per_mille=Decimal("1"),
                residential_replacement_cost_eur=Decimal("0"),
            )


if __name__ == "__main__":
    unittest.main()
