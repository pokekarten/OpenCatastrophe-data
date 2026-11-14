# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline-only source-byte, stage append and fail-closed regression tests."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.build_cat_source_stage_append_review_v0 import build_review, git_blob_sha

ROOT = Path(__file__).resolve().parents[1]
L1 = "landscape/sources-berlin-alkis-pilot-20261101.json"
L2 = "landscape/sources-worldmonitor-upstream-20261102.json"
A1 = "access/de.berlin.alkis-gebaeude.wfs.json"
A2 = "access/sk.gku.inspire-buildings.gpkg.json"
M1 = "manifests/google.open-buildings.v3.json"
M2 = "manifests/efehr.eshm20.json"
PATHS = (L1, L2, A1, A2, M1, M2)
COMMIT = "a" * 40


def github():
    return [{"type": "file", "path": p, "sha": git_blob_sha((ROOT / p).read_bytes())}
            for p in PATHS]


def record(path):
    kind = ("landscape_candidate" if path.startswith("landscape/") else
            "access_contract" if path.startswith("access/") else "admitted_manifest")
    stem = Path(path).stem
    return {
        "source_key": ("landscape_file:" if kind == "landscape_candidate" else
                       "access:" if kind == "access_contract" else "manifest:") + stem,
        "source_id": stem,
        "classification": kind,
        "git_path": path,
        "git_blob_sha": git_blob_sha((ROOT / path).read_bytes()),
        "repo": "pokekarten/OpenCatastrophe-data",
        "review_status": ("non_admission_discovery_only" if kind == "landscape_candidate"
                          else "documented_only" if kind == "access_contract"
                          else "approved_metadata_only"),
        "rights_status": ("not_reviewed" if kind == "landscape_candidate" else
                          "verified" if kind == "access_contract"
                          else "commercial:allowed;redistribution:allowed"),
        "admissible_for_raw": False,
    }


def stage():
    return [record(L1), record(A1), record(M1)]


class StageAppendReviewTests(unittest.TestCase):
    def test_original_blob_id_matches_independent_sha_and_review_is_not_an_insert(self):
        report = build_review(github(), stage(), stage(), ROOT, COMMIT)
        self.assertEqual(report["github_canonical_files"], 6)
        self.assertEqual(report["isolated_stage_exact_matches"], 3)
        self.assertEqual({x["git_path"] for x in report["manual_stage_append_candidates"]}, {L2, A2})
        self.assertEqual(report["missing_manifest_admissions_blocked"], [M2])
        for candidate in report["manual_stage_append_candidates"]:
            self.assertFalse(candidate["admissible_for_raw"])
            self.assertTrue(candidate["manual_review_required"])
            self.assertEqual(len(candidate["canonical_json_sha256"]), 64)
        self.assertFalse(report["sql_or_auto_append_generated"])
        self.assertFalse(report["production_write_authorized"])
        self.assertFalse(report["raw_data_or_model_admission_authorized"])

    def test_slovenian_source_is_not_implicitly_authorized(self):
        report = build_review(github(), stage(), stage(), ROOT, COMMIT)
        slovakia = next(x for x in report["manual_stage_append_candidates"] if x["git_path"] == A2)
        self.assertEqual(slovakia["source_key"], "access:sk.gku.inspire-buildings.gpkg")
        self.assertEqual(slovakia["review_status"], "documented_only")
        self.assertEqual(slovakia["rights_status"], "verified")
        self.assertFalse(slovakia["admissible_for_raw"])

    def test_staging_cannot_append_a_path_that_is_already_in_production(self):
        prod = stage() + [record(A2)]
        report = build_review(github(), stage(), prod, ROOT, COMMIT)
        self.assertEqual(report["stage_lags_production_do_not_append"], [A2])
        self.assertNotIn(A2, [x["git_path"] for x in report["manual_stage_append_candidates"]])

    def test_drift_is_explicit_and_does_not_replace_version(self):
        old = stage()
        old[0]["git_blob_sha"] = "f" * 40
        report = build_review(github(), old, stage(), ROOT, COMMIT)
        self.assertEqual(report["isolated_stage_version_drift"], [L1])
        self.assertEqual({x["git_path"] for x in report["manual_stage_append_candidates"]}, {L2, A2})

    def test_forged_sha_or_checkout_modification_is_rejected(self):
        inv = github()
        inv[1]["sha"] = "e" * 40
        with self.assertRaisesRegex(ValueError, "blob mismatch"):
            build_review(inv, stage(), stage(), ROOT, COMMIT)
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            for path in (L2, A2):
                (temp / path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, temp / path)
            (temp / L2).write_bytes((temp / L2).read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "blob mismatch"):
                build_review(github(), stage(), stage(), temp, COMMIT)

    def test_duplicate_identity_and_raw_promotion_are_blocked(self):
        collided = stage() + [{"source_key": "access:sk.gku.inspire-buildings.gpkg",
                              "git_path": "docs/research/old.md", "classification": "access_contract"}]
        with self.assertRaisesRegex(ValueError, "reused source identity"):
            build_review(github(), collided, stage(), ROOT, COMMIT)
        invalid = deepcopy(stage())
        invalid[0]["admissible_for_raw"] = True
        with self.assertRaises(ValueError):
            build_review(github(), invalid, stage(), ROOT, COMMIT)

    def test_pinned_commit_sha_is_required(self):
        with self.assertRaisesRegex(ValueError, "immutable"):
            build_review(github(), stage(), stage(), ROOT, "main")


if __name__ == "__main__":
    unittest.main()
