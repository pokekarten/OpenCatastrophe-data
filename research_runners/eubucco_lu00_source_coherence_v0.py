#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Aggregate only: EUBUCCO LU00 geometry-vs-attribute source-label coherence.

This is NOT building identity, legal admission, or independent source proof.
Only a bounded, already downloaded LU00 original Parquet in memory. No network,
database, coordinates, building IDs, individual records, or value export.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

PARQUET_SHA256 = "d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c"
PROVENANCE = (
    "type_source", "subtype_source", "height_source",
    "floors_source", "construction_year_source",
)
COLUMNS = ("id", "region_id", "geometry_source", *PROVENANCE)
MAX_INPUT = 256 * 1024 * 1024
MAX_ROWS = 2_000_000
MAX_ROW_GROUPS = 10_000


class CrossSourceError(ValueError):
    """Fail closed rather than publish misleading provenance counts."""


def family(value):
    if value is None or value == "":
        return "missing"
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise CrossSourceError("invalid source family identifier")
    if value == "estimated":
        return "estimated"
    if value == "osm":
        return "osm"
    if value == "msft":
        return "msft"
    if value.startswith("gov-"):
        return "gov_unverified"
    return "other_unverified"


def classify(geometry, attribute):
    g, a = family(geometry), family(attribute)
    if a in ("missing", "estimated"):
        relation = a
    elif g == "missing":
        relation = "unresolved_geometry_origin"
    elif geometry == attribute:
        relation = "same_label_not_independent_proof"
    else:
        relation = "different_label_independence_unverified"
    return g, a, relation


def audit(path: Path, expected_sha256: str) -> dict:
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise CrossSourceError("explicit lowercase SHA256 required")
    # A trusted runner must supply an independently predeclared release SHA.
    # Unit tests may use synthetic source hashes; no input is admitted by this audit.
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT:
        raise CrossSourceError("original file must be regular, local and <=256 MiB")
    try:
        original = path.read_bytes()
    except OSError as exc:
        raise CrossSourceError("cannot read local source") from exc
    if (len(original) < 12 or len(original) > MAX_INPUT or
            original[:4] != b"PAR1" or original[-4:] != b"PAR1"):
        raise CrossSourceError("invalid or oversized Parquet original")
    actual_sha = hashlib.sha256(original).hexdigest()
    if actual_sha != expected_sha256:
        raise CrossSourceError("original source SHA256 mismatch")

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise CrossSourceError("optional pinned PyArrow not installed") from exc

    try:
        parquet = pq.ParquetFile(pa.BufferReader(original))
        meta = parquet.metadata
        if (not 1 <= meta.num_rows <= MAX_ROWS
                or not 1 <= meta.num_row_groups <= MAX_ROW_GROUPS):
            raise CrossSourceError("source row or group budget exceeded")
        if len(set(parquet.schema_arrow.names)) != len(parquet.schema_arrow.names):
            raise CrossSourceError("duplicate Parquet column name")
        if set(COLUMNS) - set(parquet.schema_arrow.names):
            raise CrossSourceError("mandatory geometry/attribute lineage columns absent")
        total = 0
        geometry_families = Counter()
        matrices = {column: Counter() for column in PROVENANCE}
        relationships = {column: Counter() for column in PROVENANCE}
        # Columnar batch iterator; no ID or geometry materialises or leaves process.
        for batch in parquet.iter_batches(batch_size=4096, columns=list(COLUMNS)):
            values = batch.to_pydict()
            for idx, geom in enumerate(values["geometry_source"]):
                if values["region_id"][idx] != "LU000":
                    raise CrossSourceError("unexpected regional code in LU00")
                ident = values["id"][idx]
                if not isinstance(ident, str) or not ident or len(ident) > 256:
                    raise CrossSourceError("invalid source ID")
                gf = family(geom)
                geometry_families[gf] += 1
                for attr in PROVENANCE:
                    _, af, relation = classify(geom, values[attr][idx])
                    matrices[attr][(gf, af)] += 1
                    relationships[attr][relation] += 1
                total += 1
        if total != meta.num_rows:
            raise CrossSourceError("decoded row count differs from metadata")
    except CrossSourceError:
        raise
    except Exception as exc:
        raise CrossSourceError("Parquet original could not be decoded safely") from exc

    # Fixed, small categorical outputs: never emit IDs, geometry, original
    # provider source labels, coordinates, or any sampled record.
    return {
        "schema_version": "eubucco-lu00-source-label-coherence-v0",
        "original_file_sha256": actual_sha,
        "original_file_bytes": len(original),
        "source": "eubucco.buildings.v0.2",
        "partition": "LU00",
        "source_region": "LU000",
        "rows": total,
        "geometry_families": dict(sorted(geometry_families.items())),
        "attribute_source_label_relations": {
            attr: dict(sorted(rels.items())) for attr, rels in sorted(relationships.items())
        },
        "source_family_matrices": {
            attr: [
                {"geometry_family": geom, "attribute_family": src, "count": n}
                for (geom, src), n in sorted(counts.items())
            ] for attr, counts in sorted(matrices.items())
        },
        "source_identity_established": False,
        "independent_from_luxembourg_act2023_established": False,
        "model_input_admitted": False,
        "commercial_reuse_and_redistribution_reviewed": False,
        "individual_records_exported": False,
        "warning": (
            "Label agreement is NOT upstream asset identity; different labels are NOT "
            "independent scientific ground truth. EUBUCCO gov labels may reference "
            "the same source family as Luxembourg ACT. No date, licence, geometry "
            "match, original ID crosswalk, insurance value or CAT loss is proven."
        ),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--sha256", required=True)
    args = p.parse_args(argv)
    try:
        result = audit(args.original, args.sha256)
    except (CrossSourceError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
