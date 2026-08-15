# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from scripts.systemic_impact_chain import (
    ImpactEdge,
    ImpactNode,
    Scenario,
    ScenarioGraph,
    ScenarioResult,
    SystemicImpactError,
    analyze_graph,
    analyze_scenarios,
)

UTC = timezone.utc
T0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


def scenario(
    scenario_id: str = "baseline-case",
    *,
    state: str = "baseline",
    scientific_role: str = "model_assumption",
) -> Scenario:
    return Scenario(
        scenario_id=scenario_id,
        state=state,
        scientific_role=scientific_role,
        reference=f"synthetic:{scenario_id}",
    )


def edge(
    edge_id: str,
    source: str,
    target: str,
    *,
    role: str = "dependency",
    source_time: datetime = T0,
    target_time: datetime = T0 + timedelta(hours=1),
    evidence_class: str = "model_assumption",
    confidence: Decimal | str | int | float = "0.75",
    uncertainty_note: str = "synthetic local uncertainty",
    reference: str | None = None,
) -> ImpactEdge:
    return ImpactEdge(
        edge_id=edge_id,
        source=source,
        target=target,
        role=role,
        source_time_utc=source_time,
        target_time_utc=target_time,
        evidence_class=evidence_class,
        confidence=confidence,
        uncertainty_note=uncertainty_note,
        reference=reference or f"synthetic:{edge_id}",
    )


def reachability(result: ScenarioResult) -> dict[str, tuple[str, ...]]:
    return dict(result.downstream_reachability)


class SystemicImpactChainTests(unittest.TestCase):
    def test_result_is_deterministic_under_input_reordering(self) -> None:
        nodes = [
            ImpactNode("c", "downstream_impact"),
            ImpactNode("a", "hazard_event", "association:set-1"),
            ImpactNode("b", "direct_impact"),
        ]
        edges = [
            edge(
                "e2",
                "b",
                "c",
                source_time=T0 + timedelta(hours=1),
                target_time=T0 + timedelta(hours=2),
            ),
            edge("e1", "a", "b", role="hazard_context"),
        ]

        forward = analyze_graph(ScenarioGraph(scenario(), nodes, edges))
        reversed_input = analyze_graph(
            ScenarioGraph(scenario(), list(reversed(nodes)), list(reversed(edges)))
        )

        self.assertEqual(forward, reversed_input)
        self.assertEqual(forward.topological_order, ("a", "b", "c"))
        self.assertEqual(tuple(item.node_id for item in forward.nodes), ("a", "b", "c"))
        self.assertEqual(tuple(item.edge_id for item in forward.edges), ("e1", "e2"))

    def test_parallel_typed_edges_share_node_level_topology(self) -> None:
        nodes = [
            ImpactNode("a", "hazard_event"),
            ImpactNode("b", "direct_impact"),
        ]
        edges = [
            edge("dependency", "a", "b", role="dependency"),
            edge("amplification", "a", "b", role="amplification"),
        ]

        result = analyze_graph(ScenarioGraph(scenario(), nodes, edges))

        self.assertEqual(result.topological_order, ("a", "b"))
        self.assertEqual(reachability(result)["a"], ("b",))
        self.assertEqual(
            tuple((item.edge_id, item.role) for item in result.edges),
            (("amplification", "amplification"), ("dependency", "dependency")),
        )

    def test_unknown_dangling_and_cycle_inputs_fail_closed(self) -> None:
        with self.subTest("unknown node role"):
            with self.assertRaisesRegex(SystemicImpactError, "role"):
                analyze_graph(
                    ScenarioGraph(scenario(), [ImpactNode("a", "unknown")], [])
                )

        with self.subTest("dangling edge"):
            with self.assertRaisesRegex(SystemicImpactError, "dangling"):
                analyze_graph(
                    ScenarioGraph(
                        scenario(),
                        [ImpactNode("a", "hazard_event")],
                        [edge("e1", "a", "missing")],
                    )
                )

        with self.subTest("cycle"):
            nodes = [
                ImpactNode("a", "hazard_event"),
                ImpactNode("b", "direct_impact"),
            ]
            edges = [
                edge("e1", "a", "b", source_time=T0, target_time=T0),
                edge("e2", "b", "a", source_time=T0, target_time=T0),
            ]
            with self.assertRaisesRegex(SystemicImpactError, "acyclic"):
                analyze_graph(ScenarioGraph(scenario(), nodes, edges))

    def test_removing_dependency_changes_only_controlled_downstream_paths(self) -> None:
        nodes = [
            ImpactNode("hazard", "hazard_event"),
            ImpactNode("direct", "direct_impact"),
            ImpactNode("dependent", "downstream_impact"),
            ImpactNode("independent", "downstream_impact"),
        ]
        fixed_edges = [
            edge("trigger", "hazard", "direct", role="hazard_context"),
            edge("other", "hazard", "independent"),
        ]
        controlling = edge("controlled", "direct", "dependent")

        full = reachability(
            analyze_graph(ScenarioGraph(scenario(), nodes, fixed_edges + [controlling]))
        )
        reduced = reachability(
            analyze_graph(ScenarioGraph(scenario(), nodes, fixed_edges))
        )

        self.assertEqual(full["independent"], reduced["independent"])
        self.assertEqual(full["dependent"], reduced["dependent"])
        self.assertEqual(reduced["hazard"], ("direct", "independent"))
        self.assertEqual(full["hazard"], ("dependent", "direct", "independent"))
        self.assertEqual(full["direct"], ("dependent",))
        self.assertEqual(reduced["direct"], ())

    def test_scenarios_remain_separately_addressable(self) -> None:
        node = ImpactNode("hazard", "hazard_event")
        baseline = ScenarioGraph(scenario("baseline-case"), [node], [])
        mitigation = ScenarioGraph(
            scenario("mitigation-case", state="mitigation"), [node], []
        )

        results = analyze_scenarios([mitigation, baseline])

        self.assertEqual(
            tuple(item.scenario.scenario_id for item in results),
            ("baseline-case", "mitigation-case"),
        )
        self.assertEqual(
            tuple(item.scenario.state for item in results),
            ("baseline", "mitigation"),
        )
        with self.assertRaisesRegex(SystemicImpactError, "duplicate scenario_id"):
            analyze_scenarios([baseline, baseline])

    def test_uncertainty_and_provenance_stay_edge_local(self) -> None:
        nodes = [
            ImpactNode("hazard", "hazard_event"),
            ImpactNode("direct", "direct_impact"),
            ImpactNode("downstream", "downstream_impact"),
        ]
        edges = [
            edge(
                "physical",
                "hazard",
                "direct",
                role="hazard_context",
                evidence_class="historical_forensic",
                confidence="0.90",
                uncertainty_note="event attribution uncertainty",
                reference="synthetic:forensic-record",
            ),
            edge(
                "dependency",
                "direct",
                "downstream",
                evidence_class="stakeholder_scenario",
                confidence="0.35",
                uncertainty_note="dependency assumption uncertainty",
                reference="synthetic:stakeholder-assumption",
            ),
        ]

        result = analyze_graph(ScenarioGraph(scenario(), nodes, edges))
        by_id = {item.edge_id: item for item in result.edges}

        self.assertEqual(by_id["physical"].confidence, Decimal("0.90"))
        self.assertEqual(by_id["dependency"].confidence, Decimal("0.35"))
        self.assertEqual(
            by_id["physical"].reference, "synthetic:forensic-record"
        )
        self.assertEqual(
            by_id["dependency"].reference, "synthetic:stakeholder-assumption"
        )
        self.assertNotEqual(
            by_id["physical"].uncertainty_note,
            by_id["dependency"].uncertainty_note,
        )

    def test_association_reference_is_context_not_causality(self) -> None:
        hazard = ImpactNode("hazard", "hazard_event", "association:event-set-7")
        result = analyze_graph(ScenarioGraph(scenario(), [hazard], []))

        self.assertEqual(result.nodes[0].association_ref, "association:event-set-7")
        self.assertEqual(result.edges, ())
        self.assertEqual(reachability(result)["hazard"], ())

        with self.assertRaisesRegex(SystemicImpactError, "context only"):
            analyze_graph(
                ScenarioGraph(
                    scenario(),
                    [ImpactNode("impact", "direct_impact", "association:event-set-7")],
                    [],
                )
            )

    def test_physical_trigger_role_is_rejected_for_noncausal_evidence(self) -> None:
        nodes = [
            ImpactNode("hazard", "hazard_event"),
            ImpactNode("impact", "direct_impact"),
        ]
        for evidence_class in ("model_assumption", "stakeholder_scenario"):
            with self.subTest(evidence_class=evidence_class):
                with self.assertRaisesRegex(SystemicImpactError, "role"):
                    analyze_graph(
                        ScenarioGraph(
                            scenario(),
                            nodes,
                            [
                                edge(
                                    "unsupported-trigger",
                                    "hazard",
                                    "impact",
                                    role="physical_trigger",
                                    evidence_class=evidence_class,
                                )
                            ],
                        )
                    )

    def test_utc_confidence_temporal_and_duplicate_validation(self) -> None:
        nodes = [
            ImpactNode("a", "hazard_event"),
            ImpactNode("b", "direct_impact"),
        ]

        cases = {
            "non-utc offset": edge(
                "offset",
                "a",
                "b",
                source_time=datetime(
                    2026, 1, 1, tzinfo=timezone(timedelta(hours=1))
                ),
                target_time=datetime(
                    2026, 1, 1, 1, tzinfo=timezone(timedelta(hours=1))
                ),
            ),
            "non-finite confidence": edge("nan", "a", "b", confidence="NaN"),
            "reversed time": edge(
                "reverse",
                "a",
                "b",
                source_time=T0 + timedelta(hours=2),
                target_time=T0 + timedelta(hours=1),
            ),
        }
        for label, invalid_edge in cases.items():
            with self.subTest(label):
                with self.assertRaises(SystemicImpactError):
                    analyze_graph(ScenarioGraph(scenario(), nodes, [invalid_edge]))

        with self.subTest("duplicate node"):
            with self.assertRaisesRegex(SystemicImpactError, "duplicate node_id"):
                analyze_graph(
                    ScenarioGraph(
                        scenario(),
                        [ImpactNode("a", "hazard_event"), ImpactNode("a", "hazard_event")],
                        [],
                    )
                )

        with self.subTest("duplicate directed edge semantics"):
            with self.assertRaisesRegex(SystemicImpactError, "duplicate directed edge"):
                analyze_graph(
                    ScenarioGraph(
                        scenario(),
                        nodes,
                        [edge("e1", "a", "b"), edge("e2", "a", "b")],
                    )
                )

    def test_output_is_fixture_methodology_without_loss_semantics(self) -> None:
        result = analyze_graph(
            ScenarioGraph(
                scenario(scientific_role="stakeholder_scenario"),
                [ImpactNode("hazard", "hazard_event")],
                [],
            )
        )

        self.assertEqual(result.input_kind, "fixture")
        self.assertEqual(result.scientific_role, "methodology_benchmark")
        self.assertEqual(result.scenario.scientific_role, "stakeholder_scenario")

        field_names = {
            *ScenarioResult.__dataclass_fields__,
            *ImpactNode.__dataclass_fields__,
            *ImpactEdge.__dataclass_fields__,
        }
        prohibited = {"damage", "loss", "tiv", "policy", "reinsurance", "capital"}
        lowered = " ".join(sorted(field_names)).lower()
        self.assertTrue(all(term not in lowered for term in prohibited))


if __name__ == "__main__":
    unittest.main()
