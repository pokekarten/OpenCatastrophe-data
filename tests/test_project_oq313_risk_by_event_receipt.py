# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import unittest

from scripts import project_oq313_risk_by_event_receipt as subject


def row(
    event_id: object = 2,
    rup_id: object = 20,
    loss_hex: object = "461c4000",
    variance_hex: object = "80000000",
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "rup_id": rup_id,
        "loss_f32_be_hex": loss_hex,
        "variance_f32_be_hex": variance_hex,
    }


class ProjectOQ313RiskByEventReceiptTests(unittest.TestCase):
    def test_projection_is_deterministic_and_preserves_binary32_identity(self) -> None:
        rows = [
            row(event_id=2, rup_id=22, loss_hex="461c4000", variance_hex="80000000"),
            row(event_id=1, rup_id=11, loss_hex="45fa0000", variance_hex="00000000"),
        ]
        payload_a, identity_a = subject.project_oq313_risk_by_event_receipt(
            rows,
            portfolio_agg_id=7,
            structural_loss_id=3,
            concurrent_tasks=4,
        )
        payload_b, identity_b = subject.project_oq313_risk_by_event_receipt(
            list(reversed(rows)),
            portfolio_agg_id=7,
            structural_loss_id=3,
            concurrent_tasks=4,
        )
        self.assertEqual(payload_a, payload_b)
        self.assertEqual(identity_a, identity_b)
        self.assertEqual(identity_a["byte_count"], len(payload_a))
        self.assertEqual(len(identity_a["sha256"]), 64)
        self.assertTrue(payload_a.endswith(b"\n"))

        document = json.loads(payload_a)
        self.assertEqual(document["schema_version"], subject.SCHEMA_VERSION)
        self.assertEqual(document["source_dataset"], "risk_by_event")
        self.assertEqual(document["experiment_label"], "reconstructed_experiment")
        self.assertEqual(document["insurance_scope"], "none")
        self.assertEqual(document["openquake"]["version"], "3.13.0")
        self.assertEqual(
            document["openquake"]["commit_sha"], subject.OPENQUAKE_COMMIT_SHA
        )
        self.assertEqual(
            document["quantity"],
            {
                "loss_type": "structural",
                "minimum_asset_loss_structural": 2000,
                "name": "thresholded_ground_up_structural_replacement_cost_loss",
                "threshold_predicate": (
                    "asset_event_loss > minimum_asset_loss_structural"
                ),
                "unit": "EUR",
            },
        )
        self.assertEqual(
            document["selection"],
            {"portfolio_agg_id": 7, "structural_loss_id": 3},
        )
        self.assertEqual(document["runtime"], {"concurrent_tasks": 4})
        self.assertEqual([item["event_id"] for item in document["rows"]], [1, 2])
        self.assertEqual(document["rows"][1]["loss_f32_be_hex"], "461c4000")
        self.assertEqual(document["rows"][1]["variance_f32_be_hex"], "80000000")

    def test_empty_or_non_sequence_rows_fail_closed(self) -> None:
        for rows in ([], (), "not rows", b"not rows", bytearray(b"not rows")):
            with self.subTest(rows=type(rows).__name__):
                with self.assertRaises(subject.OQ313RiskByEventReceiptError):
                    subject.project_oq313_risk_by_event_receipt(
                        rows,  # type: ignore[arg-type]
                        portfolio_agg_id=0,
                        structural_loss_id=0,
                        concurrent_tasks=1,
                    )

    def test_non_mapping_and_unexpected_row_fields_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            subject.OQ313RiskByEventReceiptError, "^row 0 must be a mapping$"
        ):
            subject.project_oq313_risk_by_event_receipt(
                [1],  # type: ignore[list-item]
                portfolio_agg_id=0,
                structural_loss_id=0,
                concurrent_tasks=1,
            )
        extra = row()
        extra["ins_loss"] = "461c4000"
        with self.assertRaisesRegex(
            subject.OQ313RiskByEventReceiptError, "^row 0 fields must be exactly "
        ):
            subject.project_oq313_risk_by_event_receipt(
                [extra],
                portfolio_agg_id=0,
                structural_loss_id=0,
                concurrent_tasks=1,
            )

    def test_duplicate_events_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            subject.OQ313RiskByEventReceiptError, "^event_id values must be unique$"
        ):
            subject.project_oq313_risk_by_event_receipt(
                [row(event_id=1), row(event_id=1, rup_id=21)],
                portfolio_agg_id=0,
                structural_loss_id=0,
                concurrent_tasks=1,
            )

    def test_integer_identifiers_are_strict_and_bounded(self) -> None:
        cases = (
            (True, 0, 1, "portfolio_agg_id"),
            (1 << 32, 0, 1, "portfolio_agg_id"),
            (0, True, 1, "structural_loss_id"),
            (0, 256, 1, "structural_loss_id"),
            (0, 0, True, "concurrent_tasks"),
            (0, 0, 0, "concurrent_tasks"),
        )
        for agg_id, loss_id, tasks, message in cases:
            with self.subTest(message=message, value=(agg_id, loss_id, tasks)):
                with self.assertRaisesRegex(
                    subject.OQ313RiskByEventReceiptError, message
                ):
                    subject.project_oq313_risk_by_event_receipt(
                        [row()],
                        portfolio_agg_id=agg_id,  # type: ignore[arg-type]
                        structural_loss_id=loss_id,  # type: ignore[arg-type]
                        concurrent_tasks=tasks,  # type: ignore[arg-type]
                    )

        for field, value in (
            ("event_id", True),
            ("event_id", -1),
            ("event_id", 1 << 32),
            ("rup_id", True),
            ("rup_id", -1),
            ("rup_id", 1 << 32),
        ):
            candidate = row()
            candidate[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(
                    subject.OQ313RiskByEventReceiptError, field
                ):
                    subject.project_oq313_risk_by_event_receipt(
                        [candidate],
                        portfolio_agg_id=0,
                        structural_loss_id=0,
                        concurrent_tasks=1,
                    )

    def test_binary32_hex_is_strict_finite_and_non_negative(self) -> None:
        invalid_values = (
            1.0,
            "ABCDEF12",
            "123",
            "gggggggg",
            "7f800000",
            "ff800000",
            "7fc00000",
            "bf800000",
        )
        for field in ("loss_f32_be_hex", "variance_f32_be_hex"):
            for value in invalid_values:
                candidate = row()
                candidate[field] = value
                with self.subTest(field=field, value=value):
                    with self.assertRaisesRegex(
                        subject.OQ313RiskByEventReceiptError, field
                    ):
                        subject.project_oq313_risk_by_event_receipt(
                            [candidate],
                            portfolio_agg_id=0,
                            structural_loss_id=0,
                            concurrent_tasks=1,
                        )

    def test_scope_is_fixed_and_insurance_is_forbidden(self) -> None:
        cases = (
            {"loss_type": "occupants"},
            {"unit": "USD"},
            {"minimum_asset_loss_structural": True},
            {"minimum_asset_loss_structural": 0},
            {"experiment_label": "benchmark_reproduction"},
            {"policy_present": 1},
            {"insured_loss_present": 0},
            {"policy_present": True},
            {"insured_loss_present": True},
        )
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(subject.OQ313RiskByEventReceiptError):
                    subject.project_oq313_risk_by_event_receipt(
                        [row()],
                        portfolio_agg_id=0,
                        structural_loss_id=0,
                        concurrent_tasks=1,
                        **kwargs,  # type: ignore[arg-type]
                    )


if __name__ == "__main__":
    unittest.main()
