# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded official FHWA NBI public Socrata row *sample* diagnostic.

Source: data.transportation.gov/resource/pced-83j4.json
Only one deterministic, explicitly selected 50-row snapshot. No claims of
national coverage, insurer participation, verified geodetics or CAT model
input admission. No original bridge identifiers or coordinates in output.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

from research_runners.fhwa_nbi_socrata_metadata_gate_v0 import Blocked, _unique_object

CONTRACT = "OC_FHWA_NBI_SOCRATA_BOUNDED_ORIGINAL_ROW_RESEARCH_V0"
DATASET = "pced-83j4"
EXPECTED_COUNT = 50
MAX_BYTES = 200_000
COLUMNS = frozenset({
    "year", "state_code_001", "structure_number_008",
    "lat_016", "long_017", "year_built_027",
})


def _nonnegative_int(value: object, field: str, *, low: int, high: int) -> int:
    if type(value) is int:
        result = value
    elif type(value) is str and re.fullmatch(r"[0-9]{1,10}", value):
        result = int(value)
    else:
        raise Blocked(f"selected original row has invalid {field} numeric contract")
    if result < low or result > high:
        raise Blocked(f"selected original row {field} outside bounded research range")
    return result


def _coded_hundredths(value: object, width: int) -> int | None:
    """Unsigned *angular magnitude*, in exact hundredths of arcseconds.

    Legacy NBI item 16 is DDMMSSss (8 characters); item 17 DDDMMSSss
    (9 characters). Input may have lost leading zeroes through the numeric
    Socrata API. This is not a signed coordinate, CRS or bridge geometry.
    """
    if width not in (8, 9):
        return None
    if type(value) is int:
        digits = str(value)
    elif type(value) is str:
        digits = value
    else:
        return None
    if not digits or not digits.isascii() or not digits.isdigit() or len(digits) > width:
        return None
    padded = digits.zfill(width)
    degrees = int(padded[:width - 6])
    minutes = int(padded[width - 6:width - 4])
    hundredths = int(padded[width - 4:])
    # NBI permits all-zero (unknown) codes in some circumstances; never
    # turn an absent location into an actual point (0,0).
    if not (degrees or minutes or hundredths):
        return None
    if minutes >= 60 or hundredths >= 6000:
        return None
    if width == 8 and not 13 <= degrees <= 72:
        return None
    if width == 9 and not 64 <= degrees <= 175:
        return None
    return degrees * 360000 + minutes * 6000 + hundredths


def legacy_unsigned_degree_magnitude(value: object, width: int) -> float | None:
    """Exact DMS code -> unsigned degree magnitude; no automatic hemisphere.

    Kept for isolated, synthetic vector tests and ephemeral original source
    QA only. Callers must separately establish datum, hemisphere and
    independent spatial accuracy before constructing any real GeoJSON/OED.
    """
    units = _coded_hundredths(value, width)
    return units / 360000 if units is not None else None


def _zero_sentinel(value: object, width: int) -> bool:
    if type(value) is int:
        return value == 0
    return (type(value) is str and bool(value) and len(value) <= width
            and value.isascii() and value.isdigit() and
            all(char == "0" for char in value))


def _original_dms(value: object, width: int) -> bool:
    """True only for nonzero syntactically plausible legacy NBI angular codes."""
    return _coded_hundredths(value, width) is not None

def audit_rows(original: bytes, *, expected_count: int = EXPECTED_COUNT,
               expected_sha256: str | None = None,
               expected_state_code: int | None = None,
               expected_year: int | None = None) -> dict:
    """Validate original bounded rows, report aggregate diagnostics only."""
    if type(expected_count) is not int or not 1 <= expected_count <= EXPECTED_COUNT:
        raise Blocked("invalid bounded expected sample count")
    if expected_state_code is not None and (
            type(expected_state_code) is not int or not 1 <= expected_state_code <= 99):
        raise Blocked("invalid bounded expected state selector")
    if expected_year is not None and (
            type(expected_year) is not int or not 1992 <= expected_year <= 2026):
        raise Blocked("invalid bounded expected original year selector")
    if type(original) is not bytes or not 2 <= len(original) <= MAX_BYTES:
        raise Blocked("complete bounded original JSON row sample required")
    digest = sha256(original).hexdigest()
    if expected_sha256 is not None:
        if (type(expected_sha256) is not str or
                not re.fullmatch(r"[a-f0-9]{64}", expected_sha256) or
                digest != expected_sha256):
            raise Blocked("original row response SHA-256 mismatch")
    try:
        rows = json.loads(
            original.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda _: (_ for _ in ()).throw(Blocked("nonfinite JSON")),
        )
    except Blocked:
        raise
    except (UnicodeError, ValueError) as exc:
        raise Blocked("original NBI sample must be strict JSON array") from exc
    if type(rows) is not list or len(rows) != expected_count:
        raise Blocked("incomplete or oversized original NBI selected sample")
    seen = set()
    years: Counter[int] = Counter()
    states = set()
    dms_good = dms_unverified = built_valid = built_invalid = 0
    zero_sentinel_pair_count = 0
    for row in rows:
        if type(row) is not dict or not set(row).issubset(COLUMNS):
            raise Blocked("original sample must contain only six selected API fields")
        yr = _nonnegative_int(row.get("year"), "year", low=1992, high=2026)
        st = _nonnegative_int(row.get("state_code_001"), "state code", low=1, high=99)
        if expected_state_code is not None and st != expected_state_code:
            raise Blocked("selected original row violates explicit state selector")
        if expected_year is not None and yr != expected_year:
            raise Blocked("selected original row violates explicit year selector")
        ident = row.get("structure_number_008")
        if (type(ident) is not str or not 1 <= len(ident) <= 40 or
                ident.strip() != ident):
            raise Blocked("invalid NBI textual structure identity; do not coerce to number")
        key = (yr, st, ident)
        if key in seen:
            raise Blocked("duplicate bridge-year/state/structure identity in selected sample")
        seen.add(key)
        years[yr] += 1
        states.add(st)
        lat = row.get("lat_016")
        lon = row.get("long_017")
        if _zero_sentinel(lat, 8) or _zero_sentinel(lon, 9):
            zero_sentinel_pair_count += 1
        if _original_dms(lat, 8) and _original_dms(lon, 9):
            dms_good += 1
        else:
            dms_unverified += 1
        value = row.get("year_built_027")
        try:
            if value is None:
                raise Blocked("missing build-year value")
            _nonnegative_int(value, "build year", low=1800, high=yr)
            built_valid += 1
        except Blocked:
            built_invalid += 1
    return {
        "contract": CONTRACT,
        "status": "SOURCE_ROW_SAMPLE_FORMAT_DIAGNOSTIC_NOT_GEO_OR_CAT_ADMITTED",
        "source_dataset_id": DATASET,
        "original_response_sha256": digest,
        "original_response_bytes": len(original),
        "sample_rows": len(rows),
        "expected_query_state_code": expected_state_code,
        "expected_query_year": expected_year,
        "all_sample_rows_match_explicit_selectors": True,
        "year_count_histogram": {str(y): years[y] for y in sorted(years)},
        "distinct_state_codes_in_selected_sample": len(states),
        "unique_bridge_year_state_structure_in_sample": len(seen),
        "legacy_dms_format_plausible_count": dms_good,
        "legacy_dms_format_unverified_count": dms_unverified,
        "legacy_zero_sentinel_coordinate_pair_count": zero_sentinel_pair_count,
        "legacy_angular_conversion_contract": "unsigned_hundredth_arcsecond_no_CRS_or_hemisphere",
        "signed_decimal_coordinate_pair_exported": False,
        "build_year_range_plausible_count": built_valid,
        "build_year_unknown_or_unverified_count": built_invalid,
        "original_row_response_provider_signed": False,
        "metadata_source_join_independently_proven": False,
        "sample_represents_national_population": False,
        "encoded_coordinate_crs_validated": False,
        "bridge_point_coordinate_accuracy_validated": False,
        "unique_physical_bridge_identity_historically_verified": False,
        "original_inspection_condition_values_examined": False,
        "insurer_ownership_or_tiv_inferred": False,
        "source_license_scientifically_admitted": False,
        "annual_CAT_event_or_gross_net_EP_validated": False,
        "model_input_admitted": False,
        "original_individual_rows_or_coordinates_exported": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-sample", type=Path, required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-count", type=int, default=EXPECTED_COUNT)
    parser.add_argument("--expected-state-code", type=int)
    parser.add_argument("--expected-year", type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    source = args.original_sample
    if (source.is_symlink() or not source.is_file() or
            not 2 <= source.stat().st_size <= MAX_BYTES):
        parser.error("bounded original regular JSON file required")
    if args.out is not None and (args.out.is_symlink() or args.out.exists() or
                                 args.out.resolve() == source.resolve()):
        parser.error("refuse existing or source-aliased output")
    receipt = audit_rows(
        source.read_bytes(), expected_sha256=args.expected_sha256,
        expected_count=args.expected_count, expected_state_code=args.expected_state_code,
        expected_year=args.expected_year,
    )
    result = json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.out is None:
        print(result, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
