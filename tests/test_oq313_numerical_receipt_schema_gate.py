# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import unittest
from collections.abc import Callable
from typing import Any

from scripts import project_oq313_risk_by_event_receipt as numerical_contract
from scripts import run_esrm20_kosovo_residential_ebrisk_openquake313_action as subject


def _valid_payload() -> tuple[bytes, dict[str, object]]:
    return numerical_contract.project_oq313_risk_by_event_receipt(
        [
            {
                "event_id": 7,
                "rup_id": 11,
                "loss_f32_be_hex": "3f800000",
                "variance_f32_be_hex": "00000000",
            }
        ],
        portfolio_agg_id=3,
        structural_loss_id=0,
        concurrent_tasks=2,
    )


def _mutate(
    payload: bytes,
    mutation: Callable[[dict[str, Any]], None],
) -> tuple[bytes, dict[str, object]]:
    document = json.loads(payload)
    mutation(document)
    mutated = (
        json.dumps(
            document,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    return mutated, {
        "byte_count": len(mutated),
        "sha256": hashlib.sha256(mutated).hexdigest(),
    }


class OQ313NumericalReceiptSchemaGateTests(unittest.TestCase):
    def test_exact_projector_payload_passes(self) -> None:
        payload, identity = _valid_payload()
        document, observed_identity = subject._validate_numerical_receipt(
            payload,
            identity,
            expected_concurrent_tasks=2,
        )
        self.assertEqual(document["quantity"]["unit"], "EUR")
        self.assertEqual(observed_identity, identity)

    def test_extra_top_level_field_fails_closed(self) -> None:
        payload, _ = _valid_payload()
        mutated, identity = _mutate(
            payload,
            lambda doc: doc.__setitem__("raw", "forbidden"),
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "top-level fields drifted",
        ):
            subject._validate_numerical_receipt(
                mutated,
                identity,
                expected_concurrent_tasks=2,
            )

    def test_extra_nested_field_fails_closed(self) -> None:
        payload, _ = _valid_payload()
        mutated, identity = _mutate(
            payload,
            lambda doc: doc["runtime"].__setitem__("worker_detail", "forbidden"),
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "runtime fields drifted",
        ):
            subject._validate_numerical_receipt(
                mutated,
                identity,
                expected_concurrent_tasks=2,
            )

    def test_quantity_unit_drift_fails_closed(self) -> None:
        payload, _ = _valid_payload()
        mutated, identity = _mutate(
            payload,
            lambda doc: doc["quantity"].__setitem__("unit", "USD"),
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "reviewed projector contract",
        ):
            subject._validate_numerical_receipt(
                mutated,
                identity,
                expected_concurrent_tasks=2,
            )

    def test_threshold_predicate_drift_fails_closed(self) -> None:
        payload, _ = _valid_payload()
        mutated, identity = _mutate(
            payload,
            lambda doc: doc["quantity"].__setitem__(
                "threshold_predicate",
                "asset_event_loss >= minimum_asset_loss_structural",
            ),
        )
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "canonical projector contract drifted",
        ):
            subject._validate_numerical_receipt(
                mutated,
                identity,
                expected_concurrent_tasks=2,
            )

    def test_concurrent_tasks_must_match_adapter_runtime(self) -> None:
        payload, identity = _valid_payload()
        with self.assertRaisesRegex(
            subject.KosovoResidentialOQ313ActionError,
            "concurrent_tasks drifted from adapter runtime",
        ):
            subject._validate_numerical_receipt(
                payload,
                identity,
                expected_concurrent_tasks=3,
            )


if __name__ == "__main__":
    unittest.main()
