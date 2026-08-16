# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest

from scripts.myriad_hesa_association_semantics import (
    AssociationConfig,
    AssociationEdge,
    AssociationSemanticError,
    GROUPING_SEMANTICS,
    MAX_SYNTHETIC_EVENTS,
    PairEvidence,
    REFERENCE_SOURCE_BLOB_SHA1,
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


def same_time_events(*names: str) -> tuple[SyntheticEvent, ...]:
    return tuple(
        event(name, "2020-01-01T00:00:00Z", "2020-01-04T00:00:00Z")
        for name in names
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

    def test_transitive_chain_does_not_form_three_event_group(self) -> None:
        events = same_time_events("A", "B", "C")
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
        self.assertEqual(result.event_sets, (("A", "B"), ("B", "C")))
        self.assertNotIn(("A", "B", "C"), result.event_sets)
        self.assertEqual(result.unassociated_event_ids, ())

    def test_pairwise_complete_triangle_forms_three_event_group(self) -> None:
        events = same_time_events("A", "B", "C")
        result = associate_events(
            events,
            (
                PairEvidence("A", "B", True),
                PairEvidence("A", "C", True),
                PairEvidence("B", "C", True),
            ),
        )
        self.assertEqual(result.event_sets, (("A", "B", "C"),))
        self.assertEqual(len(result.direct_edges), 3)
        self.assertEqual(result.unassociated_event_ids, ())

    def test_overlapping_reference_groups_remain_separate(self) -> None:
        events = same_time_events("A", "B", "C", "D")
        result = associate_events(
            events,
            (
                PairEvidence("A", "B", True),
                PairEvidence("A", "C", True),
                PairEvidence("A", "D", False),
                PairEvidence("B", "C", True),
                PairEvidence("B", "D", True),
                PairEvidence("C", "D", True),
            ),
        )
        self.assertEqual(
            result.event_sets,
            (("A", "B", "C"), ("B", "C", "D")),
        )

    def test_pinned_reference_n5_nonmaximal_group_is_preserved(self) -> None:
        events = same_time_events("A", "B", "C", "D", "E")
        result = associate_events(
            events,
            (
                PairEvidence("A", "B", True),
                PairEvidence("A", "C", True),
                PairEvidence("A", "D", True),
                PairEvidence("A", "E", True),
                PairEvidence("B", "C", True),
                PairEvidence("B", "D", True),
                PairEvidence("B", "E", True),
                PairEvidence("C", "D", False),
                PairEvidence("C", "E", True),
                PairEvidence("D", "E", False),
            ),
        )
        self.assertEqual(
            result.event_sets,
            (
                ("A", "B", "C", "E"),
                ("A", "B", "D"),
                ("A", "B", "E"),
            ),
        )
        self.assertIn(("A", "B", "E"), result.event_sets)

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
        self.assertEqual(first.event_sets, (("A", "B"), ("B", "C")))

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

    def test_resource_bound_fails_before_pair_evidence_expansion(self) -> None:
        events = tuple(
            event(
                f"E{index:02d}",
                "2020-01-01T00:00:00Z",
                "2020-01-02T00:00:00Z",
            )
            for index in range(MAX_SYNTHETIC_EVENTS + 1)
        )
        with self.assertRaisesRegex(
            AssociationSemanticError,
            f"at most {MAX_SYNTHETIC_EVENTS} events",
        ):
            associate_events(events, ())

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
        self.assertEqual(result.grouping_semantics, "pinned_hesa_makegroups_rows_in")
        self.assertEqual(GROUPING_SEMANTICS, "pinned_hesa_makegroups_rows_in")
        self.assertEqual(
            REFERENCE_SOURCE_BLOB_SHA1,
            "0722b7e6a9ab34b35caa1de56ed4847c65da7aa2",
        )
        self.assertEqual(result.reference_repository, "judithclaassen/MYRIAD-HESA")
        self.assertEqual(
            result.reference_commit,
            "dcd2969a8f7c336853bdfa40efd7aa00798ee04b",
        )


if __name__ == "__main__":
    unittest.main()
