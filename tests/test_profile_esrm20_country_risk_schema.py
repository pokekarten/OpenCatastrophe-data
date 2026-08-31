# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest

from scripts.profile_esrm20_country_risk_schema import (
    CountryRiskSchemaProfileError,
    profile_country_risk_schema_bytes,
)


def _identity(payload: bytes) -> dict[str, object]:
    return {
        "expected_sha256": hashlib.sha256(payload).hexdigest(),
        "expected_byte_count": len(payload),
    }


class CountryRiskSchemaProfileTests(unittest.TestCase):
    def test_profiles_candidate_schema_without_returning_provider_values(self) -> None:
        payload = (
            b'Name,"AAL Residential (economic, M EUR)","AAL Total (economic, M EUR)",'
            b'"AALR Residential (economic, per mille)","AALR Total (economic, per mille)"\n'
            b"Kosovo,12.345,45.678,7.890,9.012\n"
            b"Albania,98.765,87.654,6.543,5.432\n"
        )

        profile = profile_country_risk_schema_bytes(payload, **_identity(payload))

        self.assertEqual(profile["kosovo_row_status"], "unique")
        self.assertEqual(profile["kosovo_name_literals"], ["Kosovo"])
        self.assertTrue(profile["residential_reference_schema_candidate"])
        self.assertFalse(profile["provider_numeric_values_interpreted"])
        self.assertFalse(profile["provider_values_returned"])
        rendered = json.dumps(profile, sort_keys=True)
        self.assertNotIn("12.345", rendered)
        self.assertNotIn("45.678", rendered)
        self.assertFalse(profile["annualized_metrics_authorized"])
        self.assertFalse(profile["threshold_compatibility_verified"])
        self.assertFalse(profile["reference_loss_agreement_verified"])

    def test_missing_hypothesis_fields_is_evidence_not_parse_failure(self) -> None:
        payload = b'Name,"AAL Total (economic, M EUR)"\nKosovo,42\n'

        profile = profile_country_risk_schema_bytes(payload, **_identity(payload))

        self.assertEqual(profile["kosovo_row_status"], "unique")
        self.assertFalse(profile["residential_reference_schema_candidate"])
        self.assertFalse(
            profile["secondary_hypothesis_field_presence"][
                "AAL Residential (economic, M EUR)"
            ]
        )
        self.assertFalse(
            profile["secondary_hypothesis_field_presence"][
                "AALR Residential (economic, per mille)"
            ]
        )

    def test_predeclared_kosovo_alias_is_exact_not_normalized(self) -> None:
        payload = b"Name,Metric\nRepublic of Kosovo,1\n kosovo ,2\n"

        profile = profile_country_risk_schema_bytes(payload, **_identity(payload))

        self.assertEqual(profile["kosovo_row_count"], 1)
        self.assertEqual(profile["kosovo_name_literals"], ["Republic of Kosovo"])
        self.assertEqual(profile["kosovo_row_status"], "unique")

    def test_multiple_predeclared_kosovo_alias_rows_are_ambiguous(self) -> None:
        payload = (
            b'Name,"AAL Residential (economic, M EUR)",'
            b'"AALR Residential (economic, per mille)"\n'
            b"Kosovo,1,2\n"
            b"Kosova,3,4\n"
        )

        profile = profile_country_risk_schema_bytes(payload, **_identity(payload))

        self.assertEqual(profile["kosovo_row_count"], 2)
        self.assertEqual(profile["kosovo_row_status"], "ambiguous")
        self.assertFalse(profile["residential_reference_schema_candidate"])

    def test_name_column_absence_is_structural_evidence(self) -> None:
        payload = b"Country,Metric\nKosovo,1\n"

        profile = profile_country_risk_schema_bytes(payload, **_identity(payload))

        self.assertFalse(profile["name_column_present"])
        self.assertEqual(profile["kosovo_row_status"], "name_column_absent")
        self.assertFalse(profile["residential_reference_schema_candidate"])

    def test_sha256_mismatch_fails_closed(self) -> None:
        payload = b"Name,Metric\nKosovo,1\n"
        identity = _identity(payload)
        identity["expected_sha256"] = "0" * 64

        with self.assertRaisesRegex(CountryRiskSchemaProfileError, "SHA-256"):
            profile_country_risk_schema_bytes(payload, **identity)

    def test_byte_count_mismatch_fails_closed(self) -> None:
        payload = b"Name,Metric\nKosovo,1\n"
        identity = _identity(payload)
        identity["expected_byte_count"] = len(payload) + 1

        with self.assertRaisesRegex(CountryRiskSchemaProfileError, "byte count"):
            profile_country_risk_schema_bytes(payload, **identity)

    def test_casefold_duplicate_headers_fail_closed(self) -> None:
        payload = b"Name,name\nKosovo,1\n"

        with self.assertRaisesRegex(CountryRiskSchemaProfileError, "delimiter"):
            profile_country_risk_schema_bytes(payload, **_identity(payload))

    def test_ragged_csv_fails_closed(self) -> None:
        payload = b"Name,Metric\nKosovo,1,2\n"

        with self.assertRaisesRegex(CountryRiskSchemaProfileError, "delimiter"):
            profile_country_risk_schema_bytes(payload, **_identity(payload))

    def test_nul_and_non_utf8_fail_closed(self) -> None:
        for payload in (
            b"Name,Metric\nKosovo,\x00\n",
            b"Name,Metric\nKosovo,\xff\n",
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(CountryRiskSchemaProfileError):
                    profile_country_risk_schema_bytes(payload, **_identity(payload))


if __name__ == "__main__":
    unittest.main()
