# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Regression: GLIDE identifier has one canonical source entry across shards."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PEER = ROOT / "landscape" / "sources-peer-cat-repositories-20261102.json"
MONITOR = ROOT / "landscape" / "sources-monitoring-repo-upstreams-20261102.json"
ID = "adrc.glide.disaster-identifiers"


class GLIDECanonicalOwnerTests(unittest.TestCase):
    def test_glide_is_peer_registered_once_without_monitoring_duplicate(self):
        peer = json.loads(PEER.read_text(encoding="utf-8"))["entries"]
        monitoring = json.loads(MONITOR.read_text(encoding="utf-8"))["entries"]
        matches = [e for e in peer if e["candidate_id"] == ID]
        self.assertEqual(len(matches), 1)
        self.assertFalse(any(e["candidate_id"] == ID for e in monitoring))
        self.assertEqual(len(monitoring), 22)
        self.assertEqual(matches[0]["admission_status"], "not_admitted")
        self.assertEqual(matches[0]["rights_review_status"], "not_reviewed")
        self.assertEqual(matches[0]["scientific_review_status"], "not_reviewed")
        self.assertIn("not evidence of one physical", matches[0]["note"].lower())


if __name__ == "__main__":
    unittest.main()
