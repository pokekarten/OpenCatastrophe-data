# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic Monty STAC event-source linkage gate.

No IFRC credentials, network access, STAC fetch, source-data admission, damage,
insurer loss or contractual occurrence decision. A correlation candidate is not
an identity equivalence relation and MUST NOT be used for loss aggregation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import re


class MontyLinkageBlocked(ValueError):
    """Source/temporal/support metadata missing or unsafe: fail closed."""


_NS = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_ISO3 = re.compile(r"^[A-Z]{3}$")
_HAZARD = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")


def utc(value: str) -> datetime:
    if not isinstance(value, str) or "T" not in value:
        raise MontyLinkageBlocked("explicit timezone-aware UTC-instant required")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MontyLinkageBlocked("invalid event or receipt time") from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise MontyLinkageBlocked("naive time rejected")
    return instant.astimezone(timezone.utc)


@dataclass(frozen=True)
class SourceEvent:
    trusted_source_namespace: str
    stac_item_id: str
    issuer_event_id: str
    episode_number: int
    corr_id: str
    countries: tuple[str, ...]
    hazard_codes: tuple[str, ...]
    event_start: datetime
    event_end: datetime
    bbox: tuple[float, float, float, float] | None
    controlled_received_at: datetime | None


def _labels(value: object, *, field: str, pattern: re.Pattern[str]) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise MontyLinkageBlocked(f"{field} must be a non-empty list")
    if not all(isinstance(x, str) and pattern.fullmatch(x) for x in value):
        raise MontyLinkageBlocked(f"{field} has invalid label")
    if len(set(value)) != len(value):
        raise MontyLinkageBlocked(f"{field} duplicate label")
    return tuple(sorted(value))


def _bbox(value: object) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 4 or not all(type(v) in (int, float) and math.isfinite(v) for v in value):
        raise MontyLinkageBlocked("only a finite four-coordinate 2D bbox is supported")
    lon0, lat0, lon1, lat1 = value
    if not (-180 <= lon0 <= lon1 <= 180 and -90 <= lat0 <= lat1 <= 90):
        raise MontyLinkageBlocked("invalid or antimeridian-crossing bbox")
    return tuple(float(v) for v in value)


def parse_source_event(
    item: dict,
    *,
    trusted_source_namespace: str,
    controlled_received_at_utc: str | None,
) -> SourceEvent:
    """Parse *provided* Monty event metadata, never follow STAC URLs or links.

    Source namespace and controlled receipt must be supplied by trusted ingest,
    not copied from an unauthenticated STAC item's properties.
    """
    if not isinstance(item, dict) or item.get("type") != "Feature" or not isinstance(item.get("properties"), dict):
        raise MontyLinkageBlocked("requires STAC Feature with properties")
    if not isinstance(trusted_source_namespace, str) or not _NS.fullmatch(trusted_source_namespace):
        raise MontyLinkageBlocked("trusted source namespace required")
    if not isinstance(item.get("id"), str) or not item["id"] or len(item["id"]) > 256:
        raise MontyLinkageBlocked("valid STAC item id required")
    if not isinstance(item.get("collection"), str) or not item["collection"]:
        raise MontyLinkageBlocked("STAC collection required")
    roles = item.get("roles")
    if not isinstance(roles, list) or "event" not in roles or "source" not in roles or "reference" in roles:
        raise MontyLinkageBlocked("requires source event role, not reference/hazard/impact")
    p = item["properties"]
    srcid = p.get("monty:src_event_id")
    corr = p.get("monty:corr_id")
    if not isinstance(srcid, str) or not srcid.strip() or len(srcid) > 256:
        raise MontyLinkageBlocked("issuer event identity missing")
    if not isinstance(corr, str) or not corr.strip() or len(corr) > 256:
        raise MontyLinkageBlocked("Monty source-local corr_id missing")
    episode = p.get("monty:episode_number")
    if type(episode) is not int or not 0 <= episode <= 100000:
        raise MontyLinkageBlocked("Monty episode number missing or invalid")
    countries = _labels(p.get("monty:country_codes"), field="country codes", pattern=_ISO3)
    hazards = _labels(p.get("monty:hazard_codes"), field="hazard codes", pattern=_HAZARD)
    start_value, end_value = p.get("start_datetime"), p.get("end_datetime")
    instant_value = p.get("datetime")
    if instant_value is not None:
        if start_value is not None or end_value is not None:
            raise MontyLinkageBlocked("ambiguous datetime and interval combination")
        start = end = utc(instant_value)
    else:
        if start_value is None or end_value is None:
            raise MontyLinkageBlocked("event temporal support missing")
        start, end = utc(start_value), utc(end_value)
        if end < start:
            raise MontyLinkageBlocked("reversed event support interval")
    received = utc(controlled_received_at_utc) if controlled_received_at_utc is not None else None
    return SourceEvent(
        trusted_source_namespace, item["id"], srcid, episode, corr,
        countries, hazards, start, end, _bbox(item.get("bbox")), received
    )


def _bbox_intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def compare_event_sources(a: SourceEvent, b: SourceEvent, *, knowledge_cut_utc: str) -> dict:
    """Return an evidence-candidate classification, NEVER physical/treaty merger."""
    cut = utc(knowledge_cut_utc)
    if not isinstance(a, SourceEvent) or not isinstance(b, SourceEvent):
        raise MontyLinkageBlocked("validated SourceEvent inputs required")
    evidence = sorted([
        f"{a.trusted_source_namespace}:{a.issuer_event_id}:episode-{a.episode_number}",
        f"{b.trusted_source_namespace}:{b.issuer_event_id}:episode-{b.episode_number}",
    ])
    base = {
        "classification": "SYNTHETIC_STAC_LINKAGE_GATE_NOT_AN_EVENT_MERGE",
        "knowledge_cut_utc": knowledge_cut_utc,
        "source_aliases": evidence,
        "corr_id_global_join_authorized": False,
        "physical_event_identity_verified": False,
        "contractual_occurrence_verified": False,
        "observed_loss_or_model_admitted": False,
    }
    if a.controlled_received_at is None or b.controlled_received_at is None or a.controlled_received_at > cut or b.controlled_received_at > cut:
        return {**base, "state": "NOT_KNOWABLE_AT_CUT", "spatial_check": "not_evaluated"}
    if a.trusted_source_namespace == b.trusted_source_namespace:
        if a.issuer_event_id == b.issuer_event_id and a.episode_number == b.episode_number:
            return {**base, "state": "SAME_SOURCE_EVENT_EPISODE_ALIAS_ONLY", "spatial_check": "not_evaluated"}
        return {**base, "state": "SEPARATE_SOURCE_EVENT_EPISODE_NEEDS_REVIEW", "spatial_check": "not_evaluated"}
    if not (set(a.countries) & set(b.countries)):
        return {**base, "state": "NO_COUNTRY_OVERLAP_UNRESOLVED", "spatial_check": "not_evaluated"}
    if not (set(a.hazard_codes) & set(b.hazard_codes)):
        return {**base, "state": "NO_EXACT_HAZARD_CODE_OVERLAP_UNRESOLVED", "spatial_check": "not_evaluated"}
    if a.event_end < b.event_start or b.event_end < a.event_start:
        return {**base, "state": "NONOVERLAPPING_EVENT_TIMES_NOT_MATCHED", "spatial_check": "not_evaluated"}
    if a.bbox is not None and b.bbox is not None:
        if not _bbox_intersects(a.bbox, b.bbox):
            return {**base, "state": "NONOVERLAPPING_BBOX_NOT_MATCHED", "spatial_check": "disjoint"}
        return {**base, "state": "CROSS_SOURCE_CANDIDATE_REQUIRES_REVIEW", "spatial_check": "overlap"}
    return {**base, "state": "CROSS_SOURCE_CANDIDATE_SPATIAL_UNKNOWN", "spatial_check": "unknown"}


def fixture_item(issuer_id: str, corr_id: str, event_time: str, episode: int = 1,
                 bbox: list[float] | None = None) -> dict:
    return {
        "type": "Feature", "id": "invented-" + issuer_id, "collection": "synthetic-events",
        "roles": ["event", "source"], "geometry": None, "bbox": bbox,
        "properties": {
            "monty:src_event_id": issuer_id, "monty:corr_id": corr_id,
            "monty:episode_number": episode, "monty:country_codes": ["TUR"],
            "monty:hazard_codes": ["EQ"], "datetime": event_time,
        },
    }


def demonstration() -> dict:
    cut = "2023-02-06T12:00:00Z"
    a = parse_source_event(
        fixture_item("EQ-A", "SOURCE-A-CORR", "2023-02-06T01:17:34Z", bbox=[36, 36, 38, 38]),
        trusted_source_namespace="synthetic-a", controlled_received_at_utc="2023-02-06T01:22:00Z",
    )
    b = parse_source_event(
        fixture_item("EQ-B", "SOURCE-B-CORR", "2023-02-06T01:17:34Z", bbox=[37, 36, 39, 38]),
        trusted_source_namespace="synthetic-b", controlled_received_at_utc="2023-02-06T01:25:00Z",
    )
    shock2 = parse_source_event(
        fixture_item("EQ-C", "SOURCE-A-CORR", "2023-02-06T10:24:48Z"),
        trusted_source_namespace="synthetic-b", controlled_received_at_utc="2023-02-06T11:00:00Z",
    )
    candidate = compare_event_sources(a, b, knowledge_cut_utc=cut)
    distinct = compare_event_sources(a, shock2, knowledge_cut_utc=cut)
    assert candidate["state"] == "CROSS_SOURCE_CANDIDATE_REQUIRES_REVIEW"
    assert distinct["state"] == "NONOVERLAPPING_EVENT_TIMES_NOT_MATCHED"
    assert not candidate["physical_event_identity_verified"]
    return {"scope": "INVENTED_STAC_METADATA_ONLY", "candidate": candidate, "shock_sequence": distinct}


if __name__ == "__main__":
    print(json.dumps(demonstration(), indent=2, sort_keys=True))
