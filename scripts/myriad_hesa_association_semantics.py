# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0

"""Synthetic MYRIAD-HESA-style association and event-set semantics benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Sequence

REFERENCE_REPOSITORY = "judithclaassen/MYRIAD-HESA"
REFERENCE_COMMIT = "dcd2969a8f7c336853bdfa40efd7aa00798ee04b"
REFERENCE_SOURCE_BLOB_SHA1 = "0722b7e6a9ab34b35caa1de56ed4847c65da7aa2"
INPUT_KIND = "fixture"
SCIENTIFIC_ROLE = "benchmark"
SEMANTIC_BOUNDARY = "association_not_causality"
GROUPING_SEMANTICS = "pinned_hesa_makegroups_rows_in"
MAX_SYNTHETIC_EVENTS = 64


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
    grouping_semantics: str = GROUPING_SEMANTICS


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
        if len(validated) > MAX_SYNTHETIC_EVENTS:
            raise AssociationSemanticError(
                f"synthetic benchmark supports at most {MAX_SYNTHETIC_EVENTS} events"
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
            raise AssociationSemanticError(
                "active_overlap must be boolean when provided"
            )
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
    try:
        lag = timedelta(days=lag_days)
        left_end = left.end + lag
        right_end = right.end + lag
    except OverflowError as exc:
        raise AssociationSemanticError(
            "lag_days exceeds supported temporal range"
        ) from exc
    return left.start <= right_end and right.start <= left_end


def _rows_in(
    node_ids: Sequence[int],
    pairs: Sequence[Sequence[int]],
) -> list[list[int]]:
    """Translate pinned HESA rows_in(): keep pair rows wholly inside node_ids."""

    selected = set(node_ids)
    return [
        [int(row[0]), int(row[1])]
        for row in pairs
        if row[0] in selected and row[1] in selected
    ]


def _append_reference_group(groups: list[list[int]], values: Sequence[int]) -> None:
    group = sorted(int(value) for value in values)
    if group not in groups:
        groups.append(group)


def _reference_makegroups(sub: Sequence[Sequence[int]], anchor: int) -> list[list[int]]:
    """Dependency-free translation of pinned MYRIAD-HESA makegroups().

    The slightly unusual ordinal-versus-node comparison in the inner loop is
    intentionally preserved because this benchmark targets the exact pinned
    implementation, including its demonstrated non-maximal n=5 subgroup.
    """

    groups: list[list[int]] = []
    unique_nodes = sorted(
        {
            int(value)
            for row in sub
            for value in row
            if int(value) > anchor
        }
    )
    for pivot in unique_nodes:
        row_indexes = [
            index for index, row in enumerate(sub) if pivot in row
        ]
        neighbors = sorted(
            {
                int(value)
                for index in row_indexes
                for value in sub[index]
                if int(value) != pivot
            }
        )
        neighbor_rows = _rows_in(neighbors, sub)
        if len(row_indexes) == 1:
            _append_reference_group(
                groups,
                [*sub[row_indexes[0]], anchor],
            )
        elif len(neighbor_rows) == (len(neighbors) * (len(neighbors) - 1)) // 2:
            _append_reference_group(groups, [*neighbors, anchor, pivot])
        else:
            rotating_neighbors = sorted(
                {
                    int(value)
                    for index in row_indexes
                    for value in sub[index]
                    if int(value) != pivot
                }
            )
            rows_among_neighbors = _rows_in(rotating_neighbors, sub)
            first_pivot_rows = [
                position
                for position, row_index in enumerate(row_indexes)
                if int(sub[row_index][0]) == pivot
            ]
            if not first_pivot_rows:
                continue

            for ordinal in range(first_pivot_rows[0], len(row_indexes)):
                keep_group = True
                if ordinal != 0:
                    rotating_neighbors = (
                        rotating_neighbors[1:] + rotating_neighbors[:1]
                    )

                candidate = sorted(
                    {
                        int(value)
                        for value in sub[row_indexes[ordinal]]
                        if int(value) != pivot
                    }
                )
                if not candidate:
                    continue
                if candidate[0] < anchor:
                    continue

                connected_row_indexes = [
                    index
                    for index, row in enumerate(rows_among_neighbors)
                    if candidate[0] in row
                ]
                if not connected_row_indexes:
                    _append_reference_group(
                        groups,
                        [*candidate, anchor, pivot],
                    )
                    continue

                connected = sorted(
                    {
                        int(value)
                        for index in connected_row_indexes
                        for value in rows_among_neighbors[index]
                        if int(value) != candidate[0]
                    }
                )
                connected_set = set(connected)
                followers = [
                    value
                    for value in rotating_neighbors
                    if value in connected_set
                ]
                for follower in followers:
                    # Preserve pinned source semantics exactly: `ordinal`
                    # corresponds to source variable `k`, while follower is
                    # source variable `l`.
                    if ordinal != follower:
                        proposed = [*candidate, follower]
                        proposed_rows = _rows_in(proposed, sub)
                        if len(proposed_rows) == (
                            len(proposed) * (len(proposed) - 1)
                        ) // 2:
                            if follower > anchor:
                                candidate.append(follower)
                            else:
                                keep_group = False
                                break
                if keep_group:
                    _append_reference_group(
                        groups,
                        [*candidate, anchor, pivot],
                    )
    return groups


def _reference_group_indices(
    pairs: Sequence[tuple[int, int]],
) -> tuple[tuple[int, ...], ...]:
    """Translate the pinned HESA outer pair-to-group loop."""

    current_pairs = [
        [int(left), int(right)]
        for left, right in sorted(set(pairs))
    ]
    groups: list[list[int]] = []
    source_anchors = sorted({row[0] for row in current_pairs})

    for anchor in source_anchors:
        row_indexes = [
            index for index, row in enumerate(current_pairs) if anchor in row
        ]
        if not row_indexes:
            continue
        if len(row_indexes) == 1:
            _append_reference_group(groups, current_pairs[row_indexes[0]])
            del current_pairs[row_indexes[0]]
            continue

        opposite_nodes = []
        for row_index in row_indexes:
            left, right = current_pairs[row_index]
            opposite_nodes.append(right if left == anchor else left)

        sub = _rows_in(opposite_nodes, current_pairs)
        if not sub:
            for row_index in row_indexes:
                _append_reference_group(groups, current_pairs[row_index])
            for row_index in sorted(row_indexes, reverse=True):
                del current_pairs[row_index]
            continue

        nodes_in_sub = {value for row in sub for value in row}
        standalone_rows = [
            row_index
            for row_index, opposite in zip(row_indexes, opposite_nodes)
            if opposite not in nodes_in_sub
        ]
        for row_index in standalone_rows:
            _append_reference_group(groups, current_pairs[row_index])
        for row_index in sorted(standalone_rows, reverse=True):
            del current_pairs[row_index]

        for group in _reference_makegroups(sub, anchor):
            _append_reference_group(groups, group)

    return tuple(sorted(set(tuple(group) for group in groups)))


def _pinned_hesa_event_sets(
    event_ids: Sequence[str],
    edges: Sequence[AssociationEdge],
) -> tuple[tuple[tuple[str, ...], ...], tuple[str, ...]]:
    """Return deterministic groups from the exact pinned HESA pair-to-group stage.

    Direct association edges are first mapped to the stable sorted event order
    used by this synthetic benchmark. The grouping stage then follows the pinned
    reference implementation rather than replacing it with graph connectivity
    or mathematically maximal-clique enumeration.
    """

    ordered_ids = tuple(sorted(event_ids))
    index_by_id = {
        event_id: index for index, event_id in enumerate(ordered_ids)
    }
    edge_pairs = tuple(
        sorted(
            {
                tuple(
                    sorted(
                        (
                            index_by_id[edge.event_a],
                            index_by_id[edge.event_b],
                        )
                    )
                )
                for edge in edges
            }
        )
    )

    associated_indexes = {index for pair in edge_pairs for index in pair}
    unassociated = tuple(
        event_id
        for index, event_id in enumerate(ordered_ids)
        if index not in associated_indexes
    )
    grouped_indexes = _reference_group_indices(edge_pairs)
    groups = tuple(
        tuple(ordered_ids[index] for index in group)
        for group in grouped_indexes
    )
    return groups, unassociated


def associate_events(
    events: Iterable[SyntheticEvent],
    pair_evidence: Iterable[PairEvidence],
    *,
    config: AssociationConfig = AssociationConfig(),
) -> AssociationResult:
    """Return deterministic direct associations and pinned HESA event groups.

    Pair evidence is intentionally complete and synthetic: absence is never
    treated as evidence of spatial disjointness. Event groups follow the exact
    pinned MYRIAD-HESA pair-to-group implementation and never imply physical
    causality.
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
    event_sets, unassociated = _pinned_hesa_event_sets(
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
