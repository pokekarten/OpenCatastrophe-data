# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded original Socrata 2025 / NTAD 2025 bridge-ID geometry challenger.

This is a research mismatch/coverage audit, not a source-authoritative
crosswalk, bridge exposure inventory, licensed loss model or insured location.
Fetches only 25 selected Socrata rows and at most 100 matching NTAD features.
All original coordinates and identifiers remain in memory; only aggregates
and source-response SHA-256 receipts are printed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import cos, hypot, isfinite, radians
import re
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

from research_runners.fhwa_nbi_socrata_metadata_gate_v0 import Blocked, _unique_object
from research_runners.fhwa_nbi_socrata_original_rows_v0 import (
    audit_rows, legacy_unsigned_degree_magnitude,
)

SOCRATA_HOST = "https://data.transportation.gov"
ARCGIS_HOST = "https://services.arcgis.com"
SOCRATA_API = SOCRATA_HOST + "/resource/pced-83j4.json"
NTAD_API = (
    ARCGIS_HOST + "/xOi1kZaI0eWDREZv/ArcGIS/rest/services/"
    "NTAD_National_Bridge_Inventory/FeatureServer/0/query"
)
SCHEMA = "OC_NBI_2025_INDEPENDENT_SOURCE_ID_GEOMETRY_CHALLENGE_V0"
STATE = 6
YEAR = 2025
SAMPLE_COUNT = 25
MAX_SAMPLES = 100
SOCRATA_FIELDS = (
    "year,state_code_001,structure_number_008,lat_016,long_017,year_built_027"
)
NTAD_FIELDS = (
    "STATE_CODE_001,STRUCTURE_NUMBER_008,LAT_016,LONG_017,YEAR_BUILT_027,LATDD,LONGDD"
)
SAFE_ID = re.compile(r"[A-Za-z0-9 _-]{1,15}\Z")


def _decode(original: bytes, *, upper_bound: int) -> object:
    if type(original) is not bytes or not 2 <= len(original) <= upper_bound:
        raise Blocked("original response is empty, unbounded or incomplete")
    try:
        return json.loads(
            original.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda v: (_ for _ in ()).throw(Blocked("nonfinite JSON")),
        )
    except Blocked:
        raise
    except (ValueError, UnicodeError) as exc:
        raise Blocked("not strict original source JSON") from exc


def source_rows(original: bytes) -> list[dict]:
    """Re-use source-vintaged, duplicate/identity guarded original FHWA gate."""
    audit_rows(original, expected_count=SAMPLE_COUNT,
               expected_state_code=STATE, expected_year=YEAR)
    rows = _decode(original, upper_bound=200_000)
    if type(rows) is not list:
        raise Blocked("expected original Socrata selected row array")
    for row in rows:
        ident = row.get("structure_number_008")
        if type(ident) is not str or not SAFE_ID.fullmatch(ident):
            raise Blocked("non-queryable original bridge identifier; no SQL guessing")
    return rows


def arcgis_where_from_exact_source_rows(rows: list[dict]) -> str:
    if type(rows) is not list or len(rows) != SAMPLE_COUNT:
        raise Blocked("requires verified fixed-size original source selection")
    ids = []
    for row in rows:
        if type(row) is not dict:
            raise Blocked("invalid original bridge ID row")
        ident = row.get("structure_number_008")
        if type(ident) is not str or not SAFE_ID.fullmatch(ident):
            raise Blocked("unsafe original bridge identifier; no dynamic SQL inference")
        ids.append(ident.replace("'", "''"))
    if len(set(ids)) != len(ids):
        raise Blocked("duplicate source bridge identity in query")
    quoted = ",".join("'" + ident + "'" for ident in sorted(ids))
    return ("STATE_CODE_001 IN ('06','6') "
            "AND STRUCTURE_NUMBER_008 IN (" + quoted + ")")


def _state(value: object) -> int | None:
    if type(value) is int and 1 <= value <= 99:
        return value
    if type(value) is str and re.fullmatch(r"[0-9]{1,2}", value):
        number = int(value)
        return number if 1 <= number <= 99 else None
    return None


def _valid_source_id(value: object) -> str | None:
    return value if type(value) is str and SAFE_ID.fullmatch(value) else None


def compare_sources(socrata_original: bytes, ntad_original: bytes) -> dict:
    """Only exact source-state/structure pairs can be compared.

    Discrepancies are approximate metric *challenges*, NOT surveyed truth.
    No inference about longitude sign, EPSG transform or source-row equality.
    """
    base = source_rows(socrata_original)
    layer = _decode(ntad_original, upper_bound=500_000)
    if type(layer) is not dict or layer.get("error") is not None:
        raise Blocked("NTAD original response is not an ArcGIS feature query")
    if layer.get("exceededTransferLimit") is True:
        raise Blocked("truncated NTAD query page cannot prove coverage")
    sr = layer.get("spatialReference")
    if type(sr) is not dict or sr.get("wkid") != 4326:
        raise Blocked("ArcGIS original response does not prove requested EPSG:4326")
    feats = layer.get("features")
    if type(feats) is not list or len(feats) > MAX_SAMPLES:
        raise Blocked("NTAD original response missing bounded feature array")
    selected = {(STATE, row["structure_number_008"]): row for row in base}
    if len(selected) != len(base):
        raise Blocked("duplicate source ID in source selection")
    grouped = defaultdict(list)
    invalid = unrelated = 0
    for feature in feats:
        if type(feature) is not dict or type(feature.get("attributes")) is not dict:
            raise Blocked("malformed NTAD feature attributes")
        attr = feature["attributes"]
        key = (_state(attr.get("STATE_CODE_001")),
               _valid_source_id(attr.get("STRUCTURE_NUMBER_008")))
        if None in key:
            invalid += 1
            continue
        if key not in selected:
            unrelated += 1
            continue
        grouped[key].append(feature)
    duplicates = sum(1 for group in grouped.values() if len(group) > 1)
    matched = [key for key in selected if len(grouped.get(key, [])) == 1]
    unmatched = sum(not grouped.get(key) for key in selected)
    ref_year_agree = ref_year_disagree = ref_year_unknown = 0
    geoms_valid = geoms_missing = 0
    coded_valid = coded_missing = 0
    comparisons = within_25 = within_250 = beyond_250 = 0
    max_challenger_distance = 0.0
    attr_code_concordance = attr_code_discordance = attr_code_unknown = 0
    decimal_available = decimal_missing = 0
    decimal_vs_source_comparisons = decimal_vs_source_over_25 = 0
    decimal_vs_geom_comparisons = decimal_vs_geom_over_25 = 0
    max_decimal_vs_source_m = max_decimal_vs_geom_m = 0.0
    for key in matched:
        row = selected[key]
        feature = grouped[key][0]
        attr = feature["attributes"]
        year = attr.get("YEAR_BUILT_027")
        src_year = row.get("year_built_027")
        if year is None or src_year is None:
            ref_year_unknown += 1
        else:
            try:
                ref_year_agree += int(int(year) == int(src_year))
                ref_year_disagree += int(int(year) != int(src_year))
            except (TypeError, ValueError):
                ref_year_unknown += 1
        pair_matches = []
        for src, ref, width in (
            ("lat_016", "LAT_016", 8),
            ("long_017", "LONG_017", 9),
        ):
            left = legacy_unsigned_degree_magnitude(row.get(src), width)
            right = legacy_unsigned_degree_magnitude(attr.get(ref), width)
            if left is None or right is None:
                pair_matches = []
                break
            pair_matches.append(round(left - right, 12) == 0)
        if not pair_matches:
            attr_code_unknown += 1
        elif all(pair_matches):
            attr_code_concordance += 1
        else:
            attr_code_discordance += 1
        lat = legacy_unsigned_degree_magnitude(row.get("lat_016"), 8)
        lon = legacy_unsigned_degree_magnitude(row.get("long_017"), 9)
        if lat is None or lon is None:
            coded_missing += 1
        else:
            coded_valid += 1
        # The same official NTAD layer independently publishes LATDD/LONGDD.
        # Compare their angular magnitudes to coded legacy fields and the
        # published point geometry, keeping individual values in memory only.
        dd_lat, dd_lon = attr.get("LATDD"), attr.get("LONGDD")
        decimal_ok = (
            type(dd_lat) in (float, int) and type(dd_lon) in (float, int)
            and isfinite(dd_lat) and isfinite(dd_lon)
            and 13 <= abs(dd_lat) <= 72 and 64 <= abs(dd_lon) <= 175
        )
        if decimal_ok:
            decimal_available += 1
            if lat is not None and lon is not None:
                gap = hypot(
                    abs(abs(dd_lat) - lat) * 111_320,
                    abs(abs(dd_lon) - lon) * 111_320 * cos(radians(lat)),
                )
                decimal_vs_source_comparisons += 1
                decimal_vs_source_over_25 += int(gap > 25)
                max_decimal_vs_source_m = max(max_decimal_vs_source_m, gap)
        else:
            decimal_missing += 1
        geom = feature.get("geometry")
        if (type(geom) is not dict or type(geom.get("x")) not in (int, float)
                or type(geom.get("y")) not in (int, float)
                or not isfinite(geom["x"]) or not isfinite(geom["y"])
                or not -180 <= geom["x"] <= 180 or
                not -90 <= geom["y"] <= 90 or
                geom["x"] == 0 or geom["y"] == 0):
            geoms_missing += 1
            continue
        geoms_valid += 1
        if decimal_ok:
            gap = hypot(
                abs(abs(float(geom["y"])) - abs(dd_lat)) * 111_320,
                abs(abs(float(geom["x"])) - abs(dd_lon)) * 111_320
                * cos(radians(abs(dd_lat))),
            )
            decimal_vs_geom_comparisons += 1
            decimal_vs_geom_over_25 += int(gap > 25)
            max_decimal_vs_geom_m = max(max_decimal_vs_geom_m, gap)
        if lat is None or lon is None:
            continue
        # Only unsigned-magnitude comparison: not a geodetic survey,
        # sign reconstruction, or proof that layer and source vintages match.
        delta_north = abs(abs(float(geom["y"])) - lat) * 111_320.0
        delta_east = (abs(abs(float(geom["x"])) - lon) * 111_320.0 *
                      cos(radians(lat)))
        approx_m = hypot(delta_north, delta_east)
        comparisons += 1
        max_challenger_distance = max(max_challenger_distance, approx_m)
        if approx_m <= 25:
            within_25 += 1
        elif approx_m <= 250:
            within_250 += 1
        else:
            beyond_250 += 1
    if (len(matched) + unmatched + duplicates != len(base) or
            geoms_valid + geoms_missing != len(matched) or
            ref_year_agree + ref_year_disagree + ref_year_unknown != len(matched) or
            within_25 + within_250 + beyond_250 != comparisons or
            decimal_available + decimal_missing != len(matched) or
            decimal_vs_source_comparisons > decimal_available or
            decimal_vs_geom_comparisons > decimal_available):
        raise Blocked("source join counts do not conserve")
    return {
        "schema": SCHEMA,
        "source_year": YEAR,
        "source_state_code": STATE,
        "socrata_original_sha256": sha256(socrata_original).hexdigest(),
        "socrata_original_bytes": len(socrata_original),
        "ntad_original_sha256": sha256(ntad_original).hexdigest(),
        "ntad_original_bytes": len(ntad_original),
        "socrata_selected_bridge_rows": len(base),
        "ntad_source_feature_rows": len(feats),
        "matched_unique_bridge_state_ids": len(matched),
        "source_ids_absent_in_bounded_ntad_response": unmatched,
        "source_ids_ambiguous_ntad_multiple_features": duplicates,
        "invalid_ntad_feature_identifiers": invalid,
        "ntad_feature_identifiers_not_requested": unrelated,
        "matched_source_year_built_equal": ref_year_agree,
        "matched_source_year_built_different": ref_year_disagree,
        "matched_source_year_built_unavailable": ref_year_unknown,
        "matched_nbi_coded_coordinate_strings_equal": attr_code_concordance,
        "matched_nbi_coded_coordinate_strings_different": attr_code_discordance,
        "matched_nbi_coded_coordinate_strings_unavailable": attr_code_unknown,
        "matched_ntad_valid_decimal_geometry": geoms_valid,
        "matched_ntad_missing_invalid_geometry": geoms_missing,
        "matched_source_valid_unsigned_dms": coded_valid,
        "matched_source_missing_invalid_dms": coded_missing,
        "ntad_decimal_LATDD_LONGDD_available": decimal_available,
        "ntad_decimal_LATDD_LONGDD_missing_invalid": decimal_missing,
        "ntad_decimal_vs_source_legacy_comparisons": decimal_vs_source_comparisons,
        "ntad_decimal_vs_source_legacy_over_25_m": decimal_vs_source_over_25,
        "ntad_decimal_vs_source_legacy_max_approx_m":
            round(max_decimal_vs_source_m, 2) if decimal_vs_source_comparisons else None,
        "ntad_decimal_vs_point_geometry_comparisons": decimal_vs_geom_comparisons,
        "ntad_decimal_vs_point_geometry_over_25_m": decimal_vs_geom_over_25,
        "ntad_decimal_vs_point_geometry_max_approx_m":
            round(max_decimal_vs_geom_m, 2) if decimal_vs_geom_comparisons else None,
        "angular_magnitude_comparisons": comparisons,
        "approx_delta_up_to_25_m": within_25,
        "approx_delta_over_25_up_to_250_m": within_250,
        "approx_delta_over_250_m": beyond_250,
        "max_approx_angular_delta_m": round(max_challenger_distance, 2)
        if comparisons else None,
        "original_data_sample_is_nonrandom": True,
        "socrata_and_ntad_different_snapshot_dates_possible": True,
        "longitude_sign_or_geodetic_datum_independently_proven": False,
        "zero_unmatched_geometries_silently_assumed": False,
        "requires_manual_review_of_original_angular_discrepancies":
            beyond_250 > 0 or within_250 > 0,
        "independent_point_geometry_agreement_admitted": False,
        "all_original_source_rows_or_features_exported": False,
        "independent_official_survey_validation": False,
        "complete_NBI_SNBI_crosswalk_validated": False,
        "insured_bridge_TIV_or_fragility_inferred": False,
        "model_input_admitted": False,
    }


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise Blocked("original provider redirected: fail closed")


def _get_original(url: str, bound: int) -> bytes:
    from urllib.error import HTTPError, URLError
    opener = build_opener(NoRedirects())
    request = Request(url, headers={"User-Agent": "OpenCatastrophe-research-read-only/1"})
    try:
        with opener.open(request, timeout=30) as reply:
            if reply.status != 200 or reply.geturl() != url:
                raise Blocked("original provider URL/status mismatch")
            contents = reply.read(bound + 1)
    except (HTTPError, URLError) as exc:
        raise Blocked("original public source unavailable") from exc
    if not 2 <= len(contents) <= bound:
        raise Blocked("original provider response exceeded strict byte bound")
    return contents


def run_original_pair() -> dict:
    q = urlencode({
        "$select": SOCRATA_FIELDS,
        "$where": "year=2025 AND state_code_001=6",
        "$order": "structure_number_008 ASC",
        "$limit": str(SAMPLE_COUNT),
    })
    first = _get_original(SOCRATA_API + "?" + q, 200_000)
    rows = source_rows(first)
    where = arcgis_where_from_exact_source_rows(rows)
    second_q = urlencode({
        "where": where, "outFields": NTAD_FIELDS,
        "returnGeometry": "true", "outSR": "4326",
        "resultRecordCount": str(MAX_SAMPLES), "f": "json",
    })
    second = _get_original(NTAD_API + "?" + second_q, 500_000)
    return compare_sources(first, second)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-sources", action="store_true",
                        help="retrieve only bounded official public source responses")
    opts = parser.parse_args()
    if not opts.original_sources:
        parser.error("research source-run only; use module functions for offline tests")
    print(json.dumps(run_original_pair(), sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
