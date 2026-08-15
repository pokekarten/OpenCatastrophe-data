# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Dependency-free synthetic systemic impact-chain semantics for Issue #317.

The kernel starts after event/scenario identity is supplied. It validates and
analyzes a typed directed acyclic graph without inferring event association,
physical causality, damage, loss, or insurance semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Iterable, Sequence


NODE_ROLES = frozenset(
    {
        "hazard_event",
        "exposed_system",
        "direct_impact",
        "downstream_impact",
        "mitigation_action",
    }
)
EDGE_ROLES = frozenset(
    {"hazard_context", "dependency", "amplification", "mitigation"}
)
SCENARIO_STATES = frozenset({"baseline", "changed_state", "mitigation"})
SCIENTIFIC_ROLES = frozenset(
    {"historical_forensic", "model_assumption", "stakeholder_scenario"}
)
EVIDENCE_CLASSES = SCIENTIFIC_ROLES


class SystemicImpactError(ValueError):
    """Raised when synthetic systemic-impact semantics are ambiguous or unsafe."""


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    state: str
    scientific_role: str
    reference: str


@dataclass(frozen=True)
class ImpactNode:
    node_id: str
    role: str
    association_ref: str | None = None


@dataclass(frozen=True)
class ImpactEdge:
    edge_id: str
    source: str
    target: str
    role: str
    source_time_utc: datetime
    target_time_utc: datetime
    evidence_class: str
    confidence: Decimal | str | int | float
    uncertainty_note: str
    reference: str


@dataclass(frozen=True)
class ScenarioGraph:
    scenario: Scenario
    nodes: Sequence[ImpactNode]
    edges: Sequence[ImpactEdge]


@dataclass(frozen=True)
class ScenarioResult:
    scenario: Scenario
    nodes: tuple[ImpactNode, ...]
    edges: tuple[ImpactEdge, ...]
    topological_order: tuple[str, ...]
    downstream_reachability: tuple[tuple[str, tuple[str, ...]], ...]
    input_kind: str = "fixture"
    scientific_role: str = "methodology_benchmark"


def _identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise SystemicImpactError(f"{field} must be a non-empty trimmed string")
    if any(ord(char) < 32 for char in value):
        raise SystemicImpactError(f"{field} contains control characters")
    return value


def _choice(value: object, *, field: str, allowed: frozenset[str]) -> str:
    text = _identifier(value, field=field)
    if text not in allowed:
        raise SystemicImpactError(
            f"{field} must be one of: {', '.join(sorted(allowed))}"
        )
    return text


def _utc(value: object, *, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise SystemicImpactError(f"{field} must be UTC-aware")
    if value.utcoffset() != timedelta(0):
        raise SystemicImpactError(f"{field} must use UTC offset +00:00")
    return value


def _confidence(value: object) -> Decimal:
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise SystemicImpactError("confidence must be a finite decimal in [0, 1]") from exc
    if not result.is_finite() or result < 0 or result > 1:
        raise SystemicImpactError("confidence must be a finite decimal in [0, 1]")
    return result


def _validate_scenario(scenario: Scenario) -> Scenario:
    if not isinstance(scenario, Scenario):
        raise SystemicImpactError("scenario must be a Scenario")
    return Scenario(
        _identifier(scenario.scenario_id, field="scenario_id"),
        _choice(scenario.state, field="scenario state", allowed=SCENARIO_STATES),
        _choice(
            scenario.scientific_role,
            field="scenario scientific_role",
            allowed=SCIENTIFIC_ROLES,
        ),
        _identifier(scenario.reference, field="scenario reference"),
    )


def _validate_nodes(nodes: Iterable[ImpactNode]) -> dict[str, ImpactNode]:
    if isinstance(nodes, (str, bytes)):
        raise SystemicImpactError("nodes must be an iterable of ImpactNode values")
    result: dict[str, ImpactNode] = {}
    try:
        iterator = iter(nodes)
    except TypeError as exc:
        raise SystemicImpactError("nodes must be iterable") from exc
    for node in iterator:
        if not isinstance(node, ImpactNode):
            raise SystemicImpactError("nodes must contain ImpactNode values")
        node_id = _identifier(node.node_id, field="node_id")
        role = _choice(node.role, field=f"role for {node_id}", allowed=NODE_ROLES)
        if node_id in result:
            raise SystemicImpactError(f"duplicate node_id: {node_id}")
        association_ref = node.association_ref
        if association_ref is not None:
            association_ref = _identifier(
                association_ref, field=f"association_ref for {node_id}"
            )
            if role != "hazard_event":
                raise SystemicImpactError(
                    "association_ref is context only for hazard_event nodes"
                )
        result[node_id] = ImpactNode(node_id, role, association_ref)
    if not result:
        raise SystemicImpactError("at least one node is required")
    return result


def _validate_edges(
    edges: Iterable[ImpactEdge], *, nodes: dict[str, ImpactNode]
) -> dict[str, ImpactEdge]:
    if isinstance(edges, (str, bytes)):
        raise SystemicImpactError("edges must be an iterable of ImpactEdge values")
    result: dict[str, ImpactEdge] = {}
    try:
        iterator = iter(edges)
    except TypeError as exc:
        raise SystemicImpactError("edges must be iterable") from exc
    seen_pairs: set[tuple[str, str, str]] = set()
    for edge in iterator:
        if not isinstance(edge, ImpactEdge):
            raise SystemicImpactError("edges must contain ImpactEdge values")
        edge_id = _identifier(edge.edge_id, field="edge_id")
        if edge_id in result:
            raise SystemicImpactError(f"duplicate edge_id: {edge_id}")
        source = _identifier(edge.source, field=f"source for {edge_id}")
        target = _identifier(edge.target, field=f"target for {edge_id}")
        if source not in nodes or target not in nodes:
            raise SystemicImpactError(f"edge {edge_id} has a dangling node reference")
        if source == target:
            raise SystemicImpactError(f"edge {edge_id} cannot be a self-loop")
        role = _choice(edge.role, field=f"role for {edge_id}", allowed=EDGE_ROLES)
        pair_key = (source, target, role)
        if pair_key in seen_pairs:
            raise SystemicImpactError(
                f"duplicate directed edge semantics: {source}->{target} ({role})"
            )
        seen_pairs.add(pair_key)
        source_time = _utc(
            edge.source_time_utc, field=f"source_time_utc for {edge_id}"
        )
        target_time = _utc(
            edge.target_time_utc, field=f"target_time_utc for {edge_id}"
        )
        if source_time > target_time:
            raise SystemicImpactError(f"edge {edge_id} violates temporal ordering")
        evidence_class = _choice(
            edge.evidence_class,
            field=f"evidence_class for {edge_id}",
            allowed=EVIDENCE_CLASSES,
        )
        confidence = _confidence(edge.confidence)
        uncertainty_note = _identifier(
            edge.uncertainty_note, field=f"uncertainty_note for {edge_id}"
        )
        reference = _identifier(edge.reference, field=f"reference for {edge_id}")
        result[edge_id] = ImpactEdge(
            edge_id,
            source,
            target,
            role,
            source_time,
            target_time,
            evidence_class,
            confidence,
            uncertainty_note,
            reference,
        )
    return result


def _topological_order(
    nodes: dict[str, ImpactNode], edges: dict[str, ImpactEdge]
) -> tuple[str, ...]:
    adjacency = {node_id: set() for node_id in nodes}
    indegree = {node_id: 0 for node_id in nodes}
    for edge in edges.values():
        # Topology is node-level: multiple typed edges may describe the same
        # directed node transition, but that transition contributes one indegree.
        if edge.target not in adjacency[edge.source]:
            adjacency[edge.source].add(edge.target)
            indegree[edge.target] += 1

    available = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while available:
        current = available.pop(0)
        order.append(current)
        for target in sorted(adjacency[current]):
            indegree[target] -= 1
            if indegree[target] == 0:
                available.append(target)
                available.sort()
    if len(order) != len(nodes):
        raise SystemicImpactError("systemic impact graph must be acyclic")
    return tuple(order)


def _downstream_reachability(
    nodes: dict[str, ImpactNode], edges: dict[str, ImpactEdge]
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    adjacency = {node_id: set() for node_id in nodes}
    for edge in edges.values():
        adjacency[edge.source].add(edge.target)

    rows: list[tuple[str, tuple[str, ...]]] = []
    for root in sorted(nodes):
        seen: set[str] = set()
        stack = list(sorted(adjacency[root], reverse=True))
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(sorted(adjacency[current] - seen, reverse=True))
        rows.append((root, tuple(sorted(seen))))
    return tuple(rows)


def analyze_graph(graph: ScenarioGraph) -> ScenarioResult:
    """Validate one synthetic scenario graph and return deterministic DAG evidence."""

    if not isinstance(graph, ScenarioGraph):
        raise SystemicImpactError("graph must be a ScenarioGraph")
    scenario = _validate_scenario(graph.scenario)
    nodes = _validate_nodes(graph.nodes)
    edges = _validate_edges(graph.edges, nodes=nodes)
    order = _topological_order(nodes, edges)
    return ScenarioResult(
        scenario=scenario,
        nodes=tuple(sorted(nodes.values(), key=lambda item: item.node_id)),
        edges=tuple(sorted(edges.values(), key=lambda item: item.edge_id)),
        topological_order=order,
        downstream_reachability=_downstream_reachability(nodes, edges),
    )


def analyze_scenarios(graphs: Iterable[ScenarioGraph]) -> tuple[ScenarioResult, ...]:
    """Analyze multiple scenarios without allowing one scenario to overwrite another."""

    if isinstance(graphs, (str, bytes)):
        raise SystemicImpactError("graphs must be an iterable of ScenarioGraph values")
    results: dict[str, ScenarioResult] = {}
    try:
        iterator = iter(graphs)
    except TypeError as exc:
        raise SystemicImpactError("graphs must be iterable") from exc
    for graph in iterator:
        result = analyze_graph(graph)
        scenario_id = result.scenario.scenario_id
        if scenario_id in results:
            raise SystemicImpactError(f"duplicate scenario_id: {scenario_id}")
        results[scenario_id] = result
    if not results:
        raise SystemicImpactError("at least one scenario graph is required")
    return tuple(results[key] for key in sorted(results))
