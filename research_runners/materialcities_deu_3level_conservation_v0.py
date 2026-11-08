#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original-byte Germany MaterialCities ADM0/ADM1/ADM2 conservation research gate.

It checks the same publisher's 2026.9 modelled floor area at three levels,
including all 15 function/structure components per Bundesland. It does NOT
join GADM ADM2 to Destatis AGS Kreise (402 versus 400) or infer insured assets.
Source bytes and per-region derived values remain outside the public repo.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path
import re
import zipfile

from research_runners.materialcities_adm2_gfa_preflight_v0 import (
    ADM2_MEMBER,
    GFA_FIELDS,
    MaterialCitiesPreflightError,
    _adm2_member,
    _number,
    inspect_archive,
)

ARCHIVE_MEMBERS = {
    "ADM0": "MaterialCities_adm_gfa_ADM0.csv",
    "ADM1": "MaterialCities_adm_gfa_ADM1.csv",
    "ADM2": ADM2_MEMBER,
}
EXPECTED_COUNTS = {"ADM0": 1, "ADM1": 16, "ADM2": 402}
STATE_ID = re.compile(r"DEU\.(\d{1,2})_(\d+)\Z")
DISTRICT_ID = re.compile(r"DEU\.(\d{1,2})\.(\d+)_(\d+)\Z")
MAX_ROWS = 50000
ABS_TOL_M2 = 0.01
REL_TOL = 1e-12


def _read_source_level(z: zipfile.ZipFile, level: str) -> tuple[list[dict], int]:
    member = ARCHIVE_MEMBERS[level]
    try:
        info = z.getinfo(member)
    except KeyError as exc:
        raise MaterialCitiesPreflightError(f"missing original {level} source member") from exc
    if info.file_size > 20_000_000 or info.is_dir():
        raise MaterialCitiesPreflightError("unbounded original member size")
    records = []
    rows_seen = 0
    try:
        with z.open(info) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
            header = reader.fieldnames
            if (not header or len(header) != len(set(header))
                    or not {"GID_0", *GFA_FIELDS}.issubset(header)
                    or (level != "ADM0" and "GID_1" not in header)
                    or (level == "ADM2" and "GID_2" not in header)
                    or "GFA" in header):
                raise MaterialCitiesPreflightError(f"unreviewed {level} source schema")
            for row in reader:
                rows_seen += 1
                if rows_seen > MAX_ROWS or None in row:
                    raise MaterialCitiesPreflightError("invalid or oversized CSV record set")
                if (row.get("GID_0") or "").strip() != "DEU":
                    continue
                vals = tuple(_number(row.get(field), field) for field in GFA_FIELDS)
                total = math.fsum(vals)
                if not math.isfinite(total):
                    raise MaterialCitiesPreflightError("nonfinite source component sum")
                records.append({
                    "state": (row.get("GID_1") or "").strip(),
                    "district": (row.get("GID_2") or "").strip(),
                    "values": vals,
                })
    except (UnicodeError, csv.Error, zipfile.BadZipFile, OSError, RuntimeError) as exc:
        raise MaterialCitiesPreflightError(f"unreadable {level} source member") from exc
    if not records:
        raise MaterialCitiesPreflightError(f"no German rows in {level} source")
    return records, rows_seen


def _component_sums(records: list[dict]) -> tuple[float, ...]:
    return tuple(math.fsum(row["values"][i] for row in records)
                 for i in range(len(GFA_FIELDS)))


def _require_conservation(a: tuple[float, ...], b: tuple[float, ...], context: str) -> float:
    max_delta = 0.0
    for field, x, y in zip(GFA_FIELDS, a, b):
        delta = abs(x - y)
        max_delta = max(max_delta, delta)
        if not math.isclose(x, y, abs_tol=ABS_TOL_M2, rel_tol=REL_TOL):
            raise MaterialCitiesPreflightError(
                f"source aggregation drift in {context}, component {field}")
    return max_delta


def inspect_deu_three_levels(blob: bytes, *, strict_original_counts: bool = True,
                             expected_md5: str | None = None,
                             expected_sha256: str | None = None) -> dict:
    """Source-native level and state reconciliation, no external asset join."""
    # Synthetic tests explicitly pass their own digest pins; default reads only
    # genuine original publisher bytes through the version-pinned preflight.
    args = {}
    if expected_md5 is not None:
        args["expected_md5"] = expected_md5
    if expected_sha256 is not None:
        args["expected_sha256"] = expected_sha256
    original = inspect_archive(blob, country="DEU", **args)
    if not original["complete_unique_region_keyset"]:
        raise MaterialCitiesPreflightError("German source ADM2 identities not unique")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        _adm2_member(z)  # reject unsafe ZIP members, duplicate filenames, archive bombs
        rows = {level: _read_source_level(z, level)[0] for level in ARCHIVE_MEMBERS}
    counts = {level: len(records) for level, records in rows.items()}
    if counts["ADM2"] != original["source_adm2_rows_selected"]:
        raise MaterialCitiesPreflightError("ADM2 input disagrees with canonical source preflight")
    if strict_original_counts and counts != EXPECTED_COUNTS:
        raise MaterialCitiesPreflightError("exact original Germany 1/16/402 counts drift")
    if counts["ADM0"] != 1:
        raise MaterialCitiesPreflightError("German ADM0 source is not unique")
    states = {}
    for record in rows["ADM1"]:
        state = record["state"]
        if not STATE_ID.fullmatch(state) or state in states:
            raise MaterialCitiesPreflightError("ambiguous GADM ADM1 state identity")
        states[state] = record
    districts_by_state = {key: [] for key in states}
    district_keys = set()
    for record in rows["ADM2"]:
        district = record["district"]
        state = record["state"]
        match_state = STATE_ID.fullmatch(state)
        match_district = DISTRICT_ID.fullmatch(district)
        if (not match_state or not match_district or state not in states
                or match_district.group(1) != match_state.group(1)
                or match_district.group(3) != match_state.group(2)
                or district in district_keys):
            raise MaterialCitiesPreflightError("ADM2 identity does not match parent GADM state")
        district_keys.add(district)
        districts_by_state[state].append(record)
    if any(not records for records in districts_by_state.values()):
        raise MaterialCitiesPreflightError("German GADM state has no ADM2 child rows")
    max_state_delta = 0.0
    for state, record in states.items():
        max_state_delta = max(max_state_delta, _require_conservation(
            record["values"], _component_sums(districts_by_state[state]), "GADM state"))
    national = rows["ADM0"][0]["values"]
    d01 = _require_conservation(national, _component_sums(rows["ADM1"]), "national ADM0/ADM1")
    d02 = _require_conservation(national, _component_sums(rows["ADM2"]), "national ADM0/ADM2")
    return {
        "source_candidate_id": original["source_candidate_id"],
        "original_archive_sha256": original["archive_sha256"],
        "country": "DEU",
        "source_native_counts": counts,
        "distinct_adm1_parent_keys": len(states),
        "distinct_adm2_source_keys": len(district_keys),
        "all_15_components_conserved_across_levels": True,
        "max_adm1_to_children_component_delta_m2": max_state_delta,
        "max_national_to_adm1_component_delta_m2": d01,
        "max_national_to_adm2_component_delta_m2": d02,
        "destatis_2022_kreis_count_known_separately": 400,
        "gadm_adm2_to_ags_2022_crosswalk_proven": False,
        "same_source_internal_consistency_only": True,
        "independent_building_stock_validation": False,
        "source_rights_admitted": False,
        "insurer_sites_geolocated": False,
        "insurer_tiv_inferred": False,
        "cat_model_input_approved": False,
        "research_only": True,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", required=True, type=Path, help="Original source ZIP outside Git")
    p.add_argument("--out", required=True, type=Path, help="Local non-public JSON receipt")
    args = p.parse_args()
    try:
        if args.out.exists():
            raise MaterialCitiesPreflightError("refuse to overwrite existing source receipt")
        report = inspect_deu_three_levels(args.archive.read_bytes())
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, MaterialCitiesPreflightError) as exc:
        p.exit(2, f"BLOCKED: {exc}\n")
    print("PASS: original-source internal 1/16/402 GFA hierarchy; RESEARCH ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
