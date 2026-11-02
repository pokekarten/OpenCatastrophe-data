# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline consumer-side regression for exact-loss OpenQuake EQ1 transport."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts import project_oq313_event_loss_handoff_v0 as producer
from scripts import project_oq313_risk_by_event_receipt as numerical
from scripts import validate_oq313_event_loss_handoff_v0 as consumer


def fixture():
    rows = [
        {"event_id": 8, "rup_id": 11, "rlz_id": 1,
         "loss_f32_be_hex": "3f800000", "variance_f32_be_hex": "00000000"},
        {"event_id": 3, "rup_id": 12, "rlz_id": 0,
         "loss_f32_be_hex": "40000000", "variance_f32_be_hex": "80000000"},
    ]
    receipt, identity = numerical.project_oq313_risk_by_event_receipt(
        rows, portfolio_agg_id=1, structural_loss_id=0, concurrent_tasks=1,
    )
    jsonl, manifest = producer.project_event_loss_handoff(
        receipt, expected_receipt_sha256=identity["sha256"],
    )
    return receipt, identity["sha256"], jsonl, manifest


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(receipt_hash: str, jsonl: bytes, manifest: bytes, *,
             full_receipt: bytes | None = None) -> dict:
    return consumer.validate_event_loss_handoff(
        jsonl, manifest, expected_manifest_sha256=sha(manifest),
        expected_source_receipt_sha256=receipt_hash,
        source_receipt=full_receipt,
    )


def modified(data: dict) -> bytes:
    return producer._canonical_json(data)


class ConsumerBoundaryTests(unittest.TestCase):
    def test_genuine_synthetic_handoff_passes_but_does_not_admit(self):
        original, receipt_hash, jsonl, manifest = fixture()
        result = validate(receipt_hash, jsonl, manifest)
        self.assertTrue(result["transport_validation_passed"])
        self.assertFalse(result["canonical_source_rows_reconciled"])
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["jsonl_sha256"], sha(jsonl))
        self.assertEqual(result["manifest_sha256"], sha(manifest))
        for forbidden in (
            "origin_authenticated_by_this_validation",
            "original_provider_data_rights_confirmed",
            "annualized_loss_established", "insured_loss_established",
            "oasis_odr_conformant", "nextgen_import_verified",
            "model_input_approved",
        ):
            self.assertIs(result[forbidden], False)

        reconciled = validate(receipt_hash, jsonl, manifest, full_receipt=original)
        self.assertTrue(reconciled["canonical_source_rows_reconciled"])
        self.assertFalse(reconciled["origin_authenticated_by_this_validation"])

    def test_changed_manifest_rejected_using_independent_expected_digest(self):
        _, h, jsonl, m = fixture()
        altered = bytearray(m)
        altered[10] ^= 1
        with self.assertRaisesRegex(consumer.EventLossHandoffValidationError, "manifest differs"):
            consumer.validate_event_loss_handoff(
                jsonl, bytes(altered), expected_manifest_sha256=sha(m),
                expected_source_receipt_sha256=h,
            )

    def test_wrong_source_receipt_digest_blocks_self_consistent_transport(self):
        _, h, j, m = fixture()
        other = "0" * 64 if h != "0" * 64 else "1" * 64
        with self.assertRaisesRegex(consumer.EventLossHandoffValidationError, "source receipt differs"):
            validate(other, j, m)

    def test_modified_jsonl_rejected_on_sha_mismatch(self):
        _, h, j, m = fixture()
        self.assertIn(b"3f800000", j)
        altered = j.replace(b"3f800000", b"40000000")
        with self.assertRaisesRegex(consumer.EventLossHandoffValidationError, "SHA-256 mismatch"):
            validate(h, altered, m)

    def test_duplicate_out_of_order_or_malformed_binary32_blocked_even_with_rehashed_manifest(self):
        _, h, j, m = fixture()
        rows = [json.loads(line) for line in j.splitlines()]
        for bad_rows in (
            list(reversed(rows)),
            [rows[0], rows[0]],
            [{**rows[0], "loss_f32_be_hex": "7f800000"}, rows[1]],
            [{**rows[0], "loss_f32_be_hex": "bf800000"}, rows[1]],
            [{**rows[0], "insured_loss": 50}, rows[1]],
            [{**rows[0], "event_id": True}, rows[1]],
        ):
            with self.subTest(rows=bad_rows):
                forged = b"".join(producer._canonical_json(row) for row in bad_rows)
                manifest_dict = json.loads(m)
                manifest_dict["output"]["sha256"] = sha(forged)
                manifest_dict["output"]["byte_count"] = len(forged)
                new_manifest = modified(manifest_dict)
                with self.assertRaises(consumer.EventLossHandoffValidationError):
                    validate(h, forged, new_manifest)

    def test_forged_self_consistent_loss_detected_with_full_original_receipt(self):
        receipt, h, j, m = fixture()
        rows = [json.loads(line) for line in j.splitlines()]
        rows[0]["loss_f32_be_hex"] = "40800000"
        forged = b"".join(producer._canonical_json(row) for row in rows)
        metadata = json.loads(m)
        metadata["output"]["sha256"] = sha(forged)
        metadata["output"]["byte_count"] = len(forged)
        forged_manifest = modified(metadata)
        # A self-signed manifest with caller-provided pins passes content checks,
        # but MUST NOT be called origin-authenticated.
        result = validate(h, forged, forged_manifest)
        self.assertFalse(result["canonical_source_rows_reconciled"])
        with self.assertRaisesRegex(consumer.EventLossHandoffValidationError, "canonical source"):
            validate(h, forged, forged_manifest, full_receipt=receipt)

    def test_attempt_to_promote_to_insurance_or_annualized_scope_rejected(self):
        _, h, j, m = fixture()
        base = json.loads(m)
        for key in (
            "model_input_approved", "annualization_authorized",
            "nextgen_import_verified", "public_redistribution_authorized",
        ):
            altered = json.loads(m)
            altered[key] = True
            with self.subTest(key=key):
                with self.assertRaisesRegex(consumer.EventLossHandoffValidationError, "unsupported authority"):
                    validate(h, j, modified(altered))
        base["source"]["insurance_scope"] = "insured"
        with self.assertRaisesRegex(consumer.EventLossHandoffValidationError, "insured loss"):
            validate(h, j, modified(base))

    def test_malformed_jsonl_and_bad_manifest_types_rejected(self):
        _, h, j, m = fixture()
        for corrupted in (j.rstrip(b"\n"), j.replace(b"\n", b"\r\n"), j + b"\n"):
            with self.subTest(data=corrupted[-20:]):
                meta = json.loads(m)
                meta["output"]["byte_count"] = len(corrupted)
                meta["output"]["sha256"] = sha(corrupted)
                new = modified(meta)
                with self.assertRaises(consumer.EventLossHandoffValidationError):
                    validate(h, corrupted, new)
        bad = json.loads(m)
        bad["output"]["row_count"] = True
        with self.assertRaises(consumer.EventLossHandoffValidationError):
            validate(h, j, modified(bad))

    def test_deeply_nested_untrusted_json_never_crashes_consumer(self):
        # Parsing/encoding recursion limits vary across CPython versions.
        # Always return a domain validation error, never an unhandled traceback.
        deeply_nested = b'[' * 3000 + b'0' + b']' * 3000
        with self.assertRaises(consumer.EventLossHandoffValidationError):
            consumer._parse_canonical(deeply_nested, "untrusted nested JSON")

    def test_read_only_cli_uses_pinned_hashes_and_rejects_symlinked_input(self):
        original, receipt_hash, jsonl, manifest = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            jp, mp, rp = base / "events.jsonl", base / "manifest.json", base / "receipt.json"
            jp.write_bytes(jsonl)
            mp.write_bytes(manifest)
            rp.write_bytes(original)
            result = consumer.main([
                "--jsonl", str(jp), "--manifest", str(mp),
                "--expected-manifest-sha256", sha(manifest),
                "--expected-source-receipt-sha256", receipt_hash,
                "--source-receipt", str(rp),
            ])
            self.assertEqual(result, 0)
            link = base / "linked.jsonl"
            link.symlink_to(jp)
            self.assertEqual(consumer.main([
                "--jsonl", str(link), "--manifest", str(mp),
                "--expected-manifest-sha256", sha(manifest),
                "--expected-source-receipt-sha256", receipt_hash,
            ]), 2)

    def test_source_payload_mutation_rejected_even_when_handoff_is_intact(self):
        receipt, h, j, m = fixture()
        tampered = receipt.replace(b'"portfolio_agg_id":1', b'"portfolio_agg_id":2')
        self.assertNotEqual(tampered, receipt)
        with self.assertRaisesRegex(consumer.EventLossHandoffValidationError, "source receipt"):
            validate(h, j, m, full_receipt=tampered)


if __name__ == "__main__":
    unittest.main()
