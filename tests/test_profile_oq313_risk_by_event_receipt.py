# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import struct
import tempfile
from pathlib import Path
import unittest

from scripts import profile_oq313_risk_by_event_receipt as profiler
from scripts import project_oq313_risk_by_event_receipt as projector


def _f32_hex(value: float) -> str:
    return struct.pack("!f", value).hex()


def _receipt() -> bytes:
    rows = [
        {
            "event_id": 4,
            "rup_id": 20,
            "rlz_id": 1,
            "loss_f32_be_hex": _f32_hex(40.0),
            "variance_f32_be_hex": _f32_hex(4.0),
        },
        {
            "event_id": 1,
            "rup_id": 10,
            "rlz_id": 0,
            "loss_f32_be_hex": _f32_hex(10.0),
            "variance_f32_be_hex": _f32_hex(1.0),
        },
        {
            "event_id": 3,
            "rup_id": 20,
            "rlz_id": 1,
            "loss_f32_be_hex": _f32_hex(30.0),
            "variance_f32_be_hex": _f32_hex(3.0),
        },
        {
            "event_id": 2,
            "rup_id": 10,
            "rlz_id": 0,
            "loss_f32_be_hex": _f32_hex(20.0),
            "variance_f32_be_hex": _f32_hex(2.0),
        },
    ]
    payload, _ = projector.project_oq313_risk_by_event_receipt(
        rows,
        portfolio_agg_id=7,
        structural_loss_id=0,
        concurrent_tasks=1,
    )
    return payload


class OQ313RiskByEventProfileTests(unittest.TestCase):
    def test_profile_binds_source_and_describes_empirical_rows(self) -> None:
        payload = _receipt()
        result = profiler.profile_receipt(payload)

        self.assertEqual(result["schema_version"], profiler.SCHEMA_VERSION)
        self.assertEqual(result["row_count"], 4)
        self.assertEqual(result["event_id_range"], {"minimum": 1, "maximum": 4})
        self.assertEqual(result["distinct_rup_id_count"], 2)
        self.assertEqual(result["distinct_rlz_id_count"], 2)
        self.assertEqual(
            result["rows_by_rlz_id"],
            [{"rlz_id": 0, "row_count": 2}, {"rlz_id": 1, "row_count": 2}],
        )
        self.assertEqual(
            result["source_receipt"]["identity"],
            {
                "byte_count": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            },
        )
        self.assertEqual(
            result["profile_basis"],
            "empirical_selected_event_rows_without_occurrence_weights",
        )

    def test_profile_preserves_float32_identity_and_exact_binary_sums(self) -> None:
        result = profiler.profile_receipt(_receipt())

        self.assertEqual(result["loss"]["minimum_row"]["event_id"], 1)
        self.assertEqual(result["loss"]["minimum_row"]["loss_f32_be_hex"], _f32_hex(10.0))
        self.assertEqual(result["loss"]["maximum_row"]["event_id"], 4)
        self.assertEqual(result["loss"]["maximum_row"]["loss_f32_be_hex"], _f32_hex(40.0))
        self.assertEqual(result["loss"]["top_loss_rows"][0]["event_id"], 4)
        self.assertEqual(
            result["loss"]["exact_sum_binary"],
            {"coefficient": "25", "binary_exponent": 2, "approx_decimal": "100"},
        )
        self.assertEqual(
            result["variance"]["exact_sum_binary"],
            {"coefficient": "5", "binary_exponent": 1, "approx_decimal": "10"},
        )

    def test_empirical_nearest_ranks_are_predeclared_and_nonannualized(self) -> None:
        result = profiler.profile_receipt(_receipt())
        ranks = {
            entry["label"]: (entry["rank_1_based"], entry["row"]["event_id"])
            for entry in result["loss"]["empirical_nearest_ranks"]
        }
        self.assertEqual(ranks["p50"], (2, 2))
        for label in ("p90", "p95", "p99", "p995", "p999"):
            self.assertEqual(ranks[label], (4, 4))

        for field in (
            "annualized_metrics_authorized",
            "aal_authorized",
            "oep_authorized",
            "aep_authorized",
            "historical_reproduction_verified",
            "numerical_reference_loss_verified",
            "scientific_validity_verified",
            "publication_authorized",
            "model_use_authorized",
        ):
            self.assertIs(result[field], False)

    def test_current_eq1_validator_rejects_semantic_receipt_drift(self) -> None:
        document = json.loads(_receipt().decode("utf-8"))
        document["openquake"]["version"] = "9.9.9"
        payload = (
            json.dumps(document, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
            + "\n"
        ).encode("utf-8")
        with self.assertRaises(profiler.OQ313RiskByEventProfileError):
            profiler.profile_receipt(payload)

    def test_file_path_is_offline_and_rejects_symlinks(self) -> None:
        payload = _receipt()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = root / "receipt.json"
            receipt.write_bytes(payload)
            result = profiler.profile_receipt_file(receipt)
            self.assertEqual(result["row_count"], 4)

            link = root / "receipt-link.json"
            link.symlink_to(receipt)
            with self.assertRaises(profiler.OQ313RiskByEventProfileError):
                profiler.profile_receipt_file(link)


if __name__ == "__main__":
    unittest.main()
