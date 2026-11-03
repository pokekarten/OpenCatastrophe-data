# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Only synthetic GitHub/Neon metadata for the landscape registry sync audit."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_insurance_landscape_sync_v0 import compare, load, main

P1 = "landscape/sources-alpha.json"
P2 = "landscape/sources-beta-20261103.json"
ONE = "1" * 40
TWO = "2" * 40
THREE = "3" * 40


def github():
    return [
        {"path": P1, "type": "file", "sha": ONE},
        {"path": P2, "type": "file", "sha": TWO},
        {"path": "landscape/sources-alpha.md", "type": "file", "sha": THREE},
    ]


def neon():
    return [{
        "source_key": "landscape_file:sources-alpha",
        "source_id": "sources-alpha",
        "classification": "landscape_candidate",
        "git_path": P1,
        "git_blob_sha": ONE,
        "admissible_for_raw": False,
    }]


class LandscapeSyncAuditTests(unittest.TestCase):
    def test_missing_shard_is_bounded_nonadmission_metadata_only(self):
        result = compare(github(), neon())
        self.assertEqual(result["github_landscape_shards"], 2)
        self.assertEqual(result["neon_landscape_records"], 1)
        self.assertEqual(result["exact_git_blob_matches"], 1)
        self.assertEqual(result["missing_in_neon"], [
            {"git_path": P2, "git_blob_sha": TWO}
        ])
        self.assertTrue(result["review_needed"])
        self.assertFalse(result["automatic_sync_authorized"])
        self.assertFalse(result["source_rights_or_model_admission_authorized"])
        self.assertTrue(result["repository_shard_is_not_unique_provider_dataset"])

    def test_fully_matching_shards_still_not_automatically_approved(self):
        other = {**neon()[0], "source_key": "landscape_file:sources-beta-20261103",
                 "source_id": "sources-beta-20261103", "git_path": P2,
                 "git_blob_sha": TWO}
        result = compare(github(), neon() + [other])
        self.assertFalse(result["review_needed"])
        self.assertEqual(result["exact_git_blob_matches"], 2)
        self.assertFalse(result["automatic_sync_authorized"])

    def test_modified_blob_is_version_drift_not_overwrite_license(self):
        record = {**neon()[0], "git_blob_sha": THREE}
        result = compare(github(), [record])
        self.assertEqual(len(result["shared_paths_with_blob_drift"]), 1)
        self.assertEqual(result["shared_paths_with_blob_drift"][0]["neon_blob_sha"], THREE)
        self.assertFalse(result["automatic_sync_authorized"])

    def test_wrong_type_identity_and_raw_admission_fail_closed(self):
        record = {**neon()[0], "classification": "admitted_manifest",
                  "source_key": "wrong", "admissible_for_raw": True}
        result = compare(github(), [record])
        self.assertEqual(result["wrong_classification_or_identity"], [P1])
        self.assertEqual(result["unexpected_raw_admission"], [P1])
        self.assertTrue(result["review_needed"])
        self.assertFalse(result["source_rights_or_model_admission_authorized"])

    def test_rejects_duplicate_paths_and_broken_hashes(self):
        for g, n in (
            (github() + [github()[0]], neon()),
            (github(), neon() + neon()),
            ([{**github()[0], "sha": "not-hex"}], neon()),
            (github(), [{**neon()[0], "git_blob_sha": "not-hex"}]),
            ([{**github()[0], "type": "dir"}], neon()),
        ):
            with self.subTest(g=g, n=n), self.assertRaises(ValueError):
                compare(g, n)

    def test_rejects_empty_or_noncanonical_input(self):
        for g, n in (([], neon()), (github(), []),
                     ([{"path": "other/file.json", "type": "file",
                        "sha": ONE}], neon())):
            with self.subTest(g=g, n=n), self.assertRaises(ValueError):
                compare(g, n)

    def test_cli_exit_codes_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            gh, nr = [Path(temp) / name for name in ("gh.json", "neon.json")]
            gh.write_text(json.dumps(github()), encoding="utf-8")
            nr.write_text(json.dumps(neon()), encoding="utf-8")
            command = ["--github-inventory", str(gh), "--neon-export", str(nr)]
            self.assertEqual(main(command), 2)
            gh.write_text('[{"path":"landscape/sources-alpha.json",'
                          '"path":"landscape/sources-beta.json"}]', encoding="utf-8")
            self.assertEqual(main(command), 1)
            with self.assertRaises(ValueError):
                load(gh)


if __name__ == "__main__":
    unittest.main()
