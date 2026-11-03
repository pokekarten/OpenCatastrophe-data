# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline adversarial contract tests; synthetic product metadata only."""
import unittest
from dataclasses import replace
from research_runners import usgs_product_vintage_gate_v0 as m


class ProductVintageGateTests(unittest.TestCase):
    def setUp(self):
        self.rows = m.synthetic_fixture()
        self.key = ("synthetic-network", "shakemap", "syn-shake")

    def replay(self, cut: str, rows=None):
        return m.replay_product_asof(self.rows if rows is None else rows,
                                    event_id="SYNTHETIC-EQ",
                                    product_key=self.key, knowledge_cut_utc=cut)

    def test_first_receipt_selection(self):
        first = self.replay("2023-02-06T01:25:00Z")
        self.assertEqual(first["state"], "CONTROLLED_RECEIPT_METADATA_ELIGIBLE")
        self.assertEqual(first["product_version"], self.rows[0].update_time_ms)
        self.assertFalse(first["model_admitted"])
        self.assertFalse(first["forecast_skill_proven"])

    def test_update_time_does_not_establish_receipt(self):
        cut = "2023-02-06T02:01:00Z"
        observed = self.replay(cut)
        naive = m.retrospective_update_preview(self.rows, event_id="SYNTHETIC-EQ",
                                                product_key=self.key, product_update_cut_utc=cut)
        self.assertEqual(observed["product_version"], self.rows[0].update_time_ms)
        self.assertEqual(naive["candidate_update_time_ms"], self.rows[1].update_time_ms)
        self.assertEqual(naive["state"], "RETROSPECTIVE_PRODUCT_TIME_ONLY_NOT_FORECAST")
        self.assertFalse(naive["historical_public_availability_proven"])

    def test_second_receipt_accepted_only_after_observation(self):
        late = self.replay("2023-02-06T02:03:00Z")
        self.assertEqual(late["product_version"], self.rows[1].update_time_ms)
        self.assertEqual(late["controlled_receipt_id"], "LOCAL-R1")

    def test_unpinned_product_never_eligible(self):
        losspager = m.replay_product_asof(
            self.rows, event_id="SYNTHETIC-EQ",
            product_key=("synthetic-network", "losspager", "syn-pager"),
            knowledge_cut_utc="2023-02-06T04:00:00Z")
        self.assertEqual(losspager["state"], "NO_CONTEMPORANEOUS_CONTROLLED_RECEIPT")

    def test_self_declared_update_time_cannot_prove_historical_availability(self):
        later = (replace(self.rows[0], controlled_receipt_id="LOCAL-2026",
                         first_received_at_utc="2026-11-02T12:00:00Z"),) + self.rows[1:]
        out = self.replay("2023-02-06T01:25:00Z", later)
        self.assertEqual(out["state"], "NO_CONTEMPORANEOUS_CONTROLLED_RECEIPT")

    def test_sha_without_receipt_not_eligible(self):
        unobserved = (replace(self.rows[0], controlled_receipt_id=None,
                              first_received_at_utc=None),) + self.rows[1:]
        self.assertEqual(self.replay("2023-02-06T01:25:00Z", unobserved)["state"],
                         "NO_CONTEMPORANEOUS_CONTROLLED_RECEIPT")

    def test_receipt_without_original_hash_blocks(self):
        bad = (replace(self.rows[0], original_product_sha256=None),) + self.rows[1:]
        self.assertEqual(self.replay("2023-02-06T01:25:00Z", bad)["state"], "ORIGINAL_BYTES_NOT_PINNED")

    def test_source_product_key_is_exact_not_global_preference(self):
        other_key = ("other-network", "shakemap", "syn-shake")
        other = replace(self.rows[0], source=other_key[0])
        rows = self.rows + (other,)
        result = m.replay_product_asof(rows, event_id="SYNTHETIC-EQ",
                                      product_key=other_key,
                                      knowledge_cut_utc="2023-02-06T01:25:00Z")
        self.assertEqual(result["product_key"], list(other_key))
        self.assertNotEqual(result["product_key"], list(self.key))

    def test_duplicate_version_identity_rejected(self):
        with self.assertRaisesRegex(m.ProductVintageBlocked, "duplicate"):
            m.validate_revisions(self.rows + (self.rows[0],), event_id="SYNTHETIC-EQ")

    def test_foreign_event_rejected(self):
        with self.assertRaisesRegex(m.ProductVintageBlocked, "cross-event"):
            m.validate_revisions(self.rows + (replace(self.rows[0], event_id="OTHER"),),
                                 event_id="SYNTHETIC-EQ")

    def test_missing_receipt_pair_rejected(self):
        bad = (replace(self.rows[0], first_received_at_utc=None),) + self.rows[1:]
        with self.assertRaisesRegex(m.ProductVintageBlocked, "accompany"):
            m.validate_revisions(bad, event_id="SYNTHETIC-EQ")

    def test_receipt_cannot_precede_product_update_time(self):
        bad = (replace(self.rows[0], first_received_at_utc="2023-02-06T01:19:59Z"),) + self.rows[1:]
        with self.assertRaisesRegex(m.ProductVintageBlocked, "predates"):
            m.validate_revisions(bad, event_id="SYNTHETIC-EQ")

    def test_delete_does_not_reactivate_old_version(self):
        delete = replace(self.rows[1], status="DELETE")
        result = self.replay("2023-02-06T02:03:00Z", (self.rows[0], delete, self.rows[2]))
        self.assertEqual(result["state"], "DELETED_AS_OF")

    def test_unsupported_status_and_type_rejected(self):
        for modified in (replace(self.rows[0], status="ACTIVE"),
                         replace(self.rows[0], product_type="unknown")):
            with self.subTest(modified=modified):
                with self.assertRaises(m.ProductVintageBlocked):
                    m.validate_revisions((modified,), event_id="SYNTHETIC-EQ")

    def test_unknown_first_knowledge_time_is_not_silent_zero(self):
        no_receipts = tuple(replace(r, first_received_at_utc=None,
                                    controlled_receipt_id=None) for r in self.rows)
        out = self.replay("2023-02-06T04:00:00Z", no_receipts)
        self.assertIsNone(out["product_version"])
        self.assertEqual(out["state"], "NO_CONTEMPORANEOUS_CONTROLLED_RECEIPT")

    def test_permutation_invariant(self):
        r1=self.replay("2023-02-06T02:03:00Z")
        r2=self.replay("2023-02-06T02:03:00Z", tuple(reversed(self.rows)))
        self.assertEqual(r1, r2)

    def test_bad_time_and_malformed_sha_rejected(self):
        with self.assertRaises(m.ProductVintageBlocked):
            self.replay("2023-02-06T01:25:00")
        with self.assertRaisesRegex(m.ProductVintageBlocked, "SHA"):
            m.validate_revisions((replace(self.rows[0], original_product_sha256="bad"),),
                                 event_id="SYNTHETIC-EQ")

    def test_headline(self):
        report=m.check()
        self.assertEqual(len(report["replays"]),3)
        self.assertEqual(report["classification"],"OFFLINE_SYNTHETIC_ONLY")


if __name__=="__main__":
    unittest.main()
