#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Conservative DFO v0.9.0 x HANZE v3.0.2-beta flood-event *candidate* links.

The original provider bytes are supplied locally, SHA256-pinned and never
committed here. A user-prepared country-name crosswalk is explicit evidence
input, NOT a built-in claim of harmonised geography. Common country and
overlapping dates do not prove shared event identity or source independence.
No loss, portfolio, hazard depth, catastrophe model or rights are inferred.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import io
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from research_runners.dfo_floodrecords_csv_preflight_v0 import parse_dfo_csv
from research_runners.historical_cat_benchmark_csv_preflight_v0 import (
    HANZE_COLUMNS, inspect_hanze_v302,
)

SHA = re.compile(r"[0-9a-f]{64}\Z")
ISO2 = re.compile(r"[A-Z]{2}\Z")
MAX_CANDIDATES = 100_000


class LinkageError(ValueError):
    """Fail closed when an identity, byte receipt or mapping is uncertain."""


def _sha(blob: bytes, expected: str, label: str) -> str:
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        raise LinkageError(f"{label}: expected lowercase SHA256 digest")
    got = hashlib.sha256(blob).hexdigest()
    if got != expected:
        raise LinkageError(f"{label}: source bytes disagree with pinned SHA256")
    return got


def _strict_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise LinkageError("duplicate JSON key: " + key)
        obj[key] = value
    return obj


def _country_map(blob: bytes, expected_sha256: str) -> dict[str, str]:
    _sha(blob, expected_sha256, "country crosswalk")
    if len(blob) > 200_000:
        raise LinkageError("country crosswalk exceeds supported size")
    try:
        payload = json.loads(blob.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise LinkageError("invalid crosswalk JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "mappings"}:
        raise LinkageError("expected crosswalk schema_version and mappings")
    if payload["schema_version"] != "dfo-country-hanze-v0":
        raise LinkageError("unsupported crosswalk schema")
    mappings = payload["mappings"]
    if not isinstance(mappings, list) or not 0 < len(mappings) <= 300:
        raise LinkageError("crosswalk mappings must be a bounded nonempty list")
    result = {}
    for mapping in mappings:
        if not isinstance(mapping, dict) or set(mapping) != {"dfo_country", "hanze_iso2", "mapping_evidence_url"}:
            raise LinkageError("crosswalk entry requires exact three fields")
        name, code, url = mapping["dfo_country"], mapping["hanze_iso2"], mapping["mapping_evidence_url"]
        if type(name) is not str or not name or name != name.strip() or any(x in name for x in (",", "•", ";", "/")):
            raise LinkageError("ambiguous or noncanonical DFO country label")
        if type(code) is not str or not ISO2.fullmatch(code):
            raise LinkageError("crosswalk must explicitly map to ISO2")
        if name in result:
            raise LinkageError("duplicate DFO country mapping")
        if type(url) is not str or not url.startswith("https://"):
            raise LinkageError("country mapping evidence must be an HTTPS URL")
        parsed = urlsplit(url)
        if not parsed.hostname or parsed.username or parsed.password:
            raise LinkageError("country mapping evidence URL invalid")
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise LinkageError("mapping evidence URL must not reference private IP")
        result[name] = code
    return result


def link_candidates(
    dfo_blob: bytes, dfo_sha256: str,
    hanze_blob: bytes, hanze_sha256: str,
    crosswalk_blob: bytes, crosswalk_sha256: str,
) -> dict:
    """Return possible same-country/time overlaps; not one-to-one matches."""
    dfo_sha = _sha(dfo_blob, dfo_sha256, "DFO")
    hanze_sha = _sha(hanze_blob, hanze_sha256, "HANZE")
    crosswalk = _country_map(crosswalk_blob, crosswalk_sha256)
    dfo = parse_dfo_csv(dfo_blob)
    hanze_summary = inspect_hanze_v302(hanze_blob, hanze_sha)
    reader = csv.DictReader(io.StringIO(hanze_blob.decode("utf-8-sig"), newline=""), strict=True)
    if reader.fieldnames != list(HANZE_COLUMNS):
        raise LinkageError("HANZE source fields unexpectedly differ from validated preflight")
    hanze_by_code: dict[str, list[tuple]] = {}
    for row in reader:
        code = row["country_code"]
        if not ISO2.fullmatch(code):
            continue  # Never silently map historical supranational codes.
        hanze_by_code.setdefault(code, []).append((
            date.fromisoformat(row["start_date"]),
            date.fromisoformat(row["end_date"]),
            row["id"],
            row["event_type"],
            row["cause"],
        ))
    for values in hanze_by_code.values():
        values.sort()
    pairs = []
    country_unmapped = 0
    country_unmatched = 0
    no_date_overlap = 0
    for event in dfo["events"]:
        raw_country = event["country_text_unparsed"]
        # Multi-country labels are deliberately not collapsed into a single ISO2.
        if raw_country not in crosswalk:
            country_unmapped += 1
            continue
        code = crosswalk[raw_country]
        rows = hanze_by_code.get(code)
        if not rows:
            country_unmatched += 1
            continue
        lo = date.fromisoformat(event["start_date"])
        hi = date.fromisoformat(event["end_date"])
        found = False
        for start, end, event_id, event_type, cause in rows:
            if start > hi:
                break
            if end < lo:
                continue
            found = True
            pairs.append({
                "dfo_event_id": event["dfo_event_id"],
                "hanze_event_id": event_id,
                "dfo_country_original": raw_country,
                "country_iso2_from_supplied_crosswalk": code,
                "dfo_interval": [lo.isoformat(), hi.isoformat()],
                "hanze_interval": [start.isoformat(), end.isoformat()],
                "hanze_event_type_unharmonized": event_type,
                "hanze_cause_unharmonized": cause or None,
                "relationship": "SAME_COUNTRY_AND_OVERLAPPING_DATES_ONLY",
                "same_event_confirmed": False,
                "independent_reports_confirmed": False,
                "losses_joined": False,
            })
            if len(pairs) > MAX_CANDIDATES:
                raise LinkageError("too many ambiguous event-pair candidates")
        if not found:
            no_date_overlap += 1
    pairs.sort(key=lambda p: (int(p["dfo_event_id"]), int(p["hanze_event_id"])))
    return {
        "evidence_class": "HISTORICAL_FLOOD_EVENT_CANDIDATE_LINKS_ONLY",
        "dfo_release": "v0.9.0",
        "hanze_release": "v3.0.2-beta",
        "input_sha256": {
            "dfo_csv": dfo_sha,
            "hanze_csv": hanze_sha,
            "country_crosswalk": hashlib.sha256(crosswalk_blob).hexdigest(),
        },
        "dfo_event_count": dfo["reported_event_count"],
        "hanze_event_count": hanze_summary["event_count"],
        "candidate_pair_count": len(pairs),
        "unmapped_dfo_events": country_unmapped,
        "mapped_dfo_events_with_no_hanze_country": country_unmatched,
        "mapped_dfo_events_without_overlapping_hanze_dates": no_date_overlap,
        "crosswalk_name_count": len(crosswalk),
        "dfo_release_date_anomaly": not dfo["published_release_end_year_consistent_with_csv"],
        "country_name_crosswalk_proof_independently_verified_by_code": False,
        "common_event_identity_proven": False,
        "source_independence_proven": False,
        "geographic_footprint_aligned": False,
        "economic_or_insured_loss_joined": False,
        "model_input_admitted": False,
        "missing_candidate_is_evidence_of_no_disaster": False,
        "candidate_pairs": pairs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dfo-csv", "hanze-csv", "country-crosswalk"):
        parser.add_argument("--" + name, type=Path, required=True)
        parser.add_argument("--" + name + "-sha256", type=str, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    files = [args.dfo_csv, args.hanze_csv, args.country_crosswalk]
    if args.out.resolve() in {path.resolve() for path in files}:
        raise LinkageError("output must not overwrite original source or crosswalk")
    result = link_candidates(
        args.dfo_csv.read_bytes(), args.dfo_csv_sha256,
        args.hanze_csv.read_bytes(), args.hanze_csv_sha256,
        args.country_crosswalk.read_bytes(), args.country_crosswalk_sha256,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
