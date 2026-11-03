# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic, offline negative controls for Monty cross-source event semantics."""
from copy import deepcopy
import unittest
from research_runners import monty_stac_event_linkage_gate_v0 as gate


class MontyEventLinkageTests(unittest.TestCase):
    def setUp(self):
        self.cut = "2023-02-06T12:00:00Z"

    def make(self, provider="src-a", issuer="earthquake", corr="CORR",
             date="2023-02-06T01:17:34Z", received="2023-02-06T02:00:00Z",
             episode=1, bbox=None):
        return gate.parse_source_event(
            gate.fixture_item(issuer, corr, date, episode=episode, bbox=bbox),
            trusted_source_namespace=provider, controlled_received_at_utc=received
        )

    def compare(self, a, b, cut=None):
        return gate.compare_event_sources(a, b, knowledge_cut_utc=self.cut if cut is None else cut)

    def test_same_corr_id_across_sources_is_not_event_authority(self):
        out = self.compare(self.make("usgs", "EQ-1", "SAME"), self.make("gdacs", "ALERT-1", "SAME"))
        self.assertEqual(out["state"], "CROSS_SOURCE_CANDIDATE_SPATIAL_UNKNOWN")
        self.assertFalse(out["corr_id_global_join_authorized"])
        self.assertFalse(out["physical_event_identity_verified"])
        self.assertFalse(out["contractual_occurrence_verified"])

    def test_different_corr_ids_can_be_candidate_never_authoritative(self):
        a = self.make("usgs", "E-1", "C1", bbox=[35, 35, 40, 40])
        b = self.make("gdacs", "E-2", "C2", bbox=[36, 36, 38, 38])
        out = self.compare(a, b)
        self.assertEqual(out["state"], "CROSS_SOURCE_CANDIDATE_REQUIRES_REVIEW")
        self.assertEqual(out["spatial_check"], "overlap")
        self.assertFalse(out["observed_loss_or_model_admitted"])

    def test_same_source_alias_and_episode_only(self):
        a=self.make("provider-1","local-EQ","C1")
        b=self.make("provider-1","local-EQ","DIFFERENT")
        out=self.compare(a,b)
        self.assertEqual(out["state"],"SAME_SOURCE_EVENT_EPISODE_ALIAS_ONLY")
        self.assertFalse(out["physical_event_identity_verified"])

    def test_same_source_event_id_different_episode_must_not_merge(self):
        a=self.make("provider-1","storm-A","C1",episode=1)
        b=self.make("provider-1","storm-A","C1",episode=2)
        self.assertEqual(self.compare(a,b)["state"],"SEPARATE_SOURCE_EVENT_EPISODE_NEEDS_REVIEW")

    def test_two_distinct_earthquakes_same_day_country_and_corr_id_do_not_merge(self):
        a=self.make("usgs","us6000jllz","C1","2023-02-06T01:17:34Z")
        b=self.make("gdacs","us6000jlqa","C1","2023-02-06T10:24:48Z")
        self.assertEqual(self.compare(a,b)["state"],"NONOVERLAPPING_EVENT_TIMES_NOT_MATCHED")

    def test_future_receipt_and_missing_receipt_block_asof(self):
        a=self.make("src-a","A","C")
        b=self.make("src-b","B","C",received="2023-02-07T00:00:00Z")
        self.assertEqual(self.compare(a,b)["state"],"NOT_KNOWABLE_AT_CUT")
        absent=self.make("src-b","B","C",received=None)
        self.assertEqual(self.compare(a,absent)["state"],"NOT_KNOWABLE_AT_CUT")

    def test_event_time_is_not_receipt_time(self):
        a=self.make("src-a","A","C",received="2026-11-03T09:00:00Z")
        b=self.make("src-b","B","C")
        self.assertEqual(self.compare(a,b)["state"],"NOT_KNOWABLE_AT_CUT")

    def test_country_mismatch_not_a_definitive_physical_nonmatch(self):
        a=self.make("usgs","E","C")
        item=gate.fixture_item("E2","C","2023-02-06T01:17:34Z")
        item["properties"]["monty:country_codes"]=["SYR"]
        b=gate.parse_source_event(item,trusted_source_namespace="gdacs",
            controlled_received_at_utc="2023-02-06T02:00:00Z")
        self.assertEqual(self.compare(a,b)["state"],"NO_COUNTRY_OVERLAP_UNRESOLVED")

    def test_hazard_taxonomy_no_exact_overlap_must_remain_unresolved(self):
        a=self.make("usgs","E","C")
        item=gate.fixture_item("E2","C","2023-02-06T01:17:34Z")
        item["properties"]["monty:hazard_codes"]=["MH0100"]
        b=gate.parse_source_event(item,trusted_source_namespace="gdacs",
            controlled_received_at_utc="2023-02-06T02:00:00Z")
        self.assertEqual(self.compare(a,b)["state"],"NO_EXACT_HAZARD_CODE_OVERLAP_UNRESOLVED")

    def test_spatial_bbox_nonoverlap_blocks_automatic_candidate(self):
        a=self.make("src-a","E","C",bbox=[35,35,36,36])
        b=self.make("src-b","X","C",bbox=[40,40,42,42])
        self.assertEqual(self.compare(a,b)["state"],"NONOVERLAPPING_BBOX_NOT_MATCHED")

    def test_source_must_be_explicitly_supplied_by_trusted_caller(self):
        item=gate.fixture_item("A","C","2023-02-06T01:17:34Z")
        item["properties"]["source"]="spoofed"
        with self.assertRaisesRegex(gate.MontyLinkageBlocked,"trusted source"):
            gate.parse_source_event(item,trusted_source_namespace="",
                controlled_received_at_utc="2023-02-06T02:00:00Z")

    def test_reference_hazard_impact_and_nonfeature_rejected(self):
        item=gate.fixture_item("A","C","2023-02-06T01:17:34Z")
        for roles in (["event","reference"],["hazard"],["impact"],["event","source","impact"]):
            with self.subTest(roles=roles):
                test=deepcopy(item);test["roles"]=roles
                with self.assertRaisesRegex(gate.MontyLinkageBlocked,"source event role"):
                    gate.parse_source_event(test,trusted_source_namespace="gdacs",
                        controlled_received_at_utc="2023-02-06T02:00:00Z")
        item["type"]="Collection"
        with self.assertRaises(gate.MontyLinkageBlocked):
            gate.parse_source_event(item,trusted_source_namespace="gdacs",
                controlled_received_at_utc="2023-02-06T02:00:00Z")

    def test_missing_source_id_country_hazard_corr_episode_fail_closed(self):
        for key in ("monty:src_event_id","monty:country_codes","monty:hazard_codes",
                    "monty:corr_id","monty:episode_number"):
            with self.subTest(key=key):
                item=gate.fixture_item("A","C","2023-02-06T01:17:34Z")
                item["properties"].pop(key)
                with self.assertRaises(gate.MontyLinkageBlocked):
                    gate.parse_source_event(item,trusted_source_namespace="gdacs",
                        controlled_received_at_utc="2023-02-06T02:00:00Z")

    def test_interval_validated_not_used_as_publish_time(self):
        item=gate.fixture_item("A","C","2023-02-06T01:17:34Z")
        item["properties"]["datetime"]=None
        item["properties"]["start_datetime"]="2023-02-06T01:15:00Z"
        item["properties"]["end_datetime"]="2023-02-06T02:15:00Z"
        a=gate.parse_source_event(item,trusted_source_namespace="one",
            controlled_received_at_utc="2023-02-06T03:00:00Z")
        self.assertLess(a.event_start,a.event_end)
        item["properties"]["end_datetime"]="2023-02-06T00:00:00Z"
        with self.assertRaisesRegex(gate.MontyLinkageBlocked,"reversed"):
            gate.parse_source_event(item,trusted_source_namespace="one",
                controlled_received_at_utc="2023-02-06T03:00:00Z")

    def test_unknown_or_invalid_bbox_and_clock_fail_closed(self):
        item=gate.fixture_item("A","C","2023-02-06T01:17:34Z",bbox=[200,35,220,40])
        with self.assertRaisesRegex(gate.MontyLinkageBlocked,"bbox"):
            gate.parse_source_event(item,trusted_source_namespace="src",
                controlled_received_at_utc="2023-02-06T03:00:00Z")
        with self.assertRaises(gate.MontyLinkageBlocked):
            self.make(date="2023-02-06 01:17:34")
        with self.assertRaises(gate.MontyLinkageBlocked):
            self.make(received="2023-02-06T02:00:00")

    def test_pair_order_invariance(self):
        a=self.make("src-a","A","C1",bbox=[35,35,40,40])
        b=self.make("src-b","B","C2",bbox=[35,35,40,40])
        self.assertEqual(self.compare(a,b),self.compare(b,a))

    def test_demo(self):
        d=gate.demonstration()
        self.assertEqual(d["scope"],"INVENTED_STAC_METADATA_ONLY")
        self.assertEqual(d["shock_sequence"]["state"],"NONOVERLAPPING_EVENT_TIMES_NOT_MATCHED")
        self.assertFalse(d["candidate"]["physical_event_identity_verified"])


if __name__ == "__main__":
    unittest.main()
