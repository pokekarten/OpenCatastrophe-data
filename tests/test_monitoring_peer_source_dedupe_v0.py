# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Guard canonical peer-CAT versus monitoring-upstream source identity boundaries."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "landscape"
MONITORING = ROOT / "sources-monitoring-repo-upstreams-20261102.json"
PEER = ROOT / "sources-peer-cat-repositories-20261102.json"

# Distinct provenance notes in research docs must not become second canonical
# entries for the same original-source product.
ALIAS_TO_CANONICAL = {
    "adrc.glide.disaster-identifiers": "adrc.glide.disaster-identifiers",
    "unocha.cerf.gms-api": "unocha.cerf.gms-data-api",
    "disasterscharter.activations.archive": (
        "international-charter.space-major-disasters.activations"
    ),
}


def entries(path):
    return json.loads(path.read_text(encoding="utf-8"))["entries"]


class MonitoringPeerSourceIdentityTests(unittest.TestCase):
    def test_no_cross_shard_duplicate_candidate_id_or_original_url(self):
        monitoring, peer = entries(MONITORING), entries(PEER)
        ids_a = {item["candidate_id"] for item in monitoring}
        ids_b = {item["candidate_id"] for item in peer}
        urls_a = {item["authoritative_url"].rstrip("/") for item in monitoring}
        urls_b = {item["authoritative_url"].rstrip("/") for item in peer}
        self.assertEqual(len(ids_a), len(monitoring))
        self.assertEqual(len(ids_b), len(peer))
        self.assertFalse(ids_a & ids_b, ids_a & ids_b)
        self.assertFalse(urls_a & urls_b, urls_a & urls_b)

    def test_existing_peer_identities_are_retained_with_no_new_admission(self):
        monitoring, peer = entries(MONITORING), entries(PEER)
        ids_a = {item["candidate_id"] for item in monitoring}
        ids_b = {item["candidate_id"] for item in peer}
        for dropped_id, canonical_id in ALIAS_TO_CANONICAL.items():
            with self.subTest(dropped=dropped_id, canonical=canonical_id):
                self.assertNotIn(dropped_id, ids_a)
                self.assertIn(canonical_id, ids_b)
        for item in monitoring + peer:
            with self.subTest(candidate_id=item["candidate_id"]):
                self.assertEqual(item["admission_status"], "not_admitted")


if __name__ == "__main__":
    unittest.main()
