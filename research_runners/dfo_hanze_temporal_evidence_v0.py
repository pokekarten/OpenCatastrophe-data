#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Aggregate-only temporal/cause completeness diagnostics for DFO-HANZE candidates.

Does NOT identify, score, rank, reject, or confirm individual flood matches.
All inputs must already have passed the exact-version/source-byte preflights.
"""
from __future__ import annotations

from collections import Counter
from datetime import date

RELATIONSHIP = "SAME_COUNTRY_AND_OVERLAPPING_DATES_ONLY"
DAYS_BUCKETS = ("1", "2-3", "4-7", "8+")
DELTA_BUCKETS = ("0", "1-3", "4-7", "8+")


class TemporalDiagnosticError(ValueError):
    """Candidate diagnostic cannot be generated safely."""


def _bucket(value: int, zero_allowed: bool = False) -> str:
    if value < 0 or (value == 0 and not zero_allowed):
        raise TemporalDiagnosticError("invalid day count")
    if value == 0:
        return "0"
    if value == 1:
        return "1" if not zero_allowed else "1-3"
    if value <= 3:
        return "2-3" if not zero_allowed else "1-3"
    if value <= 7:
        return "4-7"
    return "8+"


def _day(value: str) -> date:
    if type(value) is not str or len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise TemporalDiagnosticError("expected canonical YYYY-MM-DD day")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise TemporalDiagnosticError("invalid candidate day") from exc


def summarize_candidate_evidence(overlap: dict, dfo_preflight: dict) -> dict:
    """Aggregate only; NEVER export original event IDs, provider text or rows."""
    if (overlap.get("evidence_class") != "HISTORICAL_FLOOD_EVENT_CANDIDATE_LINKS_ONLY"
            or dfo_preflight.get("evidence_class") != "REPORTED_HISTORICAL_FLOOD_EVENTS_NO_DEPTH_NO_INSURED_LOSS"
            or overlap.get("common_event_identity_proven") is not False
            or overlap.get("economic_or_insured_loss_joined") is not False
            or overlap.get("model_input_admitted") is not False):
        raise TemporalDiagnosticError("wrong upstream evidence or admitted source")
    events = dfo_preflight.get("events")
    pairs = overlap.get("candidate_pairs")
    if not isinstance(events, list) or not isinstance(pairs, list):
        raise TemporalDiagnosticError("missing preflight provider events or candidates")
    dfo_cause_by_id = {}
    for event in events:
        event_id = event.get("dfo_event_id")
        if not isinstance(event_id, str) or event_id in dfo_cause_by_id:
            raise TemporalDiagnosticError("duplicate or invalid preflight DFO ID")
        cause = event.get("reported_cause_text")
        if cause is not None and type(cause) is not str:
            raise TemporalDiagnosticError("DFO cause is not provider text")
        dfo_cause_by_id[event_id] = cause
    intersections = Counter({k: 0 for k in DAYS_BUCKETS})
    start_deltas = Counter({k: 0 for k in DELTA_BUCKETS})
    pairs_with_both_cause_labels = 0
    exactly_equal_normalized_cause_text = 0
    pairs_with_dfo_cause_label = 0
    pairs_with_hanze_cause_label = 0
    pairs_with_hanze_event_type = 0
    seen = set()
    for pair in pairs:
        if (pair.get("relationship") != RELATIONSHIP
                or pair.get("same_event_confirmed") is not False
                or pair.get("losses_joined") is not False):
            raise TemporalDiagnosticError("candidate has unsupported identity or loss stage")
        did, hid = pair.get("dfo_event_id"), pair.get("hanze_event_id")
        if did not in dfo_cause_by_id or not isinstance(hid, str) or (did, hid) in seen:
            raise TemporalDiagnosticError("unrecognized or duplicate event-pair identity")
        seen.add((did, hid))
        dfo_interval, hanze_interval = pair["dfo_interval"], pair["hanze_interval"]
        if (not isinstance(dfo_interval, list) or not isinstance(hanze_interval, list)
                or len(dfo_interval) != 2 or len(hanze_interval) != 2):
            raise TemporalDiagnosticError("invalid event interval")
        ds, de = map(_day, dfo_interval)
        hs, he = map(_day, hanze_interval)
        if de < ds or he < hs:
            raise TemporalDiagnosticError("reversed event interval")
        overlap_days = (min(de, he) - max(ds, hs)).days + 1
        intersections[_bucket(overlap_days)] += 1
        start_deltas[_bucket(abs((ds - hs).days), True)] += 1
        dfo_cause = dfo_cause_by_id[did]
        hanze_cause = pair.get("hanze_cause_unharmonized")
        hanze_type = pair.get("hanze_event_type_unharmonized")
        if hanze_cause is not None and type(hanze_cause) is not str:
            raise TemporalDiagnosticError("invalid HANZE cause text")
        if hanze_type is not None and type(hanze_type) is not str:
            raise TemporalDiagnosticError("invalid HANZE event type text")
        dc, hc = (dfo_cause or "").strip(), (hanze_cause or "").strip()
        if dc:
            pairs_with_dfo_cause_label += 1
        if hc:
            pairs_with_hanze_cause_label += 1
        if isinstance(hanze_type, str) and hanze_type.strip():
            pairs_with_hanze_event_type += 1
        if dc and hc:
            pairs_with_both_cause_labels += 1
            if dc.casefold() == hc.casefold():
                exactly_equal_normalized_cause_text += 1
    if len(pairs) != overlap.get("candidate_pair_count"):
        raise TemporalDiagnosticError("candidate count changed without corresponding receipt")
    return {
        "evidence_stage": "AGGREGATE_EVENT_INTERVAL_AND_CAUSE_LABEL_COMPLETENESS_ONLY",
        "candidate_pair_count": len(pairs),
        "inclusive_temporal_overlap_days": {k: intersections[k] for k in DAYS_BUCKETS},
        "absolute_start_date_difference_days": {k: start_deltas[k] for k in DELTA_BUCKETS},
        "pairs_with_dfo_reported_cause_text": pairs_with_dfo_cause_label,
        "pairs_with_hanze_reported_cause_text": pairs_with_hanze_cause_label,
        "pairs_with_hanze_reported_event_type": pairs_with_hanze_event_type,
        "pairs_with_both_cause_texts": pairs_with_both_cause_labels,
        "pairs_with_exactly_same_casefolded_cause_text": exactly_equal_normalized_cause_text,
        "source_cause_taxonomies_harmonized": False,
        "common_flood_event_identity_confirmed": False,
        "same_geographic_footprint_confirmed": False,
        "source_reporting_independence_confirmed": False,
        "provider_rows_or_pair_details_emitted": False,
        "economic_or_insured_losses_computed": False,
        "model_source_admitted": False,
    }
