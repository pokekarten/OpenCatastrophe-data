# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only offline tests of WFP ADAM OGC catalogue preflight."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_runners.wfp_adam_collection_catalogue_preflight_v0 import (
    ADAMCatalogueError, EXPECTED_IDS, inspect_adam_catalogue_bytes,
)

ROOT = Path(__file__).resolve().parents[1]


def catalogue():
    return {
        "collections": [
            {"id": cid, "title": "Synthetic " + str(n),
             "links": [{"rel": "self", "href": "https://synthetic.example/collection"}]}
            for n, cid in enumerate(sorted(EXPECTED_IDS))
        ],
        "links": [],
    }


def raw(obj):
    return (json.dumps(obj, sort_keys=True) + "\n").encode("utf-8")


def inspect(obj):
    blob = raw(obj)
    return inspect_adam_catalogue_bytes(blob, hashlib.sha256(blob).hexdigest())


class ADAMCatalogueTests(unittest.TestCase):
    def test_exact_thirteen_collection_contract_metadata_only(self):
        result = inspect(catalogue())
        self.assertEqual(result["documented_collection_count"], 13)
        self.assertEqual(result["tropical_cyclone_collection_count"], 8)
        self.assertTrue(result["metadata_only"])
        self.assertFalse(result["events_or_footprints_downloaded"])
        self.assertFalse(result["commercial_reuse_approved"])
        self.assertFalse(result["source_admitted_for_model_use"])
        self.assertNotIn("synthetic.example", json.dumps(result))

    def test_missing_duplicate_unknown_and_pagination_must_block(self):
        cases = []
        x = catalogue()
        x["collections"].pop()
        cases.append(x)
        x = catalogue()
        x["collections"][0]["id"] = x["collections"][1]["id"]
        cases.append(x)
        x = catalogue()
        x["collections"][0]["id"] = "adam.unreviewed_new"
        cases.append(x)
        x = catalogue()
        x["collections"][0]["title"] = ""
        cases.append(x)
        x = catalogue()
        x["collections"][0]["links"] = []
        cases.append(x)
        x = catalogue()
        x["links"].append({"rel": "next", "href": "https://synthetic.example/page2"})
        cases.append(x)
        for obj in cases:
            with self.subTest(reason=json.dumps(obj)[:90]):
                with self.assertRaises(ADAMCatalogueError):
                    inspect(obj)

    def test_live_twelve_of_thirteen_documentation_drift_is_visible_and_blocked(self):
        # Synthetic reproduction of provider metadata coverage observed on
        # 2026-11-02, not a copied provider response or a dataset admission.
        current = catalogue()
        current["collections"] = [
            row for row in current["collections"]
            if row["id"] != "adam.adam_ts_disturbance_events"
        ]
        current["numberMatched"] = 12
        current["numberReturned"] = 12
        data = raw(current)
        pinned = hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ADAMCatalogueError, "missing=adam.adam_ts_disturbance_events"):
            inspect_adam_catalogue_bytes(data, pinned)
        report = inspect_adam_catalogue_bytes(data, pinned, diagnostics_only=True)
        self.assertEqual(report["reference_collection_count"], 13)
        self.assertEqual(report["observed_collection_count"], 12)
        self.assertEqual(report["missing_documented_collection_ids"], ["adam.adam_ts_disturbance_events"])
        self.assertEqual(report["tropical_cyclone_collection_count"], 7)
        self.assertFalse(report["catalogue_matches_documented_reference"])
        self.assertFalse(report["source_admitted_for_model_use"])
        self.assertFalse(report["events_or_footprints_downloaded"])
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "catalogue.json"
            out = Path(folder) / "diagnostic.json"
            source.write_bytes(data)
            cmd = [
                sys.executable,
                str(ROOT / "research_runners/wfp_adam_collection_catalogue_preflight_v0.py"),
                str(source), "--expected-sha256", pinned,
                "--out", str(out), "--diagnose-only",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 3, proc.stderr)
            self.assertIn("BLOCKED", proc.stderr)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["observed_collection_count"], 12)
            self.assertEqual(source.read_bytes(), data)

    def test_provider_declared_counts_must_match_not_just_documented_names(self):
        for wrong in (11, 14, True, -1):
            with self.subTest(wrong=wrong):
                sample = catalogue()
                sample["numberReturned"] = wrong
                with self.assertRaises(ADAMCatalogueError):
                    inspect(sample)
        partial = catalogue()
        partial["numberReturned"] = 13
        partial["numberMatched"] = 14
        with self.assertRaises(ADAMCatalogueError):
            inspect(partial)

    def test_sha_strict_json_and_size(self):
        valid = raw(catalogue())
        for bad in ("0" * 64, "Z" * 64, ""):
            with self.assertRaises(ADAMCatalogueError):
                inspect_adam_catalogue_bytes(valid, bad)
        corrupt = b'{"collections": [], "collections": []}'
        with self.assertRaisesRegex(ADAMCatalogueError, "duplicate"):
            inspect_adam_catalogue_bytes(corrupt, hashlib.sha256(corrupt).hexdigest())
        for payload in (b"", b"\xff", b"X" * 262145):
            with self.assertRaises(ADAMCatalogueError):
                inspect_adam_catalogue_bytes(payload, hashlib.sha256(payload).hexdigest())

    def test_cli_original_not_overwritten(self):
        blob = raw(catalogue())
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.json"
            out = Path(folder) / "report.json"
            source.write_bytes(blob)
            sha = hashlib.sha256(blob).hexdigest()
            command = [sys.executable,
                str(ROOT / "research_runners/wfp_adam_collection_catalogue_preflight_v0.py"),
                str(source), "--expected-sha256", sha, "--out", str(out)]
            good = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["documented_collection_count"], 13)
            bad = subprocess.run(command[:-1] + [str(source)], text=True, capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertEqual(source.read_bytes(), blob)


if __name__ == "__main__":
    unittest.main()
