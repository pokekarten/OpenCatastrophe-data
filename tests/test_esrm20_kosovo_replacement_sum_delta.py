# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest
from unittest import mock
from decimal import Decimal

from research_runners import esrm20_kosovo_replacement_sum_delta as subject


def _row(index: int, *, source: str, runtime: str):
    key = {
        "LONGITUDE": f"20.{index}",
        "LATITUDE": f"42.{index}",
        "TAXONOMY": f"PRIVATE-SYNTHETIC-TYPE-{index}",
        "OCCUPANCY": "RES",
        "NAME_2": "PRIVATE-SYNTHETIC-CITY",
        "ID_2": str(index),
        "ID_1": "1",
        "NAME_1": "PRIVATE-SYNTHETIC-REGION",
    }
    left = dict(key)
    left[subject.SOURCE_FIELD] = source
    right = {
        right: key[left] for left, right in subject.compare.KEY_FIELD_PAIRS
    }
    right[subject.RUNTIME_FIELD] = runtime
    return left, right


def _existing_profile(records: int, *, non_equal: int, max_diff: str):
    return {
        "schema_version": subject.compare.SCHEMA_VERSION,
        "record_count": records,
        "canonical_receipt_pair_verified": False,
        "source_identity": {"sha256": "a" * 64},
        "runtime_identity": {"sha256": "b" * 64},
        "comparison_key": {
            "exact_key_set_equal": True,
            "key_set_sha256": "c" * 64,
        },
        "numeric_comparisons": [{
            "source_field": subject.SOURCE_FIELD,
            "runtime_field": subject.RUNTIME_FIELD,
            "record_count": records,
            "exact_decimal_equal_count": records - non_equal,
            "non_equal_count": non_equal,
            "maximum_absolute_difference": max_diff,
        }],
        "raw_rows_returned": False,
        "external_bytes_persisted": False,
        "model_use_authorized": False,
        "publication_authorized": False,
    }


class KosovoNationalSumBridgeTests(unittest.TestCase):
    def test_source_minus_runtime_delta_is_exact_and_bounded(self):
        pairs = [
            _row(0, source="1.0000000001", runtime="1"),
            _row(1, source="2.00000000003", runtime="2"),
            _row(2, source="3.0", runtime="3.00000000004"),
        ]
        left = [p[0] for p in pairs]
        right = [p[1] for p in pairs]
        self.assertEqual(
            subject._signed_delta(left, right), Decimal("0.00000000009")
        )
        with mock.patch.object(
            subject.compare, "compare_verified_exposure_bytes",
            return_value=_existing_profile(3, non_equal=3, max_diff="0.0000000001"),
        ), mock.patch.object(
            subject.compare, "_parse_verified_rows", side_effect=[left, right],
        ):
            result = subject.analyze_verified_bytes(b"synthetic-a", b"synthetic-b")
        self.assertEqual(
            result["national_cost_signed_source_minus_runtime_eur"],
            "0.00000000009",
        )
        self.assertEqual(result["asset_cost_non_equal_count"], 3)
        self.assertFalse(result["national_cost_exact_sums_equal"])
        self.assertFalse(result["canonical_receipt_pair_verified"])
        for flag in (
            "source_or_runtime_national_cost_sum_returned",
            "individual_provider_values_returned",
            "external_bytes_persisted",
            "exact_source_to_runtime_transform_verified",
            "published_residential_aalr_denominator_verified",
            "published_reference_loss_agreement_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[flag], False, flag)
        serialized = json.dumps(result)
        self.assertNotIn("PRIVATE-SYNTHETIC", serialized)
        self.assertNotIn("synthetic-a", serialized)
        self.assertNotIn("synthetic-b", serialized)

    def test_cancelled_row_differences_keep_sum_exact_but_rows_non_equal(self):
        a, b = _row(0, source="1.01", runtime="1")
        c, d = _row(1, source="2", runtime="2.01")
        delta = subject._signed_delta([a, c], [d, b])
        self.assertEqual(delta, Decimal("0"))

    def test_key_set_drift_blocks_before_total(self):
        a, b = _row(0, source="1", runtime="1")
        _, other = _row(1, source="1", runtime="1")
        with self.assertRaisesRegex(
            subject.ReplacementSumBridgeError, "keysets"
        ):
            subject._signed_delta([a], [other])

    def test_duplicate_key_fails_without_provider_row_output(self):
        a, b = _row(0, source="1", runtime="1")
        with self.assertRaisesRegex(
            subject.compare.ExposureRuntimeComparisonError, "not unique"
        ):
            subject._signed_delta([a, a], [b, b])

    def test_rounding_context_and_malformed_cost_fail_closed(self):
        a, b = _row(0, source="1", runtime="Infinity")
        with self.assertRaisesRegex(subject.ReplacementSumBridgeError, "exactly"):
            subject._signed_delta([a], [b])

    def test_aggregate_outside_row_bound_fails_closed(self):
        a, b = _row(0, source="1.1", runtime="1")
        with mock.patch.object(
            subject.compare, "compare_verified_exposure_bytes",
            return_value=_existing_profile(1, non_equal=1, max_diff="0.01"),
        ), mock.patch.object(
            subject.compare, "_parse_verified_rows", side_effect=[[a], [b]],
        ):
            with self.assertRaisesRegex(
                subject.ReplacementSumBridgeError, "bound"
            ):
                subject.analyze_verified_bytes(b"synthetic-a", b"synthetic-b")

    def test_existing_comparison_scientific_authority_cannot_widen(self):
        a, b = _row(0, source="1", runtime="1")
        old = _existing_profile(1, non_equal=0, max_diff="0")
        old["model_use_authorized"] = True
        with mock.patch.object(
            subject.compare, "compare_verified_exposure_bytes", return_value=old
        ), mock.patch.object(
            subject.compare, "_parse_verified_rows"
        ) as parser:
            with self.assertRaisesRegex(
                subject.ReplacementSumBridgeError, "authority"
            ):
                subject.analyze_verified_bytes(b"a", b"b")
            parser.assert_not_called()

    def test_trusted_run_requires_canonical_pair(self):
        with mock.patch.object(
            subject.compare, "_fetch_fixed_payload", side_effect=[b"src", b"runtime"]
        ) as fetch, mock.patch.object(
            subject, "analyze_verified_bytes",
            return_value={"canonical_receipt_pair_verified": False},
        ):
            with self.assertRaisesRegex(
                subject.ReplacementSumBridgeError, "canonical source"
            ):
                subject.run()
            self.assertEqual(fetch.call_count, 2)


if __name__ == "__main__":
    unittest.main()
