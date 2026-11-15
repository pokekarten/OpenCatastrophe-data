#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Bounded offline scientific preflight of a REDUCED HydroATLAS v1 H01 projection.

Input JSONL is an externally prepared, local four-column projection, NOT original
provider GDB/SHP. Its SHA-256 is not the original archive SHA-256. No downloads,
source IDs/values printed, DB writes, model admission or silent missing-value repair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SOURCE = "hydrosheds.hydroatlas.v1"
FIELDS = frozenset(("HYBAS_ID", "dis_m3_pyr", "dis_m3_pmn", "dis_m3_pmx"))
H01 = ("dis_m3_pyr", "dis_m3_pmn", "dis_m3_pmx")
MAX_BYTES = 131072
MAX_ROWS = 128
LAYER = re.compile(r"BasinATLAS_v10_lev(0[1-9]|1[0-2])\Z")


class H01Blocked(ValueError):
    """Projection type, source scope or science semantics not verified."""


def _unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise H01Blocked("duplicate projected JSON field")
        result[k] = v
    return result


def _reject_constant(_):
    raise H01Blocked("nonfinite JSON constant")


def inspect(raw: bytes, *, layer: str) -> dict:
    if type(layer) is not str or not LAYER.fullmatch(layer):
        raise H01Blocked("unreviewed BasinATLAS layer")
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise H01Blocked("projection byte boundary")
    lines = raw.splitlines()
    if not 1 <= len(lines) <= MAX_ROWS:
        raise H01Blocked("projection record limit")

    seen = set()
    full = nulls = all_zero = 0
    for line in lines:
        if not line.strip():
            raise H01Blocked("blank projection row")
        try:
            row = json.loads(line.decode("utf-8"), object_pairs_hook=_unique,
                             parse_constant=_reject_constant)
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise H01Blocked("invalid projection JSON") from exc
        if type(row) is not dict or set(row) != FIELDS:
            raise H01Blocked("not an exact H01 four-field projection")
        identifier = row["HYBAS_ID"]
        if type(identifier) is not int or identifier <= 0 or identifier in seen:
            raise H01Blocked("invalid or duplicate basin identity")
        seen.add(identifier)
        triple = tuple(row[k] for k in H01)
        # Null means unresolved unknown; never infer zero or guess -9999.
        for v in triple:
            if v is not None and (type(v) not in (int, float)
                                  or not math.isfinite(v) or v < 0):
                raise H01Blocked("unverified negative, nonfinite or nonnumeric flow")
        if any(v is None for v in triple):
            nulls += 1
            continue
        mean, minimum, maximum = triple
        # H01 mn/mx are lowest/highest of twelve 1971-2000 monthly means,
        # NOT annual event maxima, return periods or observed flood peaks.
        if not minimum <= mean <= maximum:
            raise H01Blocked("H01 naturalized monthly-climatology bounds reversed")
        full += 1
        if mean == minimum == maximum == 0:
            all_zero += 1

    return {
        "profile": "hydroatlas-v1-basinh01-reduced-projection-preflight-v0",
        "source_id": SOURCE, "layer": layer,
        "reviewed_columns": list(H01), "unit": "m3/s",
        "watergap_version": "2.2", "climate_reference": "1971-2000",
        "min_max_from_twelve_long_term_monthly_means": True,
        "records": len(lines), "complete_triplets": full,
        "unresolved_null_triplets": nulls, "all_zero_triplets": all_zero,
        "projection_bytes": len(raw),
        "projection_sha256": hashlib.sha256(raw).hexdigest(),
        "projection_is_not_original_gis": True,
        "original_archive_sha256_verified": False,
        "hydrological_context_preflight_pass": nulls == 0,
        "independent_gauge_validation": False,
        "event_flood_hazard_or_return_period_approved": False,
        "CAT_model_input_approved": False,
        "source_values_ids_or_geometry_persisted_by_preflight": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projected-jsonl", type=Path, required=True)
    p.add_argument("--layer", required=True)
    args = p.parse_args(argv)
    try:
        with args.projected_jsonl.open("rb") as f:
            data = f.read(MAX_BYTES + 1)
        receipt = inspect(data, layer=args.layer)
    except (OSError, H01Blocked):
        print("BLOCKED: HydroATLAS H01 projected sample invalid", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
