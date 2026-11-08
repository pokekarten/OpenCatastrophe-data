# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict synthetic-only metadata coverage and negative provenance checks."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_cat_source_registry_two_way_v0 import compare, main

L = "landscape/sources-one.json"
A = "access/provider.one.json"
M = "manifests/provider.one.json"
S1, S2, S3, S4 = (str(i)*40 for i in range(1, 5))


def github():
    return [{"type": "file", "path": p, "sha": s}
            for p, s in ((L, S1), (A, S2), (M, S3), ("manifests/provider.one.md", S4))]


def record(path, sha):
    kind = ("landscape_candidate" if path.startswith("landscape/") else
            "access_contract" if path.startswith("access/") else "admitted_manifest")
    stem = path.split("/")[-1][:-5]
    return {
        "source_key": ("landscape_file:" if kind == "landscape_candidate" else
                       "access:" if kind == "access_contract" else "manifest:") + stem,
        "source_id": stem, "classification": kind,
        "repo": "pokekarten/OpenCatastrophe-data", "git_path": path,
        "git_blob_sha": sha,
        "review_status": ("non_admission_discovery_only" if kind == "landscape_candidate"
                          else "documented_only" if kind == "access_contract"
                          else "approved_metadata_only"),
        "rights_status": ("not_reviewed" if kind != "admitted_manifest"
                          else "commercial:allowed;redistribution:allowed"),
        "admissible_for_raw": False,
    }


def neon():
    return [record(L, S1), record(A, S2), record(M, S3)]


class SourceRegistryTwoWayTests(unittest.TestCase):
    def test_complete_coverage_is_not_permission(self):
        r = compare(github(), neon())
        self.assertFalse(r["review_needed"])
        self.assertEqual(r["github_canonical_metadata_files"], 3)
        self.assertEqual(r["neon_canonical_metadata_records"], 3)
        self.assertFalse(r["automatic_production_sync_authorized"])
        self.assertFalse(r["source_data_acquisition_or_model_use_authorized"])
        self.assertTrue(r["manifest_metadata_admission_is_not_raw_admission"])

    def test_missing_and_drift_all_three_classes(self):
        rows = neon()[:1] + [record(A, S4)]
        result = compare(github(), rows + [record(M, S4)])
        self.assertTrue(result["review_needed"])
        self.assertEqual(result["classes"]["access_contract"]["blob_drift_requires_review"][0]["git_path"], A)
        self.assertEqual(result["classes"]["admitted_manifest"]["blob_drift_requires_review"][0]["git_path"], M)
        result = compare(github(), [record(L, S1), record(M, S3)])
        self.assertEqual(result["classes"]["access_contract"]["missing_in_neon"][0]["git_path"], A)

    def test_no_silent_manifest_raw_promotion_or_identity_forgery(self):
        for change in ({"admissible_for_raw": True}, {"source_id": "other"},
                       {"source_key": "manifest:other"},
                       {"review_status": "fully_approved"},
                       {"classification": "access_contract"},
                       {"git_blob_sha": "not-sha"}):
            rows = neon()
            rows[2].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                compare(github(), rows)

    def test_duplicate_path_and_noncanonical_rejected(self):
        with self.assertRaises(ValueError):
            compare(github() + [github()[2]], neon())
        with self.assertRaises(ValueError):
            compare(github(), neon() + [neon()[-1]])
        bad = deepcopy(github())
        bad[2]["path"] = "manifests/../bad.json"
        with self.assertRaises(ValueError):
            compare(bad, neon())

    def test_historical_noncanonical_access_research_is_not_source_contract(self):
        rows = neon() + [{"classification": "access_contract", "git_path": "docs/research/receipt.md"}]
        self.assertFalse(compare(github(), rows)["review_needed"])

    def test_cli_reports_review_exit_2_and_bad_input_exit_1(self):
        with tempfile.TemporaryDirectory() as d:
            gp, np = Path(d)/"github.json", Path(d)/"neon.json"
            gp.write_text(json.dumps(github()), encoding="utf-8")
            np.write_text(json.dumps(neon()), encoding="utf-8")
            args = ["--github-inventory", str(gp), "--neon-export", str(np)]
            self.assertEqual(main(args), 0)
            np.write_text(json.dumps([record(L, S1), record(M, S3)]), encoding="utf-8")
            self.assertEqual(main(args), 2)
            gp.write_text('[{"path":"x","path":"y"}]', encoding="utf-8")
            self.assertEqual(main(args), 1)


if __name__ == "__main__":
    unittest.main()
