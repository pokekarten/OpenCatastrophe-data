# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import json
import tempfile
import unittest
from pathlib import Path
from scripts.insurance_neon_branch_merge_preflight_v0 import SCHEMA, compare, load_manifest


def fixture(sources=None, candidates=None):
    return {"format": SCHEMA, "sources": sources or [], "candidates": candidates or []}


class BranchDiffTests(unittest.TestCase):
    def test_detects_realistic_cross_branch_drift(self):
        common_main = {"source_key": "a", "git_blob_sha": "a" * 40,
                       "review_status": "verified", "rights_status": "reviewed", "admissible_for_raw": False}
        common_val = {**common_main, "git_blob_sha": "b" * 40, "rights_status": "pending"}
        left = fixture([common_main, {"source_key": "main_only"}],
                       [{"source_row_key": "x", "identity_resolution_status": "unmatched",
                         "verified_organization_id": None}])
        right = fixture([common_val, {"source_key": "val_only"}],
                        [{"source_row_key": "x", "identity_resolution_status": "unmatched",
                          "verified_organization_id": None}])
        result = compare(left, right, details=True)
        self.assertEqual(result["sources"]["shared_keys"], 1)
        self.assertEqual(result["sources"]["main_only"], 1)
        self.assertEqual(result["sources"]["validation_only"], 1)
        self.assertEqual(result["sources"]["conflict_fields"]["git_blob_sha"], 1)
        self.assertEqual(result["sources"]["conflict_fields"]["rights_status"], 1)
        self.assertTrue(result["manual_merge_review_required"])
        self.assertFalse(result["automatic_merge_authorized"])

    def test_identical_manifests_still_do_not_authorize_merge(self):
        value = fixture([{"source_key": "a", "rights_status": "not_reviewed"}])
        result = compare(value, value)
        self.assertFalse(result["manual_merge_review_required"])
        self.assertFalse(result["automatic_merge_authorized"])
        self.assertFalse(result["model_input_approved_by_this_tool"])

    def test_candidate_identity_mismatch_blocked(self):
        left = fixture(candidates=[{"source_row_key": "a", "verified_organization_id": None}])
        right = fixture(candidates=[{"source_row_key": "a", "verified_organization_id": "some-id"}])
        result = compare(left, right)
        self.assertEqual(result["organization_candidates"]["conflicting_shared_keys"], 1)
        self.assertTrue(result["manual_merge_review_required"])

    def test_reject_duplicate_keys(self):
        value = fixture([{"source_key": "same"}, {"source_key": "same"}])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_manifest(path)

    def test_accept_neon_single_row_envelope(self):
        value = fixture([{"source_key": "some"}])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_text(json.dumps([{"metadata_manifest": value}]), encoding="utf-8")
            self.assertEqual(load_manifest(path), value)

    def test_fail_closed_bad_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_text(json.dumps({"format": "wrong", "sources": [], "candidates": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path)


if __name__ == "__main__":
    unittest.main()
