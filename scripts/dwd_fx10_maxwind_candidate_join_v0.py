#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Strict candidate FX_10 ↔ Maxwind-device day-by-day source crosswalk.

Original DWD station 00003 wind-gust measurements and its metadata are already
SHA-pinned in the repository. DWD v24.03 calls FX_10 the 10-minute maximum of
wind speed. 'Windgeschwindigkeit_Maxwind' is a *candidate* equipment family;
the original tables have no verified shared foreign key. The only permissible
claim is a temporal/physical-unit candidate match under explicitly provisional
inclusive-date semantics. No instrument values or coordinates are emitted.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from scripts import dwd_metadata_temporal_evidence as frozen
from scripts.dwd_equipment_layout_evidence_v0 import PAIRS
from scripts.dwd_original_instrument_intervals_v0 import (
    EQ_HEADERS, PAR_HEADERS, ORIGINAL_ROWS, START, END,
    InstrumentAuditBlocked, _rows,
)

GUST_CODE = "FX_10"
GUST_UNIT = "m/s"
CANDIDATE_DEVICE_FAMILY = PAIRS[1]
PARAMETERS = PAIRS[4]
DWD_DEFINITION = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/10_minutes/extreme_wind/"
    "DESCRIPTION_obsgermany_climate_10min_extreme_wind_en.pdf"
)


class CandidateJoinBlocked(ValueError):
    """An original-byte, station, row or temporal matching contract failed."""


def _positive_height(value: str) -> bool:
    try:
        height = Decimal(value.strip().replace(",", "."))
    except InvalidOperation:
        return False
    # Heights are plausible candidates, not WMO-verified mast heights.
    return height.is_finite() and Decimal("0") < height <= Decimal("300")


def _daily_pair_count(eq: list[dict], params: list[dict]) -> dict:
    counts = Counter()
    monthly = {}
    distinct_candidate_equipment = set()
    unrecognized_unit_days = 0
    plausible_sensor_height_days = 0
    day = START
    while day <= END:
        e = [r for r in eq if r["__begin"] <= day <= r["__end"]]
        p = [r for r in params if r["__begin"] <= day <= r["__end"]]
        category = ("none" if not e or not p
                    else "one" if len(e) == 1 and len(p) == 1
                    else "multiple")
        counts[category] += 1
        month = day.strftime("%Y-%m")
        bucket = monthly.setdefault(month, {
            "one_candidate_pair_days": 0,
            "missing_candidate_pair_days": 0,
            "multiple_candidate_pair_days": 0,
        })
        key = {
            "one": "one_candidate_pair_days",
            "none": "missing_candidate_pair_days",
            "multiple": "multiple_candidate_pair_days",
        }[category]
        bucket[key] += 1
        if category == "one":
            e0, p0 = e[0], p[0]
            distinct_candidate_equipment.add((
                e0["Geraetetyp Name"],
                e0["Messverfahren"],
                e0["Geberhoehe ueber Grund [m]"],
            ))
            if p0["Einheit"].strip() != GUST_UNIT:
                unrecognized_unit_days += 1
            if _positive_height(e0["Geberhoehe ueber Grund [m]"]):
                plausible_sensor_height_days += 1
        day += timedelta(days=1)
    window_days = (END - START).days + 1
    if sum(counts.values()) != window_days:
        raise CandidateJoinBlocked("candidate interval audit does not conserve all calendar days")
    return {
        "window_days": window_days,
        "one_candidate_pair_days": counts["one"],
        "missing_candidate_pair_days": counts["none"],
        "multiple_candidate_pair_days": counts["multiple"],
        "one_pair_days_with_non_matching_unit": unrecognized_unit_days,
        "one_pair_days_with_plausible_unverified_sensor_height": plausible_sensor_height_days,
        "distinct_device_method_height_tuples_for_one_pair_days":
            len(distinct_candidate_equipment),
        "monthly_candidate_pair_counts": dict(sorted(monthly.items())),
    }


def inspect(
    path: Path, *, expected_sha256: str = frozen.EXPECTED_METADATA_SHA256,
) -> dict:
    # Uses the pre-existing no-follow, ZIP CRC, member-hash and
    # source-byte-tamper protections. Never interpret a different version.
    try:
        receipt = frozen._collect(
            Path(path), expected_sha256, frozen.EXPECTED_STATION_ID,
        )
        snapshot = frozen._read_bounded_regular_snapshot(
            Path(path), receipt["metadata_asset"]["byte_size"],
        )
    except (OSError, frozen.TemporalEvidenceError) as exc:
        raise CandidateJoinBlocked("exact original DWD metadata verification failed") from exc
    if hashlib.sha256(snapshot).hexdigest() != expected_sha256:
        raise CandidateJoinBlocked("original DWD metadata changed after verification")
    by_name = {
        entry["path"]: entry["sha256"]
        for members in receipt["required_family_members"].values()
        for entry in members
    }
    source_rows = {}
    try:
        with zipfile.ZipFile(io.BytesIO(snapshot), "r") as archive:
            for stem, columns in (
                (CANDIDATE_DEVICE_FAMILY, EQ_HEADERS),
                (PARAMETERS, PAR_HEADERS),
            ):
                member = stem + ".txt"
                raw = archive.read(member)
                if hashlib.sha256(raw).hexdigest() != by_name[member]:
                    raise CandidateJoinBlocked("original DWD metadata member hash mismatch")
                source_rows[stem], _footer = _rows(
                    raw, columns, stem, ORIGINAL_ROWS[stem],
                )
    except (KeyError, OSError, RuntimeError, zipfile.BadZipFile,
            InstrumentAuditBlocked) as exc:
        raise CandidateJoinBlocked("actual native DWD source table fails schema gate") from exc

    equipment = source_rows[CANDIDATE_DEVICE_FAMILY]
    original_parameter_rows = source_rows[PARAMETERS]
    selected = [
        record for record in original_parameter_rows
        if record["Parameter"].strip() == GUST_CODE
    ]
    if len(equipment) != 2 or len(original_parameter_rows) != 8 or len(selected) != 3:
        raise CandidateJoinBlocked("frozen original candidate cardinality changed")
    # Source uses other parameter codes, but must never let them contaminate
    # this single-FX_10 candidate binding.
    if {r["Parameter"].strip() for r in original_parameter_rows} != {
        "FX_10", "FNX_10", "FMX_10", "DX_10",
    }:
        raise CandidateJoinBlocked("unexpected original parameter code vocabulary")
    audit = _daily_pair_count(equipment, selected)
    if audit["window_days"] != 455:
        raise CandidateJoinBlocked("frozen DWD wind-observation window drifted")
    return {
        "profile": "opencatastrophe-dwd-fx10-maxwind-candidate-join-v0",
        "source_metadata_sha256": expected_sha256,
        "linked_original_wind_zip_sha256": frozen.MEASUREMENT_SHA256,
        "station_id": frozen.EXPECTED_STATION_ID,
        "fx10_original_parameter_records": len(selected),
        "maxwind_original_equipment_records": len(equipment),
        "parameter_code": GUST_CODE,
        "expected_unit_from_official_dwd_description": GUST_UNIT,
        "source_definition": DWD_DEFINITION,
        "candidate_device_file": CANDIDATE_DEVICE_FAMILY + ".txt",
        "original_device_parameter_foreign_key_proven": False,
        "endpoints_inclusive": "PROVISIONAL_RESEARCH_ASSUMPTION",
        "actual_source_dates_or_values_emitted": False,
        "actual_device_names_or_heights_emitted": False,
        "model_input_approved": False,
        "scientific_instrument_join_approved": False,
        **audit,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    opts = parser.parse_args(argv)
    try:
        result = inspect(opts.source_zip)
    except CandidateJoinBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "model_input_approved": False}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
