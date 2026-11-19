#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Original 2024 FPA FOD state-by-size MTBS_ID availability, grouped counts only.

Offline, immutable-SHA source reply validation; no events/coordinates/maps,
historical frequency, wildfire-cat risk or insurer data are imported.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re

MAX_BYTES = 100_000
MAX_CELLS = 400
CLASSES = "ABCDEFG"
SHA = re.compile(r"[a-f0-9]{64}\Z")
STATE = re.compile(r"[A-Z]{2}\Z")
FIELDS = {
    "state": ("esriFieldTypeString",),
    "fire_size_class": ("esriFieldTypeString",),
    "n": ("esriFieldTypeBigInteger", "esriFieldTypeInteger"),
}
ORIGINAL_2024_MARGINALS = {
    "all": dict(A=43445, B=34441, C=7296, D=1263, E=640, F=388, G=235),
    "linked": dict(A=1, B=0, C=0, D=6, E=31, F=224, G=153),
    "unlinked": dict(A=43444, B=34441, C=7296, D=1257, E=609, F=164, G=82),
}


class GroupedStateBlocked(ValueError):
    """Fail closed on unsupported source response or incoherent original counts."""


def _object(pairs):
    d = {}
    for key, val in pairs:
        if key in d:
            raise GroupedStateBlocked("duplicate original JSON field")
        d[key] = val
    return d


def _nonfinite(value):
    raise GroupedStateBlocked("nonfinite original JSON statistic")


def _parse(raw: bytes, digest: str, kind: str):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise GroupedStateBlocked(kind + ": missing/oversized original JSON bytes")
    if type(digest) is not str or not SHA.fullmatch(digest):
        raise GroupedStateBlocked(kind + ": require exact lowercase original SHA256")
    sha = hashlib.sha256(raw).hexdigest()
    if sha != digest:
        raise GroupedStateBlocked(kind + ": original JSON SHA256 mismatch")
    try:
        doc = json.loads(raw.decode("utf8"), object_pairs_hook=_object, parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GroupedStateBlocked(kind + ": malformed UTF8/JSON source response") from exc
    if not isinstance(doc, dict) or "error" in doc:
        raise GroupedStateBlocked(kind + ": provider returned error/nonobject")
    if doc.get("exceededTransferLimit") is True:
        raise GroupedStateBlocked(kind + ": transfer limit truncated source response")
    if "exceededTransferLimit" in doc and type(doc["exceededTransferLimit"]) is not bool:
        raise GroupedStateBlocked(kind + ": invalid transfer flag")
    fs = doc.get("fields")
    if not isinstance(fs, list) or len(fs) != 3:
        raise GroupedStateBlocked(kind + ": native grouped field definitions missing")
    cols = {}
    for f in fs:
        if not isinstance(f, dict) or type(f.get("name")) is not str or type(f.get("type")) is not str:
            raise GroupedStateBlocked(kind + ": invalid field metadata")
        name = f["name"].casefold()
        if name in cols:
            raise GroupedStateBlocked(kind + ": duplicated source field")
        cols[name] = f["type"]
    if set(cols) != set(FIELDS) or any(cols[k] not in FIELDS[k] for k in FIELDS):
        raise GroupedStateBlocked(kind + ": native grouped fields or types drifted")
    feats = doc.get("features")
    if not isinstance(feats, list) or not 0 < len(feats) <= MAX_CELLS:
        raise GroupedStateBlocked(kind + ": expected bounded grouped features")
    counts = {}
    for f in feats:
        if not isinstance(f, dict) or set(f) != {"attributes"} or not isinstance(f["attributes"], dict):
            raise GroupedStateBlocked(kind + ": geometry or invalid grouped feature")
        raw_attrs = f["attributes"]
        if len(raw_attrs) != 3 or any(type(k) is not str for k in raw_attrs):
            raise GroupedStateBlocked(kind + ": invalid grouped attributes")
        a = {k.casefold(): v for k, v in raw_attrs.items()}
        if len(a) != 3 or set(a) != set(FIELDS):
            raise GroupedStateBlocked(kind + ": unexpected grouped columns")
        state, cls, n = a["state"], a["fire_size_class"], a["n"]
        if type(state) is not str or not STATE.fullmatch(state):
            raise GroupedStateBlocked(kind + ": invalid state/territory code")
        if type(cls) is not str or cls not in CLASSES:
            raise GroupedStateBlocked(kind + ": invalid NWCG size class")
        if type(n) is not int or not 0 < n <= 5_000_000:
            raise GroupedStateBlocked(kind + ": invalid grouped count")
        key = (state, cls)
        if key in counts:
            raise GroupedStateBlocked(kind + ": duplicate state by size cell")
        counts[key] = n
    return counts, sha


def _pct(part: int, total: int):
    if not total:
        return None
    if not 0 <= part <= total:
        raise GroupedStateBlocked("ratio denominator invalid")
    return str((Decimal(part) * 100 / Decimal(total)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    ))


def audit_state_size(all_bytes, all_sha, yes_bytes, yes_sha, no_bytes, no_sha,
                     *, fpa_release, expected_marginals=None, expected_states=53):
    """Conserve three independent 2024 ArcGIS source populations for every cell."""
    if fpa_release != "FPA_FOD_20260615":
        raise GroupedStateBlocked("source edition differs from seventh release")
    a, hash_a = _parse(all_bytes, all_sha, "all")
    y, hash_y = _parse(yes_bytes, yes_sha, "linked")
    n, hash_n = _parse(no_bytes, no_sha, "unlinked")
    if not set(y).issubset(a) or not set(n).issubset(a):
        raise GroupedStateBlocked("subgroup outside complete state-by-size cells")
    codes = sorted({state for state, cls in a})
    if type(expected_states) is not int or not 1 <= expected_states <= 100 or len(codes) != expected_states:
        raise GroupedStateBlocked("unexpected original state/territory population")
    margins = {"all": Counter(), "linked": Counter(), "unlinked": Counter()}
    per_state = defaultdict(Counter)
    for (state, cls), total in a.items():
        linked, absent = y.get((state, cls), 0), n.get((state, cls), 0)
        if linked + absent != total:
            raise GroupedStateBlocked("three-way conservation fails in state and size")
        margins["all"][cls] += total
        margins["linked"][cls] += linked
        margins["unlinked"][cls] += absent
        for label, count in (("all", total), ("linked", linked), ("unlinked", absent)):
            per_state[state][label] += count
        if cls in "FG":
            per_state[state]["fg"] += total
            per_state[state]["fg_linked"] += linked
        if cls in "DE":
            per_state[state]["de"] += total
            per_state[state]["de_linked"] += linked
    if set(margins["all"]) != set(CLASSES):
        raise GroupedStateBlocked("missing one or more national A-G denominator classes")
    if expected_marginals is None:
        expected_marginals = ORIGINAL_2024_MARGINALS
    if set(expected_marginals) != set(margins) or any(
        {cls: margins[k][cls] for cls in CLASSES} !=
        {cls: expected_marginals[k].get(cls) for cls in CLASSES}
        for k in margins
    ):
        raise GroupedStateBlocked("prior independently audited 2024 A-G marginals drifted")
    state_rows = []
    for state in codes:
        v = per_state[state]
        state_rows.append({
            "state_code": state,
            "fpa_total": v["all"],
            "mtbs_id_present": v["linked"],
            "mtbs_id_pct_all_sizes": _pct(v["linked"], v["all"]),
            "large_fg_fpa_total": v["fg"],
            "large_fg_mtbs_id_present": v["fg_linked"],
            "large_fg_pct_if_n_ge_10": _pct(v["fg_linked"], v["fg"]) if v["fg"] >= 10 else None,
            "medium_de_fpa_total": v["de"],
            "medium_de_mtbs_id_present": v["de_linked"],
        })
    return {
        "audit": "fpa-fod-2024-state-size-mtbs-id-original-query-v0",
        "state": "THREE_WAY_CELL_COUNTS_CONSERVED_NOT_CAT_ADMITTED",
        "declared_current_edition": fpa_release,
        "publisher_fire_year": 2024,
        "original_raw_body_sha256": {"all": hash_a, "linked": hash_y, "unlinked": hash_n},
        "number_state_territory_codes": len(codes),
        "original_nonempty_cell_count": {"all": len(a), "linked": len(y), "unlinked": len(n)},
        "record_totals": {k: sum(margins[k].values()) for k in margins},
        "national_size_marginals": {
            cls: {k: margins[k][cls] for k in margins} for cls in CLASSES
        },
        "size_by_state_cells_three_way_conserved": True,
        "states_large_fg_denominator_ge_10": sum(row["large_fg_fpa_total"] >= 10 for row in state_rows),
        "linked_class_A_count_requires_identity_review": margins["linked"]["A"],
        "state_rows": state_rows,
        "same_release_2024_source_marginals_match": True,
        "source_query_origin_authenticated_by_sha256": False,
        "original_archived_fpa_asset_sha256_verified": False,
        "MTBS_ID_equivalent_to_verified_MTBS_FIRE_ID_join": False,
        "complete_and_unbiased_wildfire_incident_population": False,
        "source_rights_and_CAT_admission_granted": False,
        "insurer_event_frequency_or_losses_inferred": False,
        "individual_source_fire_ids_coordinates_or_perimeters_emitted": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("all", "linked", "unlinked"):
        parser.add_argument("--" + name + "-statistics", type=Path, required=True)
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--fpa-release", required=True)
    a = parser.parse_args(argv)
    try:
        files = (a.all_statistics, a.linked_statistics, a.unlinked_statistics)
        if any(not f.is_file() or f.stat().st_size > MAX_BYTES for f in files):
            raise GroupedStateBlocked("missing or oversized local ArcGIS source replies")
        result = audit_state_size(
            a.all_statistics.read_bytes(), a.all_sha256,
            a.linked_statistics.read_bytes(), a.linked_sha256,
            a.unlinked_statistics.read_bytes(), a.unlinked_sha256,
            fpa_release=a.fpa_release,
        )
    except (OSError, GroupedStateBlocked) as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
