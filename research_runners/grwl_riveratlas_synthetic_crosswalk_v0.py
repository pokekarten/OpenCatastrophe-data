# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-only conservative GRWL/RiverATLAS geometry crosswalk diagnostic.

No real geography, source data or insurance records are accepted. The input uses
an intentionally fictional local metric coordinate system. An accepted match
is a *candidate* only, not a hydrographic identifier or flood-model input.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

from shapely import wkt
from shapely.geometry import LineString

SCHEMA = "opencatastrophe-grwl-riveratlas-synthetic-crosswalk-v0"
MAX_FEATURES = 32
MAX_FILE_BYTES = 32768
MAX_WKT_CHARS = 2048
BUFFER_M = 20.0
MIN_BIDIRECTIONAL_OVERLAP = 0.8
MIN_ABS_COS = 0.95
SRC_RECORDS = {
    "2018": ("1297434", "GRWL_summaryStats_V01.01.zip", "c37021e144fbff19ae3fc4e701d85d38"),
    "2026": ("18624542", "GRWL_summaryStats_V01.02.zip", "cac403c1a59bce7a74432085d3f5bd3a"),
}
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")


class CrosswalkError(ValueError):
    """Input violates exact synthetic research boundaries."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise CrosswalkError(f"duplicate JSON key: {k}")
        out[k] = v
    return out


def reject_constant(value: str) -> None:
    raise CrosswalkError(f"non-finite JSON constant: {value}")


def _exact_keys(obj: Any, keys: set[str], where: str) -> None:
    if not isinstance(obj, dict) or set(obj) != keys:
        raise CrosswalkError(f"{where}: unexpected or missing fields")


def _id(value: Any) -> str:
    if type(value) is not str or not IDENTIFIER.fullmatch(value):
        raise CrosswalkError("invalid synthetic feature ID")
    return value


def _line(value: Any) -> LineString:
    if type(value) is not str or not 0 < len(value) <= MAX_WKT_CHARS:
        raise CrosswalkError("invalid synthetic WKT length/type")
    try:
        geom = wkt.loads(value)
    except Exception as exc:
        raise CrosswalkError("malformed synthetic WKT") from exc
    if not isinstance(geom, LineString) or geom.is_empty or not geom.is_valid or geom.has_z:
        raise CrosswalkError("expected valid two-dimensional LineString")
    if not math.isfinite(geom.length) or not 10 <= geom.length <= 50000:
        raise CrosswalkError("invalid synthetic line length (metres)")
    if len(geom.coords) > 128:
        raise CrosswalkError("synthetic lines exceed vertex cap")
    if any(not math.isfinite(x) or abs(x) > 100000 for xy in geom.coords for x in xy):
        raise CrosswalkError("invalid synthetic coordinate extent")
    return geom


def _direction(g: LineString) -> tuple[float, float]:
    a, b = g.coords[0], g.coords[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1:
        raise CrosswalkError("closed/near-zero endpoint direction is unsupported")
    return dx / length, dy / length


def _parse(data: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    _exact_keys(data, {"schema", "synthetic_only", "coordinate_frame", "grwl_release", "grwl_archive", "grwl_provider_md5", "grwl", "riveratlas"}, "root")
    if data["schema"] != SCHEMA or data["synthetic_only"] is not True or data["coordinate_frame"] != "LOCAL_METRIC_SYNTHETIC":
        raise CrosswalkError("only synthetic local-metric input is accepted")
    release = data["grwl_release"]
    if type(release) is not str or release not in SRC_RECORDS:
        raise CrosswalkError("unknown GRWL provider release; do not mix 2018 and 2026 files")
    _, archive, md5 = SRC_RECORDS[release]
    if data["grwl_archive"] != archive or data["grwl_provider_md5"] != md5:
        raise CrosswalkError("selected archive name/checksum disagrees with pinned provider record")
    g, r = data["grwl"], data["riveratlas"]
    if not isinstance(g, list) or not isinstance(r, list) or not 1 <= len(g) <= MAX_FEATURES or not 1 <= len(r) <= MAX_FEATURES:
        raise CrosswalkError("input feature count must be bounded and non-empty")
    parsed_g, parsed_r = [], []
    all_g, all_r = set(), set()
    for row in g:
        _exact_keys(row, {"id", "wkt", "width_mean_m", "lakeflag"}, "grwl feature")
        uid = _id(row["id"])
        if uid in all_g:
            raise CrosswalkError("duplicate synthetic GRWL feature ID")
        all_g.add(uid)
        width = row["width_mean_m"]
        if type(width) not in (int, float) or not math.isfinite(width) or not 0 < width <= 100000:
            raise CrosswalkError("invalid width_mean_m")
        if type(row["lakeflag"]) is not int or row["lakeflag"] not in (0, 1, 2, 3):
            raise CrosswalkError("invalid lakeflag")
        line = _line(row["wkt"])
        parsed_g.append({"id": uid, "line": line, "direction": _direction(line), "width_mean_m": width, "lakeflag": row["lakeflag"]})
    for row in r:
        _exact_keys(row, {"id", "wkt"}, "riveratlas feature")
        uid = _id(row["id"])
        if uid in all_r:
            raise CrosswalkError("duplicate RiverATLAS feature ID")
        all_r.add(uid)
        line = _line(row["wkt"])
        parsed_r.append({"id": uid, "line": line, "direction": _direction(line)})
    return parsed_g, parsed_r, release


def crosswalk(data: Any) -> dict[str, Any]:
    grwl, riveratlas, release = _parse(data)
    matches_by_g: dict[str, list[str]] = {row["id"]: [] for row in grwl}
    matches_by_r: dict[str, list[str]] = {row["id"]: [] for row in riveratlas}
    for g in grwl:
        if g["lakeflag"] != 0:
            continue
        for r in riveratlas:
            cosine = abs(sum(x * y for x, y in zip(g["direction"], r["direction"])))
            if cosine < MIN_ABS_COS or g["line"].distance(r["line"]) > BUFFER_M:
                continue
            overlap_g = g["line"].intersection(r["line"].buffer(BUFFER_M)).length / g["line"].length
            overlap_r = r["line"].intersection(g["line"].buffer(BUFFER_M)).length / r["line"].length
            if overlap_g >= MIN_BIDIRECTIONAL_OVERLAP and overlap_r >= MIN_BIDIRECTIONAL_OVERLAP:
                matches_by_g[g["id"]].append(r["id"])
                matches_by_r[r["id"]].append(g["id"])
    results = []
    for g in sorted(grwl, key=lambda item: item["id"]):
        candidates = sorted(matches_by_g[g["id"]])
        if g["lakeflag"] != 0:
            status = "excluded_non_river"
        elif not candidates:
            status = "no_spatial_candidate"
        elif len(candidates) != 1 or len(matches_by_r[candidates[0]]) != 1:
            status = "ambiguous_do_not_join"
        else:
            status = "one_to_one_candidate_only"
        results.append({"grwl_synthetic_id": g["id"], "candidate_riveratlas_synthetic_ids": candidates, "status": status})
    return {
        "schema": SCHEMA,
        "release_metadata_identity": {"zenodo_record": SRC_RECORDS[release][0], "grwl_release": release, "archive_name": SRC_RECORDS[release][1], "provider_md5_unverified": SRC_RECORDS[release][2]},
        "synthetic_only": True,
        "match_rule": {"max_separation_m": BUFFER_M, "minimum_bidirectional_overlap": MIN_BIDIRECTIONAL_OVERLAP, "minimum_abs_endpoint_cosine": MIN_ABS_COS},
        "results": results,
        "model_input_approved": False,
        "original_source_bytes_observed": False,
        "source_file_sha256_verified": False,
        "scientific_validation_completed": False,
        "licensing_admitted": False,
        "real_world_geometry_processed": False,
        "neon_production_modified": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--synthetic-input", type=Path)
    args = p.parse_args(argv)
    if args.synthetic_input is None:
        p.print_help()
        return 2
    try:
        if args.synthetic_input.stat().st_size > MAX_FILE_BYTES:
            raise CrosswalkError("synthetic input too large")
        data = json.loads(args.synthetic_input.read_text(encoding="utf-8"), object_pairs_hook=strict_object, parse_constant=reject_constant)
        print(json.dumps(crosswalk(data), indent=2, sort_keys=True))
    except (OSError, UnicodeError, json.JSONDecodeError, CrosswalkError) as exc:
        p.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
