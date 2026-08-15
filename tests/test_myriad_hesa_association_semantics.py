# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.myriad_hesa_association_semantics import (
    AssociationConfig,
    AssociationEdge,
    AssociationSemanticError,
    PairEvidence,
    SyntheticEvent,
    associate_events,
)


def event(
    event_id: str,
    start: str,
    end: str,
    *,
    hazard_code: str = "HZ",
    dynamic: bool = False,
    peril_label: str | None = None,
) -> SyntheticEvent:
    return SyntheticEvent(
        event_id,
        hazard_code,
        start,
        end,
        dynamic=dynamic,
        peril_label=peril_label,
    )


class MyriadHesaAssociationSemanticTests(unittest.TestCase):
    def test_direct_association_and_spatial_rejection(self) -> None:
        events = (
            event("A", "2020-01-01T00:00:00Z", "2020-01-03T00:00:00Z"),
            event("B", "2020-01-02T00:00:00Z", "2020-01-04T00:00:00Z"),
            event("C", "2020-01-02T00:00:00Z", "2020-01-04T00:00:00Z"),
        )
        result = associate_events(
            events,
            (
                PairEvidence("A", "B", True),
                PairEvidence("A", "C", False),
                PairEvidence("B", "C", False),
            ),
        )
        self.assertEqual(
            result.direct_edges,
            (AssociationEdge("A", "B", 0, False),),
        )
        self.assertEqual(result.event_sets, (("A", "B"),))
        self.assertEqual(result.unassociated_event_ids, ("C",))

    def test_inclusive_boundary_and_positive_lag(self) -> None:
        touching = (
            event("A", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
            event("B", "2020-01-02T00:00:00Z", "2020-01-03T00:00:00Z"),
        )
        result = associate_events(touching, (PairEvidence("A", "B", True),))
        self.assertEqual(len(result.direct_edges), 1)

        near_miss = (
            event("A", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
            event("B", "2020-01-04T00:00:00Z", "2020-01-05T00:00:00Z"),
        )
        without_lag = associate_events(
            near_miss,
            (PairEvidence("A", "B", True),),
        )
        with_lag = associate_events(
            near_miss,
            (PairEvidence("A", "B", True),),
            config=AssociationConfig(lag_days=2),
        )
        self.assertEqual(without_lag.direct_edges, ())
        self.assertEqual(
            with_lag.direct_edges,
            (AssociationEdge("A", "B", 2, False),),
        )

    def test_dynamic_pairs_require_and_apply_active_overlap(self) -> None:
        events = (
            event(
                "A",
                "2020-01-01T00:00:00Z",
                "2020-01-03T00:00:00Z",
                dynamic=True,
            ),
            event("B", "2020-01-02T00:00:00Z", "2020-01-04T00:00:00Z"),
        )
        rejected = associate_events(
            events,
            (PairEvidence("A", "B", True, active_overlap=False),),
        )
        accepted = associate_events(
            events,
            (PairEvidence("A", "B", True, active_overlap=True),),
        )
        self.assertEqual(rejected.direct_edges, ())
        self.assertEqual(
            accepted.direct_edges,
            (AssociationEdge("A", "B", 0, True),),
        )
        with self.assertRaisesRegex(AssociationSemanticError, "active_overlap"):
            associate_events(events, (PairEvidence("A", "B", True),))

    def test_dynamic_spatially_disjoint_pair_needs_no_active_evidence(self) -> None:
        events = (
            event(
                "A",
                "2020-01-01T00:00:00Z",
                "2020-01-03T00:00:00Z",
                dynamic=True,
            ),
            event("B", "2020-01-02T00:00:00Z", "2020-01-04T00:00:00Z"),
        )
        result = associate_events(events, (PairEvidence("A", "B", False),))
        self.assertEqual(result.direct_edges, ())
        self.assertEqual(result.event_sets, ())
        self.assertEqual(result.unassociated_event_ids, ("A", "B"))

    def test_dynamic_temporally_disjoint_pair_needs_no_active_evidence(self) -> None:
        events = (
            event(
                "A",
                "2020-01-01T00:00:00Z",
                "2020-01-02T00:00:00Z",
                dynamic=True,
            ),
            event("B", "2020-01-05T00:00:00Z", "2020-01-06T00:00:00Z"),
        )
        result = associate_events(events, (PairEvidence("A", "B", True),))
        self.assertEqual(result.direct_edges, ())
        self.assertEqual(result.event_sets, ())
        self.assertEqual(result.unassociated_event_ids, ("A", "B"))

    def test_transitive_event_set_preserves_direct_edge_semantics(self) -> None:
        events = (
            event("A", "2020-01-01T00:00:00Z", "2020-01-04T00:00:00Z"),
            event("B", "2020-01-01T00:00:00Z", "2020-01-04T00:00:00Z"),
            event("C", "2020-01-01T00:00:00Z", "2020-01-04T00:00:00Z"),
        )
        result = associate_events(
            events,
            (
                PairEvidence("A", "B", True),
                PairEvidence("B", "C", True),
                PairEvidence("A", "C", False),
            ),
        )
        self.assertEqual(
            result.direct_edges,
            (
                AssociationEdge("A", "B", 0, False),
                AssociationEdge("B", "C", 0, False),
            ),
        )
        self.assertEqual(result.event_sets, (("A", "B", "C"),))
        self.assertNotIn(AssociationEdge("A", "C", 0, False), result.direct_edges)

    def test_input_and_evidence_order_are_deterministic(self) -> None:
        events = (
            event("C", "2020-01-01T00:00:00Z", "2020-01-03T00:00:00Z"),
            event("A", "2020-01-01T00:00:00Z", "2020-01-03T00:00:00Z"),
            event("B", "2020-01-01T00:00:00Z", "2020-01-03T00:00:00Z"),
        )
        evidence = (
            PairEvidence("C", "A", False),
            PairEvidence("C", "B", True),
            PairEvidence("B", "A", True),
        )
        first = associate_events(events, evidence)
        second = associate_events(tuple(reversed(events)), tuple(reversed(evidence)))
        self.assertEqual(first, second)

    def test_pair_and_event_evidence_fail_closed(self) -> None:
        events = (
            event("A", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
            event("B", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
            event("C", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
        )
        with self.assertRaisesRegex(AssociationSemanticError, "missing pair evidence"):
            associate_events(events, (PairEvidence("A", "B", True),))
        with self.assertRaisesRegex(AssociationSemanticError, "duplicate/conflicting"):
            associate_events(
                events[:2],
                (
                    PairEvidence("A", "B", True),
                    PairEvidence("B", "A", False),
                ),
            )
        with self.assertRaisesRegex(AssociationSemanticError, "unknown event"):
            associate_events(events[:2], (PairEvidence("A", "Z", True),))
        duplicate_events = (events[0], events[0])
        with self.assertRaisesRegex(AssociationSemanticError, "duplicate event_id"):
            associate_events(duplicate_events, ())

    def test_time_and_config_validation_fail_closed(self) -> None:
        with self.assertRaisesRegex(AssociationSemanticError, "explicitly UTC-aware"):
            associate_events(
                (
                    event("A", "2020-01-01T00:00:00", "2020-01-02T00:00:00Z"),
                    event("B", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
                ),
                (PairEvidence("A", "B", True),),
            )
        with self.assertRaisesRegex(AssociationSemanticError, "must not precede"):
            associate_events(
                (
                    event("A", "2020-01-03T00:00:00Z", "2020-01-02T00:00:00Z"),
                    event("B", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
                ),
                (PairEvidence("A", "B", True),),
            )
        with self.assertRaisesRegex(AssociationSemanticError, "non-negative integer"):
            associate_events(
                (
                    event("A", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
                    event("B", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
                ),
                (PairEvidence("A", "B", True),),
                config=AssociationConfig(lag_days=-1),
            )
        with self.assertRaisesRegex(AssociationSemanticError, "supported temporal range"):
            associate_events(
                (
                    event("A", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
                    event("B", "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z"),
                ),
                (PairEvidence("A", "B", True),),
                config=AssociationConfig(lag_days=1_000_000_000),
            )

    def test_source_hazard_codes_and_noncausal_boundary_are_preserved(self) -> None:
        events = (
            event(
                "A",
                "2020-01-01T00:00:00Z",
                "2020-01-02T00:00:00Z",
                hazard_code="SRC_A",
                peril_label="flood",
            ),
            event(
                "B",
                "2020-01-01T00:00:00Z",
                "2020-01-02T00:00:00Z",
                hazard_code="SRC_B",
                peril_label="flood",
            ),
        )
        result = associate_events(events, (PairEvidence("A", "B", True),))
        identities = {item.event_id: item for item in result.event_identities}
        self.assertEqual(identities["A"].hazard_code, "SRC_A")
        self.assertEqual(identities["B"].hazard_code, "SRC_B")
        self.assertEqual(identities["A"].peril_label, identities["B"].peril_label)
        self.assertEqual(result.input_kind, "fixture")
        self.assertEqual(result.scientific_role, "benchmark")
        self.assertEqual(result.semantic_boundary, "association_not_causality")
        self.assertEqual(result.reference_repository, "judithclaassen/MYRIAD-HESA")
        self.assertEqual(
            result.reference_commit,
            "dcd2969a8f7c336853bdfa40efd7aa00798ee04b",
        )


if __name__ == "__main__":
    unittest.main()
