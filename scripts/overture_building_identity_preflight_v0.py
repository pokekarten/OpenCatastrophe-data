# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline, synthetic-testable Overture/local building crosswalk candidate gate.

Do not treat geometric overlap or syntactically valid UUID as a confirmed GERS
registry identity, an independent ground truth, actual insured TIV or model input.
No HTTP, SQL, raw-source persistence, population or insurance data is handled.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import math
from pathlib import Path
import re
import sys
from uuid import UUID

from shapely.geometry import shape

SCHEMA = "opencatastrophe-overture-building-crosswalk-preflight-v0"
MAX_INPUT_BYTES = 1_000_000
MAX_BUILDINGS_PER_SIDE = 100
MAX_COORDINATE_PAIRS = 4000
MIN_IOU = 0.75
RELEASE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})\.(\d+)\Z")


class CrosswalkError(ValueError):
    """Input is unsafe or does not satisfy the strict research-only contract."""


def _object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise CrosswalkError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _no_nonfinite(value):
    raise CrosswalkError(f"non-finite JSON number: {value}")


def _read(path):
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise CrosswalkError("oversized input")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object,
                      parse_constant=_no_nonfinite)


def _keys(obj, required, name):
    if type(obj) is not dict or set(obj) != set(required):
        raise CrosswalkError(f"{name}: wrong fields")


def _date(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise CrosswalkError(f"{name}: expected YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise CrosswalkError(f"{name}: invalid date") from exc


def _release(value):
    if type(value) is not str or not (m := RELEASE_PATTERN.fullmatch(value)):
        raise CrosswalkError("release must be an exact YYYY-MM-DD.N archive version")
    _date(m[1], "release")


def _text(value, name):
    if type(value) is not str or not 1 <= len(value) <= 128 or not value.strip():
        raise CrosswalkError(f"{name}: invalid text")
    return value


def _polygon_geometry(raw, name):
    _keys(raw, {"type", "coordinates"}, name)
    kind = raw["type"]
    if kind not in ("Polygon", "MultiPolygon"):
        raise CrosswalkError(f"{name}: only Polygon/MultiPolygon")
    polygons = [raw["coordinates"]] if kind == "Polygon" else raw["coordinates"]
    if type(polygons) is not list or not polygons:
        raise CrosswalkError(f"{name}: missing polygons")
    count = 0
    for rings in polygons:
        if type(rings) is not list or not rings:
            raise CrosswalkError(f"{name}: missing rings")
        for ring in rings:
            if type(ring) is not list or len(ring) < 4 or ring[0] != ring[-1]:
                raise CrosswalkError(f"{name}: open or short ring")
            for pair in ring:
                if type(pair) is not list or len(pair) != 2:
                    raise CrosswalkError(f"{name}: invalid coordinate pair")
                x, y = pair
                if any(type(v) not in (int, float) or not math.isfinite(v) for v in pair):
                    raise CrosswalkError(f"{name}: non-finite or nonnumeric coordinate")
                if not -180 <= x <= 180 or not -90 <= y <= 90:
                    raise CrosswalkError(f"{name}: coordinate outside EPSG:4326")
                count += 1
                if count > MAX_COORDINATE_PAIRS:
                    raise CrosswalkError(f"{name}: too many vertices")
    geom = shape(raw)
    if geom.is_empty or not geom.is_valid or geom.area <= 0:
        raise CrosswalkError(f"{name}: invalid or zero-area building geometry")
    xmin, ymin, xmax, ymax = geom.bounds
    if xmax - xmin > .2 or ymax - ymin > .2:
        raise CrosswalkError(f"{name}: oversized building or antimeridian geometry")
    return geom


def _buildings(rows, kind):
    if type(rows) is not list or not 1 <= len(rows) <= MAX_BUILDINGS_PER_SIDE:
        raise CrosswalkError(f"{kind}: invalid batch size")
    out = {}
    for row in rows:
        fields = {"local_id", "source_vintage", "geometry"} if kind == "local" else {"gers_id", "source_families", "geometry"}
        _keys(row, fields, kind)
        identifier = _text(row["local_id" if kind == "local" else "gers_id"], "id")
        if kind == "overture":
            try:
                if str(UUID(identifier)) != identifier:
                    raise ValueError("non-canonical UUID")
            except ValueError as exc:
                raise CrosswalkError("Overture ID is not canonical UUID; GERS registry status still unknown") from exc
            sources = row["source_families"]
            if type(sources) is not list or not sources or len(sources) > 12:
                raise CrosswalkError("missing bounded upstream source families")
            if len(set(sources)) != len(sources):
                raise CrosswalkError("duplicate upstream source family")
            for source in sources:
                _text(source, "source family")
        else:
            _date(row["source_vintage"], "local source vintage")
        if identifier in out:
            raise CrosswalkError(f"duplicate {kind} identifier")
        out[identifier] = (row, _polygon_geometry(row["geometry"], identifier))
    return out


def crosswalk(payload, *, expected_release):
    """Return conservative geometric *candidates*, never verified source links."""
    _keys(payload, {"schema", "overture_release", "geometry_crs", "local_source", "local_buildings", "overture_buildings"}, "payload")
    if payload["schema"] != SCHEMA or payload["geometry_crs"] != "EPSG:4326":
        raise CrosswalkError("wrong schema or non-4326 coordinates")
    _release(expected_release)
    _release(payload["overture_release"])
    if payload["overture_release"] != expected_release:
        raise CrosswalkError("mixed or moving Overture release")
    local_source = _text(payload["local_source"], "local source")
    locals_ = _buildings(payload["local_buildings"], "local")
    overtures = _buildings(payload["overture_buildings"], "overture")
    by_local = {x: [] for x in locals_}
    by_overture = {x: [] for x in overtures}
    for local_id, (_, lg) in locals_.items():
        for overture_id, (_, og) in overtures.items():
            if not lg.intersects(og):
                continue
            i_area = lg.intersection(og).area
            u_area = lg.union(og).area
            score = i_area / u_area
            if score >= MIN_IOU:
                by_local[local_id].append((overture_id, score))
                by_overture[overture_id].append(local_id)
    accepted = []
    ambiguous = []
    unmatched = []
    for local_id, edges in sorted(by_local.items()):
        if not edges:
            unmatched.append(local_id)
        elif len(edges) != 1 or len(by_overture[edges[0][0]]) != 1:
            ambiguous.append(local_id)
        else:
            oid, score = edges[0]
            overture_row = overtures[oid][0]
            accepted.append({"local_id": local_id, "overture_feature_id": oid,
                             "overlap_score": round(score, 6),
                             "shared_upstream_possible": local_source in overture_row["source_families"]})
    return {"schema": SCHEMA, "overture_release": expected_release,
            "local_source": local_source, "local_count": len(locals_), "overture_count": len(overtures),
            "one_to_one_geometric_candidates": accepted, "ambiguous_local_ids": ambiguous,
            "unmatched_local_ids": unmatched, "candidate_only": True,
            "gers_registry_membership_verified": False,
            "geometry_crs_evidence_verified": False,
            "independent_validation_approved": False,
            "raw_data_import_authorized": False, "insured_value_estimated": False,
            "model_input_approved": False,
            "note": "Polygon overlap is a geometric proxy; verify upstream IDs, rights, CRS evidence, source lineage and original bytes independently."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-release", required=True)
    args = parser.parse_args(argv)
    try:
        out = crosswalk(_read(args.input), expected_release=args.expected_release)
    except (CrosswalkError, OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
