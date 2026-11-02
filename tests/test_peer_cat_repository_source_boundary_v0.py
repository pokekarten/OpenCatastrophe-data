# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline regression guard: peer software != model-ready provider data."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "landscape" / "sources-peer-cat-repositories-20261102.json"
AUDIT = ROOT / "docs" / "research" / "peer-cat-repositories-source-audit-20261102.md"

EXPECTED = {
    "ifrc.montandon.global-crisis-data-bank.api",
    "eth.climada.data-api.v2",
    "worldbank.gfdrr.thinkhazard.screening-scores",
    "maxar.open-data.ard-disaster-imagery",
    "xview2.xbd.annotated-building-damage",
    "nasa.jpl.aria.post-event-damage-proxy-maps",
    "ifrc.go.disaster-events-fieldreports-v2",
    "unocha.cerf.gms-data-api",
    "undrr.desinventar.sendai-disaster-loss-records",
    "adrc.glide.disaster-identifiers",
    "international-charter.space-major-disasters.activations",
}

METHOD_ONLY = (
    "OasisLMF/ktools",
    "IFRCGo/pystac-monty",
    "Deltares/Delft-FIAT",
    "GNS-Science/riskscape",
    "GeoNode/geonode",
    "inasafe/inasafe",
    "AsMagiic/hurricane-cat-model",
    "microsoft/building-damage-assessment",
)


class PeerRepoSourceBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obj = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.entries = cls.obj["entries"]

    def test_expected_source_ids_and_no_aliases(self):
        self.assertEqual({e["candidate_id"] for e in self.entries}, EXPECTED)
        self.assertEqual(len(self.entries), len(EXPECTED))
        self.assertNotIn("gem.geid.2026", EXPECTED)

    def test_every_external_source_fail_closed(self):
        for e in self.entries:
            with self.subTest(candidate=e["candidate_id"]):
                self.assertEqual(e["candidate_status"], "evidence_checked")
                self.assertEqual(e["admission_status"], "not_admitted")
                self.assertEqual(e["rights_review_status"], "not_reviewed")
                self.assertEqual(e["scientific_review_status"], "not_reviewed")
                self.assertTrue(e["authoritative_url"].startswith("https://"))
                self.assertTrue(e["note"])

    def test_references_document_20_distinct_repos(self):
        text = AUDIT.read_text(encoding="utf-8")
        section = text.split("## All 20 reviewed repositories")[1].split("## Why these eleven")[0]
        rows = [line for line in section.splitlines() if line.startswith("| [")]
        self.assertEqual(len(rows), 20)
        for repo in METHOD_ONLY:
            self.assertIn("https://github.com/" + repo, section)

    def test_monty_and_ifrc_evidence_not_independent(self):
        source = next(e for e in self.entries if e["candidate_id"].startswith("ifrc.montandon"))
        ifrc = next(e for e in self.entries if e["candidate_id"].startswith("ifrc.go."))
        self.assertIn("do not count", ifrc["note"].lower())
        self.assertIn("token", source["note"].lower())

    def test_disaster_finance_not_loss_and_glide_not_occurrence(self):
        cerf = next(e for e in self.entries if e["candidate_id"].startswith("unocha.cerf"))
        self.assertIn("not actual physical damage", cerf["note"].lower())
        glide = next(e for e in self.entries if e["candidate_id"].startswith("adrc.glide"))
        self.assertIn("not evidence of one physical", glide["note"].lower())


if __name__ == "__main__":
    unittest.main()
