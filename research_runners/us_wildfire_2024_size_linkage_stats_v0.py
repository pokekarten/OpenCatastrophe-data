#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline size-stratified FPA FOD 2024 MTBS_ID population audit.

Consumes ONLY three bounded ArcGIS grouped-statistics JSON snapshots, with
caller-supplied SHA-256 receipts. No event record, coordinate or polygon data,
network requests, claims, CAT hazard/loss or source admission.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re

MAX_BYTES = 32_000
CLASSES = tuple("ABCDEFG")
HASH = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED_FIELDS = {
    "fire_size_class": "esriFieldTypeString",
    "n": ("esriFieldTypeBigInteger", "esriFieldTypeInteger"),
}
# NWCG fire size classes; last class is unbounded.
ACRE_RANGES = {
    "A": "0-0.25",
    "B": ">0.25-<10",
    "C": "10-<100",
    "D": "100-<300",
    "E": "300-<1000",
    "F": "1000-<5000",
    "G": ">=5000",
}


class SizeLinkageBlocked(ValueError):
    """Original grouped source evidence is invalid or nonconserving."""


def _strict_obj(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise SizeLinkageBlocked("duplicate JSON key")
        seen[key] = value
    return seen


def _nonfinite(token):
    raise SizeLinkageBlocked("nonfinite JSON statistic")


def _parse_grouped(blob: bytes, expected_sha256: str, label: str) -> tuple[dict[str, int], str]:
    if type(blob) is not bytes or not 0 < len(blob) <= MAX_BYTES:
        raise SizeLinkageBlocked(label + ": empty or oversized original statistics JSON")
    if type(expected_sha256) is not str or not HASH.fullmatch(expected_sha256):
        raise SizeLinkageBlocked(label + ": lowercase original-response SHA-256 required")
    digest = hashlib.sha256(blob).hexdigest()
    if digest != expected_sha256:
        raise SizeLinkageBlocked(label + ": original statistics response SHA-256 mismatch")
    try:
        data = json.loads(blob.decode("utf-8"), object_pairs_hook=_strict_obj, parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise SizeLinkageBlocked(label + ": invalid UTF-8/JSON") from exc
    if not isinstance(data, dict) or "error" in data:
        raise SizeLinkageBlocked(label + ": ArcGIS REST returned error/invalid JSON object")
    if data.get("exceededTransferLimit") is True:
        raise SizeLinkageBlocked(label + ": grouped statistics transfer limit exceeded")
    if "exceededTransferLimit" in data and type(data["exceededTransferLimit"]) is not bool:
        raise SizeLinkageBlocked(label + ": malformed transfer-limit flag")
    fields = data.get("fields")
    if not isinstance(fields, list) or len(fields) != 2:
        raise SizeLinkageBlocked(label + ": two original grouped-statistic fields required")
    actual = {}
    for field in fields:
        if not isinstance(field, dict) or type(field.get("name")) is not str or type(field.get("type")) is not str:
            raise SizeLinkageBlocked(label + ": invalid original field metadata")
        key = field["name"].casefold()
        if key in actual:
            raise SizeLinkageBlocked(label + ": duplicate field")
        actual[key] = field["type"]
    if set(actual) != set(EXPECTED_FIELDS):
        raise SizeLinkageBlocked(label + ": unsupported source group/count columns")
    for key, want in EXPECTED_FIELDS.items():
        if actual[key] not in (want if type(want) is tuple else (want,)):
            raise SizeLinkageBlocked(label + ": changed source group/count type " + key)
    features = data.get("features")
    if not isinstance(features, list) or not 0 < len(features) <= 7:
        raise SizeLinkageBlocked(label + ": expected one to seven grouped classes")
    result = {}
    for feature in features:
        if not isinstance(feature, dict) or set(feature) != {"attributes"} or not isinstance(feature["attributes"], dict):
            raise SizeLinkageBlocked(label + ": original response features must contain attributes only")
        a = {key.casefold(): value for key, value in feature["attributes"].items() if type(key) is str}
        if len(a) != 2 or set(a) != set(EXPECTED_FIELDS) or len(feature["attributes"]) != 2:
            raise SizeLinkageBlocked(label + ": unsupported or duplicated group attributes")
        group, value = a["fire_size_class"], a["n"]
        if type(group) is not str or group not in CLASSES:
            raise SizeLinkageBlocked(label + ": unknown or missing NWCG fire size class")
        if group in result:
            raise SizeLinkageBlocked(label + ": repeated size class group")
        if type(value) is not int or not 0 < value <= 5_000_000:
            raise SizeLinkageBlocked(label + ": nonpositive or non-integer reported count")
        result[group] = value
    return result, digest


def _pct(part: int, total: int) -> str:
    if total <= 0 or part < 0 or part > total:
        raise SizeLinkageBlocked("invalid fraction for size-based coverage")
    return str((Decimal(part) * Decimal(100) / Decimal(total)).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP))


def audit_size_linkage(
    all_blob: bytes, all_sha256: str,
    linked_blob: bytes, linked_sha256: str,
    unlinked_blob: bytes, unlinked_sha256: str,
    *, fpa_release: str,
) -> dict:
    """Three-way count-conserving, size-conditioned source-ID availability audit."""
    if fpa_release != "FPA_FOD_20260615":
        raise SizeLinkageBlocked("only exact 2026 seventh-edition declaration allowed")
    all_counts, all_sha = _parse_grouped(all_blob, all_sha256, "all")
    yes_counts, yes_sha = _parse_grouped(linked_blob, linked_sha256, "linked")
    no_counts, no_sha = _parse_grouped(unlinked_blob, unlinked_sha256, "unlinked")
    if set(all_counts) != set(CLASSES):
        raise SizeLinkageBlocked("complete 2024 A-G source classes required for denominator")
    rows = []
    for category in CLASSES:
        total = all_counts[category]
        linked = yes_counts.get(category, 0)
        unlinked = no_counts.get(category, 0)
        if linked + unlinked != total:
            raise SizeLinkageBlocked("grouped cohort counts fail three-way conservation: " + category)
        rows.append({
            "class": category, "acre_range": ACRE_RANGES[category],
            "reported_fpa_fire_records": total,
            "mtbs_id_present_records": linked,
            "mtbs_id_absent_records": unlinked,
            "id_present_pct_of_class": _pct(linked, total),
        })
    all_n = sum(all_counts.values())
    linked_n = sum(yes_counts.values())
    unlinked_n = sum(no_counts.values())
    if linked_n + unlinked_n != all_n:
        raise SizeLinkageBlocked("2024 source-wide rows not conserved")
    f_g = sum(all_counts[x] for x in "FG")
    f_g_linked = sum(yes_counts.get(x, 0) for x in "FG")
    a_c = sum(all_counts[x] for x in "ABC")
    a_c_linked = sum(yes_counts.get(x, 0) for x in "ABC")
    return {
        "audit": "fpa-fod-2024-mtbs-id-size-conditioned-v0",
        "state": "RESEARCH_COUNTS_CONSERVED_NOT_MODEL_ADMITTED",
        "provider_source_edition_claim": fpa_release,
        "input_original_group_statistics_sha256": {
            "all": all_sha, "mtbs_id_present": yes_sha, "mtbs_id_absent": no_sha,
        },
        "fpa_fire_year": 2024,
        "fpa_reported_records": all_n,
        "mtbs_id_present_records": linked_n,
        "mtbs_id_absent_records": unlinked_n,
        "mtbs_id_present_pct_all": _pct(linked_n, all_n),
        "class_groups": rows,
        "classes_A_C_records": a_c,
        "classes_A_C_mtbs_id_present": a_c_linked,
        "classes_F_G_records": f_g,
        "classes_F_G_mtbs_id_present": f_g_linked,
        "classes_F_G_mtbs_id_absent": f_g-f_g_linked,
        "classes_F_G_mtbs_id_present_pct": _pct(f_g_linked, f_g),
        "small_class_A_linkage_requires_identity_review": yes_counts.get("A", 0) > 0,
        "size_conditioned_missingness_nonrandom_hypothesis_for_review": True,
        "fpa_cohort_conserved_by_class_and_total": True,
        "query_selection_origin_independently_authenticated": False,
        "full_MTBS_fire_id_match_proven": False,
        "source_coverage_or_fire_frequency_established": False,
        "independent_MTBS_obs_proven": False,
        "original_archived_asset_hash_verified": False,
        "rights_and_scientific_CAT_admission_granted": False,
        "insurance_loss_or_portfolio_inferred": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for label in ("all", "linked", "unlinked"):
        parser.add_argument("--" + label + "-statistics", type=Path, required=True)
        parser.add_argument("--" + label + "-sha256", required=True)
    parser.add_argument("--fpa-release", required=True)
    args = parser.parse_args(argv)
    try:
        paths = (args.all_statistics, args.linked_statistics, args.unlinked_statistics)
        for path in paths:
            if not path.is_file() or path.stat().st_size > MAX_BYTES:
                raise SizeLinkageBlocked("missing or oversized local ArcGIS stats snapshot")
        report = audit_size_linkage(
            args.all_statistics.read_bytes(), args.all_sha256,
            args.linked_statistics.read_bytes(), args.linked_sha256,
            args.unlinked_statistics.read_bytes(), args.unlinked_sha256,
            fpa_release=args.fpa_release,
        )
    except (OSError, SizeLinkageBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
