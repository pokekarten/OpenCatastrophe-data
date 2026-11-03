# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""No-network synthetic tests for the OpenQuake event-loss consumer handoff."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from scripts import project_oq313_event_loss_handoff_v0 as handoff
from scripts import project_oq313_risk_by_event_receipt as canonical


def event(event_id: int, loss: str = "42c80000") -> dict[str, object]:
    return {
        "event_id": event_id,
        "rup_id": 100 + event_id,
        "rlz_id": event_id % 2,
        "loss_f32_be_hex": loss,
        "variance_f32_be_hex": "00000000",
    }


def fake_receipt(order=(2, 1, 3)):
    return canonical.project_oq313_risk_by_event_receipt(
        [event(i) for i in order],
        portfolio_agg_id=0,
        structural_loss_id=0,
        concurrent_tasks=1,
    )


class EventLossHandoffTests(unittest.TestCase):
    def test_exact_f32_bits_identity_and_scoped_event_id(self):
        payload, identity = fake_receipt()
        jsonl, manifest_bytes = handoff.project_event_loss_handoff(
            payload, expected_receipt_sha256=identity["sha256"],
        )
        rows = [json.loads(line) for line in jsonl.splitlines()]
        manifest = json.loads(manifest_bytes)
        self.assertEqual([item["event_id"] for item in rows], [1, 2, 3])
        self.assertEqual(rows[0]["loss_f32_be_hex"], "42c80000")
        self.assertEqual(rows[0]["variance_f32_be_hex"], "00000000")
        self.assertEqual(
            set(rows[0]),
            {"event_id", "rup_id", "rlz_id", "loss_f32_be_hex", "variance_f32_be_hex"},
        )
        self.assertEqual(manifest["source"]["receipt_sha256"], identity["sha256"])
        self.assertEqual(manifest["source"]["receipt_byte_count"], len(payload))
        self.assertEqual(manifest["source"]["openquake"]["version"], "3.13.0")
        self.assertEqual(manifest["output"]["row_count"], 3)
        self.assertEqual(manifest["output"]["sha256"], hashlib.sha256(jsonl).hexdigest())
        self.assertEqual(manifest["output"]["byte_count"], len(jsonl))
        self.assertEqual(manifest["output"]["row_id_scope"], "source_receipt_sha256_plus_event_id")

    def test_reversed_input_has_same_canonical_output(self):
        a, aid = fake_receipt((1, 3, 2))
        b, bid = fake_receipt((3, 2, 1))
        self.assertEqual(aid, bid)
        self.assertEqual(
            handoff.project_event_loss_handoff(a, expected_receipt_sha256=aid["sha256"]),
            handoff.project_event_loss_handoff(b, expected_receipt_sha256=bid["sha256"]),
        )

    def test_wrong_sha_and_wrong_checksum_syntax_rejected(self):
        payload, identity = fake_receipt()
        with self.assertRaisesRegex(handoff.EventLossHandoffError, "differs"):
            handoff.project_event_loss_handoff(
                payload, expected_receipt_sha256="a" * 64
                if identity["sha256"] != "a" * 64 else "b" * 64,
            )
        for bad in (None, "ABC", "F" * 64, "", 123):
            with self.subTest(bad=bad):
                with self.assertRaises(handoff.EventLossHandoffError):
                    handoff.project_event_loss_handoff(
                        payload, expected_receipt_sha256=bad,
                    )

    def test_canonical_validator_blocks_policy_injection_and_bad_event_rows(self):
        payload, _ = fake_receipt()
        altered = json.loads(payload)
        altered["insurance_scope"] = "policy"
        altered["rows"][0]["loss_f32_be_hex"] = "7f800000"
        mutated = json.dumps(altered, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        with self.assertRaises(handoff.EventLossHandoffError):
            handoff.project_event_loss_handoff(
                mutated, expected_receipt_sha256=hashlib.sha256(mutated).hexdigest(),
            )

    def test_handoff_cannot_authorize_annualized_insurance_or_odr_outputs(self):
        payload, identity = fake_receipt()
        _, data = handoff.project_event_loss_handoff(
            payload, expected_receipt_sha256=identity["sha256"],
        )
        result = json.loads(data)
        for prohibited in (
            "origin_authenticated_by_this_projection",
            "original_provider_data_rights_confirmed",
            "event_rates_available",
            "shaking_footprints_available",
            "insured_loss_calculated",
            "policy_coverage_applied",
            "financial_terms_applied",
            "annualization_authorized",
            "oasis_odr_conformant",
            "nextgen_import_verified",
            "model_input_approved",
            "public_redistribution_authorized",
        ):
            with self.subTest(prohibited=prohibited):
                self.assertIs(result[prohibited], False)

    def test_writes_new_outputs_without_overwriting_files(self):
        payload, identity = fake_receipt()
        rows, metadata = handoff.project_event_loss_handoff(
            payload, expected_receipt_sha256=identity["sha256"],
        )
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            ledger, manifest = root / "events.jsonl", root / "manifest.json"
            handoff.write_new_pair(ledger, manifest, rows, metadata)
            self.assertEqual(ledger.read_bytes(), rows)
            self.assertEqual(manifest.read_bytes(), metadata)
            self.assertEqual(stat.S_IMODE(ledger.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(manifest.stat().st_mode), 0o600)
            with self.assertRaises(handoff.EventLossHandoffError):
                handoff.write_new_pair(ledger, manifest, rows, metadata)
            self.assertEqual(ledger.read_bytes(), rows)

    def test_output_path_guards_symlinks_and_same_path(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            existing = root / "existing"
            existing.write_bytes(b"original")
            link = root / "link"
            link.symlink_to(existing)
            with self.assertRaises(handoff.EventLossHandoffError):
                handoff.write_new_pair(link, root / "manifest", b"x", b"y")
            with self.assertRaises(handoff.EventLossHandoffError):
                handoff.write_new_pair(existing, existing, b"x", b"y")
            self.assertEqual(existing.read_bytes(), b"original")

    def test_partial_pair_creation_is_rolled_back(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            jsonl = root / "events.jsonl"
            missing_parent_manifest = root / "absent" / "manifest.json"
            with self.assertRaises(handoff.EventLossHandoffError):
                handoff.write_new_pair(jsonl, missing_parent_manifest, b"rows\n", b"meta\n")
            self.assertFalse(jsonl.exists())

    def test_nonfinite_binary32_prevented_by_canonical_receipt_validation(self):
        row = event(1, loss="7f800000")
        with self.assertRaises(canonical.OQ313RiskByEventReceiptError):
            canonical.project_oq313_risk_by_event_receipt(
                [row], portfolio_agg_id=0, structural_loss_id=0, concurrent_tasks=1
            )


if __name__ == "__main__":
    unittest.main()
