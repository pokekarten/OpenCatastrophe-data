# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only three-way source register proof, including forged revisions."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_cat_source_registry_three_way_v0 import compare, main

A = "landscape/sources-alpha.json"
B = "landscape/sources-beta-20261103.json"
C = "access/public.hazard.catalogue.json"
D = "access/private.source.documented.json"
H1 = "1" * 40
H2 = "2" * 40
H3 = "3" * 40
H4 = "4" * 40


def github():
    return [{"path": p, "sha": h, "type": "file"}
            for p, h in ((A, H1), (B, H2), (C, H3), (D, H4))] + [
        {"path": "landscape/README.md", "sha": H1, "type": "file"},
        {"path": "access/source-access-inventory.json", "sha": H2, "type": "file"},
    ]


def record(path, sha):
    is_landscape = path.startswith("landscape/")
    stem = path.split("/")[-1][:-5]
    return {
        "source_key": ("landscape_file:" if is_landscape else "access:") + stem,
        "source_id": stem,
        "classification": "landscape_candidate" if is_landscape else "access_contract",
        "git_path": path,
        "git_blob_sha": sha,
        "repo": "pokekarten/OpenCatastrophe-data",
        "review_status": "non_admission_discovery_only" if is_landscape
                         else "documented_only",
        "rights_status": "not_reviewed",
        "admissible_for_raw": False,
    }


def stage():
    return [record(A, H1), record(B, H2), record(C, H3), record(D, H4)]


def production():
    return [record(A, H1), record(C, H2)]


class ThreeWayRegistryTests(unittest.TestCase):
    def test_missing_append_is_not_authorization_and_drift_is_not_overwritten(self):
        report = compare(github(), stage(), production())
        self.assertEqual(report["github_canonical_files"], 4)
        self.assertEqual(report["github_landscape_shards"], 2)
        self.assertEqual(report["github_access_contracts"], 2)
        self.assertEqual(report["stage_canonical_records"], 4)
        self.assertEqual(report["production_canonical_records"], 2)
        self.assertEqual(report["production_current_blob_matches"], 1)
        self.assertEqual([x["git_path"] for x in
                          report["manual_append_review_candidates"]], [D, B])
        self.assertEqual(report["production_blob_drift"], [C])
        self.assertEqual(report["historical_version_conflicts"], [C])
        self.assertTrue(report["review_needed"])
        self.assertFalse(report["automatic_production_sync_authorized"])
        self.assertFalse(report["source_or_scientific_admission_authorized"])
        self.assertFalse(report["insurer_data_or_provider_bytes_present"])

    def test_exact_three_way_match_still_does_not_allow_import(self):
        result = compare(github(), stage(), stage())
        self.assertFalse(result["review_needed"])
        self.assertEqual(result["manual_append_review_candidates"], [])
        self.assertFalse(result["automatic_production_sync_authorized"])

    def test_modified_staged_blob_not_considered_append_ready(self):
        changed = stage()
        changed[1]["git_blob_sha"] = H3
        result = compare(github(), changed, production())
        self.assertEqual(result["stage_blob_drift"], [B])
        self.assertEqual([x["git_path"] for x in
                          result["manual_append_review_candidates"]], [D])

    def test_stage_missing_cannot_be_relabelled_as_append_ready(self):
        result = compare(github(), stage()[:-1], production())
        self.assertEqual(result["stage_missing_paths"], [D])
        self.assertNotIn(D, [x["git_path"] for x in
                            result["manual_append_review_candidates"]])

    def test_bad_rights_identity_sha_and_raw_admission_all_rejected(self):
        bad = [
            {"git_blob_sha": "not-a-git-sha"},
            {"admissible_for_raw": True},
            {"source_id": "wrong"},
            {"source_key": "wrong"},
            {"classification": "admitted_manifest"},
            {"repo": "pokekarten/other"},
            {"rights_status": "verified"},
            {"review_status": "model_approved"},
        ]
        for override in bad:
            with self.subTest(override=override):
                rows = stage()
                rows[0].update(override)
                with self.assertRaises(ValueError):
                    compare(github(), rows, production())

    def test_duplicate_neon_and_github_paths_rejected(self):
        with self.assertRaises(ValueError):
            compare(github(), stage()+[stage()[0]], production())
        with self.assertRaises(ValueError):
            compare(github()+[github()[0]], stage(), production())

    def test_historical_documented_filename_does_not_rewrite_access_id(self):
        # Original public CHIRPS 3.0 contract has .documented.json on disk
        # but its immutable access_id/source_key omits that role suffix.
        path = "access/ucsb.chc.chirps.v3.0.documented.json"
        record_alias = record(path, H1)
        record_alias["source_id"] = "ucsb.chc.chirps.v3.0"
        record_alias["source_key"] = "access:ucsb.chc.chirps.v3.0"
        listing = github() + [{"path": path, "sha": H1, "type": "file"}]
        result = compare(listing, stage() + [record_alias],
                         production() + [record_alias])
        self.assertEqual(result["github_access_contracts"], 3)
        self.assertEqual(result["production_current_blob_matches"], 2)
        self.assertNotIn(path, result["historical_version_conflicts"])
        bad = deepcopy(record_alias)
        bad["source_id"] = "unrelated.provider"
        with self.assertRaises(ValueError):
            compare(listing, stage() + [bad], production())

    def test_untrusted_access_rights_status_rejected(self):
        for field, value in (
            ("rights_status", "unrestricted_commercial_model_import"),
            ("review_status", "fully_authorized"),
            ("admissible_for_raw", True),
        ):
            rows=stage()
            rows[2][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                compare(github(), rows, production())

    def test_noncanonical_historic_research_rows_do_not_become_contracts(self):
        old = {"git_path": "docs/research/old-original-access-receipt.md",
               "classification": "access_contract", "source_key": "legacy"}
        result = compare(github(), stage()+[old], production()+[old])
        self.assertEqual(result["stage_canonical_records"], 4)
        self.assertEqual(result["production_canonical_records"], 2)

    def test_cli_does_not_execute_writes_and_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[Path(d)/x for x in ("github.json","stage.json","production.json")]
            for path, obj in zip(paths, (github(), stage(), production())):
                path.write_text(json.dumps(obj),encoding="utf-8")
            args=["--github-inventory",str(paths[0]),"--stage-export",
                  str(paths[1]),"--production-export",str(paths[2])]
            self.assertEqual(main(args),2)
            paths[0].write_text('[{"path":"landscape/sources-alpha.json",'
                                '"path":"landscape/sources-beta.json"}]',encoding="utf-8")
            self.assertEqual(main(args),1)


if __name__ == "__main__":
    unittest.main()
