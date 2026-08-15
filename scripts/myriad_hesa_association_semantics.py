# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic MYRIAD-HESA-style association and event-set semantics benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Sequence

REFERENCE_REPOSITORY = "judithclaassen/MYRIAD-HESA"
REFERENCE_COMMIT = "dcd2969a8f7c336853bdfa40efd7aa00798ee04b"
INPUT_KIND = "fixture"
SCIENTIFIC_ROLE = "benchmark"
SEMANTIC_BOUNDARY = "association_not_causality"


class AssociationSemanticError(ValueError):
    """Raised when synthetic association evidence is ambiguous or unsafe."""


@dataclass(frozen=True)
class SyntheticEvent:
    event_id: str
    hazard_code: str
    start_utc: str
    end_utc: str
    dynamic: bool = False
    peril_label: str | None = None


@dataclass(frozen=True)
class PairEvidence:
    event_a: str
    event_b: str
    spatial_overlap: bool
    active_overlap: bool | None = None


@dataclass(frozen=True)
class AssociationConfig:
    lag_days: int = 0


@dataclass(frozen=True, order=True)
class EventIdentity:
    event_id: str
    hazard_code: str
    peril_label: str | None
    dynamic: bool


@dataclass(frozen=True, order=True)
class AssociationEdge:
    event_a: str
    event_b: str
    lag_days: int
    active_overlap_required: bool


@dataclass(frozen=True)
class AssociationResult:
    event_identities: tuple[EventIdentity, ...]
    direct_edges: tuple[AssociationEdge, ...]
    event_sets: tuple[tuple[str, ...], ...]
    unassociated_event_ids: tuple[str, ...]
    reference_repository: str = REFERENCE_REPOSITORY
    reference_commit: str = REFERENCE_COMMIT
    input_kind: str = INPUT_KIND
    scientific_role: str = SCIENTIFIC_ROLE
    semantic_boundary: str = SEMANTIC_BOUNDARY


@dataclass(frozen=True)
class _ValidatedEvent:
    identity: EventIdentity
    start: datetime
    end: datetime


def _trimmed_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise AssociationSemanticError(f"{label} must be a non-empty trimmed string")
    if any(ord(char) < 32 for char in value):
        raise AssociationSemanticError(f"{label} contains control characters")
    return value


def _optional_trimmed_text(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    return _trimmed_text(value, label=label)


def _utc_datetime(value: object, *, label: str) -> datetime:
    if not isinstance(value, str) or not value or value != value.strip():
        raise AssociationSemanticError(
            f"{label} must be a non-empty trimmed ISO-8601 string"
        )
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise AssociationSemanticError(f"{label} must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise AssociationSemanticError(f"{label} must be explicitly UTC-aware")
    return parsed.astimezone(timezone.utc)


def _validate_config(config: AssociationConfig) -> AssociationConfig:
    if not isinstance(config, AssociationConfig):
        raise AssociationSemanticError("config must be AssociationConfig")
    if isinstance(config.lag_days, bool) or not isinstance(config.lag_days, int):
        raise AssociationSemanticError("lag_days must be a non-negative integer")
    if config.lag_days < 0:
        raise AssociationSemanticError("lag_days must be a non-negative integer")
    return config


def _validate_events(events: Iterable[SyntheticEvent]) -> dict[str, _ValidatedEvent]:
    if isinstance(events, (str, bytes)):
        raise AssociationSemanticError("events must be an iterable of SyntheticEvent")
    try:
        iterator = iter(events)
    except TypeError as exc:
        raise AssociationSemanticError("events must be iterable") from exc

    validated: dict[str, _ValidatedEvent] = {}
    for index, event in enumerate(iterator):
        if not isinstance(event, SyntheticEvent):
            raise AssociationSemanticError(f"events[{index}] must be SyntheticEvent")
        event_id = _trimmed_text(event.event_id, label=f"events[{index}].event_id")
        if event_id in validated:
            raise AssociationSemanticError(f"duplicate event_id: {event_id}")
        hazard_code = _trimmed_text(
            event.hazard_code, label=f"events[{index}].hazard_code"
        )
        if not isinstance(event.dynamic, bool):
            raise AssociationSemanticError(f"events[{index}].dynamic must be boolean")
        peril_label = _optional_trimmed_text(
            event.peril_label, label=f"events[{index}].peril_label"
        )
        start = _utc_datetime(event.start_utc, label=f"events[{index}].start_utc")
        end = _utc_datetime(event.end_utc, label=f"events[{index}].end_utc")
        if end < start:
            raise AssociationSemanticError(
                f"event {event_id!r} end_utc must not precede start_utc"
            )
        validated[event_id] = _ValidatedEvent(
            EventIdentity(event_id, hazard_code, peril_label, event.dynamic),
            start,
            end,
        )

    if not validated:
        raise AssociationSemanticError("at least one event is required")
    return validated


def _pair_key(event_a: str, event_b: str) -> tuple[str, str]:
    return (event_a, event_b) if event_a < event_b else (event_b, event_a)


def _validate_pair_evidence(
    evidence: Iterable[PairEvidence],
    *,
    events: dict[str, _ValidatedEvent],
) -> dict[tuple[str, str], PairEvidence]:
    if isinstance(evidence, (str, bytes)):
        raise AssociationSemanticError(
            "pair_evidence must be an iterable of PairEvidence"
        )
    try:
        iterator = iter(evidence)
    except TypeError as exc:
        raise AssociationSemanticError("pair_evidence must be iterable") from exc

    validated: dict[tuple[str, str], PairEvidence] = {}
    for index, item in enumerate(iterator):
        if not isinstance(item, PairEvidence):
            raise AssociationSemanticError(
                f"pair_evidence[{index}] must be PairEvidence"
            )
        event_a = _trimmed_text(
            item.event_a, label=f"pair_evidence[{index}].event_a"
        )
        event_b = _trimmed_text(
            item.event_b, label=f"pair_evidence[{index}].event_b"
        )
        if event_a == event_b:
            raise AssociationSemanticError(
                "pair evidence must reference two distinct events"
            )
        if event_a not in events or event_b not in events:
            raise AssociationSemanticError(
                f"pair evidence references unknown event: {event_a}, {event_b}"
            )
        if not isinstance(item.spatial_overlap, bool):
            raise AssociationSemanticError("spatial_overlap must be boolean")
        if item.active_overlap is not None and not isinstance(item.active_overlap, bool):
            raise AssociationSemanticError("active_overlap must be boolean when provided")
        key = _pair_key(event_a, event_b)
        if key in validated:
            raise AssociationSemanticError(
                f"duplicate/conflicting pair evidence: {key[0]}, {key[1]}"
            )

        dynamic_pair = (
            events[key[0]].identity.dynamic or events[key[1]].identity.dynamic
        )
        if not dynamic_pair and item.active_overlap is not None:
            raise AssociationSemanticError(
                f"static pair {key[0]}, {key[1]} must not provide active_overlap"
            )

        validated[key] = PairEvidence(
            key[0], key[1], item.spatial_overlap, item.active_overlap
        )

    event_ids = sorted(events)
    expected = {
        (event_ids[left], event_ids[right])
        for left in range(len(event_ids))
        for right in range(left + 1, len(event_ids))
    }
    missing = sorted(expected - set(validated))
    if missing:
        rendered = ", ".join(f"{left}|{right}" for left, right in missing)
        raise AssociationSemanticError(f"missing pair evidence: {rendered}")
    return validated


def _temporal_overlap(
    left: _ValidatedEvent,
    right: _ValidatedEvent,
    *,
    lag_days: int,
) -> bool:
    lag = timedelta(days=lag_days)
    return left.start <= right.end + lag and right.start <= left.end + lag


def _connected_event_sets(
    event_ids: Sequence[str],
    edges: Sequence[AssociationEdge],
) -> tuple[tuple[tuple[str, ...], ...], tuple[str, ...]]:
    adjacency: dict[str, set[str]] = {event_id: set() for event_id in event_ids}
    for edge in edges:
        adjacency[edge.event_a].add(edge.event_b)
        adjacency[edge.event_b].add(edge.event_a)

    components: list[tuple[str, ...]] = []
    unassociated: list[str] = []
    visited: set[str] = set()
    for event_id in sorted(event_ids):
        if event_id in visited:
            continue
        if not adjacency[event_id]:
            visited.add(event_id)
            unassociated.append(event_id)
            continue

        stack = [event_id]
        component: set[str] = set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            visited.add(current)
            stack.extend(sorted(adjacency[current] - component, reverse=True))
        components.append(tuple(sorted(component)))

    return tuple(sorted(components)), tuple(sorted(unassociated))


def associate_events(
    events: Iterable[SyntheticEvent],
    pair_evidence: Iterable[PairEvidence],
    *,
    config: AssociationConfig = AssociationConfig(),
) -> AssociationResult:
    """Return deterministic direct associations and connected event sets.

    Pair evidence is intentionally complete and synthetic: absence is never treated as
    evidence of spatial disjointness. Event-set membership is graph connectivity under
    this benchmark, not physical causality.
    """

    config = _validate_config(config)
    validated_events = _validate_events(events)
    validated_pairs = _validate_pair_evidence(
        pair_evidence,
        events=validated_events,
    )

    edges: list[AssociationEdge] = []
    for (event_a, event_b), evidence in sorted(validated_pairs.items()):
        left = validated_events[event_a]
        right = validated_events[event_b]
        temporal = _temporal_overlap(left, right, lag_days=config.lag_days)
        if not temporal or not evidence.spatial_overlap:
            continue

        dynamic_pair = left.identity.dynamic or right.identity.dynamic
        if dynamic_pair:
            if evidence.active_overlap is None:
                raise AssociationSemanticError(
                    f"dynamic pair {event_a}, {event_b} requires explicit active_overlap"
                )
            if evidence.active_overlap is not True:
                continue

        edges.append(
            AssociationEdge(
                event_a,
                event_b,
                config.lag_days,
                dynamic_pair,
            )
        )

    direct_edges = tuple(sorted(edges))
    event_sets, unassociated = _connected_event_sets(
        tuple(sorted(validated_events)),
        direct_edges,
    )
    identities = tuple(
        validated_events[event_id].identity for event_id in sorted(validated_events)
    )
    return AssociationResult(
        identities,
        direct_edges,
        event_sets,
        unassociated,
    )
