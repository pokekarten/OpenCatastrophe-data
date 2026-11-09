# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original-byte, fail-closed landscape source revision regression tests."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_cat_landscape_revisions_v0 import (
    LandscapeRevisionBlocked, _read, compare, main,
)


def entry(cid="synthetic.building.source"):
    return {
        "candidate_id": cid, "name": "Synthetic source",
        "provider": "Public synthetic provider", "categories": ["buildings"],
        "spatial_scope": "Synthetic test geography", "temporal_scope": "2026",
        "resolution_or_granularity": "Synthetic metadata only",
        "potential_roles": ["source_research"],
        "authoritative_url": "https://example.org/source",
        "access_class_hint": "documented_public",
        "candidate_status": "evidence_checked",
        "rights_review_status": "not_reviewed",
        "scientific_review_status": "not_reviewed",
        "admission_status": "not_admitted",
        "note": "No original source bytes or model evidence",
    }


def shard():
    return {
        "schema_version": "1.0.0",
        "purpose": "Non-admission candidate discovery; no license authority.",
        "review_date": "2026-11-08",
        "entries": [entry()],
    }


def encoded(payload):
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def proof(before, after):
    a, b = encoded(before), encoded(after)
    return compare(a, b, old_blob_sha=blob(a), new_blob_sha=blob(b))


class LandscapeRevisionsTests(unittest.TestCase):
    def test_identical_original_bytes_still_do_not_authorize_use(self):
        original = shard()
        r = proof(original, original)
        self.assertEqual(r["old_candidate_count"], 1)
        self.assertFalse(r["manual_semantic_review_required"])
        for gate in ("rights_approval_authorized", "source_or_model_admission_authorized",
                     "source_bytes_downloaded", "neon_production_mutation_authorized"):
            self.assertFalse(r[gate])

    def test_addition_and_note_change_are_explicit_nonadmission_review(self):
        before, after = shard(), shard()
        after["review_date"] = "2026-11-09"
        after["entries"][0]["note"] = "Synthetic revised scientific limitation"
        after["entries"].append(entry("synthetic.other.building"))
        result = proof(before, after)
        self.assertEqual(result["old_candidate_count"], 1)
        self.assertEqual(result["new_candidate_count"], 2)
        self.assertEqual(result["added_nonadmitted_candidate_ids"],
                         ["synthetic.other.building"])
        self.assertEqual(result["modified_existing_candidate_fields"],
                         {"synthetic.building.source": ["note"]})
        self.assertEqual(result["changed_shard_header_fields"], ["review_date"])
        self.assertTrue(result["manual_semantic_review_required"])

    def test_removed_or_reidentified_source_cannot_silently_disappear(self):
        original = shard()
        changed = deepcopy(original)
        changed["entries"] = [entry("other.source")]
        with self.assertRaisesRegex(LandscapeRevisionBlocked, "removed or renamed"):
            proof(original, changed)

    def test_existing_provider_or_url_identity_cannot_silently_change(self):
        for field, changed_value in (
            ("provider", "Different institution"),
            ("authoritative_url", "https://other.example.org/data"),
        ):
            changed = shard()
            changed["entries"][0][field] = changed_value
            with self.subTest(field=field), self.assertRaisesRegex(
                LandscapeRevisionBlocked, "identity changed"
            ):
                proof(shard(), changed)

    def test_rights_science_and_admission_are_not_promotable(self):
        for field, changed_value in (
            ("rights_review_status", "verified"),
            ("scientific_review_status", "model_ready"),
            ("admission_status", "admitted"),
            ("candidate_status", "accepted"),
        ):
            changed = shard()
            changed["entries"][0][field] = changed_value
            with self.subTest(field=field), self.assertRaisesRegex(
                LandscapeRevisionBlocked, "invalid non-admission"
            ):
                proof(shard(), changed)

    def test_duplicate_candidates_secret_url_and_forged_sha_fail(self):
        duplicate = shard()
        duplicate["entries"].append(entry())
        with self.assertRaisesRegex(LandscapeRevisionBlocked, "repeated candidate_id"):
            proof(shard(), duplicate)
        forbidden = shard()
        forbidden["entries"][0]["authoritative_url"] = "http://example.org/raw"
        with self.assertRaisesRegex(LandscapeRevisionBlocked, "invalid non-admission"):
            proof(shard(), forbidden)
        data = encoded(shard())
        with self.assertRaisesRegex(LandscapeRevisionBlocked, "SHA mismatch"):
            _read(data, "0" * 40)

    def test_duplicate_json_keys_and_invalid_original_bytes_fail(self):
        valid = encoded(shard())
        malformed = valid.replace(b'"review_date":"2026-11-08"',
                                  b'"review_date":"2026-11-08","review_date":"2026-11-09"')
        with self.assertRaisesRegex(LandscapeRevisionBlocked, "duplicate JSON key"):
            _read(malformed, blob(malformed))
        for content in (b"", b"{", b"[]", b"\xff"):
            with self.subTest(content=content[:10]), self.assertRaises(LandscapeRevisionBlocked):
                _read(content, blob(content))

    def test_cli_exit_statuses(self):
        a = encoded(shard())
        changed = shard()
        changed["entries"][0]["note"] += " revised"
        b = encoded(changed)
        with tempfile.TemporaryDirectory() as d:
            older, newer = Path(d)/"old.json", Path(d)/"new.json"
            older.write_bytes(a)
            newer.write_bytes(b)
            args = ["--old", str(older), "--new", str(newer),
                    "--old-blob-sha", blob(a), "--new-blob-sha", blob(b)]
            self.assertEqual(main(args), 2)
            newer.write_bytes(a)
            self.assertEqual(main(args[:-1] + [blob(a)]), 0)
            self.assertEqual(main(args), 1)


if __name__ == "__main__":
    unittest.main()
