#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Real, SHA-pinned DFO v0.9.0 x HANZE v3.0.2-beta overlap receipt.

Only an explicitly grounded Germany -> DE mapping is attempted. The output
contains aggregate metadata; no real provider rows or individual pairs are
published. Same country and intersecting time do NOT prove shared event ID,
independent observation, flood footprint or insured loss.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request

if __package__:
    from .dfo_original_provider_byte_receipt_v0 import (
        PINNED_ORIGINAL_SHA256, PINNED_PROFILE, fetch_publisher_bytes,
        verify_source_bytes,
    )
    from .flood_event_link_candidates_v0 import link_candidates
    from .dfo_hanze_temporal_evidence_v0 import summarize_candidate_evidence
    from .dfo_floodrecords_csv_preflight_v0 import parse_dfo_csv
    from .historical_cat_csv_provider_receipt_v0 import SOURCE_RECEIPT
else:
    from dfo_original_provider_byte_receipt_v0 import (
        PINNED_ORIGINAL_SHA256, PINNED_PROFILE, fetch_publisher_bytes,
        verify_source_bytes,
    )
    from flood_event_link_candidates_v0 import link_candidates
    from dfo_hanze_temporal_evidence_v0 import summarize_candidate_evidence
    from dfo_floodrecords_csv_preflight_v0 import parse_dfo_csv
    from historical_cat_csv_provider_receipt_v0 import SOURCE_RECEIPT

UN_GERMANY_URL = "https://unstats.un.org/unsd/methodology/m49/overview/"
COUNTRY_CROSSWALK = {
    "schema_version": "dfo-country-hanze-v0",
    "mappings": [
        {
            "dfo_country": "Germany",
            "hanze_iso2": "DE",
            "mapping_evidence_url": UN_GERMANY_URL,
        }
    ],
}
HANZE_MAX_BYTES = 1_000_000


def fetch_hanze_pinned() -> bytes:
    src = SOURCE_RECEIPT["sources"]["hanze_v3_0_2_beta"]
    url = src["api_url"]
    if url != "https://zenodo.org/api/records/23670886/files/HANZE_events_v3_0_2b.csv/content":
        raise ValueError("unreviewed HANZE original URL")
    request = urllib.request.Request(
        url, headers={"User-Agent": "OpenCatastropheDFOHANZE/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        if not response.geturl().startswith("https://zenodo.org/"):
            raise ValueError("HANZE redirected outside official publisher host")
        blob = response.read(HANZE_MAX_BYTES + 1)
    if len(blob) != src["bytes"] or len(blob) > HANZE_MAX_BYTES:
        raise ValueError("HANZE original length mismatch")
    if hashlib.sha256(blob).hexdigest() != src["observed_sha256"]:
        raise ValueError("HANZE original SHA256 mismatch")
    if hashlib.md5(blob, usedforsecurity=False).hexdigest() != src["publisher_md5"]:
        raise ValueError("HANZE publisher MD5 mismatch")
    return blob


def make_aggregate_receipt(dfo: bytes, hanze: bytes) -> dict:
    """Verify original providers, then count *unconfirmed* candidate overlaps."""
    verified = verify_source_bytes(dfo, expected_sha256=PINNED_ORIGINAL_SHA256)
    for field, expected in PINNED_PROFILE.items():
        if verified[field] != expected:
            raise ValueError("DFO original profile drift: " + field)
    crosswalk = json.dumps(
        COUNTRY_CROSSWALK, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    src = SOURCE_RECEIPT["sources"]["hanze_v3_0_2_beta"]
    overlap = link_candidates(
        dfo, PINNED_ORIGINAL_SHA256,
        hanze, src["observed_sha256"],
        crosswalk, hashlib.sha256(crosswalk).hexdigest(),
    )
    pairs = overlap["candidate_pairs"]
    return {
        "schema_version": "dfo-hanze-real-provider-overlap-receipt-v0",
        "evidence_stage": "original_provider_bytes_observed_candidate_time_country_overlap_only",
        "sources": {
            "dfo_v0_9_0_sha256": PINNED_ORIGINAL_SHA256,
            "hanze_v3_0_2_beta_sha256": src["observed_sha256"],
            "country_crosswalk_sha256": overlap["input_sha256"]["country_crosswalk"],
            "country_mapping_evidence": UN_GERMANY_URL,
        },
        "dfo_provider_events": overlap["dfo_event_count"],
        "hanze_provider_events": overlap["hanze_event_count"],
        "crosswalk_country": "Germany",
        "crosswalk_iso2": "DE",
        "dfo_events_with_no_confirmed_country_mapping": overlap["unmapped_dfo_events"],
        "dfo_events_with_mapping_but_no_hanze_country": overlap["mapped_dfo_events_with_no_hanze_country"],
        "dfo_events_mapped_but_no_hanze_time_overlap": overlap["mapped_dfo_events_without_overlapping_hanze_dates"],
        "candidate_country_time_pairs": overlap["candidate_pair_count"],
        "candidate_temporal_and_cause_diagnostics": summarize_candidate_evidence(overlap, parse_dfo_csv(dfo)),
        "distinct_dfo_events_with_candidates": len({p["dfo_event_id"] for p in pairs}),
        "distinct_hanze_events_with_candidates": len({p["hanze_event_id"] for p in pairs}),
        "candidate_pair_detail_emitted": False,
        "country_mapping_independently_validated_against_an_historical_country_version": False,
        "same_event_identity_proven": False,
        "source_independence_proven": False,
        "exposure_or_tiv_joined": False,
        "observed_flood_depth_attached": False,
        "insured_loss_calculated": False,
        "model_data_admitted": False,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = make_aggregate_receipt(fetch_publisher_bytes(), fetch_hanze_pinned())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
