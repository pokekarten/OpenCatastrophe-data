# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Canonical GHSL/GASPAR source metadata, projection and scientific unit tests."""
import json
from pathlib import Path
import unittest

from research_runners.check_ghsl_source_metadata_v0 import test_current_catalogue
from research_runners.test_ghsl_source_metadata_v0 import SourceMetadataTests
from scripts.source_landscape_contract import load_landscape_shard, load_landscape_shards
from scripts.render_public_views import render_landscape_markdown

ROOT = Path(__file__).resolve().parents[1]
SHARDS = (
    "sources-ghsl-built-s-2026.json",
    "sources-ghsl-built-v-2026.json",
    "sources-fr-recognition-2026.json",
    "sources-fr-commune-recognition-2026.json",
)


class FourResearchSourcesIntegratedTests(unittest.TestCase):
    def test_four_registered_sources_share_supported_v1_contract(self):
        seen=set()
        for filename in SHARDS:
            with self.subTest(shard=filename):
                path=ROOT/"landscape"/filename
                payload=load_landscape_shard(path)
                self.assertEqual(payload["schema_version"],"1.0.0")
                self.assertIn("Non-admission",payload["purpose"])
                self.assertEqual(len(payload["entries"]),1)
                entry=payload["entries"][0]
                self.assertEqual(entry["admission_status"],"not_admitted")
                self.assertEqual(entry["rights_review_status"],"not_reviewed")
                self.assertEqual(entry["scientific_review_status"],"not_reviewed")
                self.assertNotIn(entry["candidate_id"],seen)
                seen.add(entry["candidate_id"])

    def test_every_generated_markdown_matches_canonical_renderer(self):
        for name in SHARDS:
            with self.subTest(name=name):
                path=ROOT/"landscape"/name
                source=load_landscape_shard(path)
                self.assertEqual(path.with_suffix(".md").read_text("utf-8"),
                                 render_landscape_markdown(path,source))

    def test_ghsl_area_volume_units_cannot_be_swapped(self):
        info=test_current_catalogue(ROOT)
        self.assertEqual(info["candidate_count"],2)
        self.assertFalse(info["model_input_admitted"])
        surf=load_landscape_shard(ROOT/"landscape"/SHARDS[0])["entries"][0]
        vol=load_landscape_shard(ROOT/"landscape"/SHARDS[1])["entries"][0]
        self.assertIn("m2",surf["resolution_or_granularity"])
        self.assertNotIn("m3",surf["resolution_or_granularity"])
        self.assertIn("m3",vol["resolution_or_granularity"])
        self.assertNotIn("m2",vol["resolution_or_granularity"])

    def test_french_primary_and_derived_publishers_are_separate(self):
        source=load_landscape_shard(ROOT/"landscape"/SHARDS[2])["entries"][0]
        derivative=load_landscape_shard(ROOT/"landscape"/SHARDS[3])["entries"][0]
        self.assertNotEqual(source["candidate_id"],derivative["candidate_id"])
        self.assertNotEqual(source["authoritative_url"],derivative["authoritative_url"])
        self.assertIn("GASPAR",source["name"])
        self.assertIn("TACCT",derivative["provider"])
        self.assertIn("not a CAT physical event",derivative["note"])

    def test_all_registered_candidates_still_have_distinct_global_ids(self):
        shards=load_landscape_shards(ROOT/"landscape")
        ids=[e["candidate_id"] for _,p in shards for e in p["entries"]]
        self.assertEqual(len(ids),len(set(ids)))


if __name__=="__main__":
    unittest.main()
