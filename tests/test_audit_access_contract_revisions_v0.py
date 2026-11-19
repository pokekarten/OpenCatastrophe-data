# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only access version comparison: no provider, Neon or network I/O."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_access_contract_revisions_v0 import (
    RevisionAuditBlocked, _read_contract, compare, main,
)


def payload(*, status="documented_only", source=None):
    return {
        "access_id": "esa.worldcover.2021.v200",
        "source_ids": ["esa.worldcover.2021.v200"] if source is None else source,
        "provider": "Synthetic official provider",
        "status": status,
        "rights_and_policy": {"dataset_rights_status": "verified", "notes": "synthetic"},
        "request_contract": {"allowed_operations": ["metadata"]},
    }


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


class AccessRevisionAuditTests(unittest.TestCase):
    def test_changed_access_requires_review_and_no_approvals(self):
        old = encoded(payload())
        candidate = payload(status="probe_ready")
        candidate["request_contract"]["allowed_operations"].append("sample_one_block")
        new = encoded(candidate)
        r = compare(old, new, old_blob_sha=blob(old), new_blob_sha=blob(new))
        self.assertEqual(r["changed_field_paths"], [
            "request_contract.allowed_operations", "status",
        ])
        self.assertEqual(r["changed_field_count"], 2)
        self.assertTrue(r["version_review_required"])
        for key in ("overwrite_prior_record_authorized", "automated_provider_access_authorized",
                    "raw_import_authorized", "model_input_approved"):
            self.assertFalse(r[key])
        self.assertNotIn("sample_one_block", str(r))

    def test_same_blob_is_not_a_promotion_either(self):
        old = encoded(payload())
        r = compare(old, old, old_blob_sha=blob(old), new_blob_sha=blob(old))
        self.assertEqual(r["changed_field_count"], 0)
        self.assertFalse(r["version_review_required"])
        self.assertFalse(r["model_input_approved"])

    def test_tampering_or_unpinned_sha_fails(self):
        original = encoded(payload())
        with self.assertRaisesRegex(RevisionAuditBlocked, "checksum mismatch"):
            _read_contract(original.replace(b"synthetic", b"altered__"), blob(original))
        with self.assertRaisesRegex(RevisionAuditBlocked, "invalid pinned"):
            _read_contract(original, "bad")

    def test_malformed_oversized_and_duplicate_nested_keys_fail(self):
        for x in (b"", b"z" * 100001, b"{", b"[]", b"\xff"):
            with self.subTest(x=x[:8]), self.assertRaises(RevisionAuditBlocked):
                _read_contract(x, blob(x))
        raw = encoded(payload()).replace(
            b'"dataset_rights_status":"verified"',
            b'"dataset_rights_status":"verified","dataset_rights_status":"restricted"',
        )
        with self.assertRaisesRegex(RevisionAuditBlocked, "duplicate JSON key"):
            _read_contract(raw, blob(raw))

    def test_wrong_identity_and_source_list_fail_closed(self):
        old = encoded(payload())
        new = encoded(payload(source=["a different source"]))
        with self.assertRaisesRegex(RevisionAuditBlocked, "source identity changed"):
            compare(old, new, old_blob_sha=blob(old), new_blob_sha=blob(new))
        forged = payload()
        forged["access_id"] = "../../unsafe"
        raw = encoded(forged)
        with self.assertRaisesRegex(RevisionAuditBlocked, "ID invalid"):
            _read_contract(raw, blob(raw))

    def test_cli_exit_codes_and_zero_provider_interaction(self):
        old = encoded(payload())
        new = encoded(payload(status="probe_ready"))
        with tempfile.TemporaryDirectory() as path:
            a, b = Path(path) / "old.json", Path(path) / "new.json"
            a.write_bytes(old)
            b.write_bytes(new)
            args = ["--old", str(a), "--new", str(b),
                    "--old-blob-sha", blob(old), "--new-blob-sha", blob(new)]
            self.assertEqual(main(args), 2)
            b.write_bytes(old)
            self.assertEqual(main(args[:-1] + [blob(old)]), 0)
            self.assertEqual(main(args), 1)


if __name__ == "__main__":
    unittest.main()
